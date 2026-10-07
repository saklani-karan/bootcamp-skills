"""Writes every fixture fresh on each run. Never edit the .json files by hand."""
import json, copy
GOOD = {"id": "test-sea", "title": "Test Sea", "age": 9, "look": {"font": "rounded", "bg": "auto"},
        "words": [{"answer": "Octopus", "clue": "Eight arms and three hearts"},
                  {"answer": "Dolphin", "clue": "Clever sea mammal that clicks"},
                  {"answer": "Shark", "clue": "Fish that keeps growing new teeth"},
                  {"answer": "Crab", "clue": "Scrabbles sideways along the sand"},   # 'scrabbles' must NOT trip the giveaway check
                  {"answer": "Ice cream", "clue": "A cold treat at the beach"},
                  {"answer": "Seahorse", "clue": "The dad carries the babies"}]}
def w(name, spec): json.dump(spec, open(name, "w"), ensure_ascii=False, indent=1)
w("good.json", GOOD)
def bad(name, fn):
    s = copy.deepcopy(GOOD); fn(s); w(f"bad-{name}.json", s)
bad("symbol",       lambda s: s["words"].append({"answer": "R2D2", "clue": "A beeping robot"}))
bad("short",        lambda s: s["words"].append({"answer": "A", "clue": "First letter"}))
bad("duplicate",    lambda s: s["words"].append({"answer": "shark", "clue": "Another big fish"}))
bad("no-clue",      lambda s: s["words"][0].update(clue=""))
bad("clue-gives",   lambda s: s["words"][2].update(clue="A shark is a fish"))
bad("clue-plural",  lambda s: s["words"][2].update(clue="Sharks have rows of teeth"))
bad("clue-part",    lambda s: s["words"][4].update(clue="Whipped cream on a cone"))
bad("too-few",      lambda s: s.update(words=s["words"][:3]))
bad("unplaceable",  lambda s: s["words"].append({"answer": "Zzz", "clue": "What you hear when someone sleeps"}))
bad("id",           lambda s: s.update(id="Test Sea!"))
bad("font",         lambda s: s["look"].update(font="comic"))
bad("check-no-note",lambda s: s["words"][1].update(check=True))
