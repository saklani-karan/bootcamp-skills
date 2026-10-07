"""Each fixture breaks the valid control in exactly one way. run_guards.sh expects
every bad-* fixture to be REFUSED (exit 2) and the control to build (exit 0)."""
import json, copy
ok = {"id":"guard-test","title":"Guard test","age":10,"count":3,"level":2,
      "sections":["A"],"photos":[{"key":"p1","label":"x"}],
      "questions":[{"id":f"q{i}","section":"A","lvl":2,"t":"mc","q":f"Question {i}?",
                    "opts":["Right","Wrong one","Wrong two","Wrong three"],"a":0,
                    "h":"a nudge","f":"a fact","check":True} for i in range(4)]}
def w(name, d): json.dump(d, open(name + ".json", "w"), ensure_ascii=False, indent=1)
w("good", ok)
def bad(name, fn):
    d = copy.deepcopy(ok); fn(d); w("bad-" + name, d)
bad("hint-gives-answer", lambda d: d["questions"][0].update(h="It is Right, obviously"))
bad("no-source",         lambda d: d["questions"][0].pop("check"))
bad("answer-out-of-range", lambda d: d["questions"][0].update(a=4))
bad("answer-is-bool",    lambda d: d["questions"][0].update(a=True))
bad("duplicate-option",  lambda d: d["questions"][0].update(opts=["Right","right!","Wrong","Other"]))
bad("tf-not-bool",       lambda d: d["questions"][0].update(t="tf", a=1))
bad("pic-no-photo",      lambda d: d["questions"][0].update(t="pic"))
bad("unknown-photo",     lambda d: d["questions"][0].update(photo="nope"))
bad("unknown-section",   lambda d: d["questions"][0].update(section="B"))
bad("duplicate-id",      lambda d: d["questions"][1].update(id="q0"))
bad("pool-too-small",    lambda d: [q.update(lvl=1) for q in d["questions"]])
bad("dead-link",         lambda d: d["questions"][0].update(src="https://en.wikipedia.org/wiki/This_page_does_not_exist_quizmaker_zz"))
d = copy.deepcopy(ok); w("drift", d)
# --live-photos: a picture question whose photo is named by Wikipedia article builds; with no title it is refused
d = copy.deepcopy(ok); d["photos"] = [{"key":"p1","label":"Eiffel Tower","wiki":"Eiffel Tower"}]
d["questions"][0].update(photo="p1"); w("live", d)
d = copy.deepcopy(d); d["questions"][0].update(t="pic"); w("live-pic", d)
d = copy.deepcopy(d); d["photos"][0].pop("wiki"); w("live-no-wiki", d)
json.dump([{"q":"Question 0?","a":"Right"}], open("source-ok.json","w"))
json.dump([{"q":"Question 0?","a":"right"}], open("source-drift.json","w"))
