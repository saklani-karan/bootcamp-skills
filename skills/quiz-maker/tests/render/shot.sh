#!/bin/bash
# shot.sh <quiz.html> <hash> <width> <height> <name.png> [phone]
#   hash steps (see drive.js): home | menu | play-front | play-hint | play-right | play-wrong | play-end
#   | play-history | play-answers | seek-<qid>-front | seek-<qid>-back[-wrong] | seek-<qid>-enter ; add -night/-sunset/-hand/-photo
# Kills ONLY the Chrome it started, by PID: another session may be running Chrome too.
H="$(cd "$(dirname "$0")" && pwd)"; python3 "$H/inject.py" "$1" || exit 1
cp "$H/mob.html" "$H/out/mob.html"; page=t.html; [ "$6" = phone ] && page=mob.html
UD=$(mktemp -d); rm -f "$H/out/$5"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --user-data-dir="$UD" --hide-scrollbars \
  --window-size=$3,$4 --virtual-time-budget=4000 --screenshot="$H/out/$5" "file://$H/out/$page#$2" >/dev/null 2>&1 &
pid=$!; for i in $(seq 1 60); do [ -s "$H/out/$5" ] && break; sleep 0.5; done
sleep 0.5; kill $pid 2>/dev/null; pkill -P $pid 2>/dev/null; rm -rf "$UD"
[ -s "$H/out/$5" ] && echo "$H/out/$5" || { echo "no screenshot"; exit 1; }
