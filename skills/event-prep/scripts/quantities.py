"""Per-person quantity maths for event planning.

A port of the tables in ``references/quantities.md``. The reference is the
source of truth; this file exists so the arithmetic stops being done by hand
across a long planning session, where it demonstrably drifts.

Two design decisions worth knowing before using it:

**Everything returns a range, not a number.** The reference gives bands
(180-220 g of boneless meat per person, not 200), because the underlying
reality is a band. Collapsing that to a single figure invents precision the
domain does not have, and a made-up midpoint is exactly the kind of number
that later gets defended as though it were measured. Callers see the band and
decide where in it to sit.

**The traps raise rather than guess.** Where the reference says a quantity is
ambiguous - bone-in versus boneless above all - passing the ambiguous form is
an error, not a silent assumption. See ``MEAT``.

Python 3, standard library only.
"""

from __future__ import annotations

import math
from collections import namedtuple
from datetime import datetime

__all__ = [
    "Range",
    "Meals",
    "meal_plan",
    "meat_kg",
    "edible_from_bone_in",
    "bone_in_equivalent",
    "cooked_from_raw",
    "starch_kg",
    "dips_kg",
    "pita_pieces",
    "salad_veg_kg",
    "breakfast_items",
    "drinks_count",
    "mixer_bottles",
    "ice_kg",
    "water_litres",
    "appetite_factor",
]


class Range(namedtuple("Range", "low high")):
    """A low-high band. Both ends are real; neither is 'the answer'."""

    __slots__ = ()

    def __str__(self) -> str:
        if self.low == self.high:
            return _trim(self.low)
        return f"{_trim(self.low)}-{_trim(self.high)}"

    def scaled(self, factor: float) -> "Range":
        return Range(self.low * factor, self.high * factor)

    def rounded(self, places: int = 1) -> "Range":
        return Range(round(self.low, places), round(self.high, places))


def _trim(value: float) -> str:
    """Format without trailing zeros: 5.0 -> '5', 5.25 -> '5.25'."""
    return f"{value:.10g}"


def _band(value, unit_low, unit_high=None) -> Range:
    if unit_high is None:
        unit_high = unit_low
    return Range(value * unit_low, value * unit_high)


# --------------------------------------------------------------- meat
# references/quantities.md, "Meat" - per person, per main meal, RAW weight,
# in grams.
MEAT = {
    "boneless": (180, 220),      # thighs, breast, steak
    "bone_in": (280, 320),       # drumsticks, wings, chops
    "grilled": (180, 200),       # skewered, with substantial sides
    "ground": (150, 150),        # tacos, kofta, ragu
    "whole_fish": (350, 400),
}

BONE_FRACTION = 0.30             # bone-in chicken runs ~30% bone
COOKED_YIELD = (0.70, 0.75)      # of raw, roasted or grilled


def meat_kg(headcount: int, cut: str, meals: int = 1) -> Range:
    """Raw meat in kilograms for ``headcount`` people over ``meals`` main meals.

    ``cut`` must be one of ``MEAT``. The bone-in and boneless figures are
    deliberately different rates rather than one rate plus a correction,
    because they are not the same quantity - see ``edible_from_bone_in``.

    >>> str(meat_kg(26, "grilled").rounded(2))
    '4.68-5.2'
    """
    if cut not in MEAT:
        raise ValueError(
            f"unknown cut {cut!r}. Use one of: {', '.join(sorted(MEAT))}. "
            "If someone gave you a weight without saying which, that is a "
            "question, not a value - see the bone-in correction."
        )
    if headcount < 1 or meals < 1:
        raise ValueError("headcount and meals must both be at least 1")
    low, high = MEAT[cut]
    return _band(headcount * meals / 1000, low, high)


def edible_from_bone_in(raw_kg: float) -> float:
    """Edible meat from a bone-in raw weight.

    The single most common error in this domain. Five kilos of drumsticks is
    3.5 kg of meat, which is 135 g each across 26 people - thin for a main.

    >>> edible_from_bone_in(5)
    3.5
    """
    if raw_kg < 0:
        raise ValueError("raw_kg must not be negative")
    return raw_kg * (1 - BONE_FRACTION)


def bone_in_equivalent(boneless_kg: float) -> float:
    """Bone-in raw weight delivering the same edible meat as ``boneless_kg``.

    The inverse correction, for when a plan substitutes one for the other.

    >>> round(bone_in_equivalent(3.5), 2)
    5.0
    """
    if boneless_kg < 0:
        raise ValueError("boneless_kg must not be negative")
    return boneless_kg / (1 - BONE_FRACTION)


# ------------------------------------------------- sides, dips, breakfast
# references/quantities.md, "Sides and starches" / "Mezze, dips and bread",
# per person, in grams unless noted.
STARCH = {
    "potatoes": (250, 280),      # as the main starch
    "rice_dry": (75, 90),
    "pasta_dry": (100, 100),
    "fries": (70, 80),           # as a side among many
}

DIPS = {
    "dip": (60, 80),             # hummus, baba ghannouj
    "toum": (40, 50),            # garlic sauce as a dip
}

PITA_PIECES = (2, 3)
SALAD_VEG = (150, 200)           # total vegetable per person, shared salad

# references/quantities.md, "Breakfast" - per person, per morning.
BREAKFAST = {
    "items_total": (1.5, 2),     # pastry + egg + fruit etc.
    "eggs_centrepiece": (1, 1.5),
    "eggs_with_bread": (0.5, 0.7),
    "pastry": (0.7, 1),          # manoushe, croissant or similar
}


def starch_kg(headcount: int, kind: str, meals: int = 1) -> Range:
    """Dry or raw starch in kilograms. ``kind`` must be one of ``STARCH``."""
    if kind not in STARCH:
        raise ValueError(f"unknown starch {kind!r}. Use one of: {', '.join(sorted(STARCH))}")
    if headcount < 1 or meals < 1:
        raise ValueError("headcount and meals must both be at least 1")
    low, high = STARCH[kind]
    return _band(headcount * meals / 1000, low, high)


def dips_kg(headcount: int, kind: str = "dip", occasions: int = 1) -> Range:
    """Dips in kilograms, per occasion.

    A sauce used both as a dip for grilled meat *and* as a table sauce at a
    second meal is two occasions, not one - which is why ``occasions`` exists
    rather than being folded into the rate.
    """
    if kind not in DIPS:
        raise ValueError(f"unknown dip {kind!r}. Use one of: {', '.join(sorted(DIPS))}")
    if headcount < 1 or occasions < 1:
        raise ValueError("headcount and occasions must both be at least 1")
    low, high = DIPS[kind]
    return _band(headcount * occasions / 1000, low, high)


def breakfast_items(headcount: int, mornings: float, kind: str = "items_total") -> Range:
    """Breakfast items over ``mornings``. Fractional mornings are expected -
    a departure morning is a half. See ``meal_plan``."""
    if kind not in BREAKFAST:
        raise ValueError(f"unknown breakfast item {kind!r}. Use one of: {', '.join(sorted(BREAKFAST))}")
    if headcount < 1 or mornings <= 0:
        raise ValueError("headcount must be at least 1 and mornings positive")
    low, high = BREAKFAST[kind]
    return _band(headcount * mornings, low, high)


def pita_pieces(headcount: int, occasions: int = 1) -> Range:
    """Flatbread or pita pieces, per occasion."""
    if headcount < 1 or occasions < 1:
        raise ValueError("headcount and occasions must both be at least 1")
    return _band(headcount * occasions, *PITA_PIECES)


def salad_veg_kg(headcount: int) -> Range:
    """Total vegetable for a shared salad alongside other food, in kilograms."""
    if headcount < 1:
        raise ValueError("headcount must be at least 1")
    return _band(headcount / 1000, *SALAD_VEG)


def cooked_from_raw(raw_kg: float) -> Range:
    """Cooked weight from raw, for roasted or grilled meat.

    Separate from the bone-in correction and often confused with it: yield is
    water loss during cooking, bone is never edible at all. A bone-in weight
    pays both.

    >>> str(cooked_from_raw(5).rounded(2))
    '3.5-3.75'
    """
    if raw_kg < 0:
        raise ValueError("raw_kg must not be negative")
    return _band(raw_kg, *COOKED_YIELD)


# ------------------------------------------------------------- drinks
# references/quantities.md, "Drinks" - per person, per night.
DRINKS_PER_NIGHT = {
    "party": (3, 4),
    "dinner": (2, 3),
}

DRINKING_FRACTION = 0.85         # some are driving or don't drink


def drinks_count(headcount: int, nights: int, style: str = "party",
                 drinking_fraction: float = DRINKING_FRACTION) -> Range:
    """Total drinks poured across the event.

    Applies the ~85% drinking fraction by default; pass ``drinking_fraction=1``
    for a group where everyone drinks.
    """
    if style not in DRINKS_PER_NIGHT:
        raise ValueError(f"unknown style {style!r}. Use one of: {', '.join(sorted(DRINKS_PER_NIGHT))}")
    if not 0 < drinking_fraction <= 1:
        raise ValueError("drinking_fraction must be in (0, 1]")
    if headcount < 1 or nights < 1:
        raise ValueError("headcount and nights must both be at least 1")
    low, high = DRINKS_PER_NIGHT[style]
    return _band(headcount * nights * drinking_fraction, low, high)


def mixer_bottles(spirit_litres: float, mixer_parts: float, spirit_parts: float,
                  bottle_ml: int = 750) -> dict:
    """Bottles of mixer required to match a fixed-ratio cocktail.

    **Match the mixer to the spirit or you strand one of them.** A 3:2 spritz
    means six litres of aperitif needs exactly nine litres of sparkling, which
    is twelve 750 ml bottles. Buy fewer and you are holding aperitif you
    cannot serve.

    Returns the exact litres needed, the whole bottles to buy, and the
    shortfall or surplus that rounding creates - because the rounding is the
    part that strands stock, and it is invisible if only the bottle count is
    reported.

    >>> r = mixer_bottles(6, mixer_parts=3, spirit_parts=2)
    >>> r["bottles"], r["exact_litres"], r["exact"]
    (12, 9.0, True)
    """
    if spirit_litres <= 0:
        raise ValueError("spirit_litres must be positive")
    if mixer_parts <= 0 or spirit_parts <= 0:
        raise ValueError("ratio parts must both be positive")
    if bottle_ml <= 0:
        raise ValueError("bottle_ml must be positive")

    # Work in millilitres and quench float noise before rounding up. Computing
    # the quotient directly in litres makes an exactly-divisible order look
    # like a rounding case: 3.2 L at 3:2 into 600 ml bottles gives a quotient
    # of 8.000000000000002, which ceil() turns into 9 bottles and a fabricated
    # 0.6 L surplus. Only 750 ml, being exactly representable, escaped it.
    exact_ml = spirit_litres * 1000 * mixer_parts / spirit_parts
    quotient = round(exact_ml / bottle_ml, 6)
    bottles = math.ceil(quotient)
    supplied_ml = bottles * bottle_ml
    return {
        "exact_litres": round(exact_ml / 1000, 4),
        "bottles": bottles,
        "supplied_litres": round(supplied_ml / 1000, 4),
        "surplus_litres": round((supplied_ml - exact_ml) / 1000, 4),
        "exact": bottles == quotient,
    }


# ---------------------------------------------------------- ice and water
# references/quantities.md, "Ice" and "Water" - per person, per day.
ICE_KG = {
    "cocktails": (1.0, 1.5),     # what actually runs out
    "cans": (0.5, 0.5),          # mostly beer and cans
}
ICE_FOOD_COLD = (1.0, 1.0)       # additional, when there is no fridge at all

WATER_LITRES = {
    "drinking": (2, 3),
    "drinking_hot": (4, 5),
    "cooking": (1, 2),
    "washing_up": (2, 4),
    "hygiene": (1, 2),
}
WATER_PLANNING = (6, 6)          # summer camp planning figure
WATER_FLOOR = (3, 3)             # with a tap on site for washing


def ice_kg(headcount: int, days: float, profile: str = "cocktails",
           no_fridge: bool = False) -> Range:
    """Ice in kilograms.

    With ``no_fridge=True`` the food cold-chain figure is added on top of the
    drinks figure - without a fridge, ice stops being a drinks item and
    becomes the cold chain itself.
    """
    if profile not in ICE_KG:
        raise ValueError(f"unknown profile {profile!r}. Use one of: {', '.join(sorted(ICE_KG))}")
    if headcount < 1 or days <= 0:
        raise ValueError("headcount must be at least 1 and days positive")
    low, high = ICE_KG[profile]
    total = _band(headcount * days, low, high)
    if no_fridge:
        extra = _band(headcount * days, *ICE_FOOD_COLD)
        total = Range(total.low + extra.low, total.high + extra.high)
    return total


def water_litres(headcount: int, days: float, tap_on_site: bool = False,
                 hot_weather: bool = False, itemised: bool = False) -> Range:
    """Drinking, cooking and washing water in litres.

    The heaviest line on any event without a tap, and the one most often
    missing altogether. **A litre is a kilogram** - 33 people over 3 days is
    594 L and 594 kg, which is more than most vehicle payloads. Check the
    weight against the vehicles before treating the number as settled.

    By default this returns the reference's *planning figure* - a single
    recommended rate rather than a band. That figure deliberately sits at the
    low end of the itemised component sum, because nobody uses the top of
    every category at once. Pass ``itemised=True`` for the component band,
    which is the honest worst case.

    ``tap_on_site`` means washing and hygiene come from the tap, so only
    drinking and cooking water has to be provided.

    >>> str(water_litres(33, 3))
    '594'
    >>> str(water_litres(33, 3, itemised=True))
    '594-1089'
    """
    if headcount < 1 or days <= 0:
        raise ValueError("headcount must be at least 1 and days positive")

    drinking = "drinking_hot" if hot_weather else "drinking"

    if itemised:
        keys = [drinking, "cooking"]
        if not tap_on_site:
            keys += ["washing_up", "hygiene"]
        low = sum(WATER_LITRES[k][0] for k in keys)
        high = sum(WATER_LITRES[k][1] for k in keys)
        return _band(headcount * days, low, high)

    low, high = WATER_FLOOR if tap_on_site else WATER_PLANNING
    if hot_weather:
        bump = WATER_LITRES["drinking_hot"][0] - WATER_LITRES["drinking"][0]
        low, high = low + bump, high + bump
    return _band(headcount * days, low, high)


# ------------------------------------------------------- multiplication
Meals = namedtuple("Meals", "nights dinners breakfasts late_first_dinner")

EVENING_ARRIVAL_HOUR = 18        # an arrival after 6 PM means dinner is first
BREAKFAST_HOUR = 9               # arrive before this and that morning counts
DEPARTURE_MORNING_WEIGHT = 0.5   # coffee and something standing up


def meal_plan(arrive: datetime, depart: datetime) -> Meals:
    """Which meals actually exist, from arrival and departure times.

    **Meal count comes from times, not from day count.** Dinners are nights.
    Breakfasts are the mornings people are awake and present: one per night
    stayed, plus the arrival morning if they got there before breakfast, and
    the departure morning counts as a half.

    ``late_first_dinner`` flags an arrival after 6 PM: the first meal is dinner
    and it lands late, so budget about 90 minutes from arrival to eating once
    unloading and setup are counted, and put no-preparation food out at once.

    >>> from datetime import datetime
    >>> meal_plan(datetime(2026, 8, 14, 19, 0), datetime(2026, 8, 17, 10, 0))
    Meals(nights=3, dinners=3, breakfasts=2.5, late_first_dinner=True)
    >>> meal_plan(datetime(2026, 8, 14, 7, 0), datetime(2026, 8, 17, 10, 0))
    Meals(nights=3, dinners=3, breakfasts=3.5, late_first_dinner=False)
    """
    if depart <= arrive:
        raise ValueError("depart must be after arrive")

    nights = (depart.date() - arrive.date()).days
    if nights < 1:
        raise ValueError("an event with no overnight stay has no dinners to count")

    # Dinners = nights. The day you leave has no dinner in it.
    dinners = nights

    # One morning per night stayed, minus half for the departure morning,
    # plus the arrival morning if they arrived early enough to eat it.
    breakfasts = nights - DEPARTURE_MORNING_WEIGHT
    if arrive.hour < BREAKFAST_HOUR:
        breakfasts += 1

    return Meals(nights=nights, dinners=dinners, breakfasts=breakfasts,
                 late_first_dinner=arrive.hour >= EVENING_ARRIVAL_HOUR)


def appetite_factor(day: int) -> Range:
    """Consumption multiplier for a given day, 1-indexed.

    Consumption drops noticeably after the first day - roughly 15-20% by day
    three. Scale the last day's meals down, not up.

    >>> str(appetite_factor(3))
    '0.8-0.85'
    """
    if day < 1:
        raise ValueError("day is 1-indexed")
    if day == 1:
        return Range(1.0, 1.0)
    if day == 2:
        return Range(0.9, 0.925)
    return Range(0.80, 0.85)
