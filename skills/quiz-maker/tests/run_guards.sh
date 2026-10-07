#!/bin/bash
# Every detector must be seen to fire. No pipes on the build command: a pipe swallows its exit code.
cd "$(dirname "$0")"; python3 make_fixtures.py
B=../scripts/build_quiz.py; out=$(mktemp -d); pass=0; fail=0
expect(){ want=$1; shift; python3 $B "$@" --out $out/x.html >$out/log 2>&1; got=$?
  if [ $got -eq $want ]; then pass=$((pass+1)); echo "ok    exit=$got  $*"; else fail=$((fail+1)); echo "FAIL  exit=$got want=$want  $*"; sed 's/^/      /' $out/log | head -5; fi; }
expect 0 good.json --no-net
for f in bad-*.json; do
  if [ "$f" = "bad-dead-link.json" ]; then expect 2 "$f"; else expect 2 "$f" --no-net; fi
done
expect 0 drift.json --no-net --source source-ok.json
expect 2 drift.json --no-net --source source-drift.json
# a parent's own list: an exact copy builds, a one-letter drift is refused
printf 'What gas do plants take in? | Carbon dioxide\nWhat is H2O? | Water\n' > list.txt
python3 ../scripts/from_list.py list.txt src-list.json >/dev/null
python3 - <<'PY'
import json, copy
ok = json.load(open("good.json")); ok["count"] = 2
ok["questions"][0].update(q="What gas do plants take in?", opts=["Carbon dioxide","Oxygen","Nitrogen","Helium"], a=0, h="Plants breathe in what we breathe out.")
ok["questions"][1].update(q="What is H2O?", opts=["Water","Salt","Air","Sand"], a=0, h="You drink it.")
json.dump(ok, open("list-exact.json", "w"))
bad = copy.deepcopy(ok); bad["questions"][0]["opts"][0] = "Carbon Dioxide"; json.dump(bad, open("list-drift.json", "w"))
PY
expect 0 list-exact.json --no-net --source src-list.json
expect 2 list-drift.json --no-net --source src-list.json
# live photos (a builder with no internet): a wiki-named photo builds and the page loads it online;
# without --live-photos the same quiz stays network-free; a picture with no wiki title is refused
expect 0 live.json --no-net --live-photos
if grep -q "livePhotos();" $out/x.html && grep -q '"wiki": {"p1": "Eiffel Tower"}' $out/x.html; then pass=$((pass+1)); echo "ok    live page carries the photo lookup and the wiki title"
else fail=$((fail+1)); echo "FAIL  live page is missing livePhotos() or its wiki map"; fi
expect 0 live.json --no-net
if grep -q "fetch(" $out/x.html; then fail=$((fail+1)); echo "FAIL  a normal build reached the network"
else pass=$((pass+1)); echo "ok    a normal build of the same quiz has no network call"; fi
expect 2 live-no-wiki.json --no-net --live-photos
# a picture question on a live photo would be unanswerable offline, so it is refused
expect 2 live-pic.json --no-net --live-photos
grep -q "picture questions can't use a live photo" $out/log && { pass=$((pass+1)); echo "ok    live-pic refused for its own reason"; } || { fail=$((fail+1)); echo "FAIL  live-pic refused for the wrong reason"; sed 's/^/      /' $out/log | head -3; }
echo "$pass passed, $fail failed"; [ $fail -eq 0 ]
