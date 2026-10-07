# recipe.json

```json
{
  "id": "sunday-dinners",
  "title": "Sunday dinners",
  "look": {"font": "rounded", "bg": "auto"},
  "units": "source",
  "cards": [
    {
      "id": "lemon-chicken",
      "title": "Lemon Chicken Traybake",
      "source": "@somecook on Instagram",
      "serves": 4,
      "serves_text": "Serves 4",
      "scale_to": 6,
      "times": [{"label": "Prep", "text": "15 min"}, {"label": "Cook", "text": "45 min"}],
      "ingredients": [
        {"name": "For the tray", "items": [
          {"text": "8 chicken thighs, skin on", "qty": "8", "unit": "", "item": "chicken thighs, skin on"},
          {"text": "1½ lb baby potatoes, halved", "qty": "1½", "unit": "lb", "item": "baby potatoes, halved"},
          {"text": "Salt to taste", "qty": "", "unit": "", "item": "salt"}
        ]}
      ],
      "method": [
        {"name": "", "steps": ["Heat the oven to 425°F.", "Toss everything on a tray and roast 45 minutes."]}
      ],
      "how_to_use": "",
      "notes": ["The original post suggests serving with rice."]
    }
  ]
}
```

## The file

| field | meaning |
|---|---|
| `id` | lowercase-and-dashes. Keeps this file's ticks separate from other files |
| `title` | the name of the whole set, shown small at the top |
| `look.font` | `rounded` · `clear` · `story` · `hand` |
| `look.bg` | `auto` · `snow` · `sky` · `pine` · `sunset` · `berry` · `night` |
| `units` | `source` (keep exactly, the default) · `us` · `metric` |

## A card

| field | meaning |
|---|---|
| `id` | lowercase-and-dashes, different for every card |
| `title` | the dish name as the recipe gives it. If there is none, a plain name you chose - and say so |
| `source` | who or where it came from, if the image shows it |
| `serves` | the number the recipe states, as a number. Leave out if the recipe states none |
| `serves_text` | how the recipe says it: "Serves 4", "Makes 12 muffins" |
| `base_count` | instead of `serves`, when the recipe is built on a count: `{"n": 4, "what": "chicken breasts"}` |
| `scale_to` | the number they asked for. Only with `serves` or `base_count` |
| `times` | only times the recipe gives, as written |
| `ingredients` | groups, each `{"name": "For the sauce", "items": [...]}`. `name` is `""` when there are no groups |
| `method` | groups, each `{"name": "", "steps": ["...", "..."]}`. Empty `[]` when the recipe has no method |
| `how_to_use` | only when there is no method: short, plainly general |
| `notes` | tips the recipe itself gives |

## An ingredient

| field | meaning |
|---|---|
| `text` | the line, word for word. This is what the card shows at the original size |
| `qty` | the amount, copied from `text`: `"2"`, `"1½"`, `"1 1/2"`, `"0.5"`, `"2–3"`. `""` when there is none ("a pinch", "to taste", "juice of 1 lemon") |
| `unit` | the unit, copied from `text`: `"cups"`, `"tbsp"`, `"g"`. `""` for a count ("3 eggs") |
| `item` | the rest of the line: what it is and how it's prepared |
| `flag` | only for a word that looks wrong: what it probably means |

An ingredient with no `qty` is never scaled; when the size changes the card marks it
*adjust to taste*.

## What converts, and what does not

- **US ↔ metric:** grams and kilos ↔ ounces and pounds; millilitres and litres ↔
  cups (and tablespoons or teaspoons for small amounts); fluid ounces, pints and quarts.
- **Never converted:** teaspoons and tablespoons (the same everywhere), and counts like
  cloves, cans, sticks, pinches, slices, bunches, eggs.
- **Weight never becomes volume or the other way round.** 250 g of flour stays a weight
  (about 8⅞ oz), because a cup of flour weighs different amounts depending on how it's scooped.
- The original line is kept under each converted one, so nothing is lost.
- Oven temperatures and amounts inside the steps are not converted.
