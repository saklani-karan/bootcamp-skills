#!/usr/bin/env python3
"""Build an event plan: event.json -> one self-contained HTML page.

The model writes event.json: who is coming, when, the menu, what to buy and from
where, what is already committed. It never writes a quantity or a total. This
script works out every amount with quantities.py, every cost and every subtotal,
the budget gap, and who owes what with split.py, then fills the fixed page in
assets/engine.html. The page is model-free and network-free.

It REFUSES to build when:
  - a price carries neither a "source" nor "check": true, or a line has no price
  - a cut is ambiguous ("chicken" - bone-in and boneless are different amounts)
  - a meal falls before people arrive or after they leave
  - a dietary group has nothing to eat at a meal
  - a shopping line names no store, or a store that is not in the list
  - a line says neither how its amount is worked out ("calc", "per_person") nor
    why it is a fixed count ("fixed" + "why")
  - the money does not add up (store, section and grand totals must agree, and
    a split must charge exactly what was billed)
  - the finished page would reach the network

    python3 build_event.py event.json --out plan.html [--explain]
"""
import argparse, datetime as dt, html, json, math, os, re, sys
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import quantities as q  # noqa: E402
import split as sp      # noqa: E402

ENGINE = os.path.join(HERE, "..", "assets", "engine.html")
FONTS = {"rounded", "clear", "story", "hand"}
COLOURS = {"auto", "snow", "sky", "pine", "sunset", "berry", "night"}
KG_PER = {"kg": 1.0, "g": 0.001, "lb": 0.45359237, "oz": 0.028349523125}
L_PER = {"l": 1.0, "ml": 0.001, "gal": 3.785411784, "qt": 0.946352946, "floz": 0.0295735295625}
COUNT_UNITS = {"each", "drinks", "pieces", "items"}


class Refused(Exception):
    pass


def money(x):
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def when(s, where):
    try:
        return dt.datetime.fromisoformat(str(s))
    except ValueError:
        raise Refused(f"{where}: '{s}' is not a date and time like 2026-10-17T15:00")


def unit_kind(u):
    u = str(u).lower()
    if u in KG_PER: return "mass"
    if u in L_PER: return "volume"
    if u in COUNT_UNITS: return "count"
    raise Refused(f"unknown unit '{u}': use one of {sorted(KG_PER) + sorted(L_PER) + sorted(COUNT_UNITS)}")


def unit_factor(u):
    u = str(u).lower()
    return KG_PER.get(u) or L_PER.get(u) or 1.0


# ---------------------------------------------------------------- display units
def show(value, kind, units):
    """value is kg / litres / a count. Returns text in the units the person chose."""
    if kind == "count":
        return f"{value:.0f}" if abs(value - round(value)) < 0.05 else f"{value:.1f}"
    if units == "metric":
        if kind == "mass":
            return f"{value*1000:.0f} g" if value < 1 else f"{value:.1f} kg"
        return f"{value*1000:.0f} ml" if value < 1 else f"{value:.1f} L"
    if kind == "mass":
        lb = value / KG_PER["lb"]
        return f"{value / KG_PER['oz']:.0f} oz" if lb < 1 else f"{lb:.1f} lb"
    gal = value / L_PER["gal"]
    return f"{value / L_PER['qt']:.1f} qt" if gal < 1 else f"{gal:.1f} gal"


def _t(txt):
    """'6.0 lb' -> '6 lb'; leaves '4.4 lb' alone."""
    return re.sub(r"\.0(?=\b)", "", txt)


def show_range(r, kind, units):
    if kind == "count":   # nobody buys 10.5 eggs: widen the band to whole items
        lo, hi = math.floor(r.low + 1e-9), math.ceil(r.high - 1e-9)
        return f"{lo}" if lo == hi else f"{lo}–{hi}"
    lo, hi = _t(show(r.low, kind, units)), _t(show(r.high, kind, units))
    return lo if lo == hi else f"{lo.split(' ')[0]}–{hi}"


# ---------------------------------------------------------------- the plan
CALC = {   # fn -> (callable, what it returns)
    "meat": "mass", "starch": "mass", "dips": "mass", "salad_veg": "mass", "ice": "mass",
    "pita": "count", "breakfast": "count", "drinks": "count", "water": "volume",
}


def build(spec):
    errs, warns = [], []
    for k in ("id", "title", "arrive", "depart", "groups", "meals", "stores", "shopping"):
        if k not in spec:
            errs.append(f"missing top-level field '{k}'")
    if errs:
        raise Refused("\n".join(errs))
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", str(spec["id"])):
        errs.append("id must be lowercase letters, digits and '-' (it keeps this plan's ticks separate)")
    units = spec.get("units", "us")
    if units not in ("us", "metric"):
        errs.append("units must be 'us' or 'metric'")
    look = spec.get("look", {})
    if look.get("font", "rounded") not in FONTS:
        errs.append(f"look.font must be one of {sorted(FONTS)}")
    if look.get("bg", "auto") not in COLOURS:
        errs.append(f"look.bg must be one of {sorted(COLOURS)}")
    cur = spec.get("currency", "$")

    arrive, depart = when(spec["arrive"], "arrive"), when(spec["depart"], "depart")
    if depart <= arrive:
        raise Refused("depart must be after arrive")
    nights = (depart.date() - arrive.date()).days
    plan = q.meal_plan(arrive, depart) if nights >= 1 else None
    days = round((depart - arrive).total_seconds() / 86400, 2)
    if plan and plan.late_first_dinner:
        warns.append("people arrive after 6 PM: the first dinner lands late. Put out no-cook food on arrival")

    groups = spec["groups"]
    if not groups or not all(isinstance(v, int) and v >= 0 for v in groups.values()):
        raise Refused("groups must map each group to how many people, e.g. {\"regular\": 20, \"vegetarian\": 5}")
    headcount = sum(groups.values())
    if headcount < 1:
        raise Refused("nobody is coming: groups add up to 0")

    def who(lst, where):
        lst = lst or ["everyone"]
        if "everyone" in lst:
            return list(groups)
        bad = [g for g in lst if g not in groups]
        if bad:
            errs.append(f"{where}: unknown group {bad} - groups are {sorted(groups)} or 'everyone'")
        return [g for g in lst if g in groups]

    # ---- meals: they must exist, and every group must have something at each
    meals, meal_ids = [], {}
    for i, m in enumerate(spec["meals"]):
        where = f"meal {i+1} ({m.get('name', '?')})"
        mid = m.get("id")
        if not mid or mid in meal_ids:
            errs.append(f"{where}: needs a unique id"); continue
        start = when(m.get("start"), where)
        if not arrive <= start <= depart:
            errs.append(f"{where} is at {start:%a %-d %b %H:%M}, but people are only there from "
                        f"{arrive:%a %H:%M} to {depart:%a %H:%M}. That meal does not exist - drop it or move it")
        covered = set()
        dishes = []
        for d in m.get("menu", []):
            g = who(d.get("for"), f"{where}, dish {d.get('dish', '?')}")
            covered.update(g)
            dishes.append({"dish": d.get("dish", ""), "for": [] if (not d.get("for") or "everyone" in d["for"]) else d["for"],
                           "note": d.get("note", "")})
        hungry = [g for g in groups if groups[g] and g not in covered]
        if hungry:
            errs.append(f"{where}: nothing on the menu for {', '.join(f'{g} ({groups[g]})' for g in hungry)}")
        meal_ids[mid] = start
        meals.append({"id": mid, "name": m.get("name", ""), "start": start.isoformat(timespec="minutes"),
                      "day": start.strftime("%A %-d %B"), "time": start.strftime("%-I:%M %p") if units == "us" else start.strftime("%H:%M"),
                      "open": m.get("open", ""), "dishes": dishes})
    meals.sort(key=lambda m: m["start"])

    stores = {s["name"]: s for s in spec["stores"] if s.get("name")}

    # ---- shopping: the script works out every amount and every cost
    lines = []
    for i, ln in enumerate(spec["shopping"]):
        where = f"shopping line {i+1} ({ln.get('item', '?')})"
        if not ln.get("store"):
            errs.append(f"{where}: no store - say where it is bought"); continue
        if ln["store"] not in stores:
            errs.append(f"{where}: store '{ln['store']}' is not in the stores list"); continue
        pack = ln.get("pack")
        if not pack or "price" not in pack:
            errs.append(f"{where}: no price - give pack {{size, unit, price}}"); continue
        if not ln.get("source") and not ln.get("check"):
            errs.append(f"{where}: the price has neither a source link nor \"check\": true"); continue
        try:
            pkind = unit_kind(pack.get("unit", "each"))
        except Refused as e:
            errs.append(f"{where}: {e}"); continue
        g = who(ln.get("for"), where)
        n = sum(groups[x] for x in g)
        linked = ln.get("meals", [])
        for mid in linked:
            if mid not in meal_ids:
                errs.append(f"{where}: meal '{mid}' is not one of the meals")
        modes = [k for k in ("calc", "per_person", "fixed") if k in ln]
        if len(modes) != 1:
            errs.append(f"{where}: say how the amount is worked out with exactly one of calc, per_person or fixed"); continue
        basis, kind, rng = "", pkind, None
        try:
            if "calc" in ln:
                c = dict(ln["calc"]); fn = c.pop("fn", None)
                if fn not in CALC:
                    raise Refused(f"calc.fn must be one of {sorted(CALC)}")
                kind = CALC[fn]
                nm = max(1, len(linked))
                if n < 1:
                    raise Refused("nobody in the groups this line is for")
                if fn == "meat":
                    rng = q.meat_kg(n, c.get("cut", ""), meals=nm); basis = f"{c.get('cut','').replace('_',' ')} meat for {n} people × {nm} meal{'s'*(nm>1)}"
                elif fn == "starch":
                    rng = q.starch_kg(n, c.get("kind", ""), meals=nm); basis = f"{c.get('kind','').replace('_',' ')} for {n} × {nm} meal{'s'*(nm>1)}"
                elif fn == "dips":
                    rng = q.dips_kg(n, c.get("kind", "dip"), occasions=nm); basis = f"dip for {n} × {nm}"
                elif fn == "salad_veg":
                    rng = q.salad_veg_kg(n).scaled(nm); basis = f"salad veg for {n} × {nm}"
                elif fn == "pita":
                    rng = q.pita_pieces(n, nm); basis = f"bread for {n} × {nm}"
                elif fn == "breakfast":
                    mornings = 0.0
                    for mid in linked:
                        s = meal_ids.get(mid)
                        mornings += 0.5 if (s and s.date() == depart.date()) else 1.0
                    if not mornings:
                        raise Refused("a breakfast line must list its breakfast meals")
                    rng = q.breakfast_items(n, mornings, c.get("kind", "items_total"))
                    basis = f"{n} people × {mornings:g} mornings (the leaving morning counts half)"
                elif fn == "drinks":
                    sessions = c.get("sessions", max(1, nights))
                    rng = q.drinks_count(n, sessions, c.get("style", "party"), c.get("drinking_fraction", q.DRINKING_FRACTION))
                    basis = f"{n} people × {sessions} evening{'s'*(sessions>1)}, about 85% drinking"
                elif fn == "ice":
                    rng = q.ice_kg(n, days, c.get("profile", "cans"), bool(c.get("no_fridge")))
                    basis = f"{n} people × {days:g} days" + (", no fridge: ice is the cold chain" if c.get("no_fridge") else "")
                elif fn == "water":
                    rng = q.water_litres(n, days, bool(c.get("tap_on_site")), bool(c.get("hot_weather")))
                    basis = f"{n} people × {days:g} days" + ("" if c.get("tap_on_site") else ", no tap: drinking, cooking and washing")
                    wt = rng.high if units == "metric" else rng.high / KG_PER["lb"]   # a litre of water is a kilogram
                    basis += f". It weighs about {wt:,.0f} {'kg' if units == 'metric' else 'lb'}: check what the cars can carry"
            elif "per_person" in ln:
                rate = float(ln["per_person"]); kind = pkind      # read in the pack's own unit
                v = rate * n * max(1, len(linked)) * unit_factor(pack["unit"])
                rng = q.Range(v, v); basis = f"{rate:g} each for {n} people" + (f" × {len(linked)} meals" if len(linked) > 1 else "")
            else:
                if not ln.get("why"):
                    raise Refused("a fixed count needs a \"why\" (e.g. 'one tank runs the grill all day')")
                v = float(ln["fixed"]) * unit_factor(pack["unit"]); kind = pkind; rng = q.Range(v, v); basis = ln["why"]
        except ValueError as e:   # quantities.py refuses ambiguous input rather than guessing
            errs.append(f"{where}: {e}"); continue
        except Refused as e:
            errs.append(f"{where}: {e}"); continue
        if kind != pkind:
            errs.append(f"{where}: the amount is a {kind} but the pack is sold by '{pack.get('unit')}' ({pkind})"); continue
        size = float(pack.get("size", 1))
        size_base = size * unit_factor(pack["unit"])
        sit = ln.get("sit", "high")
        need = rng.high if sit == "high" else rng.low
        packs = max(1, math.ceil(round(need / size_base, 6)))
        cost = money(pack["price"]) * packs
        lines.append({
            "id": f"l{i+1}", "item": ln["item"], "store": ln["store"], "section": ln.get("section", "Other"),
            "need": show_range(rng, kind, units), "basis": basis, "sit": "top" if sit == "high" else "bottom",
            "buy": f"{packs} × " + (pack["label"] if pack.get("label") else
                                    _t(show(size_base, kind, units)) if kind != "count" else f"{size:g}"),
            "packs": packs, "cost": str(cost), "check": bool(ln.get("check")), "source": ln.get("source", ""),
            "note": ln.get("note", ""), "for": [] if g == list(groups) else g,
        })

    if errs:
        raise Refused("\n".join(errs))
    store_order = {name: i for i, name in enumerate(stores)}
    sect_order = {}
    for l in lines:
        sect_order.setdefault((l["store"], l["section"]), len(sect_order))
    lines.sort(key=lambda l: (store_order[l["store"]], sect_order[(l["store"], l["section"])], int(l["id"][1:])))

    # ---- totals, three ways, and they must agree
    grand = sum((Decimal(l["cost"]) for l in lines), Decimal("0"))
    by_store, by_section = {}, {}
    for l in lines:
        by_store[l["store"]] = by_store.get(l["store"], Decimal("0")) + Decimal(l["cost"])
        by_section[l["section"]] = by_section.get(l["section"], Decimal("0")) + Decimal(l["cost"])
    if sum(by_store.values()) != grand or sum(by_section.values()) != grand:
        raise Refused(f"totals disagree: stores {sum(by_store.values())}, sections {sum(by_section.values())}, lines {grand}")

    # ---- budget
    committed = []
    for i, c in enumerate(spec.get("committed", [])):
        st = c.get("status", "")
        if st not in ("paid", "quoted", "estimate"):
            raise Refused(f"committed line {i+1} ({c.get('what','?')}): status must be paid, quoted or estimate")
        if st == "estimate":
            warns.append(f"'{c.get('what')}' ({cur}{money(c.get('amount', 0))}) is an estimate, not a quote. Price it before trusting the per-person figure")
        committed.append({"what": c.get("what", ""), "amount": str(money(c.get("amount", 0))), "status": st,
                          "night": c.get("night")})
    com_total = sum((Decimal(c["amount"]) for c in committed), Decimal("0"))
    coll = spec.get("collected") or {}
    payers = int(coll.get("payers", 0) or 0)
    collected = money(coll.get("per_head", 0)) * payers
    required = com_total + grand
    gap = required - collected
    per = (gap / (payers or headcount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if (payers or headcount) else Decimal("0")

    # ---- who owes what: split.py, with its conservation check
    split = None
    if spec.get("split"):
        # one bucket per section and audience: what only the vegetarians eat is paid by the vegetarians
        aud = {}
        for l in lines:
            who_for = tuple(l["for"])
            label = ", ".join(who_for)
            name = l["section"] if not who_for or label.lower() == l["section"].lower() else f"{l['section']} ({label})"
            b = aud.setdefault(name, {"amount": Decimal("0"), "section": l["section"], "for": set(who_for)})
            b["amount"] += Decimal(l["cost"])
        people, counted = [], {}
        for p in spec["split"]["people"]:
            g = p.get("group", "regular" if "regular" in groups else next(iter(groups)))
            if g not in groups:
                raise Refused(f"split: {p.get('name')} is in group '{g}', which is not one of {sorted(groups)}")
            counted[g] = counted.get(g, 0) + 1
            manual = set(p.get("excluded_from", []))
            unknown = [x for x in manual if x not in by_section and x not in {c["what"] for c in committed}]
            if unknown:
                raise Refused(f"split: {p['name']} is excluded from {unknown}, which is not a section or a committed line")
            ex = {n for n, b in aud.items() if b["section"] in manual or (b["for"] and g not in b["for"])}
            ex |= {x for x in manual if x not in by_section}
            people.append(sp.Person(name=p["name"], nights=frozenset(p.get("nights") or ["all"]),
                                    excluded_from=frozenset(ex), paid=Decimal(str(p.get("paid", 0)))))
        for g, n in groups.items():
            if counted.get(g, 0) != n:
                warns.append(f"split: {counted.get(g, 0)} people listed as '{g}', but groups say {n}")
        buckets = [sp.Bucket(c["what"], Decimal(c["amount"]), c["night"]) for c in committed if Decimal(c["amount"])]
        buckets += [sp.Bucket(n, b["amount"]) for n, b in aud.items() if b["amount"]]
        try:
            res = sp.apportion(people, buckets)
        except (sp.ConservationError, sp.NoEligiblePayers, ValueError) as e:
            raise Refused(f"the split does not work: {e}")
        split = {"rows": [{"name": n, "owes": str(res.per_person[n]), "paid": str(res.per_person[n] - res.balance[n]),
                           "balance": str(res.balance[n])} for n in [p.name for p in people]],
                 "buckets": [{"name": b.name, "amount": str(b.amount), "payers": res.denominators[b.name],
                              "night": b.night or ""} for b in buckets],
                 "billed": str(res.total_billed), "charged": str(res.total_charged),
                 "to_collect": str(sum((v for v in res.balance.values() if v > 0), Decimal("0"))),
                 "to_return": str(-sum((v for v in res.balance.values() if v < 0), Decimal("0")))}

    # ---- timeline and open questions
    tasks = []
    for t in spec.get("timeline", []):
        at = when(t.get("at"), f"timeline task '{t.get('what', '?')}'")
        if not t.get("who"):
            warns.append(f"timeline: '{t.get('what')}' has nobody's name on it. Name a person, or it will not happen")
        tasks.append({"at": at.isoformat(timespec="minutes"), "day": at.strftime("%a %-d %b"),
                      "time": at.strftime("%-I:%M %p") if units == "us" else at.strftime("%H:%M"),
                      "what": t.get("what", ""), "who": t.get("who", ""), "warn": t.get("warn", "")})
    tasks.sort(key=lambda t: t["at"])
    qs = []
    for o in spec.get("open_questions", []):
        d = o.get("decide_by")
        if d:
            when(d + ("" if "T" in str(d) else "T00:00"), f"open question '{o.get('q', '?')}'")
        else:
            warns.append(f"open question '{o.get('q')}' has no decide-by date, so it is shown as not blocking")
        qs.append({"q": o.get("q", ""), "gates": o.get("gates", ""), "by": d or ""})
    qs.sort(key=lambda o: (o["by"] == "", o["by"]))

    checks = [l for l in lines if l["check"]]
    data = {
        "id": spec["id"], "title": spec["title"], "subtitle": spec.get("subtitle", ""),
        "builtOn": spec.get("builtOn") or dt.date.today().strftime("%-d %B %Y"),
        "currency": cur, "units": units,
        "look": {"font": look.get("font", "rounded"), "bg": look.get("bg", "auto")},
        "facts": {"people": headcount, "groups": groups, "arrive": arrive.strftime("%a %-d %b, %-I:%M %p" if units == "us" else "%a %-d %b, %H:%M"),
                  "depart": depart.strftime("%a %-d %b, %-I:%M %p" if units == "us" else "%a %-d %b, %H:%M"),
                  "nights": nights, "where": spec.get("where", ""), "curfew": spec.get("curfew", "")},
        "guest": {"arrival": spec.get("arrival_note", ""), "drinks": spec.get("drinks", []),
                  "notes": spec.get("guest_notes", [])[:2], "meals": meals},
        "stores": [dict(stores[s], total=str(by_store.get(s, Decimal("0")))) for s in stores if s in by_store],
        "lines": lines, "sections": {k: str(v) for k, v in by_section.items()}, "grand": str(grand),
        "budget": {"committed": committed, "committed_total": str(com_total), "estimated": str(grand),
                   "required": str(required), "collected": str(collected), "payers": payers,
                   "per_head": str(money(coll.get("per_head", 0))), "gap": str(gap), "gap_per": str(per),
                   "per_basis": "payer" if payers else "person", "surplus": gap < 0},
        "split": split, "timeline": tasks, "questions": qs,
        "owned": spec.get("owned", []), "warnings": spec.get("page_warnings", []),
    }
    return data, warns, checks


def render(data):
    page = open(ENGINE, encoding="utf-8").read()
    for slot in ("/*__EVENT__*/null", "__TITLE__"):
        if page.count(slot) != 1:
            raise Refused(f"engine.html must contain {slot} exactly once")
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = page.replace("/*__EVENT__*/null", blob).replace("__TITLE__", html.escape(data["title"]))
    if re.search(r"fetch\(|XMLHttpRequest|<script[^>]+src=|<link[^>]+href=\"?https?:|<img[^>]+src=\"?https?:", page):
        raise Refused("the page would reach the network")
    return page


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("event"); ap.add_argument("--out", required=True)
    ap.add_argument("--explain", action="store_true", help="print every line's amount and how it was worked out")
    a = ap.parse_args()
    try:
        spec = json.load(open(a.event, encoding="utf-8"))
        data, warns, checks = build(spec)
        page = render(data)
    except Refused as e:
        print("REFUSED TO BUILD\n  " + str(e).replace("\n", "\n  "), file=sys.stderr); sys.exit(2)
    except (OSError, json.JSONDecodeError) as e:
        print(f"REFUSED TO BUILD\n  could not read {a.event}: {e}", file=sys.stderr); sys.exit(2)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(page)
    for w in warns:
        print("WARN  " + w)
    cur = data["currency"]
    if a.explain:
        for l in data["lines"]:
            print(f"  {l['item']:<34} need {l['need']:<16} buy {l['buy']:<18} {cur}{l['cost']:>8}   ({l['basis']})")
    b = data["budget"]
    print(f"built {os.path.basename(a.out)}  {data['facts']['people']} people  {len(data['lines'])} shopping lines  "
          f"shopping {cur}{data['grand']}  committed {cur}{b['committed_total']}  "
          + ("money: see the split below" if data["split"] else f"surplus {cur}{-Decimal(b['gap'])}" if b["surplus"] else f"gap {cur}{b['gap']} ({cur}{b['gap_per']} per {b['per_basis']})") + f"  {len(page)//1024} KB")
    if data["split"]:
        sp_ = data["split"]
        print(f"split: billed {cur}{sp_['billed']}, charged {cur}{sp_['charged']}; still to collect {cur}{sp_['to_collect']}, "
              f"to pay back {cur}{sp_['to_return']}")
    if checks:
        print("\nCHECK THESE prices before you shop:")
        for l in checks:
            print(f"  - {l['item']} at {l['store']}: {cur}{l['cost']} for {l['buy']}" + (f"   ({l['note']})" if l["note"] else ""))


if __name__ == "__main__":
    main()
