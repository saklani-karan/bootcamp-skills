---
name: event-prep
description: Plans and costs a gathering for a group - a backyard birthday, a BBQ, a house party, a picnic, a camping trip, a cabin or chalet weekend, a retreat - as one HTML page with a guest one-pager, a shopping list by store you can tick off in the aisle, who does what and when, the budget, who owes what, and what has to be decided by when. Use whenever someone is organising food, drinks or supplies for a group, asks how much of something to buy for a number of people, or wants to split the costs fairly.
---

# Event prep

You make one thing: a single HTML page for the person organising. The page is
already written (`assets/engine.html`) and every amount, cost and total is worked
out by a script. **Your job is the plan: who, when, what they eat, where it comes
from.** You never write a quantity or a total yourself; across a long plan,
hand-done arithmetic drifts, and that is exactly how events run out of food or money.

The page has no model inside it and makes no network calls, so it behaves the same
as a shared Claude artifact, a page hosted on Vercel, or a file double-clicked from
Downloads.

**In Microsoft Copilot Cowork**, this skill's other files (`scripts/`, `assets/`, `reference/`, `example/`) are not
next to this file. They are in the user's OneDrive at
`Documents/Cowork/skills/event-prep/`. Open them from there before you build.

## 1. Ask first, in one message, then wait

Ask all of this at once, numbered, so it can be answered in one reply:

1. **What and where.** The occasion, and the place. Is there a building with a
   kitchen, an oven, a fridge, running water? One spot, or several (a campsite and a
   beach, two cabins)?
2. **When.** Arrival day and time, leaving day and time. Any hard stop: quiet
   hours, a venue curfew, sunset with no lights.
3. **Who.** How many, and how many of them are vegetarian, vegan, gluten-free or
   have allergies. Roughly how many drink alcohol.
4. **The food.** Anything already planned, or should you suggest a menu? Which
   stores they will shop at.
5. **Money.** What is already booked or paid (venue, rentals, deposits) and for how
   much. Is money being collected, how much each, from how many people? Should it be
   split by who stayed which nights?
6. **What they already own.** Grill, coolers, camp stove, tables, a speaker.
7. **Units.** US (pounds, gallons) or metric (kilos, litres)? Default US.

If an answer is missing or vague, ask about that one thing; do not fill the gap with
a guess. If they have done this event before, ask them to **paste last time's plan
or menu** - nothing is remembered between chats. **And if what they want does not
fit the place** (an oven dish at a campsite with no oven, glass at a venue that bans
it), say so before you plan.

## 2. Write `event.json`

Read `reference/event-format.md` for the exact format; `example/tahoe-camping-weekend.json`
is a complete one. The rules that matter:

- **Every shopping line says how its amount is worked out**, never the amount:
  `calc` (the script's per-person tables: meat, starch, dips, salad, bread,
  breakfast, drinks, ice, water), `per_person` (a rate you state, like 1.5 buns each),
  or `fixed` with a `why` (one tank runs the grill all day).
- **Meat names its cut.** `boneless`, `bone_in`, `ground`, `grilled` or
  `whole_fish`. "Chicken" is refused: five pounds of drumsticks is three and a half
  pounds of meat. If they did not say, ask.
- **Every price has a `source` link or `"check": true`.** Store prices you could not
  confirm are `check`; the page marks them and the build lists them.
- **Every meal covers every group.** If the vegetarians have nothing at breakfast,
  the build refuses.
- **Name a person on every job** in the timeline, and give every open question a
  `decide_by` date: the day the answer stops being useful (the bakery needs two days'
  notice, so the question is due two days before, not "before the party").

`reference/quantities.md`, `logistics.md`, `camping-and-festivals.md` and
`documents.md` hold the knowledge behind the numbers: read the one that fits when
the event has no kitchen, no fridge, no water, a generator, or a second site.

## 3. Build

```bash
python3 scripts/build_event.py event.json --out /mnt/user-data/outputs/<name>.html --explain
```

It works out every amount with `scripts/quantities.py`, buys whole packs at the top
of each range, adds every line into store, section and grand totals and checks they
agree, reconciles the budget, and splits costs with `scripts/split.py` so that each
bill is paid only by the people it was for (a night's campsite by the people there
that night, the vegetarians' food by the vegetarians) and every cent is accounted for.

It refuses to build when:
- a price has no source and no check mark, or a line has no price
- a cut of meat is ambiguous
- a meal falls before people arrive or after they leave
- a group has nothing to eat at a meal
- a line has no store, or a store that is not in the list
- a line does not say how its amount is worked out, or a fixed count has no reason
- the split cannot charge exactly what was billed
- the page would reach the network

**Fix the plan, never the check.** Read every `WARN`: a budget line that is an
estimate rather than a quote, a job with nobody's name on it, a question with no
deadline. Say each one plainly.

## 4. Deliver

Give the file. Then, in this order:

1. **The check-these prices** the build printed. Nothing else, no disclaimer.
2. **The two or three things most likely to go wrong**, from what you planned: a late
   first dinner, the water or ice weight against the cars, a question due tomorrow.
3. **How to use it:** five tabs. *Guest page* is the one to send everyone (it has no
   prices). *Shopping list* filters by store and keeps ticks and a running total on
   that device. Every tab has *Print this*.
4. **How to share it:**
   - *In Claude:* publish it as an artifact and share the link. The viewer must be
     signed in to Claude.
   - *To anyone, no login:* host it on Vercel. Go to vercel.com, sign up free, then
     **Add New → Project** and drag the file onto the page. No renaming is needed.
     **The file name becomes the web address**, so name the file before you upload it.
     Anyone with the link can open it, and the budget tab shows names and amounts, so
     for a wide audience print or send the guest page instead.
5. **Next time:** tell them to keep the `event.json` (or paste the page's plan back)
   to start the next event from this one, re-checked against the new place.

## In a tool that cannot run the script

Say so and stop. Do not work out quantities, totals or the split by hand: that is
exactly the arithmetic that drifts, and nothing would catch it.
