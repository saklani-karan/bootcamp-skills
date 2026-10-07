#!/bin/bash
# Every detector must be seen to fire FOR ITS OWN REASON. No pipes on the build command: a pipe swallows its exit code.
cd "$(dirname "$0")"; python3 make_fixtures.py
B=../scripts/build_home.py; out=$(mktemp -d); pass=0; fail=0
ok(){ pass=$((pass+1)); echo "ok    $*"; }; no(){ fail=$((fail+1)); echo "FAIL  $*"; }
expect(){ want=$1; shift; python3 $B "$@" --out $out/x.html --ics $out/x.ics --explain >$out/log 2>&1; got=$?
  if [ $got -eq $want ]; then ok "exit=$got  $*"; [ $got -eq 2 ] && sed -n 2p $out/log | sed 's/^ */        reason: /'
  else no "exit=$got want=$want  $*"; sed 's/^/      /' $out/log | head -5; fi; }

# --- the near-miss control: starts this month, last done today, intervals of 1 and 60, southern hemisphere, renting
expect 0 good.json
python3 check_plan.py $out/log 2026-10-07 2026-11-01 >/dev/null 2>&1; [ $? -eq 1 ] && ok "check_plan.py can fail (a too-short window is caught)" || no "check_plan.py cannot fail"
python3 check_plan.py $out/log 2026-10-07 2027-10-01 && ok "good: plan rules re-checked from outside" || no "good: plan rules"
python3 validate_ics.py $out/x.ics --max-per-week 3 && ok "good: .ics is valid" || no "good: .ics invalid"
grep -q $'OCC\t2027-03-[0-9]*\t.*\tdraft-check' $out/log && ok "south: the early-autumn job falls in March" || no "south: early-autumn job not in March"
grep -q $'OCC\t2026-10-07\t' $out/log && ! grep -q $'OCC\t2026-10-0[1-6]\t' $out/log && ok "starting this month begins today, not on the 1st" || no "start clamp"
grep -q "Remind your landlord: have the AC or heat pump serviced" $out/x.html && ok "renting: a landlord job becomes a reminder" || no "landlord wording missing"
grep -q "Check the car's tyre pressure" $out/x.html && ok "uk wording: tyre" || no "uk wording missing"
grep -q "Next due January 2029" $out/x.html && ok "a 60-month job not due this year is listed with its next date" || no "later list missing"
grep -q 'WARN  safety job "Press the test button on the RCD' $out/log && ok "a fitting safety job left out is flagged" || no "missing-safety-job warning"
grep -q "Spring slot skipped: done 12 September 2026" $out/x.html && ! grep -q $'OCC\t2026-10.*yard-spring' $out/log && ok "a seasonal job done 3 weeks before its slot skips it, and says so" || no "seasonal skip"
cp $out/x.ics $out/good.ics
# escaping and folding survive a round trip: the custom why has a comma, a semicolon, backslashes and non-ASCII
python3 - $out/good.ics <<'PY' && ok "DESCRIPTION round-trips: comma, semicolon, backslash, newline, UTF-8 across a fold" || no "DESCRIPTION round trip"
import sys, json; sys.path.insert(0, ".")
import validate_ics as v
ev, errs, *_ = v.check(sys.argv[1])
why = [c for c in json.load(open("good.json"))["custom"] if c["title"] == "Descale the kettle"][0]["why"]
d = [e for e in ev if e["uid"].startswith("custom-descale-the-kettle-")]
raw = open(sys.argv[1], "rb").read()
assert not errs and d and all(e["DESCRIPTION"] == why + "\nDIY, about 15 min" for e in d), (errs, d[:1])
assert b"\\," in raw and b"\;" in raw and b"\\\\" in raw and b"\\n" in raw
PY

# --- builtOn: absent = the real date; equal to the real date is fine without the example flag
python3 - $B $out <<'PY' && ok "builtOn left out, or equal to the real date, builds without the example flag" || no "builtOn real-date control"
import sys, json, subprocess, datetime as dt
g = json.load(open("good.json")); g.pop("example"); g.pop("builtOn"); g["start"] = dt.date.today().strftime("%Y-%m")
for extra in ({}, {"builtOn": dt.date.today().strftime("%-d %B %Y")}):
    json.dump(dict(g, **extra), open(sys.argv[2] + "/real.json", "w"))
    assert subprocess.run([sys.executable, sys.argv[1], sys.argv[2] + "/real.json", "--out", sys.argv[2] + "/real.html"], capture_output=True).returncode == 0
PY
# --- regional wording: an OWNED UK home gets the unvented-cylinder check as a pro job; US says mold, UK mould
python3 - $B $out <<'PY' && ok "uk: cylinder valve check is Professional, 60 min; uk says mould, us says mold" || no "regional who/minutes/spelling"
import sys, json, subprocess
g = json.load(open("good.json")); g["home"]["tenure"] = "own"; g["features"].append("washing_machine")
g["jobs"] += [{"id": "water-heater-valve"}, {"id": "washer-clean"}, {"id": "bathroom-fan"}]
def page(words):
    json.dump(dict(g, words=words), open(sys.argv[2] + "/w.json", "w"))
    subprocess.run([sys.executable, sys.argv[1], sys.argv[2] + "/w.json", "--out", sys.argv[2] + "/w.html"], check=True, capture_output=True)
    h = open(sys.argv[2] + "/w.html").read(); d = json.loads(h.split("var HOME = ")[1].split(";\n(function")[0])
    return h, [i for m in d["months"] for i in m["items"]]
h, items = page("uk")
v = [i for i in items if i["title"].startswith("Have the unvented cylinder")]
assert v and all(i["who"] == "pro" and i["minutes"] == 60 for i in v), v[:1]
assert "becomes mould" in h and "Stops mould" in h and " mold" not in h
h, items = page("us")
v = [i for i in items if i["title"].startswith("Test the water heater's pressure-relief")]
assert v and all(i["who"] == "diy" and i["minutes"] == 10 for i in v)
assert "becomes mold" in h and "Stops mold" in h and "mould" not in h
PY

# --- the example
expect 0 ../example/columbus-house.json
python3 check_plan.py $out/log 2026-11-01 2027-11-01 && ok "example: plan rules re-checked from outside" || no "example: plan rules"
python3 validate_ics.py $out/x.ics --max-per-week 3 && ok "example: .ics is valid" || no "example: .ics invalid"
grep -q $'OCC\t2027-09-[0-9]*\t.*\tdraft-check' $out/log && ok "north: the early-autumn job falls in September" || no "north: early-autumn job not in September"
grep -q $'OCC\t2026-11-[0-9]*\t.*\tcatch-up\t1\tfurnace-service' $out/log && ok "a missed seasonal safety job (furnace, last done 13 months ago) comes first" || no "furnace catch-up"
# the validator itself must be able to fail: break the CRLFs, an escape and the fold
python3 - $out/x.ics $out/broken.ics <<'PY'
import sys; b = open(sys.argv[1], "rb").read()
b = b.replace(b"\\,", b",", 1).replace(b"\r\n ", b"", 1); i = b.rindex(b"END:VEVENT\r\n") + 10
b = b[:i] + b[i + 1:]; open(sys.argv[2], "wb").write(b)   # a comma unescaped, a fold undone, the last CRLF made a bare LF
PY
python3 validate_ics.py $out/broken.ics >$out/vlog; [ $? -eq 1 ] && grep -q "not CRLF" $out/vlog && grep -q "unescaped" $out/vlog && grep -q "octets" $out/vlog \
  && ok "validate_ics.py fails a broken file (bare LF, bare comma, unfolded line)" || { no "validate_ics.py passed a broken file"; cat $out/vlog; }

# --- every refusal, for the reason its name says
for f in bad-*.json; do expect 2 "$f"; done
for pair in "no-interval:neither an interval" "interval-zero:every 0 must be a whole number of months from 1 to 60" \
  "interval-too-long:every 61 must be a whole number of months from 1 to 60" "unknown-job:unknown job id \"paint-the-fence\"" \
  "duplicate-job:\"leak-check\" is listed twice" "duplicate-custom:is listed twice, or repeats a standard job" \
  "custom-no-why:has no \"why\"" "start-before-today:start month 2026-09 is before today" "start-day-past:start date 2026-10-06 is before today" \
  "last-done-future:last_done 2026-10-08 is in the future" "unknown-feature:unknown feature \"moat\"" "needs-feature:needs one of these features" \
  "empty-plan:the plan is empty" "seasonal-every:is seasonal" "unknown-season:unknown season \"monsoon\"" "hemisphere:hemisphere \"east\"" "builton-not-today:builtOn \"1 January 2025\" is not today" \
  "builton-flag-not-true:builtOn \"1 January 2025\" is not today" \
  "overloaded:cannot spread the jobs to 3 a week"; do
  f=bad-${pair%%:*}.json; why=${pair#*:}
  python3 $B $f --out $out/x.html 2>$out/err >/dev/null; grep -qF "$why" $out/err && ok "$f says: $why" || { no "$f did not say: $why"; sed 's/^/      /' $out/err | head -3; }
done

# the page must never reach the network: a tampered engine is refused
python3 - "$B" <<'PY' && ok "network in page is refused" || no "network in page was not refused"
import sys, tempfile, importlib.util
spec = importlib.util.spec_from_file_location("b", sys.argv[1]); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
t = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False)
t.write(open(b.ENGINE).read().replace("</body>", "<script>fetch('https://x.example')</script></body>")); t.close()
b.ENGINE = t.name
try: b.render({"title": "x"}); sys.exit(1)
except b.Refused: sys.exit(0)
PY
# the same input builds the same files, any day (builtOn pins today)
python3 $B good.json --out $out/a.html --ics $out/a.ics >/dev/null; python3 $B good.json --out $out/b.html --ics $out/b.ics >/dev/null
cmp -s $out/a.html $out/b.html && cmp -s $out/a.ics $out/b.ics && ok "rebuild is byte-identical (page and calendar)" || no "rebuild differs"
echo "$pass passed, $fail failed"; [ $fail -eq 0 ]
