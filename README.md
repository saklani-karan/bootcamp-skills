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

## Download

Grab ready-to-upload files from the [latest release](https://github.com/saklani-karan/bootcamp-skills/releases/latest):

- `<name>.skill`: load into Claude (Settings → Capabilities → Skills → Upload skill). ChatGPT accepts the same file.
- `quiz-maker-gem.skill`, `trip-planner-gem.skill`: the lighter Gemini Gem versions, wrapped as Claude skills. They need no code execution, just the instructions and `engine.html`.
- `<name>-copilot.zip`: Copilot.
- `<name>-gemini.skill`, `<name>-gem.zip`: Gemini. For a Gem, paste the `.md` instructions into a new Gem and attach `engine.html` as a knowledge file.

In Claude Code, copy a folder from `skills/` into `~/.claude/skills/` instead.

## Layout

```
skills/<name>/        Skill folder (SKILL.md, scripts/, assets/, reference/, tests/, example/)
gemini-gems/<name>/   Gem instructions (.md) + engine.html, and claude-frontmatter.md used to wrap it as a Claude skill
dist/                 Built packages (run ./package.sh)
package.sh            Rebuilds dist/ from skills/ and gemini-gems/
```

The Claude, ChatGPT, Copilot and Gemini packages contain the same files, except Quiz Maker and Itinerary Planner, which also ship as Gems.

## Releasing

Push a tag and the Release workflow builds every package and attaches it to a GitHub release:

```
git tag v1.0.0 && git push origin v1.0.0
```

## Tests

Each skill has `tests/run_guards.sh`, which runs the skill's build script against good and bad fixtures:

```
bash skills/crossword/tests/run_guards.sh
```

## Credits

Some skills include MIT-licensed code from other projects. See the `NOTICE.md` file in `crossword`, `event-prep` and `money-plan`.
