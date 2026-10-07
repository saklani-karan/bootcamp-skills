"""
crossword_core.py — shared grid logic for the crossword skill.
Imported by build_crossword.py and validator.py.
"""
from __future__ import annotations  # adaptation: runs on Python 3.9 too

import json
from dataclasses import dataclass
from enum import Enum


# ── Normalization ─────────────────────────────────────────────────────────────

_LATIN_TO_CYRILLIC = {
    'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е',
    'H': 'Н', 'K': 'К', 'M': 'М', 'O': 'О',
    'P': 'Р', 'T': 'Т', 'X': 'Х', 'Y': 'У',
}

def _is_cyrillic(word: str) -> bool:
    """Check if the word contains any Cyrillic letters."""
    return any('\u0400' <= ch <= '\u04FF' for ch in word)

def normalize_letter(ch: str, cyrillic_mode: bool = False) -> str:
    ch = ch.upper()
    if cyrillic_mode:
        return _LATIN_TO_CYRILLIC.get(ch, ch)
    return ch

def normalize_word(word: str) -> str:
    cyrillic_mode = _is_cyrillic(word)
    return "".join(normalize_letter(c, cyrillic_mode) for c in word)


# ── Direction ─────────────────────────────────────────────────────────────────

class Direction(str, Enum):
    HORIZONTAL = "H"
    VERTICAL   = "V"

    def opposite(self) -> "Direction":
        return Direction.VERTICAL if self == Direction.HORIZONTAL else Direction.HORIZONTAL


# ── Word ──────────────────────────────────────────────────────────────────────

@dataclass
class Word:
    text:      str
    row:       int
    col:       int
    direction: Direction

    def __post_init__(self):
        self.text = normalize_word(self.text)

    def cells(self) -> list[tuple[int, int, str]]:
        result = []
        for i, letter in enumerate(self.text):
            if self.direction == Direction.HORIZONTAL:
                result.append((self.row, self.col + i, letter))
            else:
                result.append((self.row + i, self.col, letter))
        return result

    def cell_set(self) -> frozenset:
        return frozenset((r, c) for r, c, _ in self.cells())

    def end_pos(self) -> tuple[int, int]:
        cells = self.cells()
        return cells[-1][0], cells[-1][1]

    def to_dict(self) -> dict:
        return {
            "text":      self.text,
            "row":       self.row,
            "col":       self.col,
            "direction": self.direction.value,
        }

    @staticmethod
    def from_dict(d: dict) -> "Word":
        return Word(
            text      = d["text"],
            row       = int(d["row"]),
            col       = int(d["col"]),
            direction = Direction(d["direction"]),
        )


# ── Grid ──────────────────────────────────────────────────────────────────────

# (dr, dc) steps for the two axes
_STEP = {
    Direction.HORIZONTAL: (0, 1),
    Direction.VERTICAL:   (1, 0),
}


class CrosswordGrid:
    def __init__(self):
        self.grid:  dict[tuple[int, int], str]       = {}
        self.usage: dict[tuple[int, int], list[str]] = {}
        self.words: list[Word]                       = []

    # ── placement ──────────────────────────────────────────────────────────

    def add_word(self, word: Word) -> dict:
        report = self._verify(word)
        if report["valid"]:
            for row, col, letter in word.cells():
                self.grid[(row, col)] = letter
                self.usage.setdefault((row, col), [])
                if word.text not in self.usage[(row, col)]:
                    self.usage[(row, col)].append(word.text)
            self.words.append(word)
        return report

    def _verify(self, word: Word) -> dict:
        """Validate placing `word` against the current grid.

        Two independent gates:
          1. Per-cell letter agreement (hard conflicts + perpendicular crossings).
          2. Adjacency gate — placing the word must not create any maximal
             letter run (length >= 2) that isn't a declared word. This single
             rule covers side-by-side sticking, end-to-end touching, and
             parallel overlap.
        """
        errors        = []
        intersections = []
        cells         = word.cells()

        for row, col, letter in cells:
            existing = self.grid.get((row, col))
            if existing is None:
                continue
            if existing == letter:
                if self._is_perpendicular(row, col, word.direction):
                    intersections.append({"row": row, "col": col, "letter": letter})
                else:
                    errors.append(
                        f"({row},{col}): '{letter}' lands on a parallel word — overlap not allowed"
                    )
            else:
                errors.append(
                    f"({row},{col}): grid has '{existing}', new word gives '{letter}' — conflict"
                )

        errors.extend(self._check_adjacency(word))

        return {
            "valid":         len(errors) == 0,
            "errors":        errors,
            "intersections": intersections,
            "word":          word.to_dict(),
        }

    def _is_perpendicular(self, row: int, col: int, new_dir: Direction) -> bool:
        for w in self.words:
            for wr, wc, _ in w.cells():
                if wr == row and wc == col and w.direction == new_dir:
                    return False
        return True

    # ── adjacency / accidental-word detection ───────────────────────────────

    def _run_through(self, cell, axis, filled) -> list:
        """Maximal run of filled cells through `cell` along `axis` (a Direction)."""
        dr, dc = _STEP[axis]
        r, c = cell
        # walk back to the run start
        while (r - dr, c - dc) in filled:
            r, c = r - dr, c - dc
        run = []
        while (r, c) in filled:
            run.append((r, c))
            r, c = r + dr, c + dc
        return run

    def _check_adjacency(self, word: Word) -> list[str]:
        """Return errors for accidental words created by placing `word`.

        We tentatively drop the word onto a copy of the grid, then look at every
        maximal horizontal/vertical run that touches one of the word's cells.
        Any run of length >= 2 whose cell set isn't a declared word is illegal.
        """
        cells = word.cells()
        filled = dict(self.grid)
        for r, c, letter in cells:
            # don't mask a hard conflict here — those are reported separately
            if filled.get((r, c), letter) == letter:
                filled[(r, c)] = letter

        declared = {w.cell_set() for w in self.words}
        declared.add(word.cell_set())

        errors = []
        reported: set = set()
        new_cells = [(r, c) for r, c, _ in cells]

        for cell in new_cells:
            for axis in (Direction.HORIZONTAL, Direction.VERTICAL):
                run = self._run_through(cell, axis, filled)
                if len(run) < 2:
                    continue
                run_set = frozenset(run)
                if run_set in declared or run_set in reported:
                    continue
                reported.add(run_set)
                text = "".join(filled[c] for c in run)
                start = run[0]
                tag = "row" if axis == Direction.HORIZONTAL else "col"
                errors.append(
                    f"placing '{word.text}' creates accidental {axis.value}-word "
                    f"'{text}' at {tag} start {start} — words are touching/sticking"
                )
        return errors

    def find_accidental_words(self) -> list[str]:
        """Global scan of the finished grid for runs that aren't declared words."""
        declared = {w.cell_set() for w in self.words}
        errors = []
        for axis in (Direction.HORIZONTAL, Direction.VERTICAL):
            dr, dc = _STEP[axis]
            for (r, c) in self.grid:
                # only start at the head of a run
                if (r - dr, c - dc) in self.grid:
                    continue
                if (r + dr, c + dc) not in self.grid:
                    continue
                run = self._run_through((r, c), axis, self.grid)
                if frozenset(run) not in declared:
                    text = "".join(self.grid[cell] for cell in run)
                    errors.append(
                        f"accidental {axis.value}-word '{text}' at {run[0]} "
                        f"— not in word list (two words are touching)"
                    )
        return errors

    # ── connectivity ─────────────────────────────────────────────────────────

    def connected_components(self) -> list[list[str]]:
        """Group words into connected clusters linked by shared (crossing) cells."""
        n = len(self.words)
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            parent[find(a)] = find(b)

        cell_words: dict[tuple[int, int], list[int]] = {}
        for i, w in enumerate(self.words):
            for r, c, _ in w.cells():
                cell_words.setdefault((r, c), []).append(i)
        for idxs in cell_words.values():
            for j in idxs[1:]:
                union(idxs[0], j)

        comps: dict[int, list[str]] = {}
        for i in range(n):
            comps.setdefault(find(i), []).append(self.words[i].text)
        return list(comps.values())

    # ── queries ────────────────────────────────────────────────────────────

    def get_intersections(self) -> list[dict]:
        return [
            {"row": r, "col": c, "letter": self.grid[(r, c)], "used_by": words}
            for (r, c), words in sorted(self.usage.items())
            if len(words) >= 2
        ]

    def number_cells(self) -> dict[tuple[int, int], int]:
        """Standard crossword numbering: every cell that starts an across or down
        word gets a number, assigned in reading order (top-to-bottom, left-to-right).
        A cell starting both directions shares one number."""
        starts = {(w.row, w.col) for w in self.words}
        ordered = sorted(starts, key=lambda rc: (rc[0], rc[1]))
        return {pos: i + 1 for i, pos in enumerate(ordered)}

    def to_export_dict(self, clues: dict | None = None) -> dict:
        """Word-ready structured export.

        Normalizes the (possibly negative) coordinate space into a 0-based
        rectangular matrix — exactly what a Word table needs — and splits the
        word list into numbered ACROSS and DOWN clue lists.

        Returns:
            {
              "rows", "cols",
              "grid":  row-major matrix; each cell is null (no cell) or
                       {"letter", "number"|null},
              "across": [{"number","answer","clue","length","row","col"}, ...],
              "down":   [...],
              "meta":   {"words","intersections"}
            }
        Coordinates in across/down are matrix (0-based) coordinates.
        """
        clues = clues or {}
        if not self.grid:
            return {"rows": 0, "cols": 0, "grid": [], "across": [], "down": [],
                    "meta": {"words": 0, "intersections": 0}}

        min_r = min(r for r, _ in self.grid)
        min_c = min(c for _, c in self.grid)
        max_r = max(r for r, _ in self.grid)
        max_c = max(c for _, c in self.grid)
        rows = max_r - min_r + 1
        cols = max_c - min_c + 1

        numbers = self.number_cells()

        matrix = [[None] * cols for _ in range(rows)]
        for (r, c), letter in self.grid.items():
            matrix[r - min_r][c - min_c] = {
                "letter": letter,
                "number": numbers.get((r, c)),
            }

        across, down = [], []
        for w in self.words:
            num = numbers.get((w.row, w.col))
            entry = {
                "number": num,
                "answer": w.text,
                "clue":   clues.get(w.text, clues.get(w.text.lower(), "")),
                "length": len(w.text),
                "row":    w.row - min_r,
                "col":    w.col - min_c,
            }
            (across if w.direction == Direction.HORIZONTAL else down).append(entry)

        across.sort(key=lambda e: (e["number"] is None, e["number"]))
        down.sort(key=lambda e: (e["number"] is None, e["number"]))

        return {
            "rows": rows,
            "cols": cols,
            "grid": matrix,
            "across": across,
            "down": down,
            "meta": {"words": len(self.words),
                     "intersections": len(self.get_intersections())},
        }

    def display(self, padding: int = 1) -> str:
        if not self.grid:
            return "(grid is empty)"
        all_rows = [r for r, _ in self.grid]
        all_cols = [c for _, c in self.grid]
        min_r, max_r = min(all_rows) - padding, max(all_rows) + padding
        min_c, max_c = min(all_cols) - padding, max(all_cols) + padding
        col_w = 3
        lines = []
        header = "     " + "".join(f"{c:{col_w}}" for c in range(min_c, max_c + 1))
        lines.append(header)
        lines.append("     " + "-" * col_w * (max_c - min_c + 1))
        for r in range(min_r, max_r + 1):
            row_str = f"{r:4} |"
            for c in range(min_c, max_c + 1):
                ch = self.grid.get((r, c), "·")
                row_str += f"  {ch}"
            lines.append(row_str)
        return "\n".join(lines)


# ── Loader ────────────────────────────────────────────────────────────────────

def load_grid(source: str) -> tuple[CrosswordGrid, list[str]]:
    """
    Parse JSON string or file path, build CrosswordGrid.
    Returns (grid, all_errors).
    """
    import os
    if os.path.isfile(source):
        with open(source, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.loads(source)

    grid   = CrosswordGrid()
    errors = []
    for word_dict in data.get("words", []):
        word   = Word.from_dict(word_dict)
        report = grid.add_word(word)
        if not report["valid"]:
            for e in report["errors"]:
                errors.append(f"  [{word.text}] {e}")
    return grid, errors
