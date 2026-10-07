---
name: chore-chart
description: "Makes a printable weekly chore rotation chart for children as one HTML page: a tab per week, a row per child and a column per day with big tick boxes, saved on the device, and a page per week to print for the fridge. A script decides every assignment so it is fair by age, never gives a chore to a child too young for it or excluded from it, and never gives anyone the same chore two weeks running when someone else can do it. Use whenever a parent wants a chore chart, a chore rota or rotation, a job chart, a fair way to share housework between kids, or a list of age-appropriate chores."
---

# Chore chart

You make one thing: a single HTML page holding a family's chore rotation. The page is
already written (`assets/engine.html`) and **every assignment is made by a script**.
Your job is the family and the chores: who the children are, which jobs, and what
someone must not do. **Never decide who does which chore yourself**, and never say
a chart is fair because it looks fair: the script works out each child's fair share
and checks it.

The page has no model inside it and makes no network calls, so it behaves the same
as a shared Claude artifact, a page hosted on Vercel, or a file double-clicked from
Downloads.

**In Microsoft Copilot Cowork**, this skill's other files (`scripts/`, `assets/`, `reference/`, `example/`) are not
next to this file. They are in the user's OneDrive at
`Documents/Cowork/skills/chore-chart/`. Open them from there before you build.

## 1. Ask first, in one message, then wait

Ask all of this at once, numbered, so it can be answered in one reply:

1. **The children.** Each child's first name and age.
2. **The chores.** Their own list, or "suggest some" and you pick from
   `reference/chores.json` by the children's ages. Say how often if it matters
   (every day, a few times a week, once a week).
3. **How long.** How many weeks (default 4), and the Monday it starts if they want
   dates on it.
4. **Which days.** Every day (default), or only some (school days, weekends).
5. **Anything a child must not do.** An allergy, a fear, a rule ("no one under 10
   near the stove").
6. **The look**, with a default if they don't mind: letters Rounded · Easy to read ·
   Storybook · Handwriting; colour Auto · Snow · Sky · Pine · Sunset · Berry · Night.

If the conversation already answers something, don't ask it again. If an age or a
name is missing, ask for that one thing; never guess an age. Do not start until you
have the answers.

## 2. Write `chart.json`

Read `reference/chart-format.md` for the exact format; `example/maya-leo-ivy.json` is
a complete one. The rules that matter:

- **Chores from the list use their `id`.** A chore of their own needs a `title`,
  `min_age`, `effort` (1-5) and `how_often` (`daily`, `2x`-`6x`, `weekly`).
- **Suggesting chores:** pick shared household jobs that most of the children are old
  enough for, a mix of daily and weekly, about 3-5 per child. Never suggest one whose
  `min_age` is above the oldest child.
- **Exclusions** go in `exclusions`, one per child and chore, with the reason.
- **Do not add `same_child_ok`** unless the parent has said yes to one child doing that
  chore every week.

## 3. Build

```bash
python3 scripts/build_chart.py chart.json --out /mnt/user-data/outputs/<name>.html
```

The script gives each chore to one child for a whole week, spreads the
few-times-a-week chores over the chosen days, and works out every child's fair share:
the week's points (effort × times) split by age weight `clamp(age − 2, 2, 12)`, never
more than what a child is allowed to do. It prints the fair share, each week's points
and the largest gap. It refuses to build when:

- a child has no age, or an age outside 3-17, or two children have the same name
- there are no chores, or weeks is outside 1-12, or a chore id is not in the list
- no child is old enough for a chore, or a chore is excluded for every child old enough
- only one child can do a chore over 2+ weeks, so it cannot rotate (unless
  `"same_child_ok": true`)
- a chore happens more times a week than there are days on the chart
- the page would reach the network

**Fix the input, never the check.** When it refuses, tell the parent the reason in
plain words and ask the one question that settles it (`reference/chart-format.md`
has a table). Read every `WARN` out to them.

## 4. Deliver

Give the file. Then, in this order:

1. **Anything the build flagged**: a refusal you resolved and how, a lowered minimum
   age, a child whose row is empty. Nothing else, no disclaimer.
2. **The fair shares** in one line each, from the build's output ("Maya 39 points a
   week, Leo 27, Ivy 12"), and why a younger child's share is smaller if the build
   says so.
3. **How to use it:** a tab per week; tap a chore to tick it, tap again to untick.
   Ticks are kept in that browser on that device only. *Who does what* shows the
   whole rotation and the points.
4. **How to print it:** *Print all weeks* gives one landscape page per week, black on
   white with big tick boxes for the fridge; *Print this week* prints one.
5. **How to share it:**
   - *In Claude:* publish it as an artifact and share the link. The viewer must be
     signed in to Claude.
   - *To anyone, no login:* host it on Vercel. Go to vercel.com, sign up free, then
     **Add New → Project** and drag the file onto the page. No renaming is needed.
     **The file name becomes the web address**, so name the file before you upload it.
     Anyone with the link can open it, and it shows the children's first names and
     ages, so keep surnames off it.
6. **Next time:** keep `chart.json`. To change a child, a chore or the weeks, edit it
   and build again; the same file always gives the same chart.

## In a tool that cannot run the script

Say so and stop. Do not hand-make the rotation: keeping every chore age-safe, nobody
repeating a chore, and the shares fair across weeks is exactly what drifts by hand,
and nothing would catch it.
