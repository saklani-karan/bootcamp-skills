"""Writes every fixture fresh on each run. Never edit the .json files by hand."""
import json, copy
GOOD = {"id": "test-cards", "title": "Test cards", "units": "source",
        "cards": [{"id": "pancakes", "title": "Pancakes", "serves": 4, "serves_text": "Serves 4",
                   "ingredients": [{"name": "", "items": [
                       {"text": "1 1/2 cups flour", "qty": "1 1/2", "unit": "cups", "item": "flour"},
                       {"text": "2 eggs", "qty": "2", "unit": "", "item": "eggs"},
                       {"text": "250 ml milk", "qty": "250", "unit": "ml", "item": "milk"},
                       {"text": "a pinch of salt", "qty": "", "unit": "", "item": "salt"}]}],
                   "method": [{"name": "", "steps": ["Whisk everything.", "Cook in a hot pan."]}]}]}
def w(name, spec): json.dump(spec, open(name, "w"), ensure_ascii=False, indent=1)
w("good.json", GOOD)
s = copy.deepcopy(GOOD); s["units"] = "us"; s["cards"][0]["scale_to"] = 6; w("good-convert.json", s)
def bad(name, fn):
    s = copy.deepcopy(GOOD); fn(s); w(f"bad-{name}.json", s)
I = lambda s: s["cards"][0]["ingredients"][0]["items"]
bad("no-title",       lambda s: s["cards"][0].update(title=""))
bad("no-ingredients", lambda s: s["cards"][0].update(ingredients=[{"name": "", "items": []}]))
bad("empty-ingredient", lambda s: I(s).append({"text": "  ", "qty": "", "unit": "", "item": ""}))
bad("empty-step",     lambda s: s["cards"][0]["method"][0]["steps"].append(""))
bad("qty-drift",      lambda s: I(s)[1].update(qty="3"))
bad("unit-drift",     lambda s: I(s)[0].update(unit="tbsp"))
bad("qty-dropped",    lambda s: I(s)[1].update(qty=""))
bad("qty-unreadable", lambda s: I(s)[0].update(qty="one and a half"))
bad("scale-no-serves",lambda s: (s["cards"][0].pop("serves"), s["cards"][0].update(scale_to=8)))
bad("unknown-unit",   lambda s: (s.update(units="metric"), I(s).append({"text": "2 gills cream", "qty": "2", "unit": "gills", "item": "cream"})))
bad("duplicate-id",   lambda s: s["cards"].append(copy.deepcopy(s["cards"][0])))
