---
name: quiz-maker
description: "Makes a fun trivia quiz for a child as a single HTML page of flashcards: tap an answer, the card flips to show the right one with a fun fact and a real photo, and the page keeps every game played and every score. Use whenever someone wants a quiz, trivia, flashcards or a game for a child about a topic, a school subject, or a trip they are about to take (including one built with the trip-planner skill). Also use when a parent brings their own questions and answers to turn into a quiz."
---

# Quiz maker

You make one thing: a single HTML page a child plays on a tablet, phone or laptop.
The engine is already written (`assets/engine.html`). **Your job is the questions.**
Never restyle or rewrite the engine for one quiz. A change to how the page works is
an engine change, affecting every quiz, and you say so.

The page has no model inside it and makes no network calls, so it behaves the same
as a shared Claude artifact, a page hosted on Vercel, or a file double-clicked from
Downloads. (The one exception is `--live-photos`, in section 3.)

**In Microsoft Copilot Cowork**, this skill's other files (`scripts/`, `assets/`,
`reference/`, `example/`) are not next to this file. They are in the user's OneDrive
at `Documents/Cowork/skills/quiz-maker/`. Open them from there before you build.

## 1. Ask first, in one message, then wait

**Before you ask anything: is there already a quiz file?** One HTML page holds
every quiz you have made for this family — it opens on an index and they pick
one. If a page already exists, list what is in it so they can say "add to that"
rather than starting a second file. If they want the new quiz added, you rebuild
the whole file from every `quiz.json`, so keep the old ones.

1. **What it's about.** A topic, a school unit, or a trip. For a trip, ask for the
   itinerary or the trip page. If one is already in this conversation, use it.
2. **Who plays.** First names and ages. Age sets the reading level.
3. **How many questions per game** (default 12) **and how tricky** (easy / medium /
   hard, default medium).
4. **Your questions or mine?** They can paste their own questions and answers, or
   you write them, or both.
5. **The look.** Offer these choices and take a default if they don't mind:
   - letters: Rounded · Easy to read · Storybook · Handwriting
   - colour: Auto (follows the device) · Snow · Sky · Pine · Sunset · Berry · Night
   - background picture: none, one of the quiz's photos, or one they upload
   Everything here can also be changed later from the page's own menu.

If the conversation already answers something, don't ask it again.

## 2. Write the questions

Read `reference/writing-trivia.md` first; it has the quality rules. Then read
`reference/quiz-schema.md` for the exact `quiz.json` format.
`example/salzburg-vienna-quiz.json` is a complete real quiz to copy the shape from.

- **Write about three times as many questions as one game uses.** Games draw from
  the pool, so replays feel new. Spread them across easy, medium and hard.
- **For a trip, tie every question to the itinerary**: a place they'll visit, a day
  they'll have, a thing they'll eat or ride. Put sections in trip order.
- **Every question needs a source URL, or `"check": true` with a short `note`.**
  The build refuses anything else. Anything marked `check` goes on the list the
  parent sees before the child plays.
- **Verify facts before you write them.** Search where you can. When a source says
  "one story" or "about", your question says so too.

### Their own questions

Copy each question and its answer **exactly**, letter for letter. You add the wrong
options, hints and facts around them, never edit them. Put their list in a text
file, one `question | answer` per line, then:

```bash
python3 scripts/from_list.py list.txt source.json
```

and build with `--source source.json`. The build refuses if one letter has drifted.
If something in their list looks wrong, leave it and tell them.

## 3. Photos

Give each place or thing a photo spec: `{"key", "label", "wiki"}` names a Wikipedia
article, and its lead image is used. Use `search` + `must` (+ `ban`) only when no
article fits. **Name the specific article**: a vague one returns a vague picture.
A trip-planner photo folder (`sm-<key>.jpg` + `manifest.json`) can be reused with
`--photos`; anything missing is fetched and saved there.

**Look at every fetched photo before you deliver.** A search once returned a grave
in another country for a hotel's name. A `pic` question whose photo doesn't clearly
show the answer is a broken question.

**If photos can't be downloaded where you are** (Copilot Cowork's builder has no
internet), build with `--no-net --live-photos`. Nothing is stored: the page loads each
photo from its `wiki` article when it is opened online, credits it, and hides it
offline. So every photo needs a `wiki` title, and that title must be right:
- **Confirm each title with a web search** before you use it: the English Wikipedia
  article must exist, have a main photo, and be about **that exact thing** — not a
  general topic it redirects to ("Christkindlmarkt" lands on *Christmas market* and
  shows Nuremberg, not Salzburg). A wrong title shows no photo, or the wrong one.
- The `cover` photo is the first thing they see: give it your most certain title.
- **No `pic` questions with live photos** — offline the photo is hidden and the card
  can't be answered. The build refuses them; put the photo on the answer side instead.
- Tell the parent: photos need the internet; offline the quiz plays without them.

## 4. Build, check, fix

```bash
# one quiz
python3 scripts/build_quiz.py quiz.json --out /mnt/user-data/outputs/<name>.html --photos photos/

# every quiz in ONE file, with an index in front of them
python3 scripts/build_quiz.py romans.json fractions.json spelling.json \
  --out /mnt/user-data/outputs/quizzes.html --photos photos/
```

With one quiz the page opens straight on that quiz, exactly as it always has.
With several it opens on an **index** titled *All quizzes* (`--title` to change it) — one row per quiz with its question count
and best score — and each quiz keeps its own scores, its own difficulty and its
own question count. There is a way back to the index from every quiz.

It refuses to build when:
- two quizzes in one file share an `id`, or share a photo `key`
- a question has no right answer, or two
- an option is duplicated
- a hint gives the answer away
- a fact has no source
- a picture question has no picture
- a difficulty can't fill a game
- a source link is dead

Fix the quiz, never the check. Read every `WARN`. **"The right answer is much the
longest option"** matters most: children learn to pick the longest one, so even out
the lengths. A 403 is a site blocking robots, not a dead link. Open it yourself.

## 5. Deliver

Give the file. Then, in this order:

1. **The check-these list** the build printed: the facts to confirm before a child
   sees them. Keep it to what the build printed. Don't pad it into a disclaimer.
2. **How to share it.**
   - *In Claude:* publish it as an artifact and share the link. The viewer must be
     signed in to Claude.
   - *To anyone, no login:* host it on Vercel. Go to vercel.com, sign up free, then
     **Add New → Project** and drag the file onto the page. No renaming is needed.
     **The file name becomes the web address**, so name the file before you upload it.
     **Anyone with that link can open it**, so leave out surnames, school names and
     home addresses.
3. **If the file holds several quizzes**, say that it opens on the index and
   that each quiz keeps its own scores.
4. **One line on the menu:** colours, letters, background picture (including their
   own photo), sound and read-aloud, every answer, and **Quizzes played**, which has
   every game, best scores per player and the trickiest questions.

Scores are saved in the browser on that device. They don't follow the child to
another device, and a browser that refuses storage keeps them only until the page
closes. The page says which.

## In a tool that can't run the script

Gemini, Copilot or ChatGPT without code running: write `quiz.json` the same way,
then take `assets/engine.html`, replace `/*__QUIZ__*/null` with the JSON and
`__TITLE__` with the quiz title. Add
`"photoKeys": []`, and leave out `pic` questions, because there is no photo
fetching. **The checks above do not run here.** You must hold every rule in
section 4 yourself, and tell the parent the page was not machine-checked.
