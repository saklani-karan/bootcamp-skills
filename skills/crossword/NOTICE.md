# Credit

The grid logic in `scripts/crossword_core.py` and `scripts/validator.py` comes from
**crossword-skill** by zorahm — https://github.com/zorahm/crossword-skill — released
under the MIT licence, copied at commit `9aa2184896a63d78fb755906b23caa3be5553f0b`
(1 June 2026).

Changed for this skill: one line in `crossword_core.py` so it runs on Python 3.9
(`from __future__ import annotations`). Everything else in this folder —
`SKILL.md`, `scripts/build_crossword.py` (automatic layout, the refusals),
`assets/engine.html` (the playable, printable page), the reference and the tests —
is new.

MIT licence, as published with the original:

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following
conditions: The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS",
WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.
