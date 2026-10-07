#!/bin/bash
# Every detector must be seen to fire FOR ITS OWN REASON. No pipes on the build command: a pipe swallows its exit code.
cd "$(dirname "$0")"; python3 make_fixtures.py
B=../scripts/build_event.py; out=$(mktemp -d); pass=0; fail=0
ok(){ pass=$((pass+1)); echo "ok    $*"; }; no(){ fail=$((fail+1)); echo "FAIL  $*"; }
expect(){ want=$1; shift; python3 $B "$@" --out $out/x.html >$out/log 2>&1; got=$?
  if [ $got -eq $want ]; then ok "exit=$got  $*"; [ $got -eq 2 ] && sed -n 2p $out/log | sed 's/^ */        reason: /'
  else no "exit=$got want=$want  $*"; sed 's/^/      /' $out/log | head -5; fi; }
expect 0 good.json
grep -q "WARN  'Cake'" $out/log && ok "an estimate is flagged as a placeholder" || no "placeholder warning missing"
expect 0 ../example/tahoe-camping-weekend.json
for f in bad-*.json; do expect 2 "$f"; done
# each bad fixture must be refused for the reason its name says, not some other error
for pair in "price-unsourced:neither a source" "no-price:no price" "ambiguous-cut:unknown cut 'chicken'" \
  "meal-before-arrival:does not exist" "meal-after-departure:does not exist" "diet-hungry:nothing on the menu for vegetarian" \
  "no-store:no store" "unknown-store:not in the stores list" "no-amount-rule:exactly one of calc" "fixed-no-why:needs a \"why\"" \
  "unknown-group:unknown group" "unknown-meal:is not one of the meals" "unit-mismatch:is a mass but the pack" \
  "committed-status:status must be paid" "split-nobody:has nobody eligible"; do
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
# the same input builds the same file
python3 $B good.json --out $out/a.html >/dev/null; python3 $B good.json --out $out/b.html >/dev/null
cmp -s $out/a.html $out/b.html && ok "rebuild is byte-identical" || no "rebuild differs"
# the original author's unit tests still pass (54 + 12)
(cd ../scripts && python3 test_quantities.py >$out/u1 2>&1 && python3 test_split.py >$out/u2 2>&1) \
  && ok "original unit tests: $(grep -h '^Ran' $out/u1 $out/u2 | tr '\n' ' ')" || { no "original unit tests"; tail -5 $out/u1 $out/u2; }
echo "$pass passed, $fail failed"; [ $fail -eq 0 ]
