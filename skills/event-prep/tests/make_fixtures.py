"""Writes every fixture fresh on each run. Never edit the .json files by hand."""
import json, copy
GOOD = {
  "id": "test-bbq", "title": "Test BBQ", "units": "us", "arrive": "2026-10-17T13:00", "depart": "2026-10-17T20:00",
  "groups": {"regular": 18, "vegetarian": 4},
  "stores": [{"name": "Costco"}, {"name": "Safeway"}],
  "meals": [{"id": "lunch", "name": "Grill lunch", "start": "2026-10-17T15:00",
             "menu": [{"dish": "Burgers", "for": ["regular"]}, {"dish": "Halloumi skewers", "for": ["vegetarian"]},
                      {"dish": "Corn", "for": ["everyone"]}]}],
  "shopping": [
    {"item": "Ground beef", "store": "Costco", "section": "Meat", "for": ["regular"], "meals": ["lunch"],
     "calc": {"fn": "meat", "cut": "ground"}, "pack": {"size": 5, "unit": "lb", "price": 24.99}, "check": True},
    {"item": "Halloumi", "store": "Safeway", "section": "Vegetarian", "for": ["vegetarian"], "meals": ["lunch"],
     "per_person": 0.4, "pack": {"size": 8, "unit": "oz", "price": 6.99}, "source": "https://www.safeway.com/"},
    {"item": "Soda and seltzer", "store": "Costco", "section": "Drinks",
     "calc": {"fn": "drinks", "style": "dinner", "sessions": 1}, "pack": {"size": 24, "unit": "each", "label": "24-pack", "price": 9.99}, "check": True},
    {"item": "Ice", "store": "Safeway", "section": "Cold", "calc": {"fn": "ice", "profile": "cans"},
     "pack": {"size": 10, "unit": "lb", "price": 3.49}, "check": True},
    {"item": "Charcoal", "store": "Costco", "section": "Grill", "fixed": 1, "why": "one bag runs the grill all afternoon",
     "pack": {"size": 1, "unit": "each", "label": "2 × 18 lb", "price": 18.99}, "check": True}],
  "committed": [{"what": "Bouncy castle", "amount": 180, "status": "paid"},
                {"what": "Cake", "amount": 75, "status": "estimate"}],
  "collected": {"per_head": 15, "payers": 10}
}
def w(name, spec): json.dump(spec, open(name, "w"), ensure_ascii=False, indent=1)
w("good.json", GOOD)
def bad(name, fn):
    s = copy.deepcopy(GOOD); fn(s); w(f"bad-{name}.json", s)
def line(s, i): return s["shopping"][i]
bad("price-unsourced",  lambda s: line(s, 0).pop("check"))
bad("no-price",         lambda s: line(s, 1)["pack"].pop("price"))
bad("ambiguous-cut",    lambda s: line(s, 0)["calc"].update(cut="chicken"))
bad("meal-before-arrival", lambda s: s["meals"].append({"id": "breakfast", "name": "Breakfast", "start": "2026-10-17T09:00",
                                                         "menu": [{"dish": "Bagels", "for": ["everyone"]}]}))
bad("meal-after-departure", lambda s: s["meals"][0].update(start="2026-10-17T21:30"))
bad("diet-hungry",      lambda s: s["meals"][0].update(menu=[d for d in s["meals"][0]["menu"] if d["dish"] != "Halloumi skewers" and d["dish"] != "Corn"]))
bad("no-store",         lambda s: line(s, 2).pop("store"))
bad("unknown-store",    lambda s: line(s, 2).update(store="Walmart"))
bad("no-amount-rule",   lambda s: line(s, 4).pop("fixed"))
bad("fixed-no-why",     lambda s: line(s, 4).pop("why"))
bad("unknown-group",    lambda s: line(s, 1).update({"for": ["vegan"]}))
bad("unknown-meal",     lambda s: line(s, 0).update(meals=["dinner"]))
bad("unit-mismatch",    lambda s: line(s, 0)["pack"].update(unit="each"))
bad("committed-status", lambda s: s["committed"][0].update(status="probably"))
bad("split-nobody",     lambda s: s.update(split={"people": [{"name": "Ann", "excluded_from": ["Drinks"]},
                                                              {"name": "Bo", "excluded_from": ["Drinks"]}]}))
