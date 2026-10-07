"""Writes every fixture fresh on each run. Never edit the .json files by hand.
good.json is also the near-miss control: it starts in the current month (today is pinned by builtOn, allowed because "example": true),
has a last-done date of exactly today, an interval of 60 months and one of 1, and is a southern-hemisphere
rented flat, so the season flip and the landlord wording are exercised too."""
import json, copy
GOOD = {
 "id": "test-flat", "title": "Test flat upkeep", "builtOn": "7 October 2026", "example": True,
 "region": "Melbourne, Australia", "hemisphere": "south", "words": "uk",
 "home": {"type": "apartment", "tenure": "rent"},
 "features": ["smoke_alarms", "ac", "water_heater", "dishwasher", "washing_machine", "range_hood", "deck", "yard", "car"],
 "start": "2026-10",
 "jobs": [{"id": "smoke-alarm-test", "last_done": "2026-10-07"}, {"id": "alarm-batteries", "last_done": "2026-02"},
          {"id": "hvac-filter", "every": 1}, {"id": "ac-service"}, {"id": "water-heater-flush"},
          {"id": "draft-check"}, {"id": "deck-check", "last_done": "2026-04-11"}, {"id": "tire-pressure"},
          {"id": "leak-check"}, {"id": "dishwasher-filter"},
          {"id": "yard-spring", "last_done": "2026-09-12"}],
 "custom": [{"title": "Descale the kettle", "every": 3, "who": "diy", "minutes": 15,
             "why": "Limescale clogs the element; use citric acid, not vinegar. Note from the drawer: C:\\kettle\\manual — “descale” means rinse twice."},
            {"title": "Check the bond paperwork", "every": 60, "last_done": "2024-01-15", "who": "diy", "minutes": 20,
             "why": "Keep the condition report and photos together for moving out."}],
 "look": {"font": "clear", "bg": "pine"}
}
def w(name, spec): json.dump(spec, open(name, "w"), ensure_ascii=False, indent=1)
w("good.json", GOOD)
def bad(name, fn):
    s = copy.deepcopy(GOOD); fn(s); w(f"bad-{name}.json", s)
def custom(s, **kw): s["custom"].append(dict({"title": "Wash the windows", "who": "diy", "minutes": 30, "why": "Grime etches glass."}, **kw))
bad("no-interval",        lambda s: custom(s))
bad("interval-zero",      lambda s: s["jobs"][2].update(every=0))
bad("interval-too-long",  lambda s: custom(s, every=61))
bad("unknown-job",        lambda s: s["jobs"].append({"id": "paint-the-fence"}))
bad("duplicate-job",      lambda s: s["jobs"].append({"id": "leak-check"}))
bad("duplicate-custom",   lambda s: custom(s, title="Clean the dishwasher filter", every=3))
bad("custom-no-why",      lambda s: custom(s, every=6, why=""))
bad("start-before-today", lambda s: s.update(start="2026-09"))
bad("start-day-past",     lambda s: s.update(start="2026-10-06"))
bad("last-done-future",   lambda s: s["jobs"][0].update(last_done="2026-10-08"))
bad("unknown-feature",    lambda s: s["features"].append("moat"))
bad("needs-feature",      lambda s: s["jobs"].append({"id": "pool-open"}))
bad("empty-plan",         lambda s: s.update(jobs=[], custom=[]))
bad("seasonal-every",     lambda s: s["jobs"][3].update(every=12))
bad("unknown-season",     lambda s: custom(s, season="monsoon"))
bad("builton-not-today",  lambda s: (s.update(builtOn="1 January 2025"), s.pop("example")))
bad("builton-flag-not-true", lambda s: s.update(builtOn="1 January 2025", example="yes"))
bad("hemisphere",         lambda s: s.update(hemisphere="east"))
bad("overloaded",         lambda s: [custom(s, title=f"Safety check {i}", every=1, safety=True, last_done="2026-10-01") for i in range(10)])
