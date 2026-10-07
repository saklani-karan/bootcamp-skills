# quiz.json

```json
{
  "id": "salzburg-vienna-trivia",
  "title": "Salzburg & Vienna Trivia",
  "subtitle": "How much do you know about your trip? 5–12 December 2026",
  "age": 10,
  "lang": "en-US",
  "count": 12,
  "level": 2,
  "players": [],
  "look": {"font": "rounded", "bg": "auto", "photo": ""},
  "cover": "salzburg-market",
  "coverAlt": "Salzburg's old town by the river",
  "builtOn": "2 October 2026",
  "sections": ["Getting there", "Salzburg", "Vienna"],
  "photos": [ {"key": "fortress", "label": "Hohensalzburg Fortress", "wiki": "Hohensalzburg Fortress"} ],
  "questions": [ ... ]
}
```

| field | meaning |
|---|---|
| `id` | lowercase-and-dashes. **Keeps this quiz's scores separate.** Reuse it only for a corrected version of the same quiz |
| `count` | questions per game. The page also offers 5 / 10 / 15 / all |
| `level` | starting difficulty: 1 easy, 2 medium, 3 hard |
| `players` | names to pre-fill. Leave empty and the page asks |
| `look.font` | `rounded` · `clear` · `story` · `hand` |
| `look.bg` | `auto` · `snow` · `sky` · `pine` · `sunset` · `berry` · `night` |
| `look.photo` | a photo key for the background, or `""` |
| `cover` | photo key for the home screen |
| `sections` | in trip or topic order. Games follow this order |
| `lang` | read-aloud voice: `en-US`, `en-GB`, `es-ES`, ... |

## A photo

| field | |
|---|---|
| `key` | short id, lowercase |
| `label` | what it shows (credits page, menu) |
| `wiki` | an English Wikipedia article title. Its lead image is used (most reliable) |
| `search` | a string or a list of Commons searches, used only if `wiki` finds nothing |
| `must` / `ban` | a search result's file name must contain one of `must` and none of `ban` |

## A question

| field | |
|---|---|
| `id` | short, unique within the quiz |
| `section` | one of `sections` |
| `lvl` | 1, 2 or 3 |
| `t` | `mc` (3–4 options) · `tf` (true/false) · `pic` (photo on the front, options) |
| `q` | the question |
| `opts` | for `mc` and `pic`: the options |
| `a` | `mc`/`pic`: index of the right option (write it first, `0`, since the page shuffles). `tf`: `true` or `false` |
| `h` | hint. Must not contain the answer |
| `f` | the "Did you know?" fact shown on the back |
| `photo` | a photo key: shown on the front (small) and back. Required for `pic` |
| `front` | `false` hides the photo on the front when it would give the answer away |
| `src` | source URL, link-checked at build |
| `check`, `note` | `true` + where it came from, when there's no URL or the fact can change |

```json
{"id": "v3", "section": "Vienna", "lvl": 1, "t": "mc", "photo": "zoo",
 "q": "The zoo you visit on Thursday holds a world record. What is it?",
 "opts": ["Oldest zoo in the world", "Biggest zoo in the world", "Most penguins in the world", "Tallest giraffe in the world"],
 "a": 0,
 "h": "Think about how long ago emperors lived in the palace next door.",
 "f": "Schönbrunn Zoo opened in 1752 and is still open today.",
 "src": "https://en.wikipedia.org/wiki/Tiergarten_Sch%C3%B6nbrunn"}
```
