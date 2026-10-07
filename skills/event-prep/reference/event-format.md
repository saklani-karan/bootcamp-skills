# event.json

One object. `example/tahoe-camping-weekend.json` uses every part of it.

## Top level

| field | meaning |
|---|---|
| `id` | lowercase-and-dashes. Keeps this plan's ticks separate in the browser |
| `title`, `subtitle`, `where` | shown at the top; `where` describes the place (kitchen? water?) |
| `units` | `us` (lb, oz, gal, qt) or `metric` (kg, g, L, ml). The maths is metric inside either way |
| `currency` | the symbol, default `$` |
| `look` | `{"font": rounded/clear/story/hand, "bg": auto/snow/sky/pine/sunset/berry/night}` |
| `arrive`, `depart` | `2026-10-09T17:00`. These decide which meals exist |
| `curfew` | any hard stop, as text |
| `groups` | `{"regular": 11, "vegetarian": 3}` - everyone, by what they eat. Adds up to the headcount |
| `owned` | what they already have, so nobody buys or rents it |
| `arrival_note`, `drinks`, `guest_notes` | for the guest page. At most two guest notes |
| `stores` | `[{"name", "hours", "phone", "address", "note"}]` in the order they will be visited |
| `meals`, `shopping`, `committed`, `collected`, `split`, `timeline`, `open_questions` | below |

## A meal

```json
{"id": "sat-dinner", "name": "Burger night", "start": "2026-10-10T18:00", "open": "",
 "menu": [{"dish": "Beef burgers", "for": ["regular"]},
          {"dish": "Veggie burgers", "for": ["vegetarian"]},
          {"dish": "Corn on the cob", "for": ["everyone"]}]}
```

`open` replaces the clock time on the guest page for self-serve meals ("Whenever
you're up, until 10"). Every group must have at least one dish at every meal.

## A shopping line

```json
{"item": "Boneless chicken thighs", "store": "Costco Truckee", "section": "Meat",
 "for": ["regular"], "meals": ["fri-dinner"],
 "calc": {"fn": "meat", "cut": "boneless"},
 "pack": {"size": 6, "unit": "lb", "price": 20.99},
 "check": true, "note": "Usual price, confirm on the day"}
```

| field | meaning |
|---|---|
| `store`, `section` | where it is bought, and the aisle or heading it sits under |
| `for` | which groups it is for; leave out for everyone |
| `meals` | the meal ids it is for. The count multiplies the amount |
| **one of** `calc` / `per_person` / `fixed` | how the amount is worked out - never the amount itself |
| `pack` | how it is sold: `size` + `unit` + `price`, and an optional `label` ("bag of 8"). The script buys whole packs |
| `source` or `check` | a link for the price, or `true` when it is not confirmed |
| `note` | a warning that belongs on this item ("ask for skin-on") |
| `sit` | `high` (default) buys the top of the range, `low` the bottom |

`unit` is one of `lb`, `oz`, `kg`, `g`, `gal`, `qt`, `floz`, `l`, `ml`, `each`.

### `calc` - the per-person tables in quantities.py

| `fn` | settings | per person |
|---|---|---|
| `meat` | `cut`: boneless · bone_in · ground · grilled · whole_fish | per main meal, raw weight |
| `starch` | `kind`: potatoes · rice_dry · pasta_dry · fries | per meal |
| `dips` | `kind`: dip · toum | per occasion |
| `salad_veg` | | per meal, total vegetable |
| `pita` | | 2-3 pieces of bread or tortilla per meal |
| `breakfast` | `kind`: items_total · eggs_centrepiece · eggs_with_bread · pastry | per morning; the leaving morning counts half |
| `drinks` | `style`: party · dinner; `sessions` (default the number of nights) | per evening, 85% drinking |
| `ice` | `profile`: cans · cocktails; `no_fridge` | per day; with no fridge the ice is the cold chain |
| `water` | `tap_on_site`, `hot_weather` | per day; the page states the weight |

`per_person` is a rate in the pack's unit (`1.5` buns each, `0.25` lb of turkey
each), multiplied by the people it is for and the number of meals.
`fixed` is a count with a `why`.

## Money

```json
"committed": [{"what": "Campsite Friday night", "amount": 45, "status": "paid", "night": "Fri"}],
"collected": {"per_head": 40, "payers": 14},
"split": {"people": [{"name": "Ana", "nights": ["Fri", "Sat"], "group": "regular", "paid": 90,
                      "excluded_from": ["Drinks"]}]}
```

- `status` is `paid`, `quoted` or `estimate`. An estimate is flagged as a placeholder.
- `night` on a committed line shares it only among the people there that night.
- `split` is optional. Each person's `group` decides which food they pay for;
  `excluded_from` names a section or a committed line they do not pay into at all
  (a driver and the beer). `paid` is what they already fronted. List every person.

## Jobs and deadlines

```json
"timeline": [{"at": "2026-10-09T15:30", "what": "Safeway: ice and water last", "who": "Dev", "warn": "Straight into the coolers"}],
"open_questions": [{"q": "How many are driving home?", "gates": "the drinks order", "decide_by": "2026-10-09"}]
```
