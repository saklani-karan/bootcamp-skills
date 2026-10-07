#!/bin/bash
# play_check.sh <quiz.html> : plays two full games with real clicks and prints errors / history / player.
# Exit 1 unless there are 0 JS errors and the history page recorded 2 quizzes for "Leo".
H="$(cd "$(dirname "$0")" && pwd)"; python3 "$H/inject.py" "$1" || exit 1
UD=$(mktemp -d)
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --user-data-dir="$UD" \
  --virtual-time-budget=6000 --dump-dom "file://$H/out/t.html#play-history" > "$H/out/dom.txt" 2>/dev/null &
pid=$!; sleep 14; kill $pid 2>/dev/null; rm -rf "$UD"
r=$(grep -o 'data-r="[^"]*"' "$H/out/dom.txt"); echo "$r"
case "$r" in *"errors=0 "*"games=2quizzes"*"players=Leo"*) exit 0;; *) exit 1;; esac
