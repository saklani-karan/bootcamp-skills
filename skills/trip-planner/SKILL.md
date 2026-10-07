---
name: trip-planner
description: Turns a trip someone is actually taking into a single shareable HTML page they can use while travelling - route, flights, hotels, a day-by-day week, places with times and prices, real traveller verdicts, per-day weather, budget and a bad-weather plan. Use whenever someone wants help planning a holiday, a city break or a family trip, or wants an itinerary they can keep, print or send to the people coming with them.
---

# Trip Planner

Someone is going somewhere and wants one page they can open in an airport, in
a taxi, and at eleven at night when a plan has fallen through. Not a summary of
your conversation. Not a wall of options for them to sort out later.

**In Microsoft Copilot Cowork**, this skill's other files (`scripts/`, `assets/`, `reference/`, `example/`) are not
next to this file. They are in the user's OneDrive at
`Documents/Cowork/skills/trip-planner/`. Open them from there before you build.

## Ask first, and do not start until you have it

Do not research or write anything until you know:

- **Where.** If undecided, ask what is pulling them there and what they have ruled out.
- **When.** Exact dates, or a window plus a length. And where they are flying from.
- **Who.** How many, and ages. **Which passports** — this decides visas and is the
  part that can cost someone the whole trip.
- **Budget.** A rough total, and whether it includes flights.
- **What they actually enjoy.** Push back on "culture" and "food". Ask for the best
  day of a past trip, and one day they would never repeat.
- **Anything already booked**, and any firm no.

If an answer is vague, say which part is vague and ask again. Do not fill the gap
with something generic.

**If what they asked for and where they are going do not match, say so before you
research.** Someone asking for snow in a city that does not get snow has made an
assumption worth surfacing on turn one, not on page three.

## Then research. Do not write from memory alone.

Run the checklist in `reference/research-checklist.md`. It names what to search
for and - more importantly - what must carry a source and what must be marked
unverified.

**The test of whether you really searched: at least one thing you find should
change the plan.** A cable car closed for maintenance, a flight that retimes, a
museum shut on the day you had chosen. If nothing you found changed anything,
you looked things up to confirm what you had already decided.

## The rules that make the page worth having

**Decide, don't offer.** Your job is to reduce the number of decisions left. Name
the actual train, the actual neighbourhood, the actual hotel, and say in a few
words why that one. Two or three real alternatives somewhere obvious is useful.
A page made of alternatives has handed the work back.

**The relocation test.** If a line would survive being moved to a different
country, delete it and write the real one. "Explore the old town" is not a plan,
it is a shape where a plan should be.

**Mark everything perishable.** Prices, opening hours, timetables, entry rules
and anything seasonal get the check mark. Being wrong about a museum's hours is
a wasted morning; being wrong about a visa is the trip. Treat those differently.

**Weather is per day and per place, never one figure for the trip.** A summit and
a city centre are different climates on the same date. And **a forecast more than
about ten days out does not exist** - say so plainly, give the long-term average
for that place on that date, and link to the live forecast for each location.
Never present an average as a forecast.

**Reviews have to do work.** Read what travellers actually say, then show what it
changed: kept, tweaked, changed, or dropped. A review that changed nothing was
decoration.

**Do not fill every hour.** Plan less than the time available, visibly. Where a
day is deliberately light, say so, so it reads as a decision rather than an
oversight.

**Lists are never capped, prose is.** Every day, every booking, every deadline
appears. Nothing hides behind "and 12 more". It is the sentences that get cut.

## What you produce

A `trip.json` matching `reference/trip-schema.md`. Then check, once, whether the
sandbox that runs Python can reach the web (your own web search may work while it cannot):

```bash
python3 scripts/check_net.py
```

It answers `internet: yes` or `internet: no` within about ten seconds. The answer
decides which of the two builds below you run. Nothing else does.

### `internet: yes` - the normal build

```bash
python3 scripts/build_page.py trip.json --out trip-brief.html
```

The script renders the page, fetches a real photograph for each named place from
Wikimedia Commons, embeds every image in the file, checks that every link
resolves, and writes the credits.

**It will refuse to build** if a price has neither a source nor a check mark, or
if a link does not resolve. That refusal is the point - fix the data, do not work
around it, and **never switch to `--no-net` or `--live-photos` to get past it**.
Run with `--explain` to see exactly which rows failed.

The finished file is **one self-contained page with no model inside it**. It works
offline, on a plane, with no account, in two years. Hand it over by giving them
the file, and tell them it can be hosted as-is if they want a link to share.

### `internet: no` - Microsoft Copilot Cowork, and possibly Claude

**Still run our builder**, with two flags:

```bash
python3 scripts/build_page.py trip.json --out trip-brief.html --no-net --live-photos
```

- **Do not write the page yourself, and do not make a "text-only adaptation".** The
  builder still runs every price rule and refusal and draws the same page.
- **Every photo needs a `wiki` title** - the English Wikipedia article about *that
  exact place*, not a general topic (a "Christmas market" article shows some other
  city's market). The build refuses a photo without one. Give the hero the title you
  are most sure of. A place with no article of its own gets no photo.
- What this build does differently - say it, do not promise more:
  - **Photos are not in the file.** The page loads each one from Wikipedia when it
    is opened with internet, and credits it. Offline, the photos are hidden and the
    rest of the page still works.
  - **No link was checked.** The page says "links not machine-checked" where the
    normal build says "checked", and the builder prints one sentence - pass it on
    word for word.
- **Describe it accurately:** *"Built with the trip-planner skill's own builder
  (`build_page.py`). This sandbox has no internet, so photos load from Wikipedia when
  you open the page online, and the links were not machine-checked."* Never call it an
  adaptation, a simplified version or text-only - and never say its links were checked.
- **Never hand over a build made with `--no-net` alone.** Its photo boxes are empty.
  The only build without internet that you hand over is `--no-net --live-photos`.

## Only if you cannot run code at all

If you can run Python, use the builder - `check_net.py` decides which build.
In a tool with no code execution, the three markdown and CSS files still work:
write the same `trip.json`, then assemble the page by hand against
`assets/style.css` and the section patterns in the schema. You lose the photo
fetching, the link checking and the refusal - so **say out loud that the prices
and links in that version are unverified**, because nothing is now stopping them
being wrong.
