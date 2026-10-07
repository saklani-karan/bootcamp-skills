#!/bin/bash
# Every detector must be seen to fire, for its own reason. No pipes on the build command: a pipe swallows its exit code.
cd "$(dirname "$0")"; python3 make_fixtures.py
B=../scripts/build_plan.py; out=$(mktemp -d); pass=0; fail=0
expect(){ want=$1; shift; python3 $B "$@" --out $out/x.html >$out/log 2>&1; got=$?
  if [ $got -eq $want ]; then pass=$((pass+1)); echo "ok    exit=$got  $*"; [ $got -eq 2 ] && sed -n 2p $out/log | cut -c1-150 | sed 's/^/        /';
  else fail=$((fail+1)); echo "FAIL  exit=$got want=$want  $*"; sed 's/^/      /' $out/log | head -5; fi; }
# reason checks: the refusal must name its own cause
reason(){ f=$1; pat=$2; python3 $B $f --out $out/x.html >$out/log 2>&1
  if grep -qi -- "$pat" $out/log; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL  $f refused for the wrong reason (wanted: $pat)"; sed 's/^/      /' $out/log | head -3; fi; }
for f in good.json good-debts-only.json good-goals-only.json good-stretch.json; do expect 0 $f; done
for f in bad-*.json; do expect 2 "$f"; done
reason bad-min-no-cover.json "would never clear it"
reason bad-balance-zero.json "balance must be more than 0"
reason bad-apr-range.json "between 0 and 100"
reason bad-min-zero.json "minimum payment must be more than 0"
reason bad-duplicate.json "two debts are called"
reason bad-goal-past.json "is not after the plan starts"
reason bad-over-budget.json "too much"
reason bad-return-range.json "between 0 and 12"
reason bad-date-format.json "YYYY-MM"
reason bad-nothing.json "at least one debt or one goal"
reason bad-text-number.json "must be a number"
reason bad-no-monthly.json "monthly_amount"
reason bad-font.json "look.font"
# the stretch plan shows the gap rather than hiding it
python3 $B good-stretch.json --out $out/s.html >/dev/null; grep -q '"short": 172.8' $out/s.html && { pass=$((pass+1)); echo "ok    stretch plan carries its shortfall"; } || { fail=$((fail+1)); echo "FAIL  stretch shortfall missing"; }
# the upstream maths still matches its own worked examples
python3 ../scripts/debt_management.py --verify >$out/v1 2>&1 && { pass=$((pass+1)); echo "ok    debt_management --verify"; } || { fail=$((fail+1)); echo "FAIL  debt_management --verify"; tail -3 $out/v1; }
python3 ../scripts/savings_goals.py --verify >$out/v2 2>&1 && { pass=$((pass+1)); echo "ok    savings_goals --verify"; } || { fail=$((fail+1)); echo "FAIL  savings_goals --verify"; tail -3 $out/v2; }
# the page must never reach the network: a tampered engine is refused
python3 - "$B" <<'PY' && { pass=$((pass+1)); echo "ok    network in page is refused"; } || { fail=$((fail+1)); echo "FAIL  network in page was not refused"; }
import sys, tempfile, importlib.util
spec = importlib.util.spec_from_file_location("b", sys.argv[1]); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
t = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False)
t.write(open(b.ENGINE).read().replace("</body>", "<script>fetch('https://x.example')</script></body>")); t.close()
b.ENGINE = t.name
try: b.render({"title": "x"}); sys.exit(1)
except b.Refused: sys.exit(0)
PY
python3 $B good.json --out $out/a.html >/dev/null; python3 $B good.json --out $out/b.html >/dev/null
cmp -s $out/a.html $out/b.html && { pass=$((pass+1)); echo "ok    rebuild is byte-identical"; } || { fail=$((fail+1)); echo "FAIL  rebuild differs"; }
echo "$pass passed, $fail failed"; [ $fail -eq 0 ]
