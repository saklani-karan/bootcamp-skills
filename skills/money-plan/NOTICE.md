# Credit

The debt and savings maths in `scripts/debt_management.py` and
`scripts/savings_goals.py` comes from **finance_skills** by Joel Lewis —
https://github.com/joellewis/finance_skills (skills `debt-management` and
`savings-goals`) — released under the MIT licence.

Changed for this skill, in `debt_management.py` only:
- numpy removed (the amortisation schedule returns plain dicts), so it runs on any Python 3.9+
- the payoff simulation also records each debt's balance at the end of every month,
  which the chart draws

`savings_goals.py` is unchanged. Both scripts' own `--verify` self-checks still pass and
run in `tests/run_guards.sh`. Everything else in this folder — `SKILL.md`,
`scripts/build_plan.py` (the refusals and the plan), `assets/engine.html`, the
reference and the tests — is new.

MIT License

Copyright (c) 2026 Joel Lewis

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
