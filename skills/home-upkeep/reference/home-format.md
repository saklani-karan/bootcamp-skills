# home.json — the format

You write this file. The script (`scripts/build_home.py`) does every date. `example/columbus-house.json`
is a complete real one.

```json
{
 "id": "columbus-house",                 // lower-case letters, digits, hyphens; names the saved ticks and the .ics
 "title": "Our house: a year of upkeep",
 "region": "Columbus, Ohio, US",          // shown on the page
 "hemisphere": "north",                  // "north" or "south": south moves every season six months
 "words": "us",                          // "us" (fall, faucet, tire) or "uk" (autumn, tap, tyre)
 "home": {"type": "house", "tenure": "own"},   // type: house, townhouse, flat, apartment, condo; tenure: own, rent
 "features": ["smoke_alarms", "furnace", "gutters"],
 "start": "2026-11",                     // a month (this month or later) or a date (today or later)
 "jobs": [
   {"id": "smoke-alarm-test", "last_done": "2026-10-03"},
   {"id": "hvac-filter", "every": 2},     // "every" may change a standard job's interval (1-60 months)
   {"id": "gutters-clean"}                // no last_done = not known
 ],
 "custom": [
   {"title": "Service the snow blower", "season": "early-autumn", "who": "diy", "minutes": 45,
    "why": "Old fuel gums the carburetor, so it won't start on the first snowy morning."}
 ],
 "look": {"font": "rounded", "bg": "auto"}
}
```

## Features

Only list what the home really has. A job that needs a feature the home does not list is refused.

| key | what it means |
|---|---|
| `smoke_alarms`, `co_alarms`, `fire_extinguisher` | the alarms and extinguisher in the home |
| `furnace` | forced-air heating (filters, yearly service) |
| `boiler` | a boiler and radiators |
| `ac` | air conditioning or a heat pump |
| `fireplace` | a wood fireplace, chimney or wood stove (not a sealed gas fire) |
| `water_heater` | a hot-water tank or cylinder (not a tankless/combi unit) |
| `dryer` | a vented clothes dryer (not condenser or heat-pump) |
| `dishwasher`, `washing_machine`, `range_hood` | the appliances |
| `gutters`, `roof` | only if the household is responsible for them (not in most flats) |
| `yard`, `deck`, `pool`, `outdoor_taps`, `sprinklers` | outside |
| `septic`, `well`, `sump_pump` | off-grid water and drainage |
| `basement` | a basement, or ground-contact rooms in a radon area |
| `garage_door` | an automatic garage door |
| `car` | a car the household looks after |

## Jobs

Pick from `reference/jobs.json` by `id`. Each standard job already carries its interval or season, its
one-line why, DIY or pro, minutes, and whether it is a safety job. Choose every job whose feature the home
has, and every job with no feature (they suit every home). Leave one out only when the person says so —
the build warns about any safety job that fits the home but is missing.

- **`last_done`**: `YYYY-MM-DD`, or `YYYY-MM` when they only know the month. Leave it out when they
  don't know. Never in the future.
- **Unknown or overdue** jobs are treated as due now; the script spreads them over the first weeks.
- **Renting**: jobs that are normally the landlord's become "Remind your landlord: …" with 5 minutes.
  Don't rewrite them yourself.

## Custom jobs

For anything the list does not cover (a koi pond, a snow blower, a re-stain). Each needs:
`title`, `why` (one line: what goes wrong if it is skipped), exactly one of `every` (whole months, 1–60)
or `season`, `who` (`diy`, `pro` or `landlord`), `minutes` (a rough guess, 1–600). Optional: `safety: true`
(never moved later than its due date), `last_done`. Don't repeat a standard job as a custom one.

## Seasons

| key | northern month | southern month |
|---|---|---|
| `spring` | April | October |
| `late-spring` | May | November |
| `summer` | July | January |
| `early-autumn` | September | March |
| `late-autumn` | November | May |
| `winter` | January | July |

Seasonal jobs fall on a Saturday. In the tropics, or anywhere the four seasons don't fit, use `every`
for custom jobs and say that seasonal jobs follow the nearest hemisphere.

## What the script does with it

- Twelve whole months from the start month. If that is this month, the plan starts today.
- No week (Monday to Sunday) holds more than 3 jobs. To make room a job moves by at most a week;
  a safety job only ever moves earlier, never past its due date.
- Overdue or never-recorded jobs: safety ones within 6 weeks of the start, the rest over the first
  3 months (or their interval, if shorter); the next ones follow on from there. A seasonal safety job
  whose last slot was missed is done now too, when its next slot is more than 3 months away.
- A seasonal job done under 60 days before its slot skips that slot.
- A job not due inside the twelve months is listed under "Left out of these twelve months" with its next date.
