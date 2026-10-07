#!/usr/bin/env python3
"""Build a money plan: plan.json -> one self-contained HTML page.

The model only writes down what the person said (debts, goals, what they can put
in each month). Every payoff month, interest total and monthly saving on the page
is computed here, by debt_management.py and savings_goals.py. The page is
model-free and network-free, so it behaves the same as a Claude artifact, on
Vercel, or double-clicked from Downloads.

It REFUSES to build when:
  - a minimum payment does not cover the interest that debt adds each month
    (that debt would never be paid off)
  - a balance is zero or negative, a rate is below 0% or above 100%, or a minimum
    payment is zero
  - two debts have the same name
  - a goal's date is not after the plan's start month
  - minimums + extra + what the goals need is more than the person said they can
    put in each month, unless a goal is marked "stretch": true
  - an assumed return is outside 0-12% a year
  - the finished page would reach the network

    python3 build_plan.py plan.json --out plan.html
"""
import argparse, datetime, html, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from debt_management import Debt, DebtManagement   # noqa: E402
from savings_goals import SavingsGoals               # noqa: E402

ENGINE = os.path.join(HERE, "..", "assets", "engine.html")
FONTS = {"rounded", "clear", "story", "hand"}
COLOURS = {"auto", "snow", "sky", "pine", "sunset", "berry", "night"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
STRATS = (("avalanche", "Highest rate first"), ("snowball", "Smallest balance first"))


class Refused(Exception):
    pass


def ym(s, where):
    m = re.fullmatch(r"(\d{4})-(\d{2})", str(s or ""))
    if not m or not 1 <= int(m.group(2)) <= 12:
        raise Refused(f"{where}: dates are written YYYY-MM, like 2027-06 (got {s!r})")
    return int(m.group(1)) * 12 + int(m.group(2)) - 1


def label(index):
    return f"{MONTHS[index % 12]} {index // 12}"


def num(v, where, field):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise Refused(f"{where}: {field} must be a number (got {v!r})")
    return float(v)


def build(spec):
    errs, warns = [], []
    for k in ("id", "title", "start", "monthly_amount"):
        if spec.get(k) in (None, ""):
            errs.append(f"missing top-level field '{k}'")
    if errs:
        raise Refused("\n".join(errs))
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", str(spec["id"])):
        errs.append("id must be lowercase letters, digits and '-'")
    look = spec.get("look", {})
    if look.get("font", "rounded") not in FONTS:
        errs.append(f"look.font must be one of {sorted(FONTS)}")
    if look.get("bg", "auto") not in COLOURS:
        errs.append(f"look.bg must be one of {sorted(COLOURS)}")
    sym = spec.get("currency_symbol", "$")
    start = ym(spec["start"], "start")
    monthly = num(spec["monthly_amount"], "monthly_amount", "monthly_amount")
    if monthly <= 0:
        errs.append("monthly_amount must be more than 0: it is everything they can put toward debts and goals each month")
    debts_in, goals_in = spec.get("debts", []), spec.get("goals", [])
    if not debts_in and not goals_in:
        errs.append("a plan needs at least one debt or one goal")

    # ---- debts
    debts, seen = [], {}
    for i, d in enumerate(debts_in):
        where = f"debt {i+1} ({d.get('name', '?')!r})"
        name = str(d.get("name", "")).strip()
        try:
            bal = num(d.get("balance"), where, "balance")
            apr = num(d.get("apr"), where, "apr")
            mn = num(d.get("minimum"), where, "minimum")
        except Refused as e:
            errs.append(str(e)); continue
        if not name:
            errs.append(f"{where}: every debt needs a name")
        elif name.casefold() in seen:
            errs.append(f"{where}: two debts are called {name!r}; give each a different name so the plan can tell them apart")
        seen.setdefault(name.casefold(), i)
        if bal <= 0:
            errs.append(f"{where}: the balance must be more than 0")
        if not 0 <= apr <= 100:
            errs.append(f"{where}: the interest rate is a yearly percentage between 0 and 100 (got {apr})")
        if mn <= 0:
            errs.append(f"{where}: the minimum payment must be more than 0")
        if bal > 0 and 0 < apr <= 100 and mn > 0:
            interest = bal * apr / 100 / 12
            if mn <= interest:
                errs.append(f"{where}: the minimum payment ({sym}{mn:,.2f}) does not cover the "
                            f"{sym}{interest:,.2f} of interest this debt adds every month, so paying the "
                            f"minimum would never clear it - the balance stays the same or grows. Check the "
                            f"figures with the person; if they are right, say so plainly before planning")
        debts.append({"name": name, "balance": bal, "apr": apr, "minimum": mn})
    extra = num(spec.get("extra", 0), "extra", "extra")
    if extra < 0:
        errs.append("extra cannot be negative")

    # ---- goals
    goals = []
    for i, g in enumerate(goals_in):
        where = f"goal {i+1} ({g.get('name', '?')!r})"
        try:
            target = num(g.get("target"), where, "target")
            saved = num(g.get("saved", 0), where, "saved")
            ret = num(g.get("return", 3.0), where, "return")
            by = ym(g.get("by"), where)
        except Refused as e:
            errs.append(str(e)); continue
        if not str(g.get("name", "")).strip():
            errs.append(f"{where}: every goal needs a name")
        if target <= 0:
            errs.append(f"{where}: the target must be more than 0")
        if saved < 0:
            errs.append(f"{where}: already saved cannot be negative")
        if not 0 <= ret <= 12:
            errs.append(f"{where}: the assumed return is a yearly percentage between 0 and 12 (got {ret})")
        months = by - start + 1
        if months < 1:
            errs.append(f"{where}: the date {label(by)} is not after the plan starts ({label(start)}) - "
                        f"ask for a date in the future")
            continue
        if months <= 36 and ret > 5:
            warns.append(f"{where}: {ret}% a year is optimistic for money needed within 3 years, which usually sits in savings")
        need = SavingsGoals.required_monthly_savings(target, ret / 100, months / 12, current_savings=saved)
        if saved >= target:
            warns.append(f"{where}: already reached - nothing more to save")
        goals.append({"name": str(g.get("name")).strip(), "target": target, "saved": saved, "ret": ret,
                      "by": label(by), "months": months, "monthly": math.ceil(round(need * 100, 6)) / 100,  # rounded UP: following the plan must reach the target
                      "stretch": bool(g.get("stretch"))})
    if errs:
        raise Refused("\n".join(errs))

    # ---- debts: both strategies, all the maths in debt_management.py
    strategies = {}
    if debts:
        dm = DebtManagement([Debt(d["name"], d["balance"], d["apr"] / 100, d["minimum"]) for d in debts], extra)
        for key, name in STRATS:
            r = dm.payoff_avalanche() if key == "avalanche" else dm.payoff_snowball()
            if r["total_months"] >= 1200:
                raise Refused("these debts would take 100 years to clear at these payments")
            order = [{"name": o["name"], "month": o["month_paid_off"], "label": label(start + o["month_paid_off"] - 1),
                      "interest": o["interest_paid"]} for o in r["payoff_order"]]
            series = [round(sum(d["balance"] for d in debts), 2)] + [round(sum(h.values()), 2) for h in r["history"]]
            strategies[key] = {"name": name, "months": r["total_months"], "interest": r["total_interest"],
                               "paid": r["total_paid"], "free": label(start + r["total_months"] - 1),
                               "first": order[0], "order": order, "series": series}
            if r["total_months"] > 360:
                warns.append(f"{name}: about {r['total_months'] // 12} years to clear everything - more each month would shorten it a lot")
        av, sb = strategies["avalanche"], strategies["snowball"]
        diff = round(sb["interest"] - av["interest"], 2)
        best = "avalanche" if diff > 0.5 else "snowball" if diff < -0.5 else "avalanche"
        strategies["best"] = best
        strategies["saving"] = abs(diff)

    # ---- does it fit?
    minimums = round(sum(d["minimum"] for d in debts), 2)
    goals_total = round(sum(g["monthly"] for g in goals), 2)
    need_total = round(minimums + (extra if debts else 0) + goals_total, 2)
    short = round(need_total - monthly, 2)
    if short > 0.5 and not any(g["stretch"] for g in goals):
        parts = [f"minimum payments {sym}{minimums:,.0f}"] if debts else []
        if debts and extra:
            parts.append(f"extra toward debts {sym}{extra:,.0f}")
        parts += [f"{g['name']} {sym}{g['monthly']:,.0f}" for g in goals]
        raise Refused(f"this plan needs {sym}{need_total:,.0f} a month ({' + '.join(parts)}) but the person said "
                      f"they can put in {sym}{monthly:,.0f} - {sym}{short:,.0f} too much.\n"
                      f"Ask them which to change: a later date for a goal, a smaller target, less extra toward "
                      f"debts, or keep it as a stretch (add \"stretch\": true to the goal) and show the gap")

    data = {
        "id": spec["id"], "title": spec["title"], "subtitle": spec.get("subtitle", ""), "sym": sym,
        "builtOn": spec.get("builtOn") or datetime.date.today().strftime("%-d %B %Y"),
        "start": label(start), "startIndex": start,
        "look": {"font": look.get("font", "rounded"), "bg": look.get("bg", "auto")},
        "debts": debts, "extra": extra, "strategies": strategies, "goals": goals,
        "budget": {"monthly": monthly, "minimums": minimums, "extra": extra if debts else 0,
                   "goals": goals_total, "need": need_total, "short": max(short, 0) if short > 0.5 else 0},
        "freed": round(minimums + extra, 2) if debts else 0,
    }
    return data, warns


def render(data):
    page = open(ENGINE, encoding="utf-8").read()
    for slot in ("/*__PLAN__*/null", "__TITLE__"):
        if page.count(slot) != 1:
            raise Refused(f"engine.html must contain {slot} exactly once")
    blob = json.dumps(data, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    page = page.replace("/*__PLAN__*/null", blob).replace("__TITLE__", html.escape(data["title"]))
    if re.search(r"fetch\(|XMLHttpRequest|<script[^>]+src=|<link[^>]+href=\"?https?:", page):
        raise Refused("the page would reach the network")
    return page


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        spec = json.load(open(a.plan, encoding="utf-8"))
        data, warns = build(spec)
        page = render(data)
    except Refused as e:
        print("REFUSED TO BUILD\n  " + str(e).replace("\n", "\n  "), file=sys.stderr); sys.exit(2)
    except (OSError, json.JSONDecodeError) as e:
        print(f"REFUSED TO BUILD\n  could not read {a.plan}: {e}", file=sys.stderr); sys.exit(2)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(page)
    for w in warns:
        print("WARN  " + w)
    s, sym = data["strategies"], data["sym"]
    line = f"built {os.path.basename(a.out)}  {len(data['debts'])} debts  {len(data['goals'])} goals"
    if s:
        b = s[s["best"]]
        line += f"  debt-free {b['free']} ({b['name'].lower()})  interest {sym}{b['interest']:,.0f}"
    line += f"  needs {sym}{data['budget']['need']:,.0f}/mo of {sym}{data['budget']['monthly']:,.0f}"
    print(line + f"  {len(page)//1024} KB")


if __name__ == "__main__":
    main()
