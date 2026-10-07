#!/bin/bash
# play_check.sh <chart.html> : drives the page with real clicks and prints what happened.
# Exit 1 unless 0 JS errors and tabs, rules, cells, ticks, persistence, rotation, the <html> tap and printing all worked.
H="$(cd "$(dirname "$0")" && pwd)"; python3 "$H/inject.py" "$1" drive || exit 1
UD=$(mktemp -d); rm -f "$H/out/dom.txt"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --user-data-dir="$UD" \
  --virtual-time-budget=3000 --dump-dom "file://$H/out/t.html" > "$H/out/dom.txt" 2>/dev/null &
pid=$!; for i in $(seq 1 40); do grep -q 'data-r=' "$H/out/dom.txt" 2>/dev/null && break; sleep 0.5; done
sleep 0.5; kill $pid 2>/dev/null; pkill -P $pid 2>/dev/null; rm -rf "$UD" 2>/dev/null
r=$(grep -o 'data-r="[^"]*"' "$H/out/dom.txt" | sed 's/&quot;/"/g'); echo "$r"
case "$r" in *"errors=0 "*"tab=ok"*"rules=ok"*"cells=ok"*"progress=ok"*"ticked=ok"*"untick=ok"*"saved=ok"*"isolated=ok"*"rota=ok"*"htmlTap=ok"*"font=clear"*"printed:"*"print-all"*"printed:"*"print-week"*) exit 0;; *) exit 1;; esac
