#!/usr/bin/env python3
"""
validator.py — validate a crossword JSON layout.

Usage:
    python3 validator.py '{"words": [...]}'
    python3 validator.py path/to/crossword.json

Checks, in order:
  1. Letter conflicts / illegal overlaps (from load).
  2. Accidental words — any run of touching letters that isn't a declared word.
  3. Connectivity — all words must form a single linked grid.
  4. Every word (when >1) must cross at least one other.

Exit code: 0 = valid, 1 = invalid or parse error.
"""

import sys
import os

# Allow running from any directory
sys.path.insert(0, os.path.dirname(__file__))
from crossword_core import load_grid


def validate(source: str) -> bool:
    try:
        grid, errors = load_grid(source)
    except Exception as exc:
        print(f"ERROR: Could not parse input — {exc}")
        return False

    if not grid.words:
        print("ERROR: No words found in input.")
        return False

    if errors:
        print(f"INVALID — {len(errors)} placement error(s):\n")
        for e in errors:
            print(e)
        print()
        return False

    # ── accidental words (touching / sticking) ──────────────────────────────
    accidental = grid.find_accidental_words()
    if accidental:
        print(f"INVALID — {len(accidental)} accidental word(s) from touching letters:\n")
        for a in accidental:
            print(f"  {a}")
        print()
        return False

    # ── connectivity ─────────────────────────────────────────────────────────
    if len(grid.words) > 1:
        comps = grid.connected_components()
        if len(comps) > 1:
            print(f"INVALID — grid is split into {len(comps)} disconnected clusters:\n")
            for i, comp in enumerate(comps, 1):
                print(f"  cluster {i}: {comp}")
            print("\n  Every word must connect to the rest through a shared letter.\n")
            return False

        # redundant given connectivity, but a clear, specific message
        intersected = set()
        for ix in grid.get_intersections():
            intersected.update(ix["used_by"])
        isolated = [w.text for w in grid.words if w.text not in intersected]
        if isolated:
            print(f"INVALID — {len(isolated)} word(s) cross nothing: {isolated}\n")
            return False

    print(f"VALID — {len(grid.words)} word(s) placed successfully.")
    print(f"  Grid bounds: rows {min(r for r,_ in grid.grid)} to {max(r for r,_ in grid.grid)}, "
          f"cols {min(c for _,c in grid.grid)} to {max(c for _,c in grid.grid)}")
    print(f"  Intersections: {len(grid.get_intersections())}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validator.py <json_string_or_file>")
        sys.exit(1)
    ok = validate(sys.argv[1])
    sys.exit(0 if ok else 1)
