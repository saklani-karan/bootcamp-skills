---
name: home-upkeep
description: "Plans a year of home maintenance as one HTML page and a calendar file: every job from smoke-alarm tests and furnace filters to gutters, the chimney, the water heater and the car, month by month with the date, why it matters, DIY or a professional, and how long it takes. Tick jobs off as they are done, download every date into Google, Apple or Outlook calendar, or print one sheet per quarter. Works for houses and flats, owners and renters (landlord jobs become reminders to the landlord), and either hemisphere. Use whenever someone asks what home maintenance to do and when, wants a home maintenance schedule, checklist or calendar, has just moved in, or keeps forgetting the filter, the gutters or the boiler service."
---

# Home upkeep

You make two things: a single HTML page holding a year of home jobs, and the same
dates as a calendar file (`.ics`). The page is already written (`assets/engine.html`)
and **every date is worked out by a script**. Your job is to find out what the home
has and when things were last done, and to choose the jobs. You never write a date
yourself: across a year of jobs, hand-placed dates pile up in one week, drift past
a safety deadline, or land in the wrong season for the hemisphere.

The page has no model inside it and makes no network calls, so it behaves the same
as a shared Claude artifact, a page hosted on Vercel, or a file double-clicked from
Downloads. Its calendar button builds the `.ics` inside the page.

**In Microsoft Copilot Cowork**, this skill's other files (`scripts/`, `assets/`, `reference/`, `example/`) are not
next to this file. They are in the user's OneDrive at
`Documents/Cowork/skills/home-upkeep/`. Open them from there before you build.

## 1. Ask first, in one message, then wait

Ask all of this at once, numbered, so it can be answered in one reply:

1. **Where the home is.** Country and region or city. This sets the seasons (south
   of the equator they flip) and the wording (US or UK).
2. **What kind of home.** House, townhouse, flat/apartment or condo, and whether
   they **own or rent**.
3. **What it has.** Offer this list to tick: smoke alarms · carbon monoxide alarms ·
   fire extinguisher · furnace (forced-air) · boiler and radiators · AC or heat pump ·
   wood fireplace or stove · hot-water tank · vented dryer · dishwasher · washing
   machine · range/cooker hood · gutters · a roof they look after · yard/garden ·
   deck/balcony · pool or hot tub · outdoor taps · sprinklers · septic tank · well ·
   sump pump · basement · automatic garage door · car(s). Anything else they look after.
4. **When the big jobs were last done, if they know**: heating service, chimney
   sweep, gutters, water heater, alarm batteries, septic, car service. "Don't know"
   is a fine answer.
5. **The start month** (default: next month).
6. **Anything else** they do regularly that should be in it, and how often.
7. **The look**, with a default if they don't mind: letters Rounded · Easy to read ·
   Storybook · Handwriting; colour Auto (follows the device) · Snow · Sky · Pine ·
   Sunset · Berry · Night. Both can be changed later from the page's Look menu.

If the conversation already answers something, don't ask it again. If an answer is
vague ("the usual stuff"), ask about that one thing; do not fill the gap with a guess.

## 2. Write `home.json`

Read `reference/home-format.md` for the exact format, the feature keys and the
seasons; `example/columbus-house.json` is a complete one. The jobs are in
`reference/jobs.json`: pick by `id`.

- **Choose every standard job whose feature the home has**, plus the ones with no
  feature (they suit every home). Leave one out only when they say so.
- **Copy last-done dates as given.** A month is enough (`2026-04`). Unknown → leave it out.
- **Renting:** keep the landlord's jobs in. The script turns them into "Remind your
  landlord: …". Don't rewrite them yourself.
- **Their own jobs go in `custom`**, each with a one-line `why`, an interval in
  months or a season, DIY/pro/landlord and rough minutes. Mark a job `safety` only if
  putting it off could hurt someone.
- **Intervals are the common, conservative ones.** If they say the manual asks for
  sooner (a filter monthly with pets), change `every` on that job; never stretch a
  safety interval to make the plan lighter.
- Set `hemisphere` and `words` from where they live. **Never write `builtOn`**: the build
  uses today's real date, and refuses a `builtOn` that differs from it (only the shipped
  example and test fixtures pin one, with `"example": true`).

## 3. Build

```bash
python3 scripts/build_home.py home.json --out /mnt/user-data/outputs/<name>.html \
        --ics /mnt/user-data/outputs/<name>.ics
```

The script expands every job over twelve months from the start, honours last-done
dates, puts seasonal jobs in the right months for the hemisphere, and spreads them so
**no week holds more than 3 jobs**: a job moves by at most a week, and a safety job
only ever moves earlier, never past its due date. Overdue or unknown jobs come first,
spread over the opening weeks.

It refuses to build when:
- a job has neither an interval nor a season, or an interval is not 1–60 whole months
- a job id is not in `reference/jobs.json`, or a job is listed twice
- a custom job has no `why`
- the start is before today, or a last-done date is in the future
- a feature is unknown, or a job needs a feature the home does not have
- the plan is empty
- the jobs cannot be spread to 3 a week within those rules
- the page would reach the network

**Fix the plan, never the check.** If the spread fails, say which job and week the
build named and ask whether to drop a job or change an interval. Read every `WARN`
(a safety job that fits the home but is missing, no smoke alarms listed) and say
each one plainly.

## 4. Deliver

Give both files. Then, in this order:

1. **The warnings** the build printed, if any. Nothing else, no disclaimer.
2. **The first month in one line:** how many jobs, and the safety ones by name.
3. **How to use it:** tick a job when it's done (ticks stay in that browser on that
   device). *Download calendar (.ics)* puts every date into Google, Apple or Outlook
   calendar, one all-day entry per job; or open the `.ics` file you were given.
   *Print* gives one sheet per quarter, with boxes to tick by hand.
4. **How to share it:**
   - *In Claude:* publish it as an artifact and share the link. The viewer must be
     signed in to Claude.
   - *To anyone, no login:* host it on Vercel. Go to vercel.com, sign up free, then
     **Add New → Project** and drag the file onto the page. No renaming is needed.
     **The file name becomes the web address**, so name the file before you upload it.
     Anyone with the link can open it, and the page shows the town, what the home has
     and what is overdue, so leave the street address out and share it with the household.
5. **Next year:** tell them to keep `home.json` (or paste the page back): next year's
   plan starts from it with the new last-done dates.

## In a tool that cannot run the script

Say so and offer the reduced version: the list of jobs that fit the home from
`reference/jobs.json`, each with its interval or season and why, **without dates**
and without a calendar file, clearly labelled as not machine-checked. Do not place
the dates by hand: spreading a year of jobs, keeping safety jobs on time and flipping
the seasons is exactly the part that goes wrong.
