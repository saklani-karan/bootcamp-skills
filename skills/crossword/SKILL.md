---
name: crossword
description: Makes a crossword on any topic as a single HTML page you can play on a tablet, phone or laptop, or print as a puzzle sheet and an answer sheet. Tap a square and type; it checks letters gently, gives a letter or a word when someone is stuck, and keeps progress. Use whenever someone wants a crossword, a word puzzle or a printable activity for a child, a family, a classroom, a party, a trip they are about to take (including one built with the trip-planner skill), or their own list of words and clues.
---

# Crossword

You make one thing: a single HTML page holding one crossword. The page is already
written (`assets/engine.html`) and the grid is laid out by a script. **Your job is
the words and the clues.** Never draw a grid yourself and never restyle the page
for one puzzle.

The page has no model inside it and makes no network calls, so it behaves the same
as a shared Claude artifact, a page hosted on Vercel, or a file double-clicked from
Downloads.

**In Microsoft Copilot Cowork**, this skill's other files (`scripts/`, `assets/`, `reference/`, `example/`) are not
next to this file. They are in the user's OneDrive at
`Documents/Cowork/skills/crossword/`. Open them from there before you build.

## 1. Ask first, in one message, then wait

1. **What it's about.** A topic, a school subject, a hobby, a trip. For a trip, ask
   for the itinerary or the trip page. If one is already in this conversation, use it.
2. **Who it's for.** First name and age, or "grown-ups". Age sets the words and the clues.
3. **How many words** (default 12; 8–15 fits a phone screen best).
4. **Your words or mine?** They can give their own words and clues, or you write
   them, or both.
5. **The look**, with a default if they don't mind:
   letters Rounded · Easy to read · Storybook · Handwriting;
   colour Auto (follows the device) · Snow · Sky · Pine · Sunset · Berry · Night.
   Both can be changed later from the page's own Look menu.

If the conversation already answers something, don't ask it again. Do not start
until you have the answers.

## 2. Write the words and clues

Read `reference/writing-clues.md` first, then write `words.json` in exactly the
format given there. `example/under-the-sea.json` is a complete real one.

- **Pick words that share common letters** (E, A, R, S, T, O). A word with rare
  letters and nothing to cross will not fit, and the build will tell you so.
- **Every clue is a fact or a fair description, never the answer in disguise.**
  The build refuses a clue that contains its own answer.
- **Check any fact you are not sure of.** Search where you can. If a clue states
  something that can change or that you could not confirm, add `"check": true` and a
  short `"note"`. The build prints those for the person to confirm.
- **Their own words:** copy each word and clue exactly as they gave it. If a clue
  gives its answer away, tell them and suggest a fix rather than changing it silently.

## 3. Build

```bash
python3 scripts/build_crossword.py words.json --out /mnt/user-data/outputs/<name>.html
```

The script tries hundreds of arrangements and keeps the most compact grid that fits
every word. It refuses to build when:
- an answer has anything but letters (spaces, hyphens and apostrophes are fine; the
  page shows them as a hint like "(3,5)")
- two answers are the same, or a clue is empty or gives its answer away
- there are fewer than 4 or more than 30 words
- a word cannot be fitted into the grid
- the finished grid fails its check (letters that clash, words touching to make a
  word nobody wrote, a word that crosses nothing)

**Fix the words, never the check.** If a word will not fit, swap it for one that
shares more letters with the others, or drop it, and **tell the person which word
and why**. Never drop a word silently. Read every `WARN` line: a grid bigger than
15 squares across is hard to play on a phone, so use fewer or shorter words.

## 4. Deliver

Give the file. Then, in this order:

1. **The check-these list** the build printed, if there is one. Nothing else, no disclaimer.
2. **How to use it:** tap a square and type; tap it again to switch between across
   and down. *Check my letters* colours any wrong letter; *Help me* shows a letter, a
   word or the whole puzzle. Progress is kept in the browser on that device.
3. **How to print it:** *Print* → *Print the puzzle* for a blank sheet, *Print the
   answers* for the answer sheet. Each fits on one page.
4. **How to share it:**
   - *In Claude:* publish it as an artifact and share the link. The viewer must be
     signed in to Claude.
   - *To anyone, no login:* host it on Vercel. Go to vercel.com, sign up free, then
     **Add New → Project** and drag the file onto the page. No renaming is needed.
     **The file name becomes the web address**, so name the file before you upload it.
     Anyone with the link can open it, so leave out surnames and school names.

## In a tool that cannot run the script

Say so and stop. Do not draw a grid by hand: placing crossing words without the
script is exactly where crosswords break, with clashing letters and words that run
into each other, and nothing would catch it.
