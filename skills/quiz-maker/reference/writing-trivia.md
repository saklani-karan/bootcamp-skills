# Writing trivia a child wants to play

## The question
- **One idea, one right answer.** If an expert could argue for a second option, rewrite it.
- **Short.** Ages 7–10: under about 110 characters, everyday words. Ages 11–14 can take more.
- **Talk to them.** "On Monday you go up this mountain..." beats "The Kitzsteinhorn is...".
- **Their units.** A US child thinks in °F, miles and dollars. Give the local unit too if it helps.
- **Gentle with hard history.** A war, a death or a disaster can be asked about. Say what
  happened plainly, without graphic detail.

## The options
- **Four for `mc` and `pic`, all plausible**, from the same family: four years, four animals,
  four buildings. A silly option is fine once in a while. It's a game. But never three.
- **Similar length.** The build warns when the right one is much the longest. Fix every warning.
- **No "all of the above"**, no trick negatives ("Which is NOT..."), no options that overlap.
- Write the right answer first (`"a": 0`). The page shuffles the order every time.

## Mix the types
- `mc`, four options: most of the quiz.
- `tf`, true or false: quick wins. Make about a third of them false, or children learn "always true".
- `pic`, a real photo on the front: "What is this?" These are the most fun. Only use one when the
  photo plainly shows the answer.

## Hint (`h`)
Nudges without naming. "It's black and white and loves bamboo", not "It's a panda".
The build refuses a hint that contains the answer's words. A hint can also connect to
something the child knows: "the same people who built the Colosseum".

## Fun fact (`f`)
One or two sentences, shown on the back after every answer, right or wrong. **This is where
the learning happens.** Give a new detail, not the answer said again. Numbers kids can picture:
"stack nine Eiffel Towers". Tie it back to the trip: "you'll see it on Tuesday".

## Difficulty (`lvl`)
- **1 easy:** guessable from everyday knowledge or the picture.
- **2 medium:** needs the trip, the topic or a good hint.
- **3 hard:** a number, a date, a name to recall.

A game at Easy draws on levels 1–2, Medium on 1–3, Hard on 2–3. The build checks every
level can fill a game.

## Being wrong is safe
The page never says "Wrong!". It says "Good guess!" or "Now you know!" and shows the fact.
Write facts that make a miss feel like getting something.

## Sources
Every question carries `src` (a URL, link-checked at build time) or `"check": true` plus a
`note` saying where the fact came from. Use `check` for anything that changes: opening hours,
prices, which animals a zoo has this year, flight times. Use it too for anything a source only
calls a story. The parent sees every `check` item before the child plays.
