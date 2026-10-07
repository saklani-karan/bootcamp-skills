#!/bin/bash
# Every detector must be seen to fire, for its own reason. No pipes on the build command: a pipe swallows its exit code.
cd "$(dirname "$0")"; python3 make_fixtures.py
B=../scripts/build_card.py; out=$(mktemp -d); pass=0; fail=0
ok(){ pass=$((pass+1)); echo "ok    $*"; }; no(){ fail=$((fail+1)); echo "FAIL  $*"; }
expect(){ want=$1; why=$2; shift 2; python3 $B "$@" --out $out/x.html >$out/log 2>&1; got=$?
  if [ $got -eq $want ] && grep -q -- "$why" $out/log; then ok "exit=$got  $*  -> $(grep -m1 -- "$why" $out/log | sed 's/^ *//')";
  else no "exit=$got want=$want  $*  (wanted reason: $why)"; sed 's/^/      /' $out/log | head -4; fi; }
expect 0 "built" good.json
expect 0 "units=us" good-convert.json
grep -q '"was": "250 ml milk"' $out/x.html && ok "a converted line keeps its source text" || no "converted line lost its source text"
expect 2 "no title"                    bad-no-title.json
expect 2 "no ingredients"              bad-no-ingredients.json
expect 2 "empty ingredient text"       bad-empty-ingredient.json
expect 2 "is empty"                    bad-empty-step.json
expect 2 "does not match its own text" bad-qty-drift.json
expect 2 "does not appear in its own"  bad-unit-drift.json
expect 2 "but qty is empty"            bad-qty-dropped.json
expect 2 "is not a number"             bad-qty-unreadable.json
expect 2 "states no servings"        bad-scale-no-serves.json
expect 2 "unknown unit"                bad-unknown-unit.json
expect 2 "duplicate card id"           bad-duplicate-id.json
# scaling maths, done by the script and never by the model
python3 - "$B" <<'PY' && ok "scaling: ½×3=1½, 2–3×2=4–6, 1 1/2×½=¾, pinch unchanged, 1 eggs->1 egg, 250 ml->1 cup (not 1 cups)" || no "scaling maths"
import sys, importlib.util
from fractions import Fraction as F
sp = importlib.util.spec_from_file_location("b", sys.argv[1]); b = importlib.util.module_from_spec(sp); sp.loader.exec_module(b)
L = lambda t, q, u, i, f: b.line_at({"text": t, "qty": q, "unit": u, "item": i}, F(f), "source")["t"]
assert L("½ cup oats", "½", "cup", "oats", 3) == "1½ cups oats"
assert L("2–3 tbsp honey", "2–3", "tbsp", "honey", 2) == "4–6 tbsp honey"
assert L("1 1/2 cups flour", "1 1/2", "cups", "flour", F(1, 2)) == "¾ cup flour"
assert L("a pinch of salt", "", "", "salt", 2) == "a pinch of salt"
assert L("2 eggs", "2", "", "eggs", F(1, 2)) == "1 egg"
assert b.line_at({"text": "250 ml milk", "qty": "250", "unit": "ml", "item": "milk"}, F(1), "us")["t"] == "1 cup milk"
assert b.line_at({"text": "a pinch of salt", "qty": "", "unit": "", "item": "salt"}, F(2), "source").get("fixed")
PY
# the page must never reach the network: a tampered engine is refused
python3 - "$B" <<'PY' && ok "network in page is refused" || no "network in page was not refused"
import sys, tempfile, json, importlib.util
sp = importlib.util.spec_from_file_location("b", sys.argv[1]); b = importlib.util.module_from_spec(sp); sp.loader.exec_module(b)
t = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False)
t.write(open(b.ENGINE).read().replace("</body>", "<script>fetch('https://x.example')</script></body>")); t.close()
b.ENGINE = t.name
try: b.render(json.load(open("good.json"))); sys.exit(1)
except b.Refused: sys.exit(0)
PY
python3 $B good.json --out $out/a.html >/dev/null; python3 $B good.json --out $out/b.html >/dev/null
cmp -s $out/a.html $out/b.html && ok "rebuild is byte-identical" || no "rebuild differs"
echo "$pass passed, $fail failed"; [ $fail -eq 0 ]
