# Documents

**Split documents by who reads them and when.** Keeping them separate is what
makes them usable — a guest scrolling past shopping costs to find dinner time
will stop reading, and a shopper filtering through recipes in a warehouse aisle
will give up on the list.

Three documents cover most events: a guest one-pager, a planning document and a
shopping list. **Treat that as the floor, not the whole set.** Once more than one
person has a job, the right number is larger — see "Sizing the set" below.

**Contents:** Guest one-pager · Planning document · Shopping list ·
Sizing the set · Formats · Keeping them in sync

---

## 1. Guest one-pager

**For:** everyone attending. **Length:** one printed page.

Contains only what a guest can act on:

- Each day, each meal, with a time or an explicit "whenever"
- What's being served, in one or two lines
- Dietary options marked **inline on every meal**, not in a footnote
- Drinks available, listed once
- At most two closing instructions — the things guests can actually do

Leave out entirely: prices, quantities, shopping, cook times, who's cooking,
logistics, equipment.

Two things worth including that people forget:

- **What happens on arrival**, if the first meal is late. Guests who know food is
  out immediately don't raid the kitchen.
- **Which meals are self-serve and open-ended** versus fixed-time. "Breakfast:
  whenever" prevents a stream of questions.

Mark dietary options per meal rather than in one block. Seven vegan guests
reading that every single meal has something for them show up relaxed; the same
information in a footnote reads as an afterthought.

## 2. Planning document

**For:** the organiser and whoever is cooking. **Length:** as long as it needs.

Structure:

```
Header — budget at a glance, all budgets in one table, by stop
Prep schedule — what happens on each day before and during
Recipes — by day, scaled, with the vegan/dietary version alongside
Breakfast — as a spread with totals for the stay
Drinks — quantities, what it pours, the recipes
Consolidated shopping list — itemised, by store, with costs
Equipment — what to bring
Venue logistics — ovens, fridges, circuits, who does what
Top up on site — safe to run short on vs. no substitute nearby
What changed — a running log if you've revised someone's original plan
```

The header table should show **every budget line together**, split by stop. When
food and drinks are tracked separately, one table showing both is what reveals
that a single store carries half the weekend's spend.

Keep a **"what changed"** section when revising an inherited plan. It lets other
organisers see what moved and why without re-litigating it.

## 3. Shopping list

**For:** whoever is in the store. **Format:** interactive if possible.

This is the document that gets used under the worst conditions — one hand, bad
signal, a trolley, background noise. Design for that:

- **Filter by store.** In a warehouse aisle nothing else should be on screen.
- **Tick-off with a running total** that follows the filter, showing progress and
  spend for the current store.
- **Phone-ahead stops first**, with tappable numbers, addresses and closing times.
- **Warnings on the item they concern** — "ask for skin-on" beside the chicken,
  "ginger or citrus" beside the mixer, "restock mid-event" beside the ice.
- **Every line individually costed.** Not category estimates.

State whether tick state survives a page refresh. If it doesn't, say so.

## Sizing the set

The three above are split by audience. The split that actually matters is **when
a document is read, and by whom** — and those come apart as soon as more than one
person has a job.

The source event ran to seven live documents. Three of them were the set above;
the three below were not, and all three earned their place:

| Document | For | Read |
|---|---|---|
| **Cook's menu** | whoever is cooking | in a kitchen, mid-cook, days later |
| **Operational schedule** | organiser and cooks | clock times, first phone call through to strike |
| **Prep assignments** | one card per dish, one name on each | by one person doing one thing |

Why these can't just live inside the planning document: the planning document is
the organiser's **reasoning**, read once, before anything happens. A cook reading
it scrolls past budget reconciliation to find out how much salt goes in the
marinade. Same information, wrong moment, wrong lifespan.

Two rules follow:

- **A person with a job gets the one job they have**, not the document that
  contains it. A card with one dish and one name is read. A schedule containing
  everyone's tasks is skimmed.
- **The set grows during planning, not at the start.** In the source event the
  prep cards appeared only once "who is cooking Sunday" turned out to have no
  home. Adding a document mid-plan should be routine — derive it from what
  already exists rather than restating it by hand.

For a small event several of these collapse into one sheet, and that's fine.
**Make the collapse a decision, not a default.**

## Formats

- **HTML** for anything that gets read on a phone or printed. Use system fonts
  only — venues have bad signal and web fonts won't load. Include print styles
  that drop navigation and avoid breaking sections across pages.
- **Markdown** for the planning document if it's being edited collaboratively.
- **PDF** for the guest page if it's going out over a file-sharing service —
  cloud storage often downloads HTML rather than previewing it, especially on
  phones. That's real friction when it's going to 30 people.

Shared cloud folders are the right home for these. The organiser edits one copy
and everyone sees the current version. Claude cannot write to a local drive —
the person downloads and files them.

## Keeping them in sync

A single quantity change usually touches at least three documents: the recipe or
menu section, the shopping list, and the guest schedule — more once the set has
grown. Update all of them in the same pass. **Every document added is another
copy of every shared figure**, which is the real cost of splitting the set and
the reason the check below has to be programmatic.

**After any edit to a costed list, re-verify that line items sum to the stated
totals.** Section headers, store subtotals and the header table all drift as
changes accumulate. Sum them programmatically and state the reconciled figure.
Silent drift is worse than a visible overspend, because nobody catches it.

**Dates and times drift exactly like figures, and are easier to miss.** In the
source event the shopping list said to phone a supplier on Thursday while the
operational schedule put that call on Wednesday — on an order the documents
themselves described as needing notice. Both were internally consistent and every
dollar reconciled. Check days, dates and clock times across documents with the
same rigour as money; a supplier phoned a day late is as broken as a total that
doesn't add up.
