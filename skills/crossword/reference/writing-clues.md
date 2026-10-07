# Writing words and clues

## words.json

```json
{
  "id": "under-the-sea",
  "title": "Under the Sea",
  "subtitle": "A crossword for Maya, age 9",
  "age": 9,
  "look": {"font": "rounded", "bg": "sky"},
  "words": [
    {"answer": "Octopus", "clue": "Eight arms, three hearts and blue blood"},
    {"answer": "Coral reef", "clue": "Busy underwater home built by tiny animals"},
    {"answer": "Seahorse", "clue": "In this fish, the dad carries the babies",
     "check": true, "note": "confirm: male seahorses carry the eggs"}
  ]
}
```

| field | meaning |
|---|---|
| `id` | lowercase-and-dashes. Keeps this puzzle's saved progress separate from others |
| `title`, `subtitle` | shown at the top and on the printed sheets |
| `age` | the youngest player. Long clues for age 10 and under get a warning |
| `look.font` | `rounded` · `clear` · `story` · `hand` |
| `look.bg` | `auto` · `snow` · `sky` · `pine` · `sunset` · `berry` · `night` |
| `answer` | letters only. Spaces, hyphens and apostrophes are allowed and shown as "(3,5)" |
| `clue` | the clue, as it will be read |
| `check`, `note` | `true` + what to confirm, for a fact that can change or that you could not verify |

## Good words

- **Mix lengths**: a few long words (7–10 letters) to build the frame, then shorter
  ones to fill across them.
- **Common letters cross best**: E, A, R, S, T, O, I, N, L. A word full of Q, X, Z, J
  may not fit; the build names it if so.
- **For a child, use words they can spell**, or will be proud to learn. Ages 6–8:
  mostly 3–6 letters. Ages 9–12: up to about 10.
- **For a trip, tie words to the itinerary**: places they'll visit, food they'll try,
  things they'll ride.

## Good clues

- **One clear answer.** If two words could both fit, add a detail that rules one out.
- **Never the answer, or part of it.** "Sharks have rows of teeth" for SHARK is
  refused, and so is "Whipped cream on a cone" for ICE CREAM.
- **Short.** Ages 6–10: under about 80 characters, everyday words.
- **Make it a small fact**, not just a definition: "Eight arms, three hearts and blue
  blood" teaches something; "A sea animal" does not.
- **Talk to them for a trip**: "On Tuesday you ride this up the mountain".
- **For grown-ups** a little wordplay is fine, but keep one fair reading.
