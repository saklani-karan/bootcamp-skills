#!/bin/bash
# shot.sh <plan.html> <width> <height> <name.png> [phone|-] [tab] : a screenshot. Kills ONLY the Chrome it started.
H="$(cd "$(dirname "$0")" && pwd)"; python3 "$H/inject.py" "$1" plain || exit 1
cp "$H/mob.html" "$H/out/mob.html"; page=t.html; [ "$5" = phone ] && page=mob.html
UD=$(mktemp -d); rm -f "$H/out/$4"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --user-data-dir="$UD" --hide-scrollbars \
  --window-size=$2,$3 --virtual-time-budget=2000 --screenshot="$H/out/$4" "file://$H/out/$page#$6" >/dev/null 2>&1 &
pid=$!; for i in $(seq 1 60); do [ -s "$H/out/$4" ] && break; sleep 0.5; done
sleep 0.5; kill $pid 2>/dev/null; pkill -P $pid 2>/dev/null; rm -rf "$UD" 2>/dev/null
[ -s "$H/out/$4" ] && echo "$H/out/$4" || { echo "no screenshot"; exit 1; }
