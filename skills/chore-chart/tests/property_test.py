"""Property test: 50 random valid families (seeded, so the run is reproducible).
For every one, re-checks from the INPUT (not from the build's own bookkeeping):
  - every chore is held by exactly one child each week, and that child is old enough and not excluded
  - nobody holds the same chore two weeks running when another eligible child exists
  - the page grid shows each owned chore on exactly its number of days, in its owner's row
  - each child's points in every week are within B of their fair share, and (2+ weeks)
    their average over the chart within B/2 (B = the biggest single chore's weekly points)
  - fair shares add up to the week's points, and building twice gives the same chart
Random inputs the build refuses are counted and redrawn (they are not failures)."""
import importlib.util, json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "..", "scripts", "build_chart.py"))
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
REF = list(b.load_reference().values())
NAMES = ["Ava", "Ben", "Cleo", "Dev", "Eli", "Fay", "Gus", "Hana"]
rng = random.Random(20261007)

def family():
    n = rng.randint(1, 6)
    kids = [{"name": NAMES[i], "age": rng.randint(3, 17)} for i in range(n)]
    days = sorted(rng.sample(b.DAYS, rng.choice([7, 7, 7, 5, 6, 3, 2])), key=b.DAYS.index)
    chores = [c["id"] for c in rng.sample(REF, rng.randint(3, 15))]
    for j in range(rng.randint(0, 2)):
        chores.append({"title": f"Custom job {j}", "min_age": rng.randint(3, 12), "effort": rng.randint(1, 5),
                       "how_often": rng.choice(["daily", "weekly", "2x"])})
    ids = [c if isinstance(c, str) else b.slug(c["title"]) for c in chores]
    excl = [{"child": rng.choice(kids)["name"], "chore": rng.choice(ids)} for _ in range(rng.randint(0, 3))]
    # a third of the time, mark every chore same_child_ok so single-child chores survive
    if rng.random() < 0.33:
        chores = [dict({"id": c}, same_child_ok=True) if isinstance(c, str) else dict(c, same_child_ok=True) for c in chores]
    return {"id": "p", "title": "p", "builtOn": "x", "children": kids, "chores": chores, "weeks": rng.randint(1, 12),
            "days": days, "exclusions": excl, "seed": rng.randint(0, 10 ** 6)}

valid, refused, worst_w, worst_p = 0, {}, 0.0, 0.0
while valid < 50:
    s = family()
    try:
        d, _ = b.build(json.loads(json.dumps(s)))
    except b.Refused as e:
        key = str(e).split(":")[0][:40]; refused[key] = refused.get(key, 0) + 1; continue
    valid += 1
    K, C, Wk = d["children"], d["chores"], d["weeks"]
    ex = {(e["child"].lower(), e["chore"]) for e in s["exclusions"]}
    elig = [[i for i, k in enumerate(K) if k["age"] >= c["min_age"] and (k["name"].lower(), c["id"]) not in ex] for c in C]
    B = max(c["points"] for c in C)
    assert abs(sum(k["share"] for k in K) - sum(c["points"] for c in C)) < 0.05 * len(K) + 1e-9, "shares do not add up"
    for w, wk in enumerate(Wk):
        assert len(wk["owner"]) == len(C)
        for k, i in enumerate(wk["owner"]):
            assert K[i]["age"] >= C[k]["min_age"], f"too young: {K[i]} {C[k]}"
            assert i in elig[k], f"excluded child given {C[k]['id']}"
            if w and len(elig[k]) > 1:
                assert Wk[w - 1]["owner"][k] != i, f"{K[i]['name']} has {C[k]['id']} weeks {w} and {w + 1}"
            shown = sum(row_cell.count(k) for row_cell in wk["grid"][i])
            others = sum(cell.count(k) for j, row in enumerate(wk["grid"]) if j != i for cell in row)
            assert shown == C[k]["times"] and others == 0, "grid does not match owner"
        for i, k in enumerate(K):
            load = sum(C[c]["points"] for c, j in enumerate(wk["owner"]) if j == i)
            assert load == wk["loads"][i]
            dev = abs(load - k["share"]); worst_w = max(worst_w, dev / B)
            assert dev <= B + 0.05, f"week {w + 1}: {k['name']} {load} vs fair {k['share']} (bound {B})"
    for i, k in enumerate(K):
        avg = sum(wk["loads"][i] for wk in Wk) / len(Wk); dev = abs(avg - k["share"]); worst_p = max(worst_p, dev / B) if len(Wk) > 1 else worst_p
        PB = B / 2 if len(Wk) > 1 else B
        assert dev <= PB + 0.05, f"{k['name']} averages {avg:.2f} vs fair {k['share']} (bound {PB})"
    d2, _ = b.build(json.loads(json.dumps(s)))
    assert d2 == d, "not reproducible"
print("refused random inputs (redrawn):", json.dumps(refused, sort_keys=True))
print(f"worst week deviation {worst_w:.2f} B (bound 1 B), worst whole-chart deviation on 2+ week charts {worst_p:.2f} B (bound 0.5 B)")
print(f"property test: 50/50 random families hold the age, exclusion, no-repeat and fairness rules")
