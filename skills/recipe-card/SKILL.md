---
name: recipe-card
description: Turns a recipe someone has found - screenshots or photos from Instagram, a blog, a cookbook page or a handwritten card, or pasted text - into a clean recipe card as a single HTML page that works in the kitchen and prints neatly. Ingredients and steps tick off as you go, and the page can make the recipe half, double or triple size with every amount worked out. Use whenever someone shares a recipe image or text and wants it tidied up, made printable, scaled, converted between US and metric, or kept; or has several recipes to turn into a set of cards.
---

# Recipe card

You make one thing: a single HTML page of recipe cards. The page is already written
(`assets/engine.html`) and every amount on it is worked out by a script. **Your job
is to read the recipe exactly.** Never restyle the page for one recipe and never do
the arithmetic yourself.

The page has no model inside it and makes no network calls, so it behaves the same
as a shared Claude artifact, a page hosted on Vercel, or a file double-clicked from
Downloads.

**In Microsoft Copilot Cowork**, this skill's other files (`scripts/`, `assets/`, `reference/`, `example/`) are not
next to this file. They are in the user's OneDrive at
`Documents/Cowork/skills/recipe-card/`. Open them from there before you build.

## 1. Read everything first

- **Read every image.** Several screenshots of one recipe are often out of order and
  overlap at the edges. Put them in order by what they say (step numbers, "Ingredients"
  before "Method", sentences that run on), and keep each overlapping line once.
- **Work out how many recipes there are.** Each recipe with its own name and its own
  ingredient list is its own card. They all go in one file.
- **Leave out everything that is not the recipe**: adverts, "jump to recipe", likes,
  comments, the author's life story, app buttons.

## 2. Then ask, in one short message, only what the recipe cannot tell you

- **Size.** Keep it as written, or make it for a different number? (Only if the
  recipe says how many it serves or makes. If it says nothing, do not offer a number
  of your own: the page simply shows it as written.)
- **Units.** Keep them exactly as the recipe has them (the default), or convert
  everything to US or to metric?
- **The look**, with a default if they don't mind: letters Rounded · Easy to read ·
  Storybook · Handwriting; colour Auto · Snow · Sky · Pine · Sunset · Berry · Night.

If they have already said, don't ask. Wait for the answer before you build.

## 3. Write recipe.json - exactly what the recipe says

Read `reference/recipe-format.md` for the format. `example/family-favourites.json` is a
complete real one: a two-part recipe and an ingredients-only marinade.

**Accuracy beats tidiness. A changed amount ruins a dish.**
- **Copy every ingredient line and every step word for word** into `text` and `steps`.
  Keep the amounts, the units and both units if the recipe gives two ("2 cups / 250 g").
- **Then split each ingredient** into `qty`, `unit` and `item` by copying those parts
  out of the same line. The build checks that they still match the line, so a "3" you
  meant to tidy into a "2" is refused.
- **Never add** an ingredient, an amount, a step, a time, a temperature or a serving
  count that the recipe does not give. Never round, "fix" or improve anything.
- **Keep groups** ("For the sauce", "For the cake") as the recipe has them, for the
  ingredients and the method both. Keep the original order.
- **Amounts written inside the steps** ("add 2 tbsp of the sauce") stay as written.
- **A word that looks wrong stays as written.** Put a short `flag` on that ingredient
  saying what it probably means; the card shows it with an asterisk and a footnote. Only
  correct a word when the recipe itself spells it correctly somewhere else.
- **Anything you cannot read** is written as `[unreadable]` where it falls. Tell the
  person what was missing so they can send a clearer picture.
- **No method at all** (a marinade, a spice mix): leave `method` empty and put a short,
  plainly general `how_to_use`. The card labels it as general guidance. The only number
  you may add there is a safe cooking temperature.
- **No recipe in the image at all:** say what you can see and ask for the recipe. Do
  not make one up.

## 4. Build

```bash
python3 scripts/build_card.py recipe.json --out /mnt/user-data/outputs/<name>.html
```

The script does all scaling and conversion. The page offers ×½, ×1, ×1½, ×2 and ×3
(and the size they asked for), each already worked out, and opens at the size they
asked for. It refuses to build when:
- a card has no title or no ingredients, or a line or a step is empty
- an ingredient's `qty` or `unit` does not match its own line
- scaling is asked for and the recipe states no servings
- conversion is asked for and a unit is one it does not know
- two cards share an id

**Fix the recipe.json, never the check.** Read every `WARN` line: each one is
something to tell the person.

## 5. Deliver

Give the file. Then, briefly:

1. **What you decided**: an order you chose for the screenshots, a title you had to
   give a recipe that had none, anything flagged, anything unreadable. Only what is
   true for this recipe.
2. **How to use it:** tap an ingredient or a step to tick it off; *Make* changes the
   size; *Print* gives one card per page, at the size on screen.
3. **How to share it:**
   - *In Claude:* publish it as an artifact and share the link. The viewer must be
     signed in to Claude.
   - *To anyone, no login:* host it on Vercel. Go to vercel.com, sign up free, then
     **Add New → Project** and drag the file onto the page. No renaming is needed.
     **The file name becomes the web address**, so name the file before you upload it.

## In a tool that cannot run the script

Say so and stop. The amounts on the page come from the script; hand-scaling a recipe
is exactly where a ½ becomes a 2 and nothing would catch it.
