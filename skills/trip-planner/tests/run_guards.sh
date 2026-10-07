#!/bin/bash
# Prove the builder's refusals actually fire. Run from anywhere.
#
# Written 2026-10-02. Every detector here was tested against known-bad input
# BEFORE the builder was trusted — a guard that has never been shown to fail
# is not a guard.
#
#   ./run_guards.sh
#
# Every refusal is checked for its OWN printed reason, not just its exit code
# (bad1 and bad2 are otherwise-valid trips with exactly one defect each).
# 2026-10-07 (lane A): --no-net labels, --live-photos, and the network guard,
# which is run against every payload in net-payloads.json (net_payloads.py).
# min-live needs the network (a real site that refuses robots).

cd "$(dirname "$0")" || exit 1
BUILD=../scripts/build_page.py
T=$(mktemp -d) || exit 1
trap 'rm -rf "$T"' EXIT
pass=0; fail=0
ok ()  { printf '  PASS  %s\n' "$1"; pass=$((pass+1)); }
bad () { printf '  FAIL  %s\n' "$1"; fail=$((fail+1)); sed -n '1,5p' "$T/log" | sed 's/^/        /'; }

refuse () {                     # refuse <fixture> <reason printed> <what it proves> [flags...]
  f=$1; why=$2; what=$3; shift 3
  python3 "$BUILD" "$f.json" --out "$T/x.html" "$@" >"$T/log" 2>&1; rc=$?
  if [ "$rc" = 2 ] && grep -qF -- "$why" "$T/log"; then ok "$(printf '%-12s exit=2  %s' "$f" "$what")"
  else bad "$(printf '%-12s exit=%s, wanted 2 with %s  %s' "$f" "$rc" "'$why'" "$what")"; fi
}

echo "guard tests — build_page.py"
refuse bad1     "has no source and is not marked check:true" "price with no source and no check mark is refused"
# bad1/bad2 must fail for that one rule only: exactly one problem line
python3 "$BUILD" bad1.json --out "$T/x.html" >"$T/log" 2>&1
[ "$(grep -c '^  - ' "$T/log")" = 1 ] && ok "bad1         its only problem is the price" || bad "bad1         fails for more than its own rule"
refuse bad2     "derived figure must also be check:true" "derived weather figure without check:true is refused"
python3 "$BUILD" bad2.json --out "$T/x.html" >"$T/log" 2>&1
[ "$(grep -c '^  - ' "$T/log")" = 1 ] && ok "bad2         its only problem is the derived figure" || bad "bad2         fails for more than its own rule"
refuse bad3     "missing required field" "structurally incomplete spec is refused, not crashed"
refuse good     "missing required field" "a stub spec still fails structural validation"
refuse min-dead "these links do not resolve" "a link that does not resolve is refused"

python3 "$BUILD" min.json --out "$T/min.html" --no-net >"$T/log" 2>&1
[ $? = 0 ] && ok "min          exit=0  a valid spec builds (offline)" || bad "min          did not build"

python3 "$BUILD" min-live.json --out "$T/live.html" >"$T/log" 2>&1
if [ $? = 0 ] && grep -q "refused a robot" "$T/log"; then ok "min-live     exit=0  a 403 is reported as blocked, not treated as dead"
else bad "min-live     403 handling wrong"; fi

# a --no-net page's own labels say "not machine-checked", never a bare "checked"
python3 visible_checked.py "$T/min.html" >"$T/log" 2>&1 \
  && ok "min          --no-net page: masthead and sources labels say not machine-checked, sentence present" \
  || bad "min          --no-net page still claims checked"
# ...and a checked build (min-live, above) keeps its "Facts checked" label
if grep -q "Facts checked" "$T/live.html" && ! grep -q "not machine-checked" "$T/live.html"; then
  ok "min-live     a link-checked page keeps 'Facts checked'"
else bad "min-live     a link-checked page lost 'Facts checked' or says 'not machine-checked'"; fi

# live photos (a builder with no internet): a wiki-named photo builds and the page loads it online
python3 "$BUILD" live.json --out "$T/lp.html" --live-photos >"$T/log" 2>&1
if [ $? = 0 ] && grep -q "livePhotos({" "$T/lp.html" && grep -q '"wiki": "Museo del Prado"' "$T/lp.html" \
   && grep -q '<style id="photos"></style>' "$T/lp.html" && grep -q "links NOT checked (--live-photos)" "$T/log"; then
  ok "live         exit=0  --live-photos builds; page carries the lookup, the wiki title and the #photos slot"
else bad "live         --live-photos build wrong"; fi
# without --live-photos the same trip stays network-free: no lookup code, no #photos slot
python3 "$BUILD" live.json --out "$T/lp0.html" --no-net >"$T/log" 2>&1
if [ $? = 0 ] && ! grep -q "livePhotos" "$T/lp0.html" && ! grep -q 'id="photos"' "$T/lp0.html"; then
  ok "live         exit=0  without --live-photos the page holds no fetching code"
else bad "live         without --live-photos the page still carries live-photo code"; fi
# a link the builder cannot reach is refused normally (min-dead, above) but builds under --live-photos
python3 "$BUILD" min-dead.json --out "$T/lp1.html" --live-photos >"$T/log" 2>&1
if [ $? = 0 ] && grep -q "links NOT checked" "$T/log" && python3 visible_checked.py "$T/lp1.html" >/dev/null; then
  ok "min-dead     exit=0  under --live-photos an unreachable link is not classed dead; page says not machine-checked"
else bad "min-dead     under --live-photos an unreachable link refused the build"; fi
# a photo the page cannot name by Wikipedia article would never show: refused, for that reason
refuse live-no-wiki 'every photo needs a "wiki" article title: ave' "a photo with no wiki title is refused under --live-photos" --live-photos
# the network guard: refused for its own reason
refuse bad-net  "the page would reach the network: <img> is not a tag" "an <img> that loads from the web is refused" --no-net

# the network guard against every payload: each refused for its own reason in both modes, legit HTML builds
python3 net_payloads.py "$BUILD" >"$T/net" 2>&1
cat "$T/net"
pass=$((pass + $(grep -c '^  PASS' "$T/net"))); fail=$((fail + $(grep -c '^  FAIL' "$T/net")))

echo
echo "$pass passed, $fail failed"
[ "$fail" = 0 ]
