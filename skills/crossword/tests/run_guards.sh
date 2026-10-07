#!/bin/bash
# Every detector must be seen to fire. No pipes on the build command: a pipe swallows its exit code.
cd "$(dirname "$0")"; python3 make_fixtures.py
B=../scripts/build_crossword.py; out=$(mktemp -d); pass=0; fail=0
expect(){ want=$1; shift; python3 $B "$@" --out $out/x.html >$out/log 2>&1; got=$?
  if [ $got -eq $want ]; then pass=$((pass+1)); echo "ok    exit=$got  $*"; else fail=$((fail+1)); echo "FAIL  exit=$got want=$want  $*"; sed 's/^/      /' $out/log | head -5; fi; }
expect 0 good.json
grep -q '"enum": "(3,5)"' $out/x.html && { pass=$((pass+1)); echo "ok    'Ice cream' shows as (3,5)"; } || { fail=$((fail+1)); echo "FAIL  enumeration (3,5) missing"; }
for f in bad-*.json; do expect 2 "$f"; done
# the page must never reach the network: a tampered engine is refused
python3 - "$B" <<'PY' && { pass=$((pass+1)); echo "ok    network in page is refused"; } || { fail=$((fail+1)); echo "FAIL  network in page was not refused"; }
import sys, os, tempfile, importlib.util
spec = importlib.util.spec_from_file_location("b", sys.argv[1]); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
t = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False)
t.write(open(b.ENGINE).read().replace("</body>", "<script>fetch('https://x.example')</script></body>")); t.close()
b.ENGINE = t.name
try: b.render({"title": "x"}); sys.exit(1)
except b.Refused: sys.exit(0)
PY
# the same input builds the same file
python3 $B good.json --out $out/a.html >/dev/null; python3 $B good.json --out $out/b.html >/dev/null
cmp -s $out/a.html $out/b.html && { pass=$((pass+1)); echo "ok    rebuild is byte-identical"; } || { fail=$((fail+1)); echo "FAIL  rebuild differs"; }
echo "$pass passed, $fail failed"; [ $fail -eq 0 ]
