#!/bin/bash
# play_check.sh <plan.html> [<plan.ics>] : drives the page with real clicks and prints what happened.
# Exit 1 unless 0 JS errors; ticking, unticking, saving, the Look menu, stray taps and the calendar button all
# worked; the calendar the page built is valid; and (given <plan.ics>) it is byte-identical to the script's file.
H="$(cd "$(dirname "$0")" && pwd)"; python3 "$H/inject.py" "$1" drive || exit 1
UD=$(mktemp -d); rm -f "$H/out/dom.txt" "$H/out/page.ics"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --user-data-dir="$UD" \
  --virtual-time-budget=4000 --dump-dom "file://$H/out/t.html" > "$H/out/dom.txt" 2>/dev/null &
pid=$!; for i in $(seq 1 40); do grep -q 'data-r=' "$H/out/dom.txt" 2>/dev/null && break; sleep 0.5; done
sleep 0.5; kill $pid 2>/dev/null; pkill -P $pid 2>/dev/null; rm -rf "$UD" 2>/dev/null
r=$(grep -o 'data-r="[^"]*"' "$H/out/dom.txt" | sed 's/&quot;/"/g'); echo "$r"
case "$r" in *"errors=0 "*"rows=ok"*"tick=ok"*"untick=ok"*"saved=ok"*"look=ok"*"strayTap=ok"*"printed"*".ics|blob ok"*"icsBytes="*) ;; *) exit 1;; esac
grep -o 'data-ics="[^"]*"' "$H/out/dom.txt" | sed 's/^data-ics="//; s/"$//' | python3 -c 'import sys,base64; sys.stdout.buffer.write(base64.b64decode(sys.stdin.read().strip()))' > "$H/out/page.ics"
python3 "$H/../validate_ics.py" "$H/out/page.ics" --max-per-week 3 | sed 's/^/page /' || exit 1
if [ -n "$2" ]; then cmp -s "$H/out/page.ics" "$2" && echo "page .ics is byte-identical to $(basename "$2") (md5 $(md5 -q "$2"))" || { echo "page .ics DIFFERS from $2"; exit 1; }; fi
