"""Apportion shared event costs across attendees.

Not a payments tool — it does not move money. It answers "what does each person
owe", which is `docs/PRODUCT.md`'s F4 (budget reconciliation) at per-person
resolution. Settling up stays somebody else's job.

Two ideas carry the whole module.

**Attendance-weighted, per night.** A weekend is not one bill divided by the
headcount. Each night is its own bucket with its own denominator, so somebody
present for two nights of three pays two nights at the rates those nights
actually cost — and a night with five people left standing costs those five far
more per head than the night with fifteen. Dividing a whole trip flatly is the
commonest way a split ends up feeling unfair to whoever stayed longest.

**Eligibility decides the denominator.** This is the correctness core, and it is
exactly where hand-built spreadsheets fail. If three vegans come off the
butcher's bill, that bill must then divide by the *meat eaters*, not by
everyone. A real spreadsheet audited for this project took three people off a
$453.75 meat bill by deleting their cells and left the divisor at 13 — so ten
shares were issued against a thirteen-way split and **$104.71 was never charged
to anyone.** The organiser absorbed it, silently, and the sheet looked correct.

So `apportion` derives every denominator from the eligibility rule itself, then
asserts conservation: what is charged must equal what was billed, to the cent.
A splitter that does not conserve money is not a splitter.

Python 3, standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

__all__ = [
    "Person", "Bucket", "Split",
    "ConservationError", "NoEligiblePayers",
    "apportion",
]


class ConservationError(AssertionError):
    """Charges did not sum to the bills. The split is wrong; do not use it."""


class NoEligiblePayers(ValueError):
    """A bucket has nobody who can pay it — usually an exclusion gone too far."""


def _money(x) -> Decimal:
    """Money is decimal. Floats lose cents, and cents are what people argue about."""
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Person:
    """One attendee.

    ``nights`` holds the night labels they actually slept, so partial attendance
    is the normal case rather than an exception. ``excluded_from`` names buckets
    they do not pay into at all — a vegan and the butcher's bill, a driver and
    the beer. ``paid`` is whatever they already fronted.
    """

    name: str
    nights: frozenset = field(default_factory=frozenset)
    excluded_from: frozenset = field(default_factory=frozenset)
    paid: Decimal = Decimal("0")

    def __post_init__(self):
        object.__setattr__(self, "nights", frozenset(self.nights))
        object.__setattr__(self, "excluded_from", frozenset(self.excluded_from))
        object.__setattr__(self, "paid", _money(self.paid))


@dataclass(frozen=True)
class Bucket:
    """One bill to divide.

    ``night=None`` spreads it across everyone who attended at all — a shop run,
    a rental. ``night="Fri"`` restricts it to the people who slept that night,
    which is how a site fee should behave when people arrive and leave on
    different days.
    """

    name: str
    amount: Decimal
    night: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "amount", _money(self.amount))


@dataclass
class Split:
    per_person: dict        # name -> total owed
    per_bucket: dict        # bucket name -> {person: share}
    balance: dict           # name -> owed minus already paid
    denominators: dict      # bucket name -> how many people carried it
    total_billed: Decimal
    total_charged: Decimal

    def report(self) -> str:
        w = max((len(n) for n in self.per_person), default=8)
        rows = [f"{'name':<{w}}  {'owes':>9}  {'paid':>9}  {'balance':>9}",
                "-" * (w + 35)]
        for n in sorted(self.per_person, key=lambda k: -self.balance[k]):
            paid = self.per_person[n] - self.balance[n]
            rows.append(f"{n:<{w}}  {self.per_person[n]:>9}  "
                        f"{paid:>9}  {self.balance[n]:>9}")
        rows += ["-" * (w + 35),
                 f"{'billed':<{w}}  {self.total_billed:>9}",
                 f"{'charged':<{w}}  {self.total_charged:>9}"]
        return "\n".join(rows)


def _eligible(people, bucket):
    """Who pays into this bucket.

    A per-night bucket reaches only the people who slept that night. A shared
    bucket reaches everyone who attended at all — which deliberately excludes a
    person with no nights recorded, because they were not there.
    """
    out = []
    for p in people:
        if bucket.name in p.excluded_from:
            continue
        if bucket.night is not None:
            if bucket.night in p.nights:
                out.append(p)
        elif p.nights:
            out.append(p)
    return out


def apportion(people, buckets, *, strict=True) -> Split:
    """Divide every bucket among the people eligible for it.

    Raises ``NoEligiblePayers`` if a bucket has no payers, and
    ``ConservationError`` if the arithmetic loses or invents money.

    Rounding remainders are handed out a cent at a time, so each bucket lands
    exactly on its bill rather than a cent either side.
    """
    if not people:
        raise ValueError("no people to split between")
    names = [p.name for p in people]
    if len(set(names)) != len(names):
        dupes = sorted({n for n in names if names.count(n) > 1})
        raise ValueError(
            f"duplicate names: {', '.join(dupes)} — shares would be ambiguous"
        )

    per_person = {p.name: Decimal("0") for p in people}
    per_bucket, denominators = {}, {}

    for b in buckets:
        elig = _eligible(people, b)
        if not elig:
            raise NoEligiblePayers(
                f"bucket {b.name!r} (${b.amount}) has nobody eligible to pay it. "
                f"Either an exclusion went too far or the night label is wrong."
            )
        denominators[b.name] = len(elig)

        base = (b.amount / len(elig)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        shares = {p.name: base for p in elig}

        # Hand out the rounding remainder a cent at a time. Without this, a
        # three-way split of $10 lands a cent off and the conservation check —
        # correctly — refuses the entire result.
        drift = b.amount - base * len(elig)
        cents = int((drift / Decimal("0.01")).to_integral_value())
        order = sorted(shares)
        for i in range(abs(cents)):
            shares[order[i % len(order)]] += (
                Decimal("0.01") if cents > 0 else Decimal("-0.01")
            )

        if sum(shares.values()) != b.amount:
            raise ConservationError(
                f"bucket {b.name!r} failed to balance: shares sum to "
                f"${sum(shares.values())} against ${b.amount}"
            )

        per_bucket[b.name] = shares
        for n, v in shares.items():
            per_person[n] += v

    billed = sum((b.amount for b in buckets), Decimal("0"))
    charged = sum(per_person.values(), Decimal("0"))
    if strict and billed != charged:
        raise ConservationError(
            f"charged ${charged} against ${billed} billed — a gap of "
            f"${billed - charged}. Somebody absorbs that difference, and it is "
            f"almost always whoever fronted the money."
        )

    balance = {p.name: per_person[p.name] - p.paid for p in people}
    return Split(per_person, per_bucket, balance, denominators, billed, charged)
