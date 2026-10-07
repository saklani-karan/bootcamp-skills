#!/bin/bash
# Every detector must be seen to fire FOR ITS OWN REASON. No pipes on the build command: a pipe swallows its exit code.
cd "$(dirname "$0")"; python3 make_fixtures.py
B=../scripts/build_chart.py; out=$(mktemp -d); pass=0; fail=0
ok(){ pass=$((pass+1)); echo "ok    $*"; }; no(){ fail=$((fail+1)); echo "FAIL  $*"; }
expect(){ want=$1; shift; python3 $B "$@" --out $out/x.html >$out/log 2>&1; got=$?
  if [ $got -eq $want ]; then ok "exit=$got  $*"; [ $got -eq 2 ] && sed -n 2p $out/log | sed 's/^ */        reason: /'
  else no "exit=$got want=$want  $*"; sed 's/^/      /' $out/log | head -5; fi; }
expect 0 good.json
grep -q "max deviation" $out/log && ok "the build prints its fairness summary" || no "fairness summary missing"
expect 0 ../example/maya-leo-ivy.json
for f in near-*.json; do expect 0 "$f"; done
for f in bad-*.json; do expect 2 "$f"; done
# each bad fixture must be refused for the reason its name says, not some other error
for pair in "too-young-for-all:no child is old enough for 'Mow the lawn" "excluded-everyone:is excluded for every child old enough" \
  "age-missing:Ben has no valid age (None)" "age-too-young:age is 2: the chart is for children aged 3 to 17" \
  "age-too-old:age is 18: the chart is for children aged 3 to 17" "age-not-number:has no valid age ('eleven')" \
  "duplicate-name:two children are called" "no-chores:there are no chores" "weeks-zero:weeks is 0" "weeks-13:weeks is 13" \
  "cannot-rotate:only Ana can do 'Vacuum a room', so it cannot rotate" "unknown-id:unknown chore id 'dishes'" \
  "no-children:there are no children" "bad-day:'Funday' is not a day" "too-often:happens 3 times a week but the chart has only 2 days" \
  "start-not-monday:start must be a Monday" "exclusion-unknown-child:exclusion names 'Dee'" \
  "custom-incomplete:is a custom chore and needs effort" "duplicate-chore:is listed twice"; do
  f=bad-${pair%%:*}.json; why=${pair#*:}
  python3 $B $f --out $out/x.html 2>$out/err >/dev/null; grep -qF "$why" $out/err && ok "$f says: $why" || { no "$f did not say: $why"; sed 's/^/      /' $out/err | head -3; }
done
# a lowered min_age builds but is said out loud
python3 - "$out/low.json" <<'PY'
import json, sys; s = json.load(open("good.json")); s["chores"].append({"id": "mop", "min_age": 9}); json.dump(s, open(sys.argv[1], "w"))
PY
python3 $B $out/low.json --out $out/x.html >$out/log 2>&1 && grep -q "WARN  Mop the kitchen floor: min_age lowered from 10 to 9" $out/log && ok "a lowered min_age builds with a WARN" || no "lowered min_age not warned"
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
# the same input builds the same file
python3 $B good.json --out $out/a.html >/dev/null; python3 $B good.json --out $out/b.html >/dev/null
cmp -s $out/a.html $out/b.html && ok "rebuild is byte-identical" || no "rebuild differs"
# a different seed gives a different (but still valid) chart: the shuffle is real, not decorative
python3 - "$out/seed.json" <<'PY'
import json, sys; s = json.load(open("good.json")); s["seed"] = 7; json.dump(s, open(sys.argv[1], "w"))
PY
python3 $B $out/seed.json --out $out/c.html >/dev/null && ! cmp -s $out/a.html $out/c.html && ok "another seed builds a different chart" || no "seed has no effect"
# the rules hold on 50 random families
python3 property_test.py >$out/prop 2>&1 && ok "$(tail -1 $out/prop)" || { no "property test"; tail -8 $out/prop; }
echo "$pass passed, $fail failed"; [ $fail -eq 0 ]
