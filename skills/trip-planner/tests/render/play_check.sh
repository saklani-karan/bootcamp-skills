#!/bin/bash
# play_check.sh <trip.html> [online|offline] [min-loaded]
# Clicks every control on the page (booking boxes, contents and rail links, print), waits for
# live photos, prints one report line, then judges it. offline = Chrome sent to a dead proxy
# (127.0.0.1:9), so nothing on the web is reachable.
# FAIL (exit 1) on any of:
#   errors>0 (photo-loader faults are counted in errors, and shown as photo-errors)
#   a failed control check · the page not whole · any GREY photo box (neither shown nor hidden)
#   live page, online:  0 photos loaded (or fewer than min-loaded, if given)
#   live page, offline: any photo loaded
#   embedded page (normal build): any photo key not shown
# Kills ONLY the Chrome it started, by PID: another session may be running Chrome too.
H="$(cd "$(dirname "$0")" && pwd)"; python3 "$H/inject.py" "$1" || exit 1
MODE="${2:-online}"; MIN="${3:-1}"
NET=(); [ "$MODE" = offline ] && NET=(--proxy-server=127.0.0.1:9 --proxy-bypass-list="<-loopback>")
UD=$(mktemp -d); rm -f "$H/out/dom.txt"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --user-data-dir="$UD" \
  "${NET[@]}" --virtual-time-budget=25000 --dump-dom "file://$H/out/t.html#play" > "$H/out/dom.txt" 2>/dev/null &
pid=$!; for i in $(seq 1 120); do kill -0 $pid 2>/dev/null || break; sleep 0.5; done
kill $pid 2>/dev/null; pkill -P $pid 2>/dev/null; rm -rf "$UD"
r=$(grep -o 'data-r="[^"]*"' "$H/out/dom.txt" | sed 's/^data-r="//;s/"$//')
echo "${r:-no report (page did not finish)}"
python3 - "$r" "$MODE" "$MIN" <<'PY'
import re, sys
r, mode, mn = sys.argv[1], sys.argv[2], int(sys.argv[3])
def n(k):
    m = re.search(r"\b" + k + r"=(\d+)", r); return int(m.group(1)) if m else -1
why = []
if not r: why.append("no report")
else:
    if n("errors") != 0: why.append(f"errors={n('errors')} (photo-errors={n('photo-errors')})")
    if n("failed") != 0: why.append(f"{n('failed')} control checks failed")
    if "wrap=whole" not in r: why.append("page not whole")
    if n("grey") != 0: why.append(f"{n('grey')} photo keys left as grey boxes")
    keys, loaded = n("keys"), n("loaded")
    if n("live") == 1 and mode == "online" and keys > 0 and loaded < mn:
        why.append(f"live page online: {loaded} of {keys} photos loaded, wanted at least {mn}")
    if n("live") == 1 and mode == "offline" and loaded != 0:
        why.append(f"live page offline: {loaded} photos loaded - the proxy did not hold")
    if n("live") == 0 and loaded != keys:
        why.append(f"embedded page: {loaded} of {keys} photo keys shown")
print("VERDICT: " + ("PASS" if not why else "FAIL - " + "; ".join(why)))
sys.exit(1 if why else 0)
PY
