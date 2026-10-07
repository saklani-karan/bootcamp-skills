#!/usr/bin/env python3
"""Build a crossword: words.json -> one self-contained HTML page you can play and print.

The model writes the words and clues. This script does everything that must not
be left to judgement: it lays the grid out, checks it, and fills the fixed page
in assets/engine.html. The page is model-free and network-free, so it behaves the
same as a Claude artifact, on Vercel, or double-clicked from Downloads.

It REFUSES to build when:
  - an answer has anything but letters (spaces, hyphens and apostrophes are allowed
    and shown as a hint like "(3,5)"), or is shorter than 2 letters
  - two answers are the same
  - a clue is empty, or contains its own answer
  - there are fewer than 4 or more than 30 words
  - any word cannot be fitted into one connected grid (it names them; it never
    drops a word silently)
  - the finished grid fails the checker: a letter clash, two words touching to
    make a word nobody wrote, or a word that crosses nothing
  - the finished page would reach the network

    python3 build_crossword.py words.json --out crossword.html [--explain]
"""
import argparse, datetime, html, json, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from crossword_core import CrosswordGrid, Word, Direction, normalize_word  # noqa: E402

ENGINE = os.path.join(HERE, "..", "assets", "engine.html")
FONTS = {"rounded", "clear", "story", "hand"}
COLOURS = {"auto", "snow", "sky", "pine", "sunset", "berry", "night"}
TRIES = 200         # extra seeded word orders tried after the longest-first order


class Refused(Exception):
    pass


def letters_only(answer):
    """'Ice cream' -> ('ICECREAM', '(3,5)').  'T-rex' -> ('TREX', '(1-3)')."""
    raw = str(answer).strip()
    parts = re.split(r"([ \-'’])", raw)
    lens, seps = [], []
    for p in parts:
        if p in (" ", "-", "'", "’"):
            seps.append(p)
        elif p:
            lens.append(p)
    word = "".join(lens)
    enum = ""
    if len(lens) > 1:
        out = str(len(lens[0]))
        for sep, part in zip(seps, lens[1:]):
            out += ("-" if sep == "-" else "" if sep in "'’" else ",") + str(len(part))
        enum = f"({out})"
    return normalize_word(word), enum


def fold(s):
    return re.sub(r"[^\w]+", " ", str(s).lower()).strip()


# ---------------------------------------------------------------- validation
def validate(spec):
    errs, warns = [], []
    for k in ("id", "title", "words"):
        if not spec.get(k):
            errs.append(f"missing top-level field '{k}'")
    if errs:
        raise Refused("\n".join(errs))
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", str(spec["id"])):
        errs.append("id must be lowercase letters, digits and '-' (it keeps this puzzle's progress separate)")
    look = spec.get("look", {})
    if look.get("font", "rounded") not in FONTS:
        errs.append(f"look.font must be one of {sorted(FONTS)}")
    if look.get("bg", "auto") not in COLOURS:
        errs.append(f"look.bg must be one of {sorted(COLOURS)}")

    words = spec["words"]
    if not 4 <= len(words) <= 30:
        errs.append(f"{len(words)} words: a crossword needs between 4 and 30")

    entries, seen = [], {}
    for i, w in enumerate(words):
        where = f"word {i+1} ({w.get('answer', '?')!r})"
        ans, clue = w.get("answer", ""), str(w.get("clue", "")).strip()
        text, enum = letters_only(ans)
        if not text or not all(ch.isalpha() for ch in text):
            errs.append(f"{where}: an answer can only be letters (spaces, hyphens and apostrophes are fine)")
            continue
        if len(text) < 2:
            errs.append(f"{where}: an answer needs at least 2 letters")
        if text in seen:
            errs.append(f"{where}: the same answer as word {seen[text]}")
        seen.setdefault(text, i + 1)
        if not clue:
            errs.append(f"{where}: no clue")
        else:
            tokens = fold(clue).split()
            parts = [text.lower()] + [p for p in fold(ans).split() if len(p) >= 3]
            if any(t in (p, p + "s", p + "es") for t in tokens for p in parts):
                errs.append(f"{where}: the clue gives the answer away")
        if w.get("check") and not w.get("note"):
            errs.append(f"{where}: \"check\": true needs a short \"note\" saying what to confirm")
        if len(clue) > 110 and spec.get("age", 99) <= 10:
            warns.append(f"{where}: a long clue for age {spec.get('age')} ({len(clue)} characters)")
        entries.append({"text": text, "enum": enum, "clue": clue, "answer": str(ans).strip(),
                        "check": bool(w.get("check")), "note": w.get("note", "")})
    if errs:
        raise Refused("\n".join(errs))
    return entries, warns


# ---------------------------------------------------------------- layout
def _bounds(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return min(rs), max(rs), min(cs), max(cs)


def _placements(grid, text):
    """Every legal crossing placement for `text` (the search the original suggest.py did)."""
    out, seen = [], set()
    for ex in grid.words:
        d = ex.direction.opposite()
        for er, ec, el in ex.cells():
            for i, ch in enumerate(text):
                if ch != el:
                    continue
                r, c = (er, ec - i) if d == Direction.HORIZONTAL else (er - i, ec)
                if (r, c, d) in seen:
                    continue
                seen.add((r, c, d))
                cand = Word(text, r, c, d)
                rep = grid._verify(cand)
                if rep["valid"]:
                    out.append((cand, len(rep["intersections"])))
    return out


def _score(grid, cand, crossings):
    r0, r1, c0, c1 = _bounds(list(grid.grid) + [(r, c) for r, c, _ in cand.cells()])
    h, w = r1 - r0 + 1, c1 - c0 + 1
    # compact first: a long thin grid does not fit a phone, crossings break ties
    return (max(h, w), h * w, -crossings, cand.row, cand.col, cand.direction.value)


def try_order(order):
    grid = CrosswordGrid()
    first, rest = order[0], list(order[1:])
    grid.add_word(Word(first, 0, 0, Direction.HORIZONTAL))
    progress = True
    while rest and progress:
        progress = False
        for text in list(rest):
            opts = _placements(grid, text)
            if not opts:
                continue
            cand, _ = min(opts, key=lambda o: _score(grid, o[0], o[1]))
            if grid.add_word(cand)["valid"]:
                rest.remove(text); progress = True
    return grid, rest


def layout(texts):
    base = sorted(texts, key=lambda t: (-len(t), texts.index(t)))
    orders = [base]
    for seed in range(TRIES):
        o = base[1:]; random.Random(seed).shuffle(o); orders.append([base[0]] + o)
    best = None
    for i, order in enumerate(orders):
        grid, left = try_order(order)
        r0, r1, c0, c1 = _bounds(grid.grid)
        h, w = r1 - r0 + 1, c1 - c0 + 1
        key = (len(left), max(h, w), h * w, -len(grid.get_intersections()), i)
        if best is None or key < best[0]:
            best = (key, grid, left)
    return best[1], best[2]


def check_grid(grid):
    probs = list(grid.find_accidental_words())
    comps = grid.connected_components()
    if len(comps) > 1:
        probs.append(f"the grid is split into {len(comps)} separate pieces: {comps}")
    crossed = set()
    for ix in grid.get_intersections():
        crossed.update(ix["used_by"])
    lonely = [w.text for w in grid.words if w.text not in crossed]
    if lonely and len(grid.words) > 1:
        probs.append(f"words that cross nothing: {lonely}")
    return probs


# ---------------------------------------------------------------- page
def puzzle_data(spec, entries, grid):
    by_text = {e["text"]: e for e in entries}
    ex = grid.to_export_dict({})
    cells = [[None if c is None else {"l": c["letter"], "n": c["number"]} for c in row] for row in ex["grid"]]

    def side(lst):
        return [{"n": e["number"], "row": e["row"], "col": e["col"], "len": e["length"],
                 "clue": by_text[e["answer"]]["clue"], "enum": by_text[e["answer"]]["enum"],
                 "answer": by_text[e["answer"]]["answer"]} for e in lst]
    return {
        "id": spec["id"], "title": spec["title"], "subtitle": spec.get("subtitle", ""),
        "builtOn": spec.get("builtOn") or datetime.date.today().strftime("%-d %B %Y"),
        "look": {"font": spec.get("look", {}).get("font", "rounded"),
                 "bg": spec.get("look", {}).get("bg", "auto")},
        "rows": ex["rows"], "cols": ex["cols"], "cells": cells,
        "across": side(ex["across"]), "down": side(ex["down"]),
    }


def render(data):
    page = open(ENGINE, encoding="utf-8").read()
    for slot in ("/*__PUZZLE__*/null", "__TITLE__"):
        if page.count(slot) != 1:
            raise Refused(f"engine.html must contain {slot} exactly once")
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = page.replace("/*__PUZZLE__*/null", blob).replace("__TITLE__", html.escape(data["title"]))
    if re.search(r"fetch\(|XMLHttpRequest|<script[^>]+src=|<link[^>]+href=\"?https?:", page):
        raise Refused("the page would reach the network")
    return page


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words"); ap.add_argument("--out", required=True)
    ap.add_argument("--explain", action="store_true", help="print the grid and every clue as built")
    a = ap.parse_args()
    try:
        spec = json.load(open(a.words, encoding="utf-8"))
        entries, warns = validate(spec)
        grid, left = layout([e["text"] for e in entries])
        if left:
            raise Refused("these words would not fit into one connected grid: " + ", ".join(left) +
                          "\n  swap them for words that share more letters with the others, or drop them"
                          " - and tell the person which ones and why")
        probs = check_grid(grid)
        if probs:
            raise Refused("the grid failed its check:\n  " + "\n  ".join(probs))
        data = puzzle_data(spec, entries, grid)
        page = render(data)
    except Refused as e:
        print("REFUSED TO BUILD\n  " + str(e).replace("\n", "\n  "), file=sys.stderr); sys.exit(2)
    except (OSError, json.JSONDecodeError) as e:
        print(f"REFUSED TO BUILD\n  could not read {a.words}: {e}", file=sys.stderr); sys.exit(2)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(page)
    for w in warns:
        print("WARN  " + w)
    if data["cols"] > 15 or data["rows"] > 15:
        print(f"WARN  the grid is {data['rows']}x{data['cols']}: big for a phone. Fewer or shorter words make it smaller")
    if a.explain:
        print(grid.display())
    n = len(entries)
    print(f"built {os.path.basename(a.out)}  {n} words  {data['rows']}x{data['cols']} grid  "
          f"{len(grid.get_intersections())} crossings  {len(page)//1024} KB")
    chk = [e for e in entries if e["check"]]
    if chk:
        print("\nCHECK THESE before anyone plays:")
        for e in chk:
            print(f"  - {e['clue']}  ->  {e['answer']}   ({e['note']})")


if __name__ == "__main__":
    main()
