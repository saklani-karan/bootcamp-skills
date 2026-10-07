# Bootcamp Skills

Agent skills from the [AI Learning Hub skills library](https://ai-learning-hub-741.emergent.host/library/skills). Each skill turns an everyday task into a single HTML page you can use on a phone, tablet or laptop, or print.

| Skill | What it does |
| --- | --- |
| [Quiz Maker](skills/quiz-maker) | Generate itinerary-based trivia and turn it into a scored quiz page. |
| [Itinerary Planner](skills/trip-planner) | Turn a destination and dates into a day-by-day itinerary page. |
| [Crossword](skills/crossword) | Make a crossword on any topic you can play on a device or print as a puzzle sheet and answer sheet. |
| [Event Prep](skills/event-prep) | Plan a gathering, from a birthday or BBQ to a camping weekend: shopping list by store, task assignments, a budget and who owes whom. |
| [Money Plan](skills/money-plan) | Turn debts and savings goals into a one-page plan: when you could be debt-free, which repayment order costs less interest, and how much to save each month. |
| [Recipe Card](skills/recipe-card) | Turn a recipe screenshot, photo, cookbook page or pasted text into a clean, printable card, scaled to half, double or triple. |
| [Chore Chart](skills/chore-chart) | Create a printable weekly chore chart that rotates jobs fairly by age. |
| [Home Upkeep](skills/home-upkeep) | Create a 12-month home maintenance plan with a printable checklist and a calendar file. |

## Layout

```
skills/<name>/        Skill folder (SKILL.md, scripts/, assets/, reference/, tests/, example/)
gemini-gems/<name>/   Gemini Gem versions where they differ (instructions .md + engine.html)
dist/claude/          <name>.skill  — upload to Claude (also works for ChatGPT)
dist/copilot/         <name>.zip    — upload to Copilot
dist/gemini/          <name>.skill or <name>-gem.zip — upload to Gemini
package.sh            Rebuilds dist/ from skills/ and gemini-gems/
```

The Claude, ChatGPT and Copilot packages contain the same files. Gemini uses the same files too, except for Quiz Maker and Itinerary Planner, which ship as Gems.

## Using a skill

- **Claude:** Settings → Capabilities → Skills → upload the `.skill` file from `dist/claude/`. In Claude Code, copy the folder into `~/.claude/skills/` instead.
- **ChatGPT:** upload the same `.skill` file from `dist/claude/`.
- **Copilot:** upload the `.zip` from `dist/copilot/`.
- **Gemini:** upload the file from `dist/gemini/`, or for a Gem, paste the `.md` instructions into a new Gem and attach `engine.html`.

## Tests

Each skill has `tests/run_guards.sh`, which runs the skill's build script against good and bad fixtures:

```
bash skills/crossword/tests/run_guards.sh
```

## Credits

Some skills include MIT-licensed code from other projects. See the `NOTICE.md` file in `crossword`, `event-prep` and `money-plan`.
