"""validate_ics.py <file.ics> [--max-per-week N] : checks a calendar file against the parts of RFC 5545 this
skill relies on, without trusting the code that wrote it. Exit 1 with every problem listed, else one ok line.
  - CRLF line endings only; every physical line <= 75 octets and valid UTF-8 on its own (no split characters)
  - VCALENDAR with VERSION:2.0 and PRODID; balanced VEVENTs
  - each VEVENT: one UID (unique), DTSTAMP (UTC), DTSTART;VALUE=DATE and DTEND;VALUE=DATE the next day,
    SUMMARY and DESCRIPTION; TEXT values escaped (no bare , or ; and only \\\\ \; \\, \\n escapes)
  - optional: no Monday-to-Sunday week holds more than N events"""
import datetime as dt, re, sys

def unescape(v):
    out, i = [], 0
    while i < len(v):
        c = v[i]
        if c == "\\":
            if i + 1 >= len(v) or v[i + 1] not in "\;,nN":
                raise ValueError("bad escape at %d" % i)
            out.append("\n" if v[i + 1] in "nN" else v[i + 1]); i += 2; continue
        if c in ",;":
            raise ValueError("unescaped %r at %d" % (c, i))
        out.append(c); i += 1
    return "".join(out)

def parse(raw):
    errs = []
    if not raw.endswith(b"\r\n"): errs.append("file does not end with CRLF")
    if raw.count(b"\n") != raw.count(b"\r\n") or raw.count(b"\r") != raw.count(b"\r\n"): errs.append("a line ending is not CRLF")
    phys = raw[:-2].split(b"\r\n") if raw.endswith(b"\r\n") else raw.split(b"\r\n")
    folded = 0
    for n, p in enumerate(phys, 1):
        if len(p) > 75: errs.append("line %d is %d octets (max 75)" % (n, len(p)))
        try: p.decode("utf-8")
        except UnicodeDecodeError: errs.append("line %d splits a UTF-8 character" % n)
        if p.startswith(b" "): folded += 1
    logical = []
    for p in phys:
        s = p.decode("utf-8", "replace")
        if s.startswith(" ") and logical: logical[-1] += s[1:]
        else: logical.append(s)
    return logical, errs, folded, max(len(p) for p in phys)

def check(path, max_week=None):
    raw = open(path, "rb").read()
    L, errs, folded, longest = parse(raw)
    if not L or L[0] != "BEGIN:VCALENDAR" or L[-1] != "END:VCALENDAR": errs.append("not wrapped in BEGIN/END:VCALENDAR")
    if "VERSION:2.0" not in L: errs.append("no VERSION:2.0")
    if not any(l.startswith("PRODID:") and len(l) > 7 for l in L): errs.append("no PRODID")
    events, cur = [], None
    for l in L:
        if l == "BEGIN:VEVENT":
            if cur is not None: errs.append("nested VEVENT")
            cur = {}
        elif l == "END:VEVENT":
            if cur is None: errs.append("END:VEVENT without BEGIN")
            else: events.append(cur)
            cur = None
        elif cur is not None:
            name, _, val = l.partition(":")
            cur.setdefault(name, []).append(val)
        elif l.startswith("X-WR-CALNAME:"):
            try: unescape(l[13:])
            except ValueError as e: errs.append("X-WR-CALNAME: %s" % e)
    if cur is not None: errs.append("VEVENT not closed")
    uids, weeks, out = set(), {}, []
    for k, e in enumerate(events, 1):
        for need in ("UID", "DTSTAMP", "DTSTART;VALUE=DATE", "DTEND;VALUE=DATE", "SUMMARY", "DESCRIPTION"):
            if len(e.get(need, [])) != 1: errs.append("event %d: %s appears %d times" % (k, need, len(e.get(need, []))))
        if errs and any(len(e.get(n, [])) != 1 for n in ("UID", "DTSTART;VALUE=DATE", "DTEND;VALUE=DATE")): continue
        uid = e["UID"][0]
        if uid in uids: errs.append("event %d: duplicate UID %s" % (k, uid))
        uids.add(uid)
        if not re.fullmatch(r"\d{8}T\d{6}Z", e.get("DTSTAMP", [""])[0]): errs.append("event %d: DTSTAMP not UTC date-time" % k)
        try:
            s = dt.datetime.strptime(e["DTSTART;VALUE=DATE"][0], "%Y%m%d").date()
            d = dt.datetime.strptime(e["DTEND;VALUE=DATE"][0], "%Y%m%d").date()
            if d != s + dt.timedelta(days=1): errs.append("event %d: DTEND is not the day after DTSTART" % k)
            wk = s - dt.timedelta(days=s.weekday()); weeks[wk] = weeks.get(wk, 0) + 1
        except ValueError: errs.append("event %d: DTSTART/DTEND not YYYYMMDD" % k); continue
        txt = {}
        for f in ("SUMMARY", "DESCRIPTION"):
            try: txt[f] = unescape(e.get(f, [""])[0])
            except ValueError as x: errs.append("event %d %s: %s" % (k, f, x))
        out.append({"uid": uid, "date": s, **txt})
    if max_week and weeks and max(weeks.values()) > max_week:
        bad = [str(w) for w, n in sorted(weeks.items()) if n > max_week]
        errs.append("weeks with more than %d events: %s" % (max_week, ", ".join(bad)))
    return out, errs, folded, longest, (max(weeks.values()) if weeks else 0)

if __name__ == "__main__":
    a = sys.argv[1:]; mw = int(a[a.index("--max-per-week") + 1]) if "--max-per-week" in a else None
    ev, errs, folded, longest, busiest = check(a[0], mw)
    if errs:
        print("ics INVALID: " + a[0]); [print("  - " + x) for x in errs[:20]]; sys.exit(1)
    print("ics ok: %d events, %d folded lines, longest line %d octets, busiest week %d" % (len(ev), folded, longest, busiest))
