"""Writes every fixture fresh on each run. Never edit the .json files by hand."""
import json, copy
GOOD = {"id": "test-plan", "title": "Test plan", "start": "2026-11", "monthly_amount": 1500,
        "look": {"font": "rounded", "bg": "auto"},
        "debts": [{"name": "Card A", "balance": 3000, "apr": 22.0, "minimum": 90},
                  {"name": "Card B", "balance": 1200, "apr": 18.0, "minimum": 40},
                  {"name": "Car", "balance": 9000, "apr": 6.0, "minimum": 250}],
        "extra": 300,
        "goals": [{"name": "Rainy day", "target": 5000, "saved": 1000, "by": "2028-06", "return": 3.0}]}
def w(name, spec): json.dump(spec, open(name, "w"), indent=1)
w("good.json", GOOD)
d = copy.deepcopy(GOOD); d["goals"] = []; w("good-debts-only.json", d)
g = copy.deepcopy(GOOD); g["debts"] = []; g.pop("extra"); w("good-goals-only.json", g)
s = copy.deepcopy(GOOD); s["monthly_amount"] = 700; s["goals"][0]["stretch"] = True; w("good-stretch.json", s)
def bad(name, fn):
    x = copy.deepcopy(GOOD); fn(x); w(f"bad-{name}.json", x)
bad("min-no-cover",  lambda x: x["debts"][0].update(minimum=50))          # 3000 * 22% / 12 = 55 a month of interest
bad("balance-zero",  lambda x: x["debts"][1].update(balance=0))
bad("apr-range",     lambda x: x["debts"][1].update(apr=180))
bad("min-zero",      lambda x: x["debts"][2].update(minimum=0))
bad("duplicate",     lambda x: x["debts"][1].update(name="card a"))
bad("goal-past",     lambda x: x["goals"][0].update(by="2026-03"))
bad("over-budget",   lambda x: x.update(monthly_amount=700))
bad("return-range",  lambda x: x["goals"][0].update(**{"return": 25}))
bad("date-format",   lambda x: x["goals"][0].update(by="June 2028"))
bad("nothing",       lambda x: x.update(debts=[], goals=[]))
bad("text-number",   lambda x: x["debts"][0].update(balance="3,000"))
bad("no-monthly",    lambda x: x.pop("monthly_amount"))
bad("font",          lambda x: x["look"].update(font="comic"))
