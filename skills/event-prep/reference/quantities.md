# Quantities

Per-person maths for converting a headcount into amounts to buy.

**These tables are ported to `scripts/quantities.py` — run it rather than
applying them by hand.** This file stays the source of truth: if the two ever
disagree, this file is right and the script has drifted. Its test suite asserts
every constant below, so that disagreement should fail loudly rather than
silently. `scripts/build_event.py` calls it for you - see "3. Build" in `SKILL.md`.

**Contents:** Meat · Sides and starches · Mezze, dips and bread · Salads ·
Breakfast · Drinks · Ice · Water · Multiplication rules · Appetite decay ·
Pack sizes · Physical footprint

---

## Meat

Per person, per main meal, **raw weight**:

| Cut | Amount |
|---|---|
| Boneless (thighs, breast, steak) | 180–220 g |
| **Bone-in (drumsticks, wings, chops)** | **280–320 g** |
| Grilled/skewered, with substantial sides | 180–200 g |
| Ground (tacos, kofta, ragù) | 150 g |
| Whole fish | 350–400 g |

**The bone-in correction is the single most common error.** Bone-in chicken runs
about 30% bone. Five kilos of drumsticks is 3.5 kg of edible meat — 135 g each
across 26 people, which is thin for a main. Five kilos of boneless is 5 kg of
meat. When someone gives a weight, establish which they mean before scaling.

It is also the clearest example of a trap this domain is full of — two quantities
that share a name or a unit, mean different things, and break the plan somewhere
unrelated to where the mistake was made. Bone-in vs boneless
meat is the food case; `logistics.md` has the electrical ones (watts vs
watt-hours, mAh vs watt-hours). Treat an ambiguous unit as a question, not a value.

Boneless also eats *smaller* than bone-in at the same weight: no picking, no
second piece, less mess. People stop sooner.

Cooked yield is roughly 70–75% of raw for roasted or grilled meat.

## Sides and starches

| Item | Per person |
|---|---|
| Potatoes as the main starch | 250–280 g |
| Rice, dry | 75–90 g |
| Pasta, dry | 100 g |
| Frozen fries as a side among many | 70–80 g |
| Tortillas | 3 |

## Mezze, dips and bread

| Item | Per person, per occasion |
|---|---|
| Dips (hummus, baba ghannouj) | 60–80 g |
| Garlic sauce / toum as a dip | 40–50 g |
| Flatbread or pita | 2–3 pieces |

Toum used both as a dip for grilled meat *and* as a table sauce at a second meal
needs roughly double what a single mezze spread would.

Serve dips in **several small bowls, not one large one.** At a table of 26,
people won't reach across for it, and half the batch goes untouched.

## Salads

For a shared salad alongside other food, roughly 150–200 g of total vegetable per
person. A chopped salad for 26 is about 4 heads of romaine, 2 kg tomatoes, 1.5 kg
cucumber.

Dress immediately before serving, never in advance.

## Breakfast

Self-serve breakfast is a **spread, not a plate each.** Nobody eats a full
breakfast four mornings running, and a mid-afternoon main meal compresses it
further.

| Item | Per person, per morning |
|---|---|
| Total items (pastry + egg + fruit etc.) | 1.5–2 |
| Eggs, when eggs are the centrepiece | 1–1.5 |
| Eggs, when there's bread or pastry alongside | 0.5–0.7 |
| Pastry, manoushe, or similar | 0.7–1 |

**Late nights push breakfast later and shrink it.** If people wake at 10 or 11
and eat again at 3, breakfast is coffee and something in the hand. Buy
accordingly, and expect eggs to go largely unused on the middle days.

**Departure mornings need almost nothing** — coffee, something to eat standing
up, leftovers.

## Drinks

Per person, per night:

| Event type | Drinks |
|---|---|
| Party | 3–4 |
| Dinner-focused | 2–3 |

Assume roughly 85% of the headcount drinks; some are driving or don't.

Conversions:

| | |
|---|---|
| Spritz | 60 ml aperitif + 90 ml sparkling + soda |
| Standard cocktail | 50–60 ml spirit |
| 750 ml bottle | 12–15 cocktails |
| 1 L bottle | 16–20 cocktails |
| Case of 24 | 24 |

**Match the mixer to the spirit, or you strand one of them.** A 3:2 spritz means
six litres of aperitif needs exactly twelve 750 ml bottles of sparkling. Buy
fewer and you're left holding aperitif you can't serve. Do this arithmetic
explicitly whenever a cocktail has a fixed ratio.

**Over-buying alcohol is low-risk in a way over-buying food isn't.** Unopened
bottles keep indefinitely and are often returnable. Warehouse or discount outlets
may sell final — check before relying on returns.

## Ice

**This is what actually runs out.** 1–1.5 kg per person per day for a
cocktail-heavy event, 0.5 kg if it's mostly beer and cans. Spritz served over a
full glass of ice consumes far more than people budget for.

Buy enough for the first two days and **plan a mid-event restock**. Check whether
the venue has icemakers before buying — two working icemakers changes the number
substantially.

With no fridge, ice stops being a drinks item and becomes the cold chain itself —
budget roughly **1 kg per person per day for food cold on top of the drinks
figure**, use block rather than cubed, and see `camping-and-festivals.md`.

## Water

At a building this is free and invisible. Without one it is **the heaviest line
on the list**, and the most commonly forgotten entirely.

| Use | Litres per person per day |
|---|---|
| Drinking, moderate summer | 2–3 |
| Drinking, hot weather or exertion | 4–5 |
| Cooking, coffee, rinsing | 1–2 |
| Washing up | 2–4 |
| Hands, teeth, basic hygiene | 1–2 |
| **Planning figure, summer camp** | **6** |
| Floor, if there's a tap on site for washing | 3 |

**Do the weight, always.** 33 people over 3 days at 6 L is 594 L — and 594 kg,
about thirty 20 L jerry cans. That is more than most vehicle payloads, which is
why water is asked about before the menu rather than after: no water on site
means a drier menu, a smaller group, or a vehicle that carries nothing else.

**Ask whether there is water on site, whether it is potable, and how far away it
is.** Non-potable still covers washing up and hands, which is over half the
total. A standpipe with a twenty-minute queue is a cost that lands on whoever is
cooking.

Water is unusually easy to design down: one-pot meals cut washing-up more than
any other choice, food chopped at home carries no rinse water into the field, and
a three-basin wash-up uses a fraction of what running water does.

## Multiplication rules

- **Dinners = nights.** Not days.
- **Breakfasts = mornings people are actually awake and present.** An evening
  arrival removes one. A departure morning is a half. **Operationally: an
  arrival before 9 AM catches that morning's breakfast; later doesn't** — the
  cutoff is what makes this countable rather than a judgement call each time.
- **An arrival after 6 PM means the first meal is dinner, and it lands late** —
  budget 90 minutes from arrival to eating, once unloading and setup are counted.
  Put no-preparation food out immediately.
- Never carry a per-day figure into a consolidated total without multiplying it.
  Check any inherited plan for exactly this.

## Appetite decay

Consumption drops noticeably after the first day — roughly 15–20% by day three.
People snack, sleep late, and drink instead of eating. Scale the last day's meals
down, not up.

| Day | Multiplier |
|---|---|
| 1 | 1.0 |
| 2 | 0.90–0.925 |
| 3 and after | 0.80–0.85 |

**Day 2 is interpolated, not observed.** The 15–20% figure is a day-three
observation; the middle day is the straight line between them and should be the
first thing corrected once a real event is measured. Day 4 doesn't keep falling —
the curve flattens once people have settled into eating less.

The exception is a mid-afternoon main meal, which carries more weight than an
evening one because it's often the only substantial meal of the day.

## Pack sizes force the numbers

Warehouse quantities are not arbitrary. Eggs come in flats of 30, so 200 becomes
210. Avocados come in bags of five and ripen together — buy two-thirds firm.
Bread and pastry come in multipacks. State the pack count, not just the item
count, or the shopper has to work it out in the aisle.

**Buy herbs no more than a day or two ahead.** Parsley bought Monday will not
survive to Sunday.

## Every quantity has a physical footprint

A quantity is not finished when it has a price. **Ask where it goes, what keeps
it cold, and who carries it.** Those three questions are where plans actually
break, and a costed list cannot answer any of them.

The characteristic failure: a number arrives, **the budget barely moves, and the
real consequence lands somewhere nobody was looking.** In the source event, 336
cans of drink came to $354 — under 4% of the weekend — and about 143 kg,
competing for fridge shelves with 14.5 kg of meat, 7 kg of dips, 1 kg of labneh
and 3 kg of salad. Cold, not money, turned out to be the binding constraint on
the whole event, and nothing in this file had a column for it.

Carry three attributes alongside every significant line:

| Attribute | Decides |
|---|---|
| **Mass or volume** | Vehicles, and whether one trip is one trip |
| **Needs cold** | Fridge, freezer, cooler or nothing — all competing for the same shelves |
| **Which site** | A quantity is always *somewhere*. See multi-site in `logistics.md` |

What that surfaces, none of it visible from a priced list:

- **Vehicle count.** 240 beers, 96 hard seltzers and 90 kg of ice do not fit in
  one car alongside luggage for a weekend. In the source event two vehicles was
  noticed by a person, not derived from the plan.
- **Fridge contention.** Everything needing cold competes for a volume nobody
  measured. Total it before arrival and decide what stays out — most cans do.
- **What cold means at each site.** A cooler outdoors is not a fridge. An
  electric cooler is a fridge, and also a sustained electrical load that runs
  while everyone is asleep — see `logistics.md`.
- **Who carries it.** For a second site, load-in is a scheduled task with a name
  on it, not something that happens spontaneously.

**Drinks are the usual offender**: cheap per unit, bought in bulk, heavy, and
mostly needing to be cold — every attribute that makes footprint bite at once.
Ice is the second, and worse: it is the one line that is *purely* footprint, has
no substitute, and melts.
