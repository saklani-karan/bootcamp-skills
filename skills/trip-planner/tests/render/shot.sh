#!/bin/bash
# shot.sh <trip.html> <view> <width> <height> <name.png> [phone] [offline]
#   view: top | credits | a section id (route, week, places, hotels, planb ...)
#   phone renders inside a 390px iframe (mob.html); offline sends Chrome to a dead proxy.
# The view shows that one block alone (headless screenshots ignore scrolling); 20 virtual s lets live photos load.
# Kills ONLY the Chrome it started, by PID.
H="$(cd "$(dirname "$0")" && pwd)"; python3 "$H/inject.py" "$1" || exit 1
cp "$H/mob.html" "$H/out/mob.html"; page=t.html; [ "$6" = phone ] && page=mob.html
NET=(); [ "$7" = offline ] && NET=(--proxy-server=127.0.0.1:9 --proxy-bypass-list="<-loopback>")
UD=$(mktemp -d); rm -f "$H/out/$5"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --user-data-dir="$UD" --hide-scrollbars \
  "${NET[@]}" --window-size=$3,$4 --virtual-time-budget=20000 --screenshot="$H/out/$5" "file://$H/out/$page#view-$2" >/dev/null 2>&1 &
pid=$!; for i in $(seq 1 120); do [ -s "$H/out/$5" ] && break; sleep 0.5; done
sleep 0.5; kill $pid 2>/dev/null; pkill -P $pid 2>/dev/null; rm -rf "$UD"
[ -s "$H/out/$5" ] && echo "$H/out/$5" || { echo "no screenshot"; exit 1; }
