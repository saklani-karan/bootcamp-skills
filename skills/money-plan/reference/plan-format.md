# plan.json

```json
{
  "id": "rivera-household",
  "title": "The Rivera money plan",
  "subtitle": "Clearing the cards and the car, and saving for a rainy day",
  "start": "2026-11",
  "monthly_amount": 2400,
  "look": {"font": "rounded", "bg": "auto"},
  "debts": [
    {"name": "Visa card", "balance": 6800, "apr": 24.99, "minimum": 204},
    {"name": "Car loan", "balance": 14200, "apr": 7.4, "minimum": 389}
  ],
  "extra": 450,
  "goals": [
    {"name": "Emergency fund", "target": 10000, "saved": 2500, "by": "2028-10", "return": 3.0}
  ]
}
```

| field | meaning |
|---|---|
| `id` | lowercase-and-dashes; keeps this page's saved choices separate |
| `title`, `subtitle` | shown at the top. No surnames if the page may be shared |
| `start` | the first month of the plan, `YYYY-MM`. Usually next month |
| `monthly_amount` | **everything** they can put toward debts and goals each month, minimums included |
| `currency_symbol` | optional, default `$` |
| `look.font` | `rounded` · `clear` · `story` · `hand` |
| `look.bg` | `auto` · `snow` · `sky` · `pine` · `sunset` · `berry` · `night` |

## A debt

| field | meaning |
|---|---|
| `name` | what they call it. Must be different from every other debt |
| `balance` | owed now, in dollars |
| `apr` | yearly interest rate as a percentage: `24.99`, not `0.2499` |
| `minimum` | the minimum monthly payment, in dollars |

`extra` (top level) is what they add toward debts each month **on top of** all
minimums. When a debt is cleared, its minimum moves to the next one automatically.

## A goal

| field | meaning |
|---|---|
| `name` | what it is for |
| `target` | the amount they need, in dollars |
| `saved` | already put aside for it (default 0) |
| `by` | month and year they need it, `YYYY-MM` |
| `return` | assumed yearly interest on the savings, as a percentage (default 3). Say it is an assumption |
| `stretch` | `true` only when the person knowingly wants a goal that does not fit their budget shown, with the gap |

Leave `debts` or `goals` out (or empty) if they have none. At least one is needed.
