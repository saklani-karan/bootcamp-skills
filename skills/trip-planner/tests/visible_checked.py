#!/usr/bin/env python3
"""visible_checked.py <page.html> : for a --no-net / --live-photos build, where no link was checked.
Reads only what the BUILDER writes about checking - the masthead's date label (span.asof) and the
sources heading (the first <h3> in div.src) - and the builder's not-checked sentence (p.not-checked).
Exit 1 if either label says "checked" without "not machine-checked", or the sentence is missing.
Text the trip's author wrote (e.g. "neither score was checked") is theirs, not a claim by the build."""
import html, re, sys
s = open(sys.argv[1], encoding="utf-8").read()
def text(frag):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", frag))).strip()
asof = re.search(r'<span class="asof">(.*?)</span>', s, re.S)
src = re.search(r'<div class="src"><h3>(.*?)</h3>', s, re.S)
sentence = re.search(r'<p class="not-checked"[^>]*>(.*?)</p>', s, re.S)
bad = []
for name, m in (("masthead label", asof), ("sources heading", src)):
    if not m:
        bad.append(f"{name}: not found")
        continue
    t = text(m.group(1))
    print(f"  {name}: {t!r}")
    if re.search(r"checked", t, re.I) and "not machine-checked" not in t.lower():
        bad.append(f"{name} says checked: {t!r}")
if not sentence:
    bad.append("the not-machine-checked sentence is missing")
else:
    print(f"  sentence: {text(sentence.group(1))[:70]!r}...")
for b in bad:
    print("  FAIL " + b)
sys.exit(1 if bad else 0)
