#!/usr/bin/env python3
"""A parent's own list -> source.json, copied exactly, for build_quiz.py --source.

One card per line:  question | answer
Blank lines and lines starting with # are skipped. Nothing is trimmed inside the
text, so a capital, a spelling or a full stop survives exactly as the parent wrote it.

    python3 from_list.py list.txt source.json
"""
import json, sys

src, out = sys.argv[1], sys.argv[2]
items, unread = [], []
for n, line in enumerate(open(src, encoding="utf-8").read().splitlines(), 1):
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    if line.count("|") != 1:
        unread.append(f"line {n}: {line}")
        continue
    q, a = (part.strip() for part in line.split("|"))
    if not q or not a:
        unread.append(f"line {n}: {line}")
        continue
    items.append({"q": q, "a": a})
json.dump(items, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(items)} questions copied to {out}")
if unread:
    print("Could not read these lines. Ask the parent, don't guess:")
    for u in unread:
        print("  " + u)
