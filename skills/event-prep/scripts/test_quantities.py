"""Tests for quantities.py.

Three kinds of test here, and the third is the point:

1. **Constants match the reference.** If ``references/quantities.md`` and this
   module ever disagree, the module is wrong. These tests fail loudly rather
   than letting the port drift from its source.
2. **The reference's own worked examples.** The numbers the reference quotes in
   prose — the bone-in 5 kg, the 3:2 spritz, the 594 L — are reproduced here so
   that prose stays true. This is not exhaustive over the whole document; it
   covers the worked examples, not every figure mentioned in passing.
3. **The source event, as regression.** Real quantities from the August 2026
   chalet weekend, checked against what the script says they should have been.
   Where the event sat outside the band, the test asserts *that* - the
   disagreement is a finding, not a failure, and pinning it stops a future
   edit quietly "fixing" the script to match the event.

Run: ``python -m unittest discover skill/scripts`` or ``python test_quantities.py``
"""

import doctest
import unittest
from datetime import datetime

import quantities as q


# The source event: 33 guests (26 regular, 7 vegan), Fri 14 - Mon 17 Aug 2026.
GUESTS = 33
EATERS = 26          # the non-vegan count most dishes were scaled to
ARRIVE = datetime(2026, 8, 14, 19, 0)
DEPART = datetime(2026, 8, 17, 10, 0)


class TestRange(unittest.TestCase):
    def test_formats_without_trailing_zeros(self):
        self.assertEqual(str(q.Range(5.0, 5.0)), "5")
        self.assertEqual(str(q.Range(4.68, 5.2)), "4.68-5.2")
        self.assertEqual(str(q.Range(0.8, 0.85)), "0.8-0.85")

    def test_scaled_and_rounded(self):
        self.assertEqual(q.Range(2.0, 4.0).scaled(0.5), q.Range(1.0, 2.0))
        self.assertEqual(q.Range(4.68, 5.24).rounded(1), q.Range(4.7, 5.2))


class TestConstantsMatchReference(unittest.TestCase):
    """references/quantities.md is the source of truth. Guard the port."""

    def test_meat_rates(self):
        self.assertEqual(q.MEAT["boneless"], (180, 220))
        self.assertEqual(q.MEAT["bone_in"], (280, 320))
        self.assertEqual(q.MEAT["grilled"], (180, 200))
        self.assertEqual(q.MEAT["ground"], (150, 150))
        self.assertEqual(q.MEAT["whole_fish"], (350, 400))
        self.assertEqual(q.BONE_FRACTION, 0.30)

    def test_starch_dip_and_breakfast_rates(self):
        self.assertEqual(q.STARCH["potatoes"], (250, 280))
        self.assertEqual(q.STARCH["rice_dry"], (75, 90))
        self.assertEqual(q.STARCH["pasta_dry"], (100, 100))
        self.assertEqual(q.STARCH["fries"], (70, 80))
        self.assertEqual(q.DIPS["dip"], (60, 80))
        self.assertEqual(q.DIPS["toum"], (40, 50))
        self.assertEqual(q.PITA_PIECES, (2, 3))
        self.assertEqual(q.SALAD_VEG, (150, 200))
        self.assertEqual(q.COOKED_YIELD, (0.70, 0.75))
        self.assertEqual(q.BREAKFAST["items_total"], (1.5, 2))
        self.assertEqual(q.BREAKFAST["eggs_centrepiece"], (1, 1.5))
        self.assertEqual(q.BREAKFAST["eggs_with_bread"], (0.5, 0.7))
        self.assertEqual(q.BREAKFAST["pastry"], (0.7, 1))

    def test_drink_ice_and_water_rates(self):
        self.assertEqual(q.DRINKS_PER_NIGHT["party"], (3, 4))
        self.assertEqual(q.DRINKS_PER_NIGHT["dinner"], (2, 3))
        self.assertEqual(q.DRINKING_FRACTION, 0.85)
        self.assertEqual(q.ICE_KG["cocktails"], (1.0, 1.5))
        self.assertEqual(q.ICE_KG["cans"], (0.5, 0.5))
        self.assertEqual(q.ICE_FOOD_COLD, (1.0, 1.0))
        self.assertEqual(q.WATER_PLANNING, (6, 6))
        self.assertEqual(q.WATER_FLOOR, (3, 3))

    def test_every_water_component_individually(self):
        """Summed assertions let two rows swap without failing. The audit
        demonstrated exactly that, so each row is pinned to the table."""
        self.assertEqual(q.WATER_LITRES["drinking"], (2, 3))
        self.assertEqual(q.WATER_LITRES["drinking_hot"], (4, 5))
        self.assertEqual(q.WATER_LITRES["cooking"], (1, 2))
        self.assertEqual(q.WATER_LITRES["washing_up"], (2, 4))
        self.assertEqual(q.WATER_LITRES["hygiene"], (1, 2))

    def test_meal_plan_thresholds(self):
        self.assertEqual(q.DEPARTURE_MORNING_WEIGHT, 0.5)
        self.assertEqual(q.BREAKFAST_HOUR, 9)
        self.assertEqual(q.EVENING_ARRIVAL_HOUR, 18)


class TestBoneInCorrection(unittest.TestCase):
    """The single most common error in the domain."""

    def test_five_kilos_of_drumsticks_is_three_and_a_half_of_meat(self):
        self.assertAlmostEqual(q.edible_from_bone_in(5), 3.5)

    def test_thin_for_a_main_across_26(self):
        # The reference's own worked example: 3.5 kg over 26 people is 135 g each.
        grams_each = q.edible_from_bone_in(5) * 1000 / 26
        self.assertAlmostEqual(grams_each, 134.6, places=1)
        self.assertLess(grams_each, q.MEAT["boneless"][0],
                        "135 g is below the boneless band - that is the point")

    def test_inverse_round_trips(self):
        self.assertAlmostEqual(q.bone_in_equivalent(3.5), 5.0)
        self.assertAlmostEqual(q.edible_from_bone_in(q.bone_in_equivalent(4.2)), 4.2)

    def test_ambiguous_cut_is_an_error_not_a_guess(self):
        with self.assertRaises(ValueError) as ctx:
            q.meat_kg(26, "chicken")
        self.assertIn("question, not a value", str(ctx.exception))


class TestMealPlan(unittest.TestCase):
    """Meal count comes from times, not day count."""

    def test_source_event(self):
        plan = q.meal_plan(ARRIVE, DEPART)
        self.assertEqual(plan.nights, 3)
        self.assertEqual(plan.dinners, 3)
        self.assertEqual(plan.breakfasts, 2.5)

    def test_evening_arrival_has_no_arrival_day_breakfast(self):
        evening = q.meal_plan(ARRIVE, DEPART)
        morning = q.meal_plan(datetime(2026, 8, 14, 7, 0), DEPART)
        self.assertEqual(morning.breakfasts - evening.breakfasts, 1.0)

    def test_departure_morning_is_a_half(self):
        plan = q.meal_plan(datetime(2026, 8, 14, 19, 0), datetime(2026, 8, 15, 10, 0))
        self.assertEqual(plan.nights, 1)
        self.assertEqual(plan.breakfasts, 0.5)

    def test_rejects_reversed_and_same_day(self):
        with self.assertRaises(ValueError):
            q.meal_plan(DEPART, ARRIVE)
        with self.assertRaises(ValueError):
            q.meal_plan(datetime(2026, 8, 14, 9, 0), datetime(2026, 8, 14, 23, 0))


class TestMixerRatios(unittest.TestCase):
    """Match the mixer to the spirit or you strand one of them."""

    def test_reference_worked_example(self):
        # "A 3:2 spritz means six litres of aperitif needs exactly twelve
        # 750 ml bottles of sparkling."
        r = q.mixer_bottles(6, mixer_parts=3, spirit_parts=2, bottle_ml=750)
        self.assertEqual(r["exact_litres"], 9.0)
        self.assertEqual(r["bottles"], 12)
        self.assertTrue(r["exact"])
        self.assertEqual(r["surplus_litres"], 0.0)

    def test_source_event_bottle_order(self):
        # The LIVE order: 6 x 1 L Aperol against 12 x 750 ml Prosecco = 9 L.
        # Exactly 3:2. (The order was halved from 10/20 late in planning; these
        # tests pinned the superseded figures for a day, which is precisely the
        # drift they exist to prevent — hence the live figures now.)
        r = q.mixer_bottles(6, mixer_parts=3, spirit_parts=2, bottle_ml=750)
        self.assertEqual(r["bottles"], 12)
        self.assertTrue(r["exact"], "the real order matched the ratio deliberately")

    def test_the_750ml_aperol_trap(self):
        # The open question on the live order: at 750 ml rather than 1 L the
        # aperitif volume drops and the Prosecco no longer matches.
        litre_format = q.mixer_bottles(6, 3, 2)["bottles"]
        small_format = q.mixer_bottles(6 * 0.75, 3, 2)["bottles"]
        self.assertEqual(litre_format, 12)
        self.assertEqual(small_format, 9)
        self.assertEqual(litre_format - small_format, 3,
                         "3 spare Prosecco if the Aperol turns out to be 750 ml")

    def test_rounding_surplus_is_reported(self):
        r = q.mixer_bottles(5, mixer_parts=3, spirit_parts=2, bottle_ml=750)
        self.assertEqual(r["exact_litres"], 7.5)
        self.assertEqual(r["bottles"], 10)
        self.assertTrue(r["exact"])
        r2 = q.mixer_bottles(4, mixer_parts=3, spirit_parts=2, bottle_ml=750)
        self.assertEqual(r2["exact_litres"], 6.0)
        self.assertEqual(r2["bottles"], 8)

    def test_rejects_nonsense(self):
        for bad in [(0, 3, 2), (6, 0, 2), (6, 3, 0)]:
            with self.assertRaises(ValueError):
                q.mixer_bottles(*bad)
        with self.assertRaises(ValueError):
            q.mixer_bottles(6, 3, 2, bottle_ml=0)

    def test_non_750ml_formats_do_not_round_up_on_float_noise(self):
        """Regression. Computing the quotient in litres made exactly-divisible
        orders look like rounding cases: 3.2 L at 3:2 into 600 ml gave a
        quotient of 8.000000000000002, so 9 bottles and a fabricated 0.6 L
        surplus. Only 750 ml, being exactly representable, escaped it."""
        for spirit, ml, expected in [(3.2, 600, 8), (2.1, 350, 9), (4.2, 900, 7)]:
            r = q.mixer_bottles(spirit, 3, 2, bottle_ml=ml)
            self.assertEqual(r["bottles"], expected,
                             f"{spirit} L into {ml} ml should be {expected} bottles")
            self.assertTrue(r["exact"], f"{spirit} L into {ml} ml divides exactly")
            self.assertEqual(r["surplus_litres"], 0.0)


class TestWater(unittest.TestCase):
    """The heaviest line, and the one most often missing."""

    def test_the_594_figure(self):
        # Quoted in references/quantities.md, camping-and-festivals.md and README.
        litres = q.water_litres(GUESTS, 3)
        self.assertEqual(litres.low, 594)
        self.assertEqual(litres.high, 594)

    def test_a_litre_is_a_kilogram(self):
        # The whole reason the figure matters: 594 L is more than most payloads.
        self.assertGreater(q.water_litres(GUESTS, 3).low, 500)

    def test_tap_on_site_collapses_it(self):
        self.assertEqual(q.water_litres(GUESTS, 3, tap_on_site=True).low, 297)

    def test_itemised_is_the_honest_worst_case(self):
        band = q.water_litres(GUESTS, 3, itemised=True)
        self.assertEqual(band.low, 594)      # planning figure sits at the floor
        self.assertEqual(band.high, 1089)

    def test_hot_weather_raises_drinking_only(self):
        self.assertEqual(q.water_litres(GUESTS, 3, hot_weather=True).low, 792)


class TestSourceEventRegression(unittest.TestCase):
    """Real quantities from August 2026, checked against the script."""

    def assertInBand(self, value, band, msg=""):
        self.assertGreaterEqual(value, band.low, msg)
        self.assertLessEqual(value, band.high, msg)

    def test_bbq_protein_in_band(self):
        # Taouk 2.5 kg + kafta 2.5 kg for 26, grilled with substantial sides.
        self.assertInBand(5.0, q.meat_kg(EATERS, "grilled"))

    def test_sniyet_chicken_in_band(self):
        self.assertInBand(5.5, q.meat_kg(EATERS, "boneless"))

    def test_sniyet_potatoes_in_band(self):
        self.assertInBand(7.0, q.starch_kg(EATERS, "potatoes"))

    def test_hummus_and_baba_in_band(self):
        band = q.dips_kg(GUESTS)
        self.assertInBand(2.5, band)   # hummus
        self.assertInBand(2.0, band)   # baba ghannouj

    def test_ice_in_band(self):
        # 90 kg across Friday and Saturday for 33 people.
        self.assertInBand(90, q.ice_kg(GUESTS, 2, "cocktails"))

    # ---- where the event and the reference disagree. Pinned deliberately. ----

    def test_toum_was_marginally_under(self):
        """Toum served as a Friday dip AND a Sunday table sauce is two
        occasions. 2.5 kg is just below the band the reference asks for."""
        band = q.dips_kg(GUESTS, "toum", occasions=2)
        self.assertAlmostEqual(band.low, 2.64)
        self.assertLess(2.5, band.low,
                        "the event bought 2.5 kg against a 2.64 kg floor")

    def test_breakfast_was_bought_for_three_mornings_not_two_and_a_half(self):
        """60 manakish at ~20 a morning is 3 mornings. The reference makes the
        departure morning a half, so it wanted 2.5. The event over-bought
        Monday, which is the cheap direction to be wrong in."""
        plan = q.meal_plan(ARRIVE, DEPART)
        self.assertEqual(plan.breakfasts, 2.5)
        pastry = q.breakfast_items(GUESTS, plan.breakfasts, "pastry")
        self.assertAlmostEqual(pastry.low, 57.75)
        self.assertAlmostEqual(pastry.high, 82.5)
        self.assertInBand(60, pastry)   # 5 dozen still lands inside the band

    def test_drinks_poured_above_the_party_rate(self):
        """The live pour is 336 cans + 100 spritz + 50 margaritas + 12
        tequila-kombucha = 498 drinks across 3 nights. The reference's party
        rate tops out well below that - the event chose to over-pour, and the
        script should say so rather than agree."""
        band = q.drinks_count(GUESTS, 3, "party")
        self.assertAlmostEqual(band.high, 336.6, places=1)
        self.assertGreater(498, band.high)

    def test_the_live_spritz_pour_matches_the_bottle_order(self):
        """6 L of Aperol at 60 ml an aperitif is 100 spritz - the figure the
        live documents carry, and the one that replaced 166."""
        spritz = 6000 // 60
        self.assertEqual(spritz, 100)
        self.assertEqual(q.mixer_bottles(6, 3, 2)["exact_litres"], 9.0)


class TestUncoveredBranches(unittest.TestCase):
    """Branches the audit found had no test at all."""

    def test_ice_with_no_fridge_adds_the_food_cold_figure(self):
        self.assertEqual(q.ice_kg(33, 3, "cans"), q.Range(49.5, 49.5))
        self.assertEqual(q.ice_kg(33, 3, "cans", no_fridge=True), q.Range(148.5, 148.5))

    def test_itemised_water_with_a_tap(self):
        # drinking (2,3) + cooking (1,2) only; washing and hygiene come from the tap
        self.assertEqual(q.water_litres(33, 3, tap_on_site=True, itemised=True),
                         q.Range(297, 495))

    def test_zero_and_negative_inputs_raise_consistently(self):
        for call in (lambda: q.meat_kg(0, "grilled"),
                     lambda: q.starch_kg(0, "potatoes"),
                     lambda: q.dips_kg(0),
                     lambda: q.breakfast_items(0, 2),
                     lambda: q.drinks_count(0, 3),
                     lambda: q.ice_kg(0, 3),
                     lambda: q.water_litres(0, 3),
                     lambda: q.pita_pieces(0),
                     lambda: q.salad_veg_kg(0)):
            with self.assertRaises(ValueError):
                call()

    def test_the_formerly_dead_constants_now_have_functions(self):
        self.assertEqual(q.pita_pieces(26), q.Range(52, 78))
        self.assertEqual(q.salad_veg_kg(26), q.Range(3.9, 5.2))
        self.assertEqual(q.cooked_from_raw(5).rounded(2), q.Range(3.5, 3.75))

    def test_late_first_dinner_flag(self):
        late = q.meal_plan(ARRIVE, DEPART)
        early = q.meal_plan(datetime(2026, 8, 14, 7, 0), DEPART)
        self.assertTrue(late.late_first_dinner, "7 PM arrival: dinner is the first meal")
        self.assertFalse(early.late_first_dinner)

    def test_breakfast_hour_boundary(self):
        before = q.meal_plan(datetime(2026, 8, 14, 8, 59), DEPART)
        at = q.meal_plan(datetime(2026, 8, 14, 9, 0), DEPART)
        self.assertEqual(before.breakfasts, 3.5)
        self.assertEqual(at.breakfasts, 2.5)


class TestAppetiteDecay(unittest.TestCase):
    def test_first_day_is_unscaled(self):
        self.assertEqual(q.appetite_factor(1), q.Range(1.0, 1.0))

    def test_day_two_is_the_documented_interpolation(self):
        # quantities.md now carries this row explicitly, flagged as interpolated
        self.assertEqual(q.appetite_factor(2), q.Range(0.9, 0.925))

    def test_day_three_is_fifteen_to_twenty_percent_down(self):
        band = q.appetite_factor(3)
        self.assertAlmostEqual(band.low, 0.80)
        self.assertAlmostEqual(band.high, 0.85)

    def test_later_days_do_not_keep_falling(self):
        self.assertEqual(q.appetite_factor(5), q.appetite_factor(3))

    def test_is_one_indexed(self):
        with self.assertRaises(ValueError):
            q.appetite_factor(0)


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(q))
    return tests


if __name__ == "__main__":
    unittest.main(verbosity=2)
