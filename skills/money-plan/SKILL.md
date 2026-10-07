---
name: money-plan
description: Turns someone's debts and savings goals into one clear page they can keep - when they will be debt-free, how much interest each way of paying off costs (highest rate first or smallest balance first), the month each debt disappears, how much to put aside each month for each goal, and whether it all fits what they can afford. Use whenever someone wants help paying off credit cards or loans, asks which debt to pay first, wants to save for something by a date, or wants to see whether their money plan adds up.
---

# Money plan

You make one thing: a single HTML page that shows a person's own money plan. The
page is already written (`assets/engine.html`) and **every number on it is worked
out by the script** - payoff months, interest, monthly savings, whether it fits.
**Your job is to ask well and write down exactly what they tell you.** Never work
out a payoff date, an interest total or a monthly saving yourself, in the page or
in the chat.

The page has no model inside it and makes no network calls, so it behaves the
same as a shared Claude artifact, a page hosted on Vercel, or a file double-clicked
from Downloads.

**In Microsoft Copilot Cowork**, this skill's other files (`scripts/`, `assets/`, `reference/`, `example/`) are not
next to this file. They are in the user's OneDrive at
`Documents/Cowork/skills/money-plan/`. Open them from there before you build.

## 1. Ask first, in one message, then wait

1. **What they are working on:** paying off debts, saving for something, or both.
2. **For each debt:** a name they will recognise ("Visa card"), what is owed now,
   the yearly interest rate (the APR on the statement), and the minimum monthly payment.
3. **How much extra** they can put toward debts each month, on top of the minimums.
4. **For each goal:** what it is, how much they need, by when (month and year), and
   how much is already saved. Offer a cautious **3% a year** for savings interest and
   say plainly it is an assumption; they can change it.
5. **The total they can put in each month** toward debts and goals together,
   minimums included.
6. **The look**, with a default if they don't mind: letters Rounded · Easy to read ·
   Storybook · Handwriting; colour Auto · Snow · Sky · Pine · Sunset · Berry · Night.

If they don't know a rate or a minimum, tell them where it is printed (the latest
statement or the lender's app) rather than guessing. If the conversation already
answers something, don't ask it again.

## 2. Write plan.json

Read `reference/plan-format.md` and write `plan.json` exactly in that shape, using
**their numbers as they gave them**. `example/rivera-household.json` is a complete one.
Leave out anything they did not mention - never invent a debt, a rate or a goal.

## 3. Build

```bash
python3 scripts/build_plan.py plan.json --out /mnt/user-data/outputs/<name>.html
```

It refuses to build when:
- **a minimum payment does not cover the interest** a debt adds each month - that
  debt would never be paid off. Tell the person exactly that, in plain words, and
  check the figures with them. This is the most important thing the page can catch.
- a balance is zero or negative, a rate is outside 0-100%, or a minimum is zero
- two debts have the same name
- a goal's date is not in the future
- debts and goals together need more each month than they said they can put in -
  ask which to change (a later date, a smaller target, less extra toward debts), or
  mark the goal `"stretch": true` to show the gap on the page instead
- an assumed savings return is outside 0-12% a year

**Fix the input with the person, never the check.** Read every `WARN` line and pass
it on in plain words.

## 4. Deliver

Give the file. Then, briefly:

1. **The short answer** the page leads with: debt-free month, which order saves more
   and by how much, what each goal needs a month, and whether it fits. Copy these
   from the page; do not recompute them.
2. **What the two orders mean:** *highest rate first* (pay extra on the most
   expensive debt first - usually costs least) and *smallest balance first* (clear
   the smallest debt first - an early win that keeps some people going). Both are
   on the page; the tabs switch between them.
3. **One honest line:** the numbers are a plan worked out from what they entered,
   not a guarantee - rates, income and life change, and they can ask for a new page
   any time.
4. **How to share it, and the risk of doing so:**
   - *In Claude:* publish it as an artifact; the viewer must be signed in to Claude.
   - *To anyone, no login:* host it on Vercel - vercel.com, sign up free,
     **Add New → Project**, drag the file onto the page. No renaming is needed;
     **the file name becomes the web address.** **Anyone with that link sees your
     balances and goals**, so think twice before hosting a real plan, and never put
     account numbers in it.

You explain; you do not sell. Never recommend a product, a lender, a balance
transfer or an investment, and never tell someone what to do with their money
beyond what their own numbers show.

## In a tool that cannot run the script

Say so and stop. Money maths done by hand drifts - a payoff month off by one, an
interest total that does not add up - and nothing would catch it.
