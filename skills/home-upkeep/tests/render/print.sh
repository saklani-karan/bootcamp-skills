#!/bin/bash
# print.sh <plan.html> : prints the page to out/plan.pdf the way a browser's Print would (one sheet per quarter).
H="$(cd "$(dirname "$0")" && pwd)"; python3 "$H/inject.py" "$1" plain || exit 1
UD=$(mktemp -d); rm -f "$H/out/plan.pdf"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --user-data-dir="$UD" --no-pdf-header-footer \
  --print-to-pdf="$H/out/plan.pdf" "file://$H/out/t.html" >/dev/null 2>&1 &
pid=$!; for i in $(seq 1 40); do [ -s "$H/out/plan.pdf" ] && break; sleep 0.5; done
sleep 1; kill $pid 2>/dev/null; pkill -P $pid 2>/dev/null; rm -rf "$UD" 2>/dev/null
[ -s "$H/out/plan.pdf" ] && echo "$H/out/plan.pdf" || { echo "no pdf"; exit 1; }
