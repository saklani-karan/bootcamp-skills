"""check_plan.py <explain.txt> <first_day> <end_exclusive> : re-checks the dates the build printed with --explain,
without trusting the build's own self-check. Every rule the build claims:
  - every date inside the plan; no Monday-to-Sunday week over 3 jobs
  - a job "due" on a date moves at most 7 days; a SAFETY job never lands after its due date"""
import datetime as dt, sys
D = lambda s: dt.date.fromisoformat(s)
first, end = D(sys.argv[2]), D(sys.argv[3]); errs, weeks, n = [], {}, 0
for line in open(sys.argv[1]):
    p = line.rstrip("\n").split("\t")
    if p[0] != "OCC" or p[1] == "date": continue
    n += 1; date, due, nominal, kind, safety, job = D(p[1]), D(p[2]), D(p[3]), p[4], p[5] == "1", p[6]
    if not first <= date < end: errs.append(f"{job} {date} is outside {first}..{end}")
    if date > due: errs.append(f"{job} {date} is after its due-by {due}")
    if kind == "due" and abs((date - nominal).days) > 7: errs.append(f"{job} moved {(date - nominal).days} days")
    if kind == "due" and safety and date > nominal: errs.append(f"safety job {job} moved later, {nominal} -> {date}")
    wk = date - dt.timedelta(days=date.weekday()); weeks[wk] = weeks.get(wk, 0) + 1
over = [f"{w}={c}" for w, c in sorted(weeks.items()) if c > 3]
if over: errs.append("weeks over 3: " + ", ".join(over))
if errs: print("plan INVALID"); [print("  - " + e) for e in errs]; sys.exit(1)
print(f"plan ok: {n} dates, busiest week {max(weeks.values())}, every date in {first}..{end}, safety never late, moves <= 7 days")
