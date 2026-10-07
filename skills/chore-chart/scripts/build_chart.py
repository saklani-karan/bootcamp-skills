#!/usr/bin/env python3
"""Build a weekly chore rotation chart: chart.json -> one self-contained HTML page.

The model writes chart.json: the children (first name, age), the chores (ids from
reference/chores.json and/or custom ones), how many weeks, which days, and what a
child must not do. It never assigns a chore. This script decides every assignment,
every day a chore lands on, every point and every fair share, then fills the fixed
page in assets/engine.html. The page is model-free and network-free.

HOW IT IS FAIR
  points    a chore's weekly points = effort (1-5) x times it happens that week
            (daily = every chosen day, 3x = three times, weekly = once).
  weight    each child's age weight = clamp(age - 2, 2, 12): a 3- or 4-year-old 2,
            a 10-year-old 8, 14 and over 12.
  fair share  the week's points shared in proportion to weight, EXCEPT that a child
            cannot be given more than the chores they are old enough for and not
            excluded from (and, over 2+ weeks, a rotating chore at most every other
            week): their unreachable share is passed on, in proportion to weight, to
            the children who can do it (exact weighted water-filling over every group
            of children, so no group is promised more than it can do).
  rotation  a chore belongs to one child for a whole week. No child gets the same
            chore two weeks running when another child can do it. The assignment
            minimises, week by week, the squared gap between each child's points and
            their fair share, both that week and over the weeks so far; a seeded
            shuffle breaks ties, so the same input always gives the same chart.
  bound     every child's points in every week are within B of their fair share, and
            (on a chart of 2+ weeks) their average over the whole chart within B/2,
            where B = the biggest single chore's weekly points. tests/property_test.py checks it on 50
            random families; a build that misses it prints a WARN.

It REFUSES to build (exit 2, with the reason) when:
  - a child has no age, or an age outside 3-17, or two children share a name
  - there are no children, more than 8, no chores, or more than 40
  - weeks is outside 1-12, or a day is not a day of the week
  - a chore id is not in reference/chores.json (and has no "title" of its own)
  - a chore is one no child is old enough for
  - a chore is excluded for every child old enough to do it
  - a chore only one child may do would have to repeat week after week
    (2+ weeks) and is not marked "same_child_ok": true
  - a chore happens more times a week than there are days on the chart
  - the finished page would reach the network

    python3 build_chart.py chart.json --out chart.html [--explain]
"""
import argparse, datetime as dt, hashlib, html, itertools, json, os, random, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "assets", "engine.html")
REFERENCE = os.path.join(HERE, "..", "reference", "chores.json")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_NAMES = {d.lower(): i for i, d in enumerate(DAYS)}
DAY_NAMES.update({n: i for i, n in enumerate(["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])})
FONTS = {"rounded", "clear", "story", "hand"}
COLOURS = {"auto", "snow", "sky", "pine", "sunset", "berry", "night"}
KID_COLOURS = ["#E4572E", "#2E86AB", "#3BA55C", "#8E5BD9", "#E09F1F", "#D6457A", "#1FA3A0", "#8A6E4B"]
MAX_KIDS, MAX_CHORES = 8, 40


class Refused(Exception):
    pass


def weight(age):
    return max(2, min(12, age - 2))


def times_per_week(how, ndays, where):
    if how == "daily":
        return ndays
    if how == "weekly":
        return 1
    m = re.fullmatch(r"([2-6])x", str(how))
    if not m:
        raise Refused(f"{where}: how_often must be daily, weekly or 2x-6x (times a week), not {how!r}")
    n = int(m.group(1))
    if n > ndays:
        raise Refused(f"{where}: happens {n} times a week but the chart has only {ndays} day{'s' if ndays > 1 else ''}; make it daily or choose more days")
    return n


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "chore"


def load_reference():
    return {c["id"]: c for c in json.load(open(REFERENCE, encoding="utf-8"))["chores"]}


# ---------------------------------------------------------------- validation
def validate(spec):
    warns = []
    if not isinstance(spec, dict):
        raise Refused("the chart file must be a JSON object")
    kids = spec.get("children")
    if not isinstance(kids, list) or not kids:
        raise Refused("there are no children: list each child's first name and age")
    if len(kids) > MAX_KIDS:
        raise Refused(f"{len(kids)} children: one chart holds at most {MAX_KIDS}")
    children, seen = [], {}
    for i, k in enumerate(kids):
        name = str((k or {}).get("name", "")).strip() if isinstance(k, dict) else ""
        if not name:
            raise Refused(f"child {i + 1} has no name")
        age = k.get("age")
        if isinstance(age, bool) or not isinstance(age, int):
            raise Refused(f"{name} has no valid age ({age!r}): give a whole number from 3 to 17")
        if not 3 <= age <= 17:
            raise Refused(f"{name}'s age is {age}: the chart is for children aged 3 to 17")
        if name.lower() in seen:
            raise Refused(f"two children are called {seen[name.lower()]}" + (f" ({name})" if name != seen[name.lower()] else "")
                          + ": give each a different name (add an initial)")
        seen[name.lower()] = name
        children.append({"name": name, "age": age, "weight": weight(age)})

    weeks = spec.get("weeks", 4)
    if isinstance(weeks, bool) or not isinstance(weeks, int) or not 1 <= weeks <= 12:
        raise Refused(f"weeks is {weeks!r}: a chart runs for 1 to 12 weeks")

    raw_days = spec.get("days", DAYS)
    if not isinstance(raw_days, list) or not raw_days:
        raise Refused("days must be a list of days of the week, e.g. [\"Mon\", \"Wed\", \"Fri\"]")
    idx = []
    for d in raw_days:
        i = DAY_NAMES.get(str(d).strip().lower())
        if i is None:
            raise Refused(f"{d!r} is not a day of the week (use Mon, Tue, Wed, Thu, Fri, Sat, Sun)")
        if i in idx:
            raise Refused(f"{DAYS[i]} is listed twice in days")
        idx.append(i)
    days = sorted(idx)

    start = spec.get("start")
    if start is not None:
        try:
            sd = dt.date.fromisoformat(str(start))
        except ValueError:
            raise Refused(f"start {start!r} is not a date (use YYYY-MM-DD)")
        if sd.weekday() != 0:
            raise Refused(f"start must be a Monday: {start} is a {sd.strftime('%A')}")
        start = sd

    ref = load_reference()
    raw = spec.get("chores")
    if not isinstance(raw, list) or not raw:
        raise Refused("there are no chores: list the chores, or pick some from reference/chores.json")
    if len(raw) > MAX_CHORES:
        raise Refused(f"{len(raw)} chores: one chart holds at most {MAX_CHORES}")
    chores, ids = [], set()
    for i, c in enumerate(raw):
        if isinstance(c, str):
            c = {"id": c}
        if not isinstance(c, dict):
            raise Refused(f"chore {i + 1} must be an id or an object")
        if "title" in c:   # a custom chore: everything must be given
            title = str(c["title"]).strip()
            where = f"chore {title!r}"
            for f in ("min_age", "effort", "how_often"):
                if f not in c:
                    raise Refused(f"{where} is a custom chore and needs {f}")
            base = {"id": c.get("id") or slug(title), "title": title}
        else:
            cid = c.get("id")
            if cid not in ref:
                near = [r for r in ref if cid and (str(cid) in r or r in str(cid))]
                raise Refused(f"unknown chore id {cid!r}" + (f" (did you mean {', '.join(near[:3])}?)" if near else "")
                              + ": use an id from reference/chores.json, or give a custom chore a title, min_age, effort and how_often")
            base = dict(ref[cid])
            where = f"chore {cid!r}"
        ch = dict(base)
        for f in ("min_age", "effort", "how_often", "same_child_ok", "day", "note"):
            if f in c:
                ch[f] = c[f]
        if ch["id"] in ids:
            raise Refused(f"{where} is listed twice")
        ids.add(ch["id"])
        ma = ch["min_age"]
        if isinstance(ma, bool) or not isinstance(ma, int) or not 3 <= ma <= 17:
            raise Refused(f"{where}: min_age must be a whole number from 3 to 17, not {ma!r}")
        if "title" not in c and "min_age" in c and ma < ref[c["id"]]["min_age"]:
            warns.append(f"{ch['title']}: min_age lowered from {ref[c['id']]['min_age']} to {ma} as asked; make sure that is right")
        ef = ch["effort"]
        if isinstance(ef, bool) or not isinstance(ef, int) or not 1 <= ef <= 5:
            raise Refused(f"{where}: effort must be 1 to 5, not {ef!r}")
        if not isinstance(ch.get("same_child_ok", False), bool):
            raise Refused(f"{where}: same_child_ok must be true or false")
        ch["times"] = times_per_week(ch["how_often"], len(days), where)
        if "day" in ch:
            di = DAY_NAMES.get(str(ch["day"]).strip().lower())
            if ch["times"] != 1 or di is None or di not in days:
                raise Refused(f"{where}: \"day\" is only for a once-a-week chore, and must be one of the chart's days")
            ch["day"] = di
        ch["points"] = ch["effort"] * ch["times"]
        chores.append(ch)

    names = {k["name"].lower(): i for i, k in enumerate(children)}
    excl = set()
    for e in spec.get("exclusions", []) or []:
        who, what = str(e.get("child", "")), e.get("chore")
        if who.lower() not in names:
            raise Refused(f"exclusion names {who!r}, who is not one of the children")
        if what not in ids:
            raise Refused(f"exclusion for {who} names chore {what!r}, which is not on the chart")
        excl.add((names[who.lower()], what))

    for ch in chores:
        old = [i for i, k in enumerate(children) if k["age"] >= ch["min_age"]]
        if not old:
            raise Refused(f"no child is old enough for {ch['title']!r} (from age {ch['min_age']}; the oldest child is "
                          f"{max(k['age'] for k in children)}): drop it, or lower its min_age if you are sure")
        ok = [i for i in old if (i, ch["id"]) not in excl]
        if not ok:
            raise Refused(f"{ch['title']!r} is excluded for every child old enough to do it ("
                          + ", ".join(children[i]["name"] for i in old) + "): drop it or lift an exclusion")
        if len(ok) == 1 and weeks > 1 and not ch.get("same_child_ok"):
            raise Refused(f"only {children[ok[0]]['name']} can do {ch['title']!r}, so it cannot rotate: "
                          f"{children[ok[0]]['name']} would do it all {weeks} weeks. Mark it \"same_child_ok\": true if that is fine")
        ch["eligible"] = ok

    look = spec.get("look", {}) or {}
    if look.get("font", "rounded") not in FONTS or look.get("bg", "auto") not in COLOURS:
        raise Refused(f"look must use font {sorted(FONTS)} and bg {sorted(COLOURS)}")
    for i, k in enumerate(children):
        if not any(i in ch["eligible"] for ch in chores):
            warns.append(f"{k['name']} ({k['age']}) is too young for, or excluded from, every chore on the list: "
                         "their row will be empty. Add a chore they can do")
    return children, chores, weeks, days, start, warns


# ---------------------------------------------------------------- fair share
def fair_shares(children, chores, weeks=1):
    """Exact weighted water-filling. Raise every child's share at the rate of their
    weight; a group of children stops rising when it holds every point it is able
    to do. Over 2+ weeks a chore that rotates can be held by any one child at most
    every other week, so one child counts for half its points and two or more for
    all of them. Returns Fractions that add up to the week's total points."""
    n = len(children)
    w = [Fraction(k["weight"]) for k in children]
    able = {}
    for mask in range(1, 1 << n):
        A = [i for i in range(n) if mask >> i & 1]
        tot = Fraction(0)
        for ch in chores:
            m = sum(1 for i in A if i in ch["eligible"])
            per = Fraction(ch["points"], 2) if weeks > 1 and len(ch["eligible"]) > 1 else Fraction(ch["points"])
            tot += min(Fraction(ch["points"]), m * per)
        able[mask] = tot
    share, active = [None] * n, set(range(n))
    while active:
        best, tight = None, []
        for mask, cap in able.items():
            A = [i for i in range(n) if mask >> i & 1]
            act = [i for i in A if i in active]
            if not act:
                continue
            lam = (cap - sum(share[i] for i in A if i not in active)) / sum(w[i] for i in act)
            if best is None or lam < best:
                best, tight = lam, [act]
            elif lam == best:
                tight.append(act)
        freeze = set(i for act in tight for i in act)
        for i in freeze:
            share[i] = best * w[i]
        active -= freeze
    return share


# ---------------------------------------------------------------- assignment
def assign(children, chores, weeks, seed):
    """Returns plan[week][chore_index] = child_index."""
    n, rng = len(children), random.Random(seed)
    T = [float(s) for s in fair_shares(children, chores, weeks)]
    cum = [0.0] * n
    done = [[0] * len(chores) for _ in range(n)]    # times child i has held chore k
    plan = []
    for w in range(weeks):
        prev = plan[-1] if plan else None
        allowed = []
        for k, ch in enumerate(chores):
            el = list(ch["eligible"])
            if prev is not None and len(el) > 1:
                el = [i for i in el if i != prev[k]]
            allowed.append(el)
        order = list(range(n)); rng.shuffle(order)
        rank = {c: r for r, c in enumerate(order)}
        tgt_cum = [(w + 1) * t for t in T]

        def cost(load, a):
            s = 0.0
            for i in range(n):
                s += (load[i] - T[i]) ** 2 + (cum[i] + load[i] - tgt_cum[i]) ** 2
            # a small pull towards variety: a chore you have held often costs a little more
            s += 0.1 * sum(done[a[k]][k] for k in range(len(chores)))
            return s

        load, a = [0.0] * n, [None] * len(chores)
        seq = sorted(range(len(chores)), key=lambda k: (-chores[k]["points"], len(allowed[k]), chores[k]["id"]))
        for k in seq:
            p = chores[k]["points"]
            def inc(i):
                return ((load[i] + p - T[i]) ** 2 - (load[i] - T[i]) ** 2
                        + (cum[i] + load[i] + p - tgt_cum[i]) ** 2 - (cum[i] + load[i] - tgt_cum[i]) ** 2
                        + 0.1 * done[i][k])
            i = min(allowed[k], key=lambda i: (round(inc(i), 9), rank[i]))
            a[k] = i; load[i] += p
        # local search: best single move or swap, until nothing improves
        cur = cost(load, a)
        for _ in range(500):
            best = None
            for k in range(len(chores)):
                p, i = chores[k]["points"], a[k]
                for j in allowed[k]:
                    if j == i:
                        continue
                    load[i] -= p; load[j] += p; a[k] = j
                    c = cost(load, a)
                    load[i] += p; load[j] -= p; a[k] = i
                    if c < cur - 1e-9 and (best is None or c < best[0] - 1e-9):
                        best = (c, [(k, j)])
            for k1, k2 in itertools.combinations(range(len(chores)), 2):
                i1, i2 = a[k1], a[k2]
                if i1 == i2 or i2 not in allowed[k1] or i1 not in allowed[k2]:
                    continue
                p1, p2 = chores[k1]["points"], chores[k2]["points"]
                load[i1] += p2 - p1; load[i2] += p1 - p2; a[k1], a[k2] = i2, i1
                c = cost(load, a)
                load[i1] -= p2 - p1; load[i2] -= p1 - p2; a[k1], a[k2] = i1, i2
                if c < cur - 1e-9 and (best is None or c < best[0] - 1e-9):
                    best = (c, [(k1, i2), (k2, i1)])
            if best is None:
                break
            for k, j in best[1]:
                load[a[k]] -= chores[k]["points"]; load[j] += chores[k]["points"]; a[k] = j
            cur = best[0]
        for k, i in enumerate(a):
            done[i][k] += 1
        for i in range(n):
            cum[i] += load[i]
        plan.append(a)
    return plan


def slots(chores, days):
    """The days each chore lands on, staggered so chores of the same frequency do not pile up on one day."""
    d, seen = len(days), {}
    for ch in chores:
        t = ch["times"]
        if "day" in ch:
            ch["slots"] = [days.index(ch["day"])]
            continue
        off = seen.get(t, 0); seen[t] = off + 1
        if t == d:
            ch["slots"] = list(range(d))
        else:
            step = d // t
            ch["slots"] = sorted(set((int(i * d / t) + off % max(1, step)) % d for i in range(t)))
            if len(ch["slots"]) < t:   # never happens with t <= d, kept as a guard
                ch["slots"] = list(range(t))


# ---------------------------------------------------------------- build
def build(spec):
    children, chores, weeks, days, start, warns = validate(spec)
    canon = json.dumps({k: spec.get(k) for k in ("children", "chores", "weeks", "days", "exclusions")}, sort_keys=True)
    seed = spec.get("seed")
    if seed is None:
        seed = int(hashlib.sha256(canon.encode()).hexdigest()[:8], 16)
    slots(chores, days)
    shares = fair_shares(children, chores, weeks)
    plan = assign(children, chores, weeks, seed)
    n = len(children)
    B = max(ch["points"] for ch in chores)

    # every rule, re-checked on the finished plan (a plan that breaks one is never written)
    for w, a in enumerate(plan):
        for k, i in enumerate(a):
            ch = chores[k]
            if i not in ch["eligible"] or children[i]["age"] < ch["min_age"]:
                raise Refused(f"internal: week {w + 1} gave {ch['title']} to {children[i]['name']}, who may not do it")
            if w and plan[w - 1][k] == i and len(ch["eligible"]) > 1:
                raise Refused(f"internal: {children[i]['name']} has {ch['title']} two weeks running")

    loads = [[sum(chores[k]["points"] for k, j in enumerate(a) if j == i) for i in range(n)] for a in plan]
    week_dev = max(abs(l[i] - float(shares[i])) for l in loads for i in range(n))
    avg = [sum(l[i] for l in loads) / weeks for i in range(n)]
    period_dev = max(abs(avg[i] - float(shares[i])) for i in range(n))
    if week_dev > B + 1e-9:
        warns.append(f"a week is {week_dev:.1f} points off someone's fair share, more than the bound {B}")
    PB = B / 2 if weeks > 1 else B
    if period_dev > PB + 1e-9:
        warns.append(f"over the whole chart someone averages {period_dev:.1f} points a week off their fair share, more than {PB:g}")
    total = sum(ch["points"] for ch in chores)
    W = sum(k["weight"] for k in children)
    for i, k in enumerate(children):
        k["colour"] = KID_COLOURS[i % len(KID_COLOURS)]
        k["share"] = round(float(shares[i]), 1)
        k["age_share"] = round(total * k["weight"] / W, 1)
        k["avg"] = round(avg[i], 1)
        k["can"] = sum(1 for ch in chores if i in ch["eligible"])
        if abs(k["share"] - k["age_share"]) >= 0.05 and k["share"] < k["age_share"]:
            k["why"] = f"less than an age share ({k['age_share']:g}): {k['can']} of the {len(chores)} chores are ones {k['name']} can do"
    week_list = []
    for w, a in enumerate(plan):
        grid = [[[] for _ in days] for _ in range(n)]
        for k in sorted(range(len(chores)), key=lambda k: (-chores[k]["effort"], chores[k]["title"])):
            for s in chores[k]["slots"]:
                grid[a[k]][s].append(k)
        label = f"Week {w + 1}"
        dates = None
        if start:
            d0 = start + dt.timedelta(weeks=w)
            dates = [(d0 + dt.timedelta(days=d)).strftime("%-d %b") for d in days]
            label += " · " + (d0 + dt.timedelta(days=days[0])).strftime("%-d %b") + " – " + (d0 + dt.timedelta(days=days[-1])).strftime("%-d %b")
        week_list.append({"n": w + 1, "label": label, "dates": dates, "grid": grid, "loads": loads[w], "owner": a,
                          "ticks": sum(len(cell) for row in grid for cell in row)})
    data = {
        "id": str(spec.get("id") or slug(spec.get("title", "chores"))),
        "title": str(spec.get("title") or "Our chore chart"),
        "subtitle": spec.get("subtitle") or f"{weeks} week{'s' if weeks > 1 else ''} · " + (
            "every day" if len(days) == 7 else ", ".join(DAYS[d] for d in days)),
        "builtOn": spec.get("builtOn") or dt.date.today().strftime("%-d %B %Y"),
        "look": {"font": (spec.get("look") or {}).get("font", "rounded"), "bg": (spec.get("look") or {}).get("bg", "auto")},
        "days": [DAYS[d] for d in days],
        "children": children,
        "chores": [{"id": c["id"], "title": c["title"], "effort": c["effort"], "times": c["times"], "points": c["points"],
                    "how": c["how_often"], "note": c.get("note", ""), "same": bool(c.get("same_child_ok")) and len(c["eligible"]) == 1,
                    "min_age": c["min_age"]} for c in chores],
        "weeks": week_list,
        "fair": {"bound": B, "period_bound": PB, "week_dev": round(week_dev, 1), "period_dev": round(period_dev, 1), "total": total, "seed": seed},
    }
    return data, warns


def render(data):
    page = open(ENGINE, encoding="utf-8").read()
    for slot in ("/*__CHART__*/null", "__TITLE__"):
        if page.count(slot) != 1:
            raise Refused(f"engine.html must contain {slot} exactly once")
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = page.replace("/*__CHART__*/null", blob).replace("__TITLE__", html.escape(data["title"]))
    if re.search(r"fetch\(|XMLHttpRequest|<script[^>]+src=|<link[^>]+href=\"?https?:|<img[^>]+src=\"?https?:", page):
        raise Refused("the page would reach the network")
    return page


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("chart"); ap.add_argument("--out", required=True)
    ap.add_argument("--explain", action="store_true", help="print who has which chore each week")
    a = ap.parse_args()
    try:
        spec = json.load(open(a.chart, encoding="utf-8"))
        data, warns = build(spec)
        page = render(data)
    except Refused as e:
        print("REFUSED TO BUILD\n  " + str(e), file=sys.stderr); sys.exit(2)
    except (OSError, json.JSONDecodeError) as e:
        print(f"REFUSED TO BUILD\n  could not read {a.chart}: {e}", file=sys.stderr); sys.exit(2)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(page)
    for w in warns:
        print("WARN  " + w)
    K, C, F = data["children"], data["chores"], data["fair"]
    print(f"built {os.path.basename(a.out)}  {len(K)} children  {len(C)} chores  {len(data['weeks'])} weeks  "
          f"{F['total']} points a week  {len(page) // 1024} KB")
    print("fair share per week (points; weight = clamp(age-2, 2, 12)):")
    for i, k in enumerate(K):
        per = " ".join(f"{wk['loads'][i]:>3}" for wk in data["weeks"])
        print(f"  {k['name']:<12} age {k['age']:>2}  weight {k['weight']:>2}  fair {k['share']:>5}  weeks: {per}   average {k['avg']}"
              + (f"   ({k['why']})" if k.get("why") else ""))
    print(f"max deviation: {F['week_dev']} in any one week (bound {F['bound']} = biggest chore), "
          f"{F['period_dev']} averaged over the chart (bound {F['period_bound']:g})")
    if a.explain:
        for wk in data["weeks"]:
            print(f"  {wk['label']}: " + "; ".join(f"{C[k]['title']} → {K[i]['name']}" for k, i in enumerate(wk["owner"])))


if __name__ == "__main__":
    main()
