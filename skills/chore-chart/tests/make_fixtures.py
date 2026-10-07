"""Writes every fixture fresh on each run. Never edit the .json files by hand."""
import json, copy, glob, os
for f in glob.glob("bad-*.json") + glob.glob("near-*.json"):
    os.remove(f)
GOOD = {
  "id": "test-chores", "title": "Test chores", "weeks": 3, "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  "builtOn": "7 October 2026",
  "children": [{"name": "Ana", "age": 11}, {"name": "Ben", "age": 9}, {"name": "Cy", "age": 4}],
  "chores": ["set-table", "toys-away", "unload-dishwasher", "vacuum", "trash-out",
             {"title": "Feed the fish", "min_age": 4, "effort": 1, "how_often": "daily"}],
  "exclusions": [{"child": "Ben", "chore": "toys-away", "why": "test"}]
}
def w(name, spec): json.dump(spec, open(name, "w"), ensure_ascii=False, indent=1)
w("good.json", GOOD)
def make(prefix, name, fn):
    s = copy.deepcopy(GOOD); fn(s); w(f"{prefix}-{name}.json", s)
def bad(name, fn): make("bad", name, fn)
def near(name, fn): make("near", name, fn)
# ---- refusals: one per reason
bad("too-young-for-all",  lambda s: s["chores"].append("mow-lawn"))                         # min 14, oldest 11
bad("excluded-everyone",  lambda s: s["exclusions"].extend([{"child": "Ana", "chore": "toys-away"}, {"child": "Cy", "chore": "toys-away"}]))  # all three excluded
bad("age-missing",        lambda s: s["children"][1].pop("age"))
bad("age-too-young",      lambda s: s["children"][2].update(age=2))
bad("age-too-old",        lambda s: s["children"][0].update(age=18))
bad("age-not-number",     lambda s: s["children"][0].update(age="eleven"))
bad("duplicate-name",     lambda s: s["children"].append({"name": "ana", "age": 6}))
bad("no-chores",          lambda s: s.update(chores=[]))
bad("weeks-zero",         lambda s: s.update(weeks=0))
bad("weeks-13",           lambda s: s.update(weeks=13))
bad("cannot-rotate",      lambda s: s["children"][1].update(age=8))  # vacuum is 9+: only Ana
bad("unknown-id",         lambda s: s["chores"].append("dishes"))
# extra input checks
bad("no-children",        lambda s: s.update(children=[]))
bad("bad-day",            lambda s: s.update(days=["Mon", "Funday"]))
bad("too-often",          lambda s: s.update(days=["Sat", "Sun"]) or s["chores"].remove("trash-out") or s["chores"].append("sweep-kitchen"))  # 3x on 2 days
bad("start-not-monday",   lambda s: s.update(start="2026-10-14"))
bad("exclusion-unknown-child", lambda s: s["exclusions"].append({"child": "Dee", "chore": "vacuum"}))
bad("custom-incomplete",  lambda s: s["chores"].append({"title": "Polish shoes", "min_age": 8}))
bad("duplicate-chore",    lambda s: s["chores"].append("toys-away"))
# ---- near misses: must BUILD
near("ages-3-and-17",     lambda s: (s["children"][2].update(age=3), s["children"][0].update(age=17)))
near("one-week-one-child",lambda s: (s.update(weeks=1), s["children"][1].update(age=8)))       # vacuum: only Ana, but 1 week
near("same-child-ok",     lambda s: (s["children"][1].update(age=8), s["chores"].remove("vacuum"), s["chores"].append({"id": "vacuum", "same_child_ok": True})))
near("min-age-equals-oldest", lambda s: (s["children"][1].update(age=11), s["chores"].append("run-laundry")))  # min 11, Ana and Ben are 11
near("weeks-12",          lambda s: s.update(weeks=12))
near("weekdays-3x",       lambda s: (s.update(days=["Mon", "Wed", "Fri"]), s["chores"].append("sweep-kitchen")))  # 3x on exactly 3 days
near("excluded-all-but-two", lambda s: s["exclusions"].append({"child": "Cy", "chore": "feed-the-fish"}))
