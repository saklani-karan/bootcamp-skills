# chart.json — the format

`example/maya-leo-ivy.json` is a complete one. You write the people and the chores;
`scripts/build_chart.py` decides who does what, on which day, every week.

```json
{
  "id": "maya-leo-ivy-autumn",          // optional: ticks are saved under this name on the device
  "title": "Maya, Leo & Ivy's chore chart",
  "start": "2026-10-12",                // optional, must be a Monday: weeks then show dates
  "weeks": 4,                           // 1-12, default 4
  "days": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],   // default every day
  "look": {"font": "rounded", "bg": "sunset"},
  "children": [ {"name": "Maya", "age": 12}, {"name": "Ivy", "age": 5} ],
  "chores": [
    "set-table",                                       // an id from chores.json
    {"id": "feed-pet", "same_child_ok": true},          // an id, with a setting changed
    {"title": "Feed the fish", "min_age": 4, "effort": 1, "how_often": "daily"}   // their own chore
  ],
  "exclusions": [ {"child": "Leo", "chore": "feed-pet", "why": "allergic to the cat"} ]
}
```

## Children
- **First names only**, each different (two Sams → "Sam B" and "Sam T").
- **Age** is a whole number from 3 to 17. Never guess an age: ask.
- At most 8 children on one chart.

## Chores
- **From the list**: use the `id` from `reference/chores.json` exactly. Pick by age —
  a chore whose `min_age` is above every child's age is refused.
- **Their own chore**: give `title`, `min_age`, `effort` and `how_often`, all four.
  `effort` 1 = a minute or two, no skill; 3 = 15-20 minutes; 5 = a real job, 30+ minutes.
  Be conservative with `min_age` for anything with knives, heat, chemicals, machines or water.
- **`how_often`**: `daily` (every chosen day), `2x` … `6x` (times a week, spread over
  the chosen days), or `weekly`. A once-a-week chore may name its `"day": "Sat"`.
- **Changing a listed chore**: `{"id": "vacuum", "how_often": "2x"}`. Lowering `min_age`
  is allowed only when the parent says their child can do it; the build prints a WARN.
- **`same_child_ok: true`** only when the parent agrees that the one child able to do
  a chore may do it every week (see below). Never add it to make a refusal go away.
- Shared household chores only. "Make your own bed" is not a rotation chore; leave it off.

## Exclusions
"Anything a child must not do": one line per child and chore, with a short `why`
(allergy, fear, a promise). The `chore` is the id (for their own chore: the title in
lower case with dashes, e.g. `feed-the-fish`).

## Why a build is refused, and what to do
| Printed reason | Do this |
|---|---|
| no child is old enough for X | drop it, or ask whether a child really can do it (then lower `min_age`) |
| X is excluded for every child old enough | drop it, or ask which exclusion can go |
| only Ana can do X, so it cannot rotate | ask: is it fine that Ana does it every week? yes → `same_child_ok: true`; no → drop it |
| happens 3 times a week but the chart has only 2 days | make it `daily`, or choose more days |
| age / name / weeks / day / unknown chore id | fix the input; ask if you do not know |
