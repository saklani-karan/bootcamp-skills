#!/bin/bash
# print.sh <chart.html> <print-week|print-all|print-rota|all> : out/<mode>.pdf, as Print would.
H="$(cd "$(dirname "$0")" && pwd)"; m=$2; [ "$m" = all ] && python3 "$H/inject.py" "$1" plain || python3 "$H/inject.py" "$1" "$m" || exit 1
UD=$(mktemp -d); rm -f "$H/out/$m.pdf"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --user-data-dir="$UD" --no-pdf-header-footer \
  --print-to-pdf="$H/out/$m.pdf" "file://$H/out/t.html" >/dev/null 2>&1 &
pid=$!; for i in $(seq 1 40); do [ -s "$H/out/$m.pdf" ] && break; sleep 0.5; done
sleep 1; kill $pid 2>/dev/null; pkill -P $pid 2>/dev/null; rm -rf "$UD" 2>/dev/null
[ -s "$H/out/$m.pdf" ] && echo "$H/out/$m.pdf" || { echo "no pdf"; exit 1; }
