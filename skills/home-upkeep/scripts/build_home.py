#!/usr/bin/env python3
"""Build a year of home upkeep: home.json -> one self-contained HTML page (+ an .ics calendar).

The model writes home.json: where the home is, what it has, which jobs from
reference/jobs.json apply, any custom jobs, when jobs were last done, the start
month. It never writes a date. This script works out every date: it expands each
job over the twelve months from the start, honours last-done dates, puts seasonal
jobs in the right months for the hemisphere, and spreads the load so that no
week (Monday to Sunday) holds more than MAX_PER_WEEK jobs. To spread, a job moves
by at most one week, and a safety job only ever moves EARLIER, never past its due
date. Then it fills the fixed page in assets/engine.html and, with --ics, writes
the same calendar the page's "Download calendar" button builds.

It REFUSES to build (exit 2, with the reason) when:
  - a job has neither an interval ("every", months) nor a season
  - an interval is not a whole number of months from 1 to 60
  - a job id is not in reference/jobs.json, or a job is listed twice
  - a custom job has no "why"
  - the start month is before today (today is the machine's real date; a "builtOn" that differs from it
    is refused unless the file also says "example": true - only the shipped example and test fixtures do)
  - a last-done date is in the future
  - a feature is not one the reference knows, or a job needs a feature the home lacks
  - the plan is empty
  - the jobs cannot be spread to MAX_PER_WEEK a week within the rules above
  - the finished page would reach the network

    python3 build_home.py home.json --out plan.html [--ics plan.ics] [--explain]
"""
import argparse, calendar, datetime as dt, heapq, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, "..", "assets", "engine.html")
JOBS = os.path.join(HERE, "..", "reference", "jobs.json")

MAX_PER_WEEK = 3          # no Monday-to-Sunday week holds more jobs than this
SHIFT_DAYS = 7            # a job moves at most this far to make room (safety jobs: earlier only)
CATCHUP_SAFETY_DAYS = 42  # an overdue or never-recorded safety job lands within this many days of the start
CATCHUP_MAX_MONTHS = 3    # other overdue jobs are spread over at most this many months (or their interval, if shorter)
CATCHUP_SEASON_DAYS = 91 # ...and a seasonal safety job that was missed is done now if its next slot is further off than this
SEASON_SKIP_DAYS = 60     # a seasonal job done this recently before its slot is not repeated in that slot

FONTS = {"rounded", "clear", "story", "hand"}
COLOURS = {"auto", "snow", "sky", "pine", "sunset", "berry", "night"}
HOME_TYPES = {"house": "House", "townhouse": "Townhouse", "flat": "Flat", "apartment": "Apartment", "condo": "Condo"}
TENURE = {"own": "owned", "rent": "rented"}
ENTRY_KEYS = {"id", "last_done", "every"}
CUSTOM_KEYS = {"title", "why", "every", "season", "who", "minutes", "safety", "last_done"}
WHO = {"diy": "DIY", "pro": "Professional", "landlord": "Landlord"}


class Refused(Exception):
    pass


# ---------- dates ----------
def parse_built(s):
    for f in ("%d %B %Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s, f).date()
        except (TypeError, ValueError):
            pass
    raise Refused(f'builtOn "{s}" is not a date like "7 October 2026"')


def parse_day(s, what):
    if not isinstance(s, str):
        raise Refused(f"{what} must be a date like 2026-04-15 or a month like 2026-04")
    try:
        if re.fullmatch(r"\d{4}-\d{2}", s):
            return dt.datetime.strptime(s + "-01", "%Y-%m-%d").date(), True
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            return dt.datetime.strptime(s, "%Y-%m-%d").date(), False
    except ValueError:
        pass
    raise Refused(f'{what} "{s}" is not a date like 2026-04-15 or a month like 2026-04')


def add_months(d, n):
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def monday(d):
    return d - dt.timedelta(days=d.weekday())


def first_saturday(y, m):
    d = dt.date(y, m, 1)
    return d + dt.timedelta(days=(5 - d.weekday()) % 7)


def day_label(d):
    return d.strftime("%a ") + str(d.day) + d.strftime(" %b")


def long_label(d):
    return d.strftime("%a ") + str(d.day) + d.strftime(" %B %Y")


def hours(mins):
    h, m = divmod(mins, 60)
    return f"{h} h {m} min" if h and m else f"{h} h" if h else f"{m} min"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


# ---------- the calendar file (assets/engine.html builds the same bytes in the page) ----------
def ics_escape(s):
    s = str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    return re.sub(r"\r\n|\r|\n", lambda _: "\\n", s)


def ics_fold(line):
    out, cur, n = [], "", 0
    for ch in line:
        b = len(ch.encode("utf-8"))
        if n + b > 75:
            out.append(cur)
            cur, n = " ", 1
        cur += ch
        n += b
    out.append(cur)
    return "\r\n".join(out)


def ics_text(ics):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:" + ics["prodid"], "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             "X-WR-CALNAME:" + ics_escape(ics["calname"])]
    for e in ics["events"]:
        lines += ["BEGIN:VEVENT", "UID:" + e["uid"], "DTSTAMP:" + ics["dtstamp"],
                  "DTSTART;VALUE=DATE:" + e["start"], "DTEND;VALUE=DATE:" + e["end"],
                  "SUMMARY:" + ics_escape(e["summary"]), "DESCRIPTION:" + ics_escape(e["description"]),
                  "TRANSP:TRANSPARENT", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(ics_fold(l) for l in lines) + "\r\n"


# ---------- validate ----------
def build(spec):
    ref = json.load(open(JOBS, encoding="utf-8"))
    FEATURES, SEASONS = ref["features"], {k: v for k, v in ref["seasons"].items() if not k.startswith("_")}
    REF = {j["id"]: j for j in ref["jobs"]}
    warns = []

    pid = spec.get("id", "")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,60}", str(pid)):
        raise Refused(f'id "{pid}" must be lower-case letters, digits and hyphens (it names the saved ticks and the calendar)')
    title = str(spec.get("title", "")).strip()
    if not title:
        raise Refused("the plan needs a title")
    real = dt.date.today()
    today = parse_built(spec["builtOn"]) if spec.get("builtOn") else real
    if today != real and spec.get("example") is not True:
        raise Refused(f'builtOn "{spec["builtOn"]}" is not today ({real.strftime("%-d %B %Y")}): leave builtOn out and the '
                      f'build uses the real date. Only a pinned example or test fixture may set it, with "example": true.')
    words = spec.get("words", "us")
    if words not in ("us", "uk"):
        raise Refused(f'words "{words}" must be "us" or "uk"')
    hemi = spec.get("hemisphere", "north")
    if hemi not in ("north", "south"):
        raise Refused(f'hemisphere "{hemi}" must be "north" or "south"')
    region = str(spec.get("region", "")).strip()
    if not region:
        raise Refused("region is missing: say where the home is (it sets the seasons and the wording)")
    home = spec.get("home") or {}
    if home.get("type") not in HOME_TYPES:
        raise Refused(f'home type "{home.get("type")}" must be one of: ' + ", ".join(HOME_TYPES))
    if home.get("tenure") not in TENURE:
        raise Refused(f'home tenure "{home.get("tenure")}" must be "own" or "rent"')
    renting = home["tenure"] == "rent"
    feats = spec.get("features", [])
    if not isinstance(feats, list):
        raise Refused("features must be a list")
    for f in feats:
        if f not in FEATURES:
            raise Refused(f'unknown feature "{f}" - the features this skill knows are: ' + ", ".join(FEATURES))
    feats = set(feats)
    look = spec.get("look") or {}
    if look.get("font", "rounded") not in FONTS or look.get("bg", "auto") not in COLOURS:
        raise Refused("look.font must be one of " + "/".join(sorted(FONTS)) + " and look.bg one of " + "/".join(sorted(COLOURS)))

    s_raw = spec.get("start")
    sd, month_only = parse_day(s_raw, "start")
    first_of_start = sd.replace(day=1)
    if month_only:
        if first_of_start < today.replace(day=1):
            raise Refused(f'start month {s_raw} is before today ({today.isoformat()}): a plan starts this month or later')
        start = max(sd, today)
    else:
        if sd < today:
            raise Refused(f'start date {s_raw} is before today ({today.isoformat()}): a plan starts today or later')
        start = sd
    end = add_months(first_of_start, 12)          # exclusive: twelve whole calendar months, the first may be partial

    def season_month(key):
        m = SEASONS[key]["north"]
        return m if hemi == "north" else (m + 5) % 12 + 1

    # ---- the job list ----
    jobs, seen_titles = [], {}

    def check_every(v, who):
        if isinstance(v, bool) or not isinstance(v, int) or v <= 0 or v > 60:
            raise Refused(f'{who}: every {v!r} must be a whole number of months from 1 to 60')
        return v

    def check_last(v, who):
        if v is None:
            return None
        d, _ = parse_day(v, f"{who}: last_done")
        if d > today:
            raise Refused(f'{who}: last_done {v} is in the future (today is {today.isoformat()})')
        return d

    for e in spec.get("jobs", []):
        jid = e.get("id")
        extra = set(e) - ENTRY_KEYS
        if extra:
            raise Refused(f'job "{jid}": unknown field(s) {", ".join(sorted(extra))} - a job entry takes id, last_done and every')
        if jid not in REF:
            raise Refused(f'unknown job id "{jid}" - it is not in reference/jobs.json (write it as a custom job instead)')
        if any(j["id"] == jid for j in jobs):
            raise Refused(f'job "{jid}" is listed twice')
        r = REF[jid]
        if r["applies_if"] and not feats & set(r["applies_if"]):
            raise Refused(f'job "{jid}" needs one of these features, which the home does not list: ' + ", ".join(r["applies_if"]))
        every = r.get("every")
        if "every" in e:
            if r.get("season"):
                raise Refused(f'job "{jid}" is seasonal ({", ".join(r["season"])}); it has no interval to change')
            every = check_every(e["every"], f'job "{jid}"')
        t = r.get("title_uk") if words == "uk" and r.get("title_uk") else r["title"]
        y = r.get("why_uk") if words == "uk" and r.get("why_uk") else r["why"]
        who = r.get("who_uk") if words == "uk" and r.get("who_uk") else r["who"]
        mins = r.get("est_minutes_uk") if words == "uk" and r.get("est_minutes_uk") else r["est_minutes"]
        if renting and r["landlord"]:
            t, who, mins = "Remind your landlord: " + t[0].lower() + t[1:], "landlord", 5
        jobs.append({"id": jid, "title": t, "why": y, "every": every, "season": r.get("season"), "who": who,
                     "minutes": mins, "safety": bool(r["safety"]), "last": check_last(e.get("last_done"), f'job "{jid}"'),
                     "custom": False, "ref_title": r["title"]})

    for c in spec.get("custom", []):
        ct = str(c.get("title", "")).strip()
        who = f'custom job "{ct or "(no title)"}"'
        if not ct:
            raise Refused("a custom job has no title")
        extra = set(c) - CUSTOM_KEYS
        if extra:
            raise Refused(f'{who}: unknown field(s) {", ".join(sorted(extra))}')
        if not str(c.get("why", "")).strip():
            raise Refused(f'{who} has no "why": one line on what goes wrong if it is skipped')
        has_e, has_s = c.get("every") is not None, bool(c.get("season"))
        if not has_e and not has_s:
            raise Refused(f'{who} has neither an interval ("every", in months) nor a season')
        if has_e and has_s:
            raise Refused(f'{who}: give "every" or "season", not both')
        every = check_every(c["every"], who) if has_e else None
        season = None
        if has_s:
            season = c["season"] if isinstance(c["season"], list) else [c["season"]]
            for s in season:
                if s not in SEASONS:
                    raise Refused(f'{who}: unknown season "{s}" - use one of: ' + ", ".join(SEASONS))
        if c.get("who", "diy") not in WHO:
            raise Refused(f'{who}: who must be diy, pro or landlord')
        mins = c.get("minutes")
        if isinstance(mins, bool) or not isinstance(mins, int) or not 1 <= mins <= 600:
            raise Refused(f'{who}: minutes must be a whole number from 1 to 600 (a rough guess is fine)')
        jid = "custom-" + slug(ct)
        if any(j["id"] == jid for j in jobs) or any(j["ref_title"].lower() == ct.lower() or j["title"].lower() == ct.lower() for j in jobs):
            raise Refused(f'{who} is listed twice, or repeats a standard job')
        jobs.append({"id": jid, "title": ct, "why": str(c["why"]).strip(), "every": every, "season": season,
                     "who": c.get("who", "diy"), "minutes": mins, "safety": bool(c.get("safety", False)),
                     "last": check_last(c.get("last_done"), who), "custom": True, "ref_title": ct})

    for j in jobs:
        if not j["every"] and not j["season"]:
            raise Refused(f'job "{j["id"]}" has neither an interval nor a season')
    if not jobs:
        raise Refused("the plan is empty: choose at least one job from reference/jobs.json or add a custom one")

    chosen = {j["id"] for j in jobs}
    for r in ref["jobs"]:
        if r["safety"] and r["id"] not in chosen and (not r["applies_if"] or feats & set(r["applies_if"])):
            warns.append(f'safety job "{r.get("title_uk") if words == "uk" and r.get("title_uk") else r["title"]}" fits this home but is not in the plan - leave it out only if they said so')
    if "smoke_alarms" not in feats:
        warns.append("no smoke alarms listed - every home should have them; check that is right")

    # ---- dates: every occurrence, spread so no week holds more than MAX_PER_WEEK ----
    load, placed, later, skipped, heap, seq = {}, [], [], [], [], [0]

    def push(item):
        seq[0] += 1
        heapq.heappush(heap, (item["latest"], 0 if item["job"]["safety"] else 1, item["preferred"], item["job"]["id"], seq[0], item))

    def regular(job, nominal, chain):
        lo = max(start, nominal - dt.timedelta(days=SHIFT_DAYS))
        hi = nominal if job["safety"] else min(end - dt.timedelta(days=1), nominal + dt.timedelta(days=SHIFT_DAYS))
        cands = [d for d in (nominal, nominal - dt.timedelta(days=SHIFT_DAYS), nominal + dt.timedelta(days=SHIFT_DAYS)) if lo <= d <= hi]
        push({"job": job, "kind": "due", "nominal": nominal, "preferred": nominal, "latest": hi, "cands": cands, "chain": chain})

    def window(job, kind, frm, to, chain, nominal=None):
        # the first day, then every Saturday after it, up to the last day allowed: one try per week
        cands, d = [frm], frm + dt.timedelta(days=(5 - frm.weekday()) % 7 or 7)
        while d <= to:
            cands.append(d)
            d += dt.timedelta(days=7)
        push({"job": job, "kind": kind, "nominal": nominal or frm, "preferred": frm, "latest": to, "cands": cands, "chain": chain})

    # seasonal slots: jobs sharing a month take its 1st, 2nd, 3rd, 4th Saturday in turn, in id order
    slots = []
    for j in sorted(jobs, key=lambda x: x["id"]):
        for s in j["season"] or []:
            m = season_month(s)
            y = first_of_start.year if m >= first_of_start.month else first_of_start.year + 1
            slots.append((dt.date(y, m, 1), j, s))
    turn, first_slot = {}, {}
    for month1, j, s in sorted(slots, key=lambda x: (x[0], x[1]["id"])):
        w = turn.get(month1, 0)
        turn[month1] = w + 1
        nominal = first_saturday(month1.year, month1.month) + dt.timedelta(days=7 * (w % 4))
        first_slot[j["id"]] = min(first_slot.get(j["id"], nominal), nominal)
        if j["last"] and (nominal - j["last"]).days < SEASON_SKIP_DAYS:
            skipped.append((j, s, nominal))
            continue
        j.setdefault("season_label", {})[nominal] = SEASONS[s][words]
        if nominal < start:   # this month's slot has passed: fit it in before the month is out
            month_end = dt.date(month1.year, month1.month, calendar.monthrange(month1.year, month1.month)[1])
            window(j, "season", start, max(start, month_end), None, nominal=start)
        else:
            regular(j, nominal, None)
    # a seasonal SAFETY job whose last slot was missed (or never recorded) does not wait months for its next one
    for j in sorted(jobs, key=lambda x: x["id"]):
        if not (j["season"] and j["safety"]) or j["id"] not in first_slot:
            continue
        fs, gap = first_slot[j["id"]], 365 // len(j["season"]) + 31
        if (fs - start).days > CATCHUP_SEASON_DAYS and (j["last"] is None or (fs - j["last"]).days > gap):
            window(j, "catch-up", start, start + dt.timedelta(days=CATCHUP_SAFETY_DAYS - 1), None)

    for j in sorted(jobs, key=lambda x: x["id"]):
        if not j["every"]:
            continue
        e = j["every"]
        if j["last"] and add_months(j["last"], e) >= start:
            nxt = add_months(j["last"], e)
            if nxt < end:
                regular(j, nxt, (j["last"], 1))
            else:
                later.append((j, nxt))
        else:   # overdue, or never recorded: due now, spread over the first weeks
            to = start + dt.timedelta(days=CATCHUP_SAFETY_DAYS - 1) if j["safety"] else \
                add_months(start, min(e, CATCHUP_MAX_MONTHS)) - dt.timedelta(days=1)
            window(j, "catch-up", start, min(to, end - dt.timedelta(days=1)), "first")

    while heap:
        it = heapq.heappop(heap)[-1]
        j = it["job"]
        spot = next((d for d in it["cands"] if load.get(monday(d), 0) < MAX_PER_WEEK), None)
        if spot is None:
            wk = monday(it["cands"][0] if it["cands"] else it["preferred"])
            raise Refused(f'cannot spread the jobs to {MAX_PER_WEEK} a week: "{j["title"]}" (due {long_label(it["latest"])}) '
                          f'finds every week it may move to full, from the week of {long_label(wk)}. '
                          f'Drop a job, lengthen an interval, or move a last-done date.')
        load[monday(spot)] = load.get(monday(spot), 0) + 1
        placed.append({"job": j, "date": spot, "kind": it["kind"], "nominal": it["nominal"], "latest": it["latest"]})
        ch = it["chain"]
        if ch:
            base, k = (spot, 1) if ch == "first" else (ch[0], ch[1] + 1)
            nxt = add_months(base, j["every"] * k)
            if nxt < end:
                regular(j, nxt, (base, k))

    # ---- check what was done before anything is shown ----
    weeks = {}
    for p in placed:
        weeks[monday(p["date"])] = weeks.get(monday(p["date"]), 0) + 1
        if not start <= p["date"] < end:
            raise Refused(f'internal check: {p["job"]["id"]} landed outside the plan on {p["date"]}')
        if p["date"] > p["latest"]:
            raise Refused(f'internal check: {p["job"]["id"]} landed after its due date')
        if p["job"]["safety"] and p["kind"] == "due" and p["date"] > p["nominal"]:
            raise Refused(f'internal check: safety job {p["job"]["id"]} moved past its due date')
    if max(weeks.values()) > MAX_PER_WEEK:
        raise Refused("internal check: a week holds more than %d jobs" % MAX_PER_WEEK)
    uids = [f'{p["job"]["id"]}-{p["date"].strftime("%Y%m%d")}@home-upkeep.{pid}' for p in placed]
    if len(set(uids)) != len(uids):
        raise Refused("internal check: two calendar entries share an id")

    # ---- page data ----
    placed.sort(key=lambda p: (p["date"], 0 if p["job"]["safety"] else 1, p["job"]["title"]))
    months, ics_events = [], []
    for i in range(12):
        m1 = add_months(first_of_start, i)
        items = [p for p in placed if p["date"].year == m1.year and p["date"].month == m1.month]
        mins = sum(p["job"]["minutes"] for p in items)
        rows = []
        for p in items:
            j, d = p["job"], p["date"]
            uid = f'{j["id"]}-{d.strftime("%Y%m%d")}@home-upkeep.{pid}'
            moved = ""
            if p["kind"] == "due" and d != p["nominal"]:
                moved = ("a week early, to keep that week light" if d < p["nominal"] else "a week late, to keep that week light")
            note = {"catch-up": "Overdue or never recorded, so it comes first",
                    "season": "This month's slot has passed"}.get(p["kind"], "")
            if p["kind"] == "due" and j["season"]:
                note = "Every " + j["season_label"].get(p["nominal"], "season")
            elif p["kind"] == "due" and j["every"]:
                note = "Every month" if j["every"] == 1 else f'Every {j["every"]} months'
            rows.append({"uid": uid, "date": d.isoformat(), "day": day_label(d), "title": j["title"], "why": j["why"],
                         "who": j["who"], "whoLabel": WHO[j["who"]], "minutes": j["minutes"], "safety": j["safety"],
                         "custom": j["custom"], "note": note, "moved": moved})
            who_line = {"diy": f'DIY, about {hours(j["minutes"])}', "pro": f'Book a professional, about {hours(j["minutes"])}',
                        "landlord": "The landlord's job: send them a message"}[j["who"]]
            ics_events.append({"uid": uid, "start": d.strftime("%Y%m%d"), "end": (d + dt.timedelta(days=1)).strftime("%Y%m%d"),
                               "summary": j["title"], "description": j["why"] + "\n" + who_line +
                               ("\nSafety job: do not put it off." if j["safety"] else "")})
        months.append({"key": m1.strftime("%Y-%m"), "label": m1.strftime("%B %Y"), "quarter": i // 3,
                       "count": len(items), "minutes": mins, "time": hours(mins), "items": rows})
    quarters = []
    for q in range(4):
        a, b = add_months(first_of_start, 3 * q), add_months(first_of_start, 3 * q + 2)
        quarters.append({"n": q + 1, "label": a.strftime("%b %Y") + " – " + b.strftime("%b %Y")})
    later_rows = []
    for j, nxt in sorted(later, key=lambda x: (x[1], x[0]["title"])):
        later_rows.append({"title": j["title"], "note": f'Next due {nxt.strftime("%B %Y")}' +
                           (f' (last done {j["last"].strftime("%B %Y")})' if j["last"] else "")})
    for j, s, nominal in skipped:
        later_rows.append({"title": j["title"], "note": f'{SEASONS[s][words].capitalize()} slot skipped: done {j["last"].strftime("%-d %B %Y")}, '
                           f'under {SEASON_SKIP_DAYS} days before it'})

    total = sum(p["job"]["minutes"] for p in placed)
    busiest = max(weeks.values())
    when = first_of_start.strftime("%B %Y") + " to " + add_months(first_of_start, 11).strftime("%B %Y")
    data = {
        "id": pid, "title": title, "words": words,
        "subtitle": f'{region} · {HOME_TYPES[home["type"]]}, {TENURE[home["tenure"]]} · {when}',
        "builtOn": today.strftime("%-d %B %Y"),
        "look": {"font": look.get("font", "rounded"), "bg": look.get("bg", "auto")},
        "facts": {"jobs": len(jobs), "dates": len(placed), "time": hours(total), "busiest": busiest, "cap": MAX_PER_WEEK,
                  "starts": long_label(start)},
        "months": months, "quarters": quarters, "later": later_rows,
        "rules": [f"No week (Monday to Sunday) has more than {MAX_PER_WEEK} jobs. To make room a job moves by at most a week; "
                  f"a safety job only ever moves earlier, never past its due date.",
                  f"A job that is overdue, or whose last date you didn't know, is treated as due now: safety jobs land in the "
                  f"first {CATCHUP_SAFETY_DAYS // 7} weeks, the rest are spread over the first {CATCHUP_MAX_MONTHS} months, "
                  f"and the next ones follow on from there. A seasonal safety job that missed its last slot is done now "
                  f"too, when its next slot is more than {CATCHUP_SEASON_DAYS // 30} months away.",
                  "Seasons are for the " + ("southern" if hemi == "south" else "northern") + " hemisphere; seasonal jobs fall on a Saturday.",
                  "Intervals are the common, conservative ones. A manual, an installer or local rules can say sooner: follow them."],
        "ics": {"name": pid + ".ics", "prodid": "-//AI 101 Bootcamp//home-upkeep//EN", "calname": title,
                "dtstamp": today.strftime("%Y%m%d") + "T000000Z", "events": ics_events},
    }
    return data, warns, placed, skipped


def render(data):
    page = open(ENGINE, encoding="utf-8").read()
    for slot in ("/*__HOME__*/null", "__TITLE__"):
        if page.count(slot) != 1:
            raise Refused(f"engine.html must contain {slot} exactly once")
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = page.replace("/*__HOME__*/null", blob).replace("__TITLE__", html.escape(data["title"]))
    if re.search(r"fetch\(|XMLHttpRequest|<script[^>]+src=|<link[^>]+href=\"?https?:|<img[^>]+src=\"?https?:", page):
        raise Refused("the page would reach the network")
    return page


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("home"); ap.add_argument("--out", required=True)
    ap.add_argument("--ics", help="also write the calendar file the page's button downloads")
    ap.add_argument("--explain", action="store_true", help="print every date and why it is there")
    a = ap.parse_args()
    try:
        spec = json.load(open(a.home, encoding="utf-8"))
        data, warns, placed, skipped = build(spec)
        page = render(data)
    except Refused as e:
        print("REFUSED TO BUILD\n  " + str(e).replace("\n", "\n  "), file=sys.stderr); sys.exit(2)
    except (OSError, json.JSONDecodeError) as e:
        print(f"REFUSED TO BUILD\n  could not read {a.home}: {e}", file=sys.stderr); sys.exit(2)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(page)
    if a.ics:
        with open(a.ics, "w", encoding="utf-8", newline="") as f:
            f.write(ics_text(data["ics"]))
    for w in warns:
        print("WARN  " + w)
    if a.explain:
        print("OCC\tdate\tdue_by\tnominal\tkind\tsafety\tjob")
        for p in sorted(placed, key=lambda p: (p["date"], p["job"]["id"])):
            print(f'OCC\t{p["date"]}\t{p["latest"]}\t{p["nominal"]}\t{p["kind"]}\t{int(p["job"]["safety"])}\t{p["job"]["id"]}')
        for j, s, nominal in skipped:
            print(f'SKIP\t{nominal}\t{s}\t{j["id"]}\tdone {j["last"]}')
    f = data["facts"]
    print(f'built {os.path.basename(a.out)}  {f["jobs"]} jobs  {f["dates"]} dates  {f["time"]} in the year  '
          f'busiest week {f["busiest"]} of {f["cap"]}  starts {f["starts"]}  {len(page)//1024} KB'
          + (f'  + {os.path.basename(a.ics)} ({len(data["ics"]["events"])} events)' if a.ics else ""))


if __name__ == "__main__":
    main()
