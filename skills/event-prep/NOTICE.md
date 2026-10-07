# Credit

This skill is adapted from **event-prep** by David Sleiman —
https://github.com/Denkos-DS/event-prep — released under the MIT licence, copied at
commit `d8f74f5841e3e224900882b00d6e54130242f6af` (20 August 2026).

Taken unchanged from the original:
- `scripts/quantities.py` and `scripts/split.py` (the per-person maths and the cost split)
- `scripts/test_quantities.py` and `scripts/test_split.py` (their 54 + 12 unit tests)
- `reference/logistics.md` and `documents.md`
- `reference/quantities.md` and `camping-and-festivals.md`, except four lines that pointed
  at sections of the original `SKILL.md` (or its `docs/PRODUCT.md`) that this skill does
  not have; they now point at what this skill does have

New for this skill: `SKILL.md` (rewritten to ask everything in one message and to keep
nothing between chats), `scripts/build_event.py` (the model writes the plan, the script
works out every amount, cost, total and split, and refuses a bad plan),
`assets/engine.html` (the fixed page), `reference/event-format.md`, the example and
the tests.

MIT License

Copyright (c) 2026 David Sleiman

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
