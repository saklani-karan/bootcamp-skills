# Logistics

Venue constraints, rentals, power, cooking timelines, and transport.

**Contents:** Venue survey · Multiple sites · Cooking capacity · Cook-day
timelines · Power · Generators · Batteries, solar and vehicles · Sound systems ·
Sourcing and store routing · Cold chain and transport · Make-ahead

For events with no building — camping, festival camps — read
`camping-and-festivals.md` alongside this.

---

## Venue survey

Ask these before planning the menu. Each one has bitten a plan that skipped it.

**Is there a building?** — ask this before the rest, because everything below
assumes one. A building silently supplies water, cold, cooking, power, shelter,
toilets and waste disposal. Remove it and each becomes a line item with a weight,
a cost and an owner. **For camping, festival camps or anything else without a
building, use the camp survey in `camping-and-festivals.md` instead of the
kitchen and power sections below** — the sites, cooking-capacity, power, and
cold-chain material here still applies, and applies harder.

**Sites** — ask this next, because the rest of the survey assumes an answer
- How many separate places does this happen in? Never assume one.
- How far apart, in walking minutes rather than metres?
- Is there vehicle access between them?
- Where is there mains power, and where isn't there?
- Is the route between them lit?

**Kitchen**
- How many ovens, across how many buildings? What size?
- Fridge capacity — total, not per unit. A weekend for 30 can involve 15 kg of
  meat plus dips, dairy and drinks, and they compete for the same shelves.
- Freezer space, if anything is travelling frozen.
- Is there a barbecue? Gas or charcoal, and who's bringing fuel?

**Power**
- How many circuits, and which outlets are on which? This matters more than total
  amperage — see below.
- Is there an outdoor outlet for sound and lighting?

**Site**
- Distance to the nearest grocery store. This changes how lean you can buy.
- Noise curfew or quiet hours. Ask explicitly; it drives the whole schedule.
- Parking and load-in distance.

**Beds and buildings**
- If people are split across multiple units, the kitchen work is split too. Name
  who is responsible for which building's oven.

## Multiple sites

**Ask how many places the event happens in before anything else, and treat
single-site as the special case.** Camping trips and festival camps are
multi-site by definition — the stage, the tents, the water and the cooking are
in four different places. Even a chalet weekend can have the party somewhere the
kitchen isn't.

Measure the separation in **walking minutes, not metres**. Ten minutes each way
means every forgotten thing costs twenty.

What a second site changes:

- **Consumables have to be where the people are.** Nobody walks twenty minutes
  for a drink, so drinks and ice migrate to the other site — into coolers, which
  lose ice far faster than a fridge does. A quantity computed for one location is
  wrong for two.
- **Fuel, spares and tools belong at the site that consumes them.** Running dry
  mid-set with the fuel ten minutes away is twenty-five minutes of silence.
- **Load-in becomes a scheduled task.** Speakers, a sub, stands, cables, a
  generator and fuel do not travel 500–800 m spontaneously. Ask about vehicle
  access; if there is none, it's two people and several trips, and it needs a
  slot with names on it.
- **A curfew triggers a migration, not just silence.** When the music stops
  everyone walks back. Put the late-night food at the destination *before* people
  leave, or they arrive to a dark kitchen.
- **Light the route.** People walking unlit ground late at night after several
  hours of drinking is the highest-consequence risk in most weekends. Phone
  torches are the default plan and half the phones will be flat. Solar stake
  lights, headlamps or lanterns at the turns cost almost nothing in advance and
  cannot be bought on the night.
- **Each site needs an owner**, and it can't be the same person.

## Cooking capacity

**Count trays against ovens before committing to a dish.** A tray bake for 26
needs roughly four deep pans. Four pans do not fit in one domestic oven. If the
group is split across buildings, distribute the trays and assign one person per
oven whose only job is that oven.

Rented ovens run cold and slow. Preheat everything simultaneously and start
earlier than the recipe says.

**Don't crowd protein.** Overlapping pieces steam instead of roasting and the
skin never crisps. An extra pan is cheaper than a ruined main.

Disposable foil pans buckle when loaded — slide a rimmed baking sheet underneath
each one.

**Count burners the same way when there is no oven.** A two-burner camp stove
realistically feeds 8–10 people per sitting, so 33 people is three or four stoves
running at once, one large pot over a fire, or a menu that doesn't need everyone
fed simultaneously. See `camping-and-festivals.md`, which also covers which
dishes survive the loss of an oven and which have no equivalent at all.

## Cook-day timelines

Build backwards from the serving time, and write it as a clock, not as durations.
People cooking in an unfamiliar kitchen after a late night cannot do arithmetic.

```
| 1:00 PM | Preheat, prep vegetables       |
| 1:35 PM | Trays in, covered              |
| 1:55 PM | ← the handoff step             |
| 2:40 PM | Temperature check              |
| 3:00 PM | Serve                          |
```

**Identify the single step most likely to be missed** — usually a handoff partway
through, where something goes in or comes off — and mark it. Tell people to set a
phone alarm for it in every building.

Name the cooks in advance, in the plan, by role. A 1 PM start on the morning
after a party is not something to leave to whoever volunteers at noon.

Build in 30–40 minutes of slack and say that it's there.

**Explain the reason behind any counter-intuitive instruction.** "Don't stir"
and "don't reduce it further" both look like mistakes to a helpful person. Attach
the why or they'll be overridden.

## Power

**Watts and watt-hours answer different questions, and most power problems are a
confusion between them.**

- **Watts (W)** — how much can run *at once*. Exceed it and something trips or
  cuts out. This is a wall, and it is instant.
- **Watt-hours (Wh)** — how *long* it lasts. Capacity divided by average draw.

Size the source on watts. Size the battery on watt-hours. Say which one any
number you're given refers to, and if it's ambiguous, ask.

**Peak decides what trips; average decides how long it lasts.** Powered speakers
draw their nameplate figure only on bass peaks — a rig peaking at 2,780 W can
average 820 W over an evening. Using peak for runtime makes batteries look three
times worse than they are; using average for sizing trips the supply on the first
loud song.

**Household circuits are the constraint people hit first.** A 15 A / 120 V circuit
is 1,800 W, and you should plan on 1,440 W continuous (the 80% rule). Two air
fryers alone are roughly 3,000 W. They will trip a breaker if they share a
circuit with a kettle.

Typical loads:

| Appliance | Running W | Average W | Surge |
|---|---|---|---|
| Air fryer | 1,400–1,700 | same | — |
| Kettle | 1,500 | same | — |
| Coffee maker | 800–1,200 | same | — |
| Microwave | 1,000–1,500 | same | — |
| Fridge | 150–200 | 50–80 | 600–800 |
| **Electric cooler, 12 V compressor** | **40–60** | **15–25** | — |
| Powered speaker, 12–15" | 300–800 | 120–200 | — |
| Powered subwoofer | 500–1,000 | 250–350 | — |
| LED string lighting | 50–100 | same | — |
| Portable AC | 1,000–1,500 | same | 2,500+ |

**The loads that break a plan are the sustained ones, not the loud ones.** An air
fryer draws twenty times what an electric cooler does and runs for fifteen
minutes. The cooler draws almost nothing and runs while everyone is asleep — two
of them are roughly 864 Wh a day, which is most of a typical camping battery
bank. Anything that runs unattended for twenty-four hours gets multiplied by
twenty-four before you compare it to anything.

## Generators

1. Sum the running watts of everything that will be on simultaneously.
2. Add the *largest single* surge figure, not all of them — motors rarely start
   together.
3. Add 25% headroom.

A sound rig plus lighting plus a fridge is usually 2,000–3,000 W, which is a
mid-size inverter generator. Add cooking appliances and you're at 5,000 W+.

**Inverter generators cost more and are worth it** for anything with audio or
electronics — clean power, and dramatically quieter, which matters when there's
already a noise curfew, and matters double when the generator sits with the
crowd rather than with the neighbours. Check the rated noise in dBA at 7 m.

**A rental line is not a rental spec.** A price tells you nothing about whether
the machine carries the load. Whenever a rental appears as a budget line, ask
what it has to run.

**Ask for run time at 50% load, not the headline figure**, which is quoted at
quarter load. Tank sizes in the same power class vary by a factor of two, so
"3,500 W inverter" can mean five hours or nine. Confirm fuel type, buy fuel in
advance, and keep it at the site the generator is on. Generators are rated in
running watts *and* peak watts; the peak figure is the marketing number.

## Batteries, solar and vehicles

Increasingly the answer isn't a generator at all. Ask what the organiser already
owns before sizing anything to rent.

**Power stations — the output rating is a ceiling you cannot raise.** A 500 W
station cannot start an 800 W speaker; it cuts out instantly. And **stations
cannot be ganged** — each device sees exactly one battery, so owning six of them
doesn't raise the ceiling at all. Generator sizing is additive; battery sizing is
not. This single distinction settles most "can we run the PA off batteries"
questions, and the answer is almost always no.

**Power banks are rated in mAh at 3.7 V, not at the 5 V they hand you.** Convert
before comparing to anything: `Wh = mAh × 3.7 ÷ 1000`, then take roughly 65% for
conversion losses. 136,000 mAh sounds enormous and is about 327 Wh usable —
around 22 phone charges. Banks are USB only. Never a speaker, never a cooler.

**Solar recharges; it does not supply.** Realistic daily yield is roughly
`nominal W × peak sun hours × 0.65` — about 585 Wh/day for 200 W of folding panel
in a northern summer. Against a running PA that's a fraction of live demand. It
refills a bank overnight; it cannot feed a party.

**An EV with V2L is in a different league — 50–100× everything else combined**,
and typically outputs 3.7 kW, enough to run a whole party rig silently with no
fuel and no refuelling trip. Whether a given car supports it is the highest-
leverage question in this whole section, and **owners frequently don't know** —
it varies by model year and market, and often needs a specific adapter. Ask them
to check the charging menu or the manual. If it works, it beats a generator on
every axis except that you should still keep the generator as backup.

**Multi-day battery budget**, which is the camping case:

```
daily draw  = sum of (average W × hours per day) for everything
daily solar = nominal panel W × peak sun hours × 0.65
net         = daily solar − daily draw
days        = bank Wh ÷ (daily draw − daily solar), when draw exceeds solar
```

State the day it runs out, not just the deficit. "Two nights work, the third
night is where the coolers die" is actionable; "379 Wh/day short" isn't. Close a
gap by running fewer of the sustained loads, raising a fridge setpoint, pre-
chilling on mains before leaving, or adding panel — in that order, because the
first three are free.

## Sound systems

For a group of 30–50 outdoors, two powered tops on stands is usually enough, with
a sub if there's dancing. That's roughly 1,000–2,000 W of speaker.

Rental checklist:
- Powered (self-amplified) speakers are simpler than passive plus amp.
- Stands, speaker cables, and an XLR or 3.5 mm input for a phone or controller.
- A small mixer if more than one source, or if anyone is DJing.
- Weather cover if anything is outdoors.
- Confirm pickup and return times and whether return is same-day — a Monday
  return on a Sunday-departure weekend is a problem.

**The curfew sets the schedule, not the rig.** An 11 PM music cutoff means the
event runs mid-afternoon to late evening, which pulls the main meal to around
3 PM. Plan food around that before booking anything.

## Sourcing and store routing

Route by what each store is actually good for:

- **Warehouse club** — bulk staples, eggs, dairy, produce, cooking oil, foil pans,
  beer where legally sold. Usually the largest single line by a wide margin.
- **Specialty or ethnic grocer** — spices, regional pantry items, specific breads,
  specialty produce. Small total, non-substitutable contents.
- **Butcher** — marinated and prepared meats, house-made sauces. Better than
  packaged, and often the same counter sells the accompaniments.
- **Bakery** — fresh bread and pastry. Almost always needs ordering ahead.
- **Liquor retailer** — check volume-discount thresholds. Buying to reach a
  threshold can pay for itself, but discounted stock is often final sale.

**Flag every phone-ahead item and put them first in the document.** Bakeries and
butchers cannot produce large orders on the spot. Give the call a deadline.

**Split the list into "safe to run short on" and "no substitute nearby."** If
there's a shop near the venue, staples can be bought lean and topped up. Specialty
items, pre-marinated meat, and anything ordered ahead cannot. Expect a shop near a
holiday venue to run 20–40% above warehouse prices — buying lean pays on things
you might not need and costs you on things you're certain to use.

**Where you cannot top up at all, the whole split collapses into one list.** A
festival site you can't leave and re-enter has no shop at any price, so "safe to
run short on" becomes an empty category and every quantity has to be right on the
day you pack. Establish re-entry rules before deciding how lean to buy.

## Cold chain and transport

- **Frozen items double as cooler ice.** Marinated meat frozen flat in bags keeps
  the cooler cold and thaws over the journey.
- **Not everything needs the fridge.** Dry-dough breads like za'atar flatbread
  hold three days sealed at room temperature. **The fridge is the worst place
  for them** — staling is starch retrogradation and it runs fastest at fridge
  temperatures, while the drying-out is what the bag prevents. So: tightly
  bagged, at room temperature, and the fridge space stays free for something
  that needs it.
- **House-made sauces have no preservatives** and won't keep like sealed
  supermarket equivalents. Fine over a weekend, but keep them cold and covered.
- Bulk shopping for 30 people does not fit in one car alongside luggage. Plan two
  vehicles or a dedicated run.

**With no fridge at the other end, all of this becomes the cold chain rather than
just the journey** — block ice over cubed, food and drinks in separate coolers,
everything pre-chilled at home, and a menu that arcs from most perishable to
least across the days. See `camping-and-festivals.md`.

## Make-ahead

**What travels well:** marinated raw meat, cooked grains, dips, anything with
liquid in the pan. Saucy tray bakes reheat far better than dry roasts — the
liquid protects the contents.

**What doesn't:** dressed salads, fried anything, cut potatoes (they grey and
weep), reheated dry-roasted potatoes (they go grainy).

**Acid timing.** Don't marinate in citrus or vinegar for more than a few hours.
Two days in acid turns the surface of meat mealy and chalky. Marinate in oil,
aromatics and zest ahead; add the juice 45 minutes to an hour before cooking.
Cut surfaces take acid faster than skin-covered ones, so boneless needs less time
than bone-in.

**If cooking fully in advance:** pull protein about 3 °C below target, since
reheating finishes it. Cool spread out and uncovered until steaming stops, then
refrigerate — stacking hot food into a sealed container holds it in the danger
zone for hours. Reheat covered, then uncover for the last ten minutes.

**Hold back the finishing touches regardless.** Fresh herbs, citrus, sumac, sauces
and garnishes go on at the venue. That fresh top note is most of what makes
reheated food taste cooked rather than warmed.
