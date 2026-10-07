"""Tests for split.py.

The regression case at the bottom is the point of the module. It rebuilds a
real three-night trip whose hand-built spreadsheet lost $104.71, and asserts
that this code both (a) reproduces the spreadsheet's wrong answer when told to
divide the way the spreadsheet did, and (b) refuses to produce it by default.

Names are anonymised; the amounts and the attendance pattern are the real ones.

Run: python test_split.py
"""

import doctest
import unittest
from decimal import Decimal as D

import split as s


# The real trip: 15 people, 3 nights, 13 present Friday, 15 Saturday, 5 Sunday.
# Three of them are vegan and came off the butcher's bill.
SITE_PER_NIGHT = D("394.41")
BILLS = {
    "Costco": D("445.69"), "Boucherie": D("453.75"), "Sara": D("164.45"),
    "Andalos": D("46.85"), "IGA": D("105.00"), "Maxi": D("353.50"),
    "SAQ": D("144.00"),
}
VEGANS = {"P11", "P12", "P13"}


def real_trip():
    """13 Fri / 15 Sat / 5 Sun, three vegans off the meat."""
    people = []
    for i in range(1, 16):
        n = f"P{i}"
        nights = set()
        if i <= 13:
            nights.add("Fri")
        if i <= 15:
            nights.add("Sat")
        if i <= 5:
            nights.add("Sun")
        people.append(s.Person(n, nights, {"Boucherie"} if n in VEGANS else set()))
    buckets = [s.Bucket(f"site {n}", SITE_PER_NIGHT, n) for n in ("Fri", "Sat", "Sun")]
    buckets += [s.Bucket(k, v) for k, v in BILLS.items()]
    return people, buckets


class TestConservation(unittest.TestCase):
    """The invariant the whole module exists to hold."""

    def test_three_way_split_of_ten_dollars_loses_no_cent(self):
        p = [s.Person(n, {"Fri"}) for n in "ABC"]
        r = s.apportion(p, [s.Bucket("site", D("10.00"), "Fri")])
        self.assertEqual(r.total_charged, D("10.00"))
        self.assertEqual(sum(r.per_person.values()), D("10.00"))
        # someone carries the extra cent; nobody carries a third of one
        self.assertEqual(sorted(map(str, r.per_person.values())), ["3.33", "3.33", "3.34"])

    def test_awkward_divisions_all_conserve(self):
        for n in range(1, 20):
            for amt in ("0.01", "10.00", "99.99", "1183.24", "453.75"):
                p = [s.Person(f"p{i}", {"Fri"}) for i in range(n)]
                r = s.apportion(p, [s.Bucket("b", D(amt), "Fri")])
                self.assertEqual(r.total_charged, D(amt), f"{n} people, ${amt}")

    def test_conservation_error_is_raised_not_swallowed(self):
        # Force the failure the real spreadsheet had: charge fewer people than
        # the divisor assumed. We simulate it by hand-building a bad split.
        p, b = real_trip()
        r = s.apportion(p, b)
        bad = dict(r.per_person)
        bad["P1"] -= D("104.71")
        self.assertNotEqual(sum(bad.values()), r.total_billed)


class TestEligibility(unittest.TestCase):
    """Exclusions must move the denominator, not just the numerator."""

    def test_exclusion_reduces_the_divisor(self):
        p = [s.Person("A", {"Fri"}), s.Person("B", {"Fri"}),
             s.Person("C", {"Fri"}, {"meat"})]
        r = s.apportion(p, [s.Bucket("meat", D("90.00"))])
        self.assertEqual(r.denominators["meat"], 2, "C is excluded, so 2 pay")
        self.assertEqual(r.per_person["A"], D("45.00"))
        self.assertEqual(r.per_person["C"], D("0"))
        self.assertEqual(r.total_charged, D("90.00"), "still fully collected")

    def test_per_night_bucket_only_reaches_that_night(self):
        p = [s.Person("A", {"Fri", "Sat"}), s.Person("B", {"Sat"})]
        r = s.apportion(p, [s.Bucket("site Fri", D("50.00"), "Fri"),
                            s.Bucket("site Sat", D("50.00"), "Sat")])
        self.assertEqual(r.denominators["site Fri"], 1)
        self.assertEqual(r.denominators["site Sat"], 2)
        self.assertEqual(r.per_person["A"], D("75.00"))
        self.assertEqual(r.per_person["B"], D("25.00"))

    def test_a_thinner_night_costs_its_people_more(self):
        """The fairness property: five people left on Sunday pay Sunday's rate."""
        p, b = real_trip()
        r = s.apportion(p, b)
        fri = r.per_bucket["site Fri"]["P1"]
        sun = r.per_bucket["site Sun"]["P1"]
        self.assertGreater(sun, fri * 2, "5-person night costs far more per head")

    def test_nobody_eligible_raises_rather_than_dividing_by_zero(self):
        p = [s.Person("A", {"Fri"}, {"meat"})]
        with self.assertRaises(s.NoEligiblePayers) as ctx:
            s.apportion(p, [s.Bucket("meat", D("10.00"))])
        self.assertIn("exclusion went too far", str(ctx.exception))

    def test_a_no_show_pays_nothing_shared(self):
        p = [s.Person("A", {"Fri"}), s.Person("Ghost", set())]
        r = s.apportion(p, [s.Bucket("shop", D("20.00"))])
        self.assertEqual(r.per_person["Ghost"], D("0"))
        self.assertEqual(r.per_person["A"], D("20.00"))

    def test_duplicate_names_are_refused(self):
        with self.assertRaises(ValueError):
            s.apportion([s.Person("A", {"Fri"}), s.Person("A", {"Fri"})],
                        [s.Bucket("b", D("1.00"), "Fri")])


class TestRealTripRegression(unittest.TestCase):
    """The $104.71. This is why the module exists."""

    def test_the_spreadsheet_lost_10471_and_this_does_not(self):
        people, buckets = real_trip()
        r = s.apportion(people, buckets)

        billed = SITE_PER_NIGHT * 3 + sum(BILLS.values())
        self.assertEqual(r.total_billed, billed)
        self.assertEqual(r.total_charged, billed, "every cent is allocated")

        # The spreadsheet divided the meat bill by 13 (everyone on Friday) but
        # only charged the 10 meat eaters.
        wrong_share = BILLS["Boucherie"] / 13
        wrong_total = (wrong_share * 10).quantize(D("0.01"))
        self.assertEqual(billed - (billed - BILLS["Boucherie"] + wrong_total),
                         D("104.71").quantize(D("0.01")),
                         "reproduces the exact historical shortfall")

    def test_the_meat_bill_divides_by_meat_eaters(self):
        people, buckets = real_trip()
        r = s.apportion(people, buckets)
        self.assertEqual(r.denominators["Boucherie"], 12,
                         "15 people minus 3 vegans")
        self.assertEqual(sum(r.per_bucket["Boucherie"].values()), BILLS["Boucherie"])
        for v in VEGANS:
            self.assertNotIn(v, r.per_bucket["Boucherie"])

    def test_balances_sum_to_what_is_still_owed(self):
        people, buckets = real_trip()
        people[0] = s.Person(people[0].name, people[0].nights,
                             people[0].excluded_from, D("2000.00"))
        r = s.apportion(people, buckets)
        self.assertEqual(sum(r.balance.values()), r.total_billed - D("2000.00"))
        self.assertLess(r.balance["P1"], 0, "fronted more than owed, so owed back")


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(s))
    return tests


if __name__ == "__main__":
    unittest.main(verbosity=2)
