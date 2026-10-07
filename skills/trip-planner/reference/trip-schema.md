# trip.json — the shape

One object. Keys below. Anything ending `_html` may contain `<a href>`, `<strong>`
and `<em>`; everything else is escaped for you, so write plain text there.

## Money cells — the rule the build enforces

Every price is an object, never a bare number:

```json
{ "text": "€183 for four", "source": "https://www.kitzsteinhorn.at/en/tickets-prices/top-of-salzburg" }
{ "text": "price", "check": true }
```

**A price with neither `source` nor `check: true` fails the build.** That is
deliberate. If you could not find the real figure, mark it `check` — do not
invent one to make the page look finished.

## Top level

```json
{
  "page_title": "Madrid and Barcelona",
  "eyebrow": "TRIP BRIEF · 5–12 DECEMBER 2026",
  "title_html": "Madrid <em>and</em> Barcelona",
  "subtitle": "One line on the shape of the trip.",
  "asof": "2 October 2026",
  "footer": "Madrid and Barcelona · 5–12 Dec 2026",
  "facts": [{"label":"TRAVELLERS","value":"4","note":"2 adults · twins, 10"}],
  "critical": {"headline":"...", "detail":"..."},
  "toc_groups": [["Decide","before you book"], ["The week","what you'll do"], ["Practical","money and the rest"]],
  "sections": [
    {"id":"route","title":"The route","tag":"2 bases","kind":"diagram","group":"Decide","note_html":"…","short":"Route"}
  ],
  "photos": [ … ], "route": [ … ], "weather": [ … ], "flights": [ … ],
  "hotels": [ … ], "deadlines": [ … ], "days": [ … ], "places": [ … ],
  "reviews": [ … ], "budget": { … }, "planb": { … }, "ground": [ … ],
  "bookings": [ … ], "addresses": [ … ], "sources": [ … ]
}
```

`sections` controls both the page order and the contents board. `kind` is the
little label ("diagram", "8 days", "chart"); `group` must match a `toc_groups`
name.

## photos

```json
{"key":"prado", "label":"Museo del Prado", "wiki":"Museo del Prado",
 "search":["Museo del Prado facade"], "must":["prado"], "ban":["interior"],
 "alt":"The Prado's main facade.", "hero":false, "caption":"…"}
```

`wiki` (an English Wikipedia article title) is tried first and is much more
reliable than search. `must` requires one of those words in the file's title;
`ban` rejects it. **Use both.** A bare search for a hotel once returned a
photograph of a grave in another country.

One photo may set `"hero": true` — it becomes the masthead band.

Reference a photo anywhere with its `key`: `"photo": "prado"`.

## The repeating shapes

| key | one entry looks like |
|---|---|
| `route` | `{"kind":"stop","name":"SFO","meta":"Depart Sat 5 Dec"}` · `{"kind":"leg","label_html":"Fly 11 h"}` · `{"kind":"base","name":"Madrid","nights":"3 nights","tone":"s","meta_html":"…","photo":"…","trips":[{"tag":"Day trip","html":"…"}]}` |
| `weather` | `{"day":"Sun 6","where_html":"<strong>Madrid</strong>","temp_html":"12 °C / 3 °C","light":"08:30 – 17:50","note_html":"…","key":false,"travel":false,"check":false,"derived":false}` |
| `flights` | `{"tag":"Outbound","tone":"out","pill":"Pick this one","legs":[{"route":"SFO 15:20 → MAD 11:40","note":"next day","sub_html":"…","quiet":"…"}],"alt_html":"…","fare":{…}}` |
| `hotels` | `{"name_html":"<a href=…>Hotel X</a>","when":"Madrid · 6–9 Dec","tone":"s","meta":"address","rate":{…},"score":"8.7","score_src":"Booking.com","verdicts":[{"kind":"plus","label":"Loved","text":"…"}],"so":"…","photo":"…"}` |
| `deadlines` | `{"date":"Oct 7","what":"Book flights","kind":"key","pill":"Budget hinges on it"}` — `kind` is `crit`/`key`/`go`/`now`/`""` |
| `days` | `{"day":"Mon 7","where":"Madrid","tone":"s","main_html":"…","sub_html":"…","pill":"Full","pill_tone":"warn","photo":"…"}` |
| `places` | `{"when":"Mon 7 Dec","tone":"s","name_html":"<a …>Prado</a>","price":{…},"extra":"09:00","note":"…","photo":"…"}` |
| `reviews` | `{"name":"Prado","source":"Tripadvisor","loved":"…","watch":"…","so":"…","verdict":"Changed","tone":"cool"}` |
| `budget` | `{"headline":"…","alt":"…","cap":7000,"scale":9000,"scenarios":[{"label":"…","total":7250,"items":[{"key":"flights","usd":3800}]}]}` |
| `planb` | `{"steps":[{"tag":"If","html":"…"}],"swaps":[{"name_html":"…","text":"…","photo":"…"}]}` |
| `ground` | `{"name":"Money","a_html":"…","b":"…","check":true,"danger":false}` |
| `bookings` | `{"id":"flights","item":"Flights — …","date":"5 & 12 Dec"}` |
| `addresses` | `{"place_html":"Prado","address":"Calle de Ruiz de Alarcón 23, 28014 Madrid","phone":"+34 …"}` |
| `sources` | `{"label":"Facts","html":"<a …>…</a> · <a …>…</a>"}` |

`tone` values: `s` (first base), `v` (second base). Pill tones: `good`, `warn`,
`cool`, `crit`, `mute`.

## Running it

```bash
python3 scripts/build_page.py trip.json --out trip-brief.html --explain
```

`--explain` prints every link check and every photo decision. `--no-net` skips
both — useful while drafting, but never for the version you hand over, because
nothing has been verified. The one exception is a builder whose sandbox has no
internet (`python3 scripts/check_net.py` says `internet: no`): there, build with
`--no-net --live-photos` (every photo then needs a `wiki` title), and the page says
its links were not machine-checked. A build with `--no-net` alone is never handed over.
