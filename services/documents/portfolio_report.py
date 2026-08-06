"""
Portfolio report — assembling what a client's whole book looks like.

Pure. Unit-tested in ``tests/test_portfolio_report.py``. Takes already-fetched
rows (the same shapes ``services/portfolio/aggregate.py`` produces) and returns
a view model.

This document has two readers and they want opposite things. The client's
operations lead wants the worst fields first so they know where to drive
tomorrow. A lender wants the shape of the whole book and an honest account of
what is not known. The report serves the second and lets the first read the
attention list — it is a report, not a task queue.

Same posture as the evidence pack: **hectares observed are not hectares under
management**, and the difference is stated rather than smoothed.

.. warning::

   ``ATTENTION_URGENCIES`` decides which fields a client is told to look at, and
   ``STALE_AFTER_DAYS`` decides when an observation stops counting as current.
   Both are judgement calls carried over from the portfolio screen's thresholds,
   not agronomist-reviewed. A lender acting on this is making a credit decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Sequence

#: Urgencies that put a field on the attention list. ``awaiting_data`` is
#: excluded on purpose — it is not a field in trouble, it is a field we cannot
#: see, and it is reported separately so the two are never confused.
ATTENTION_URGENCIES: frozenset[str] = frozenset({"critical", "high"})

#: Beyond this, an observation is reported as stale rather than current. Matches
#: the portfolio screen so a document and a screen never disagree about which
#: fields are fresh.
STALE_AFTER_DAYS = 7

#: Band order, worst first, so a distribution table reads the way the attention
#: list does.
BAND_ORDER: tuple[str, ...] = ("critical", "poor", "fair", "good", "excellent")


@dataclass(frozen=True)
class FieldRow:
    """One field in the portfolio, as already assembled elsewhere."""

    field_id: str
    field_name: str
    grower_id: str | None
    grower_name: str | None
    district: str | None
    crop_type: str | None
    hectares: float | None
    kurima_score: int | None
    band: str | None
    urgency: str
    primary_concern: str | None
    days_since_observation: int | None

    @property
    def is_observed(self) -> bool:
        """Whether anything has been seen on this field at all.

        A score is the evidence of observation: the aggregator returns ``None``
        until there is something to score.
        """
        return self.kurima_score is not None

    @property
    def is_stale(self) -> bool:
        """Observed once, but not recently enough to speak for today."""
        if not self.is_observed or self.days_since_observation is None:
            return False
        return self.days_since_observation > STALE_AFTER_DAYS

    @property
    def needs_attention(self) -> bool:
        return self.urgency in ATTENTION_URGENCIES


@dataclass(frozen=True)
class BandCount:
    band: str
    fields: int
    hectares: float


@dataclass(frozen=True)
class DistrictRow:
    district: str
    fields: int
    hectares: float
    observed_fields: int


@dataclass(frozen=True)
class PortfolioReport:
    """The view model a template renders. Every claim comes from here."""

    client_name: str
    coverage_start: date
    coverage_end: date
    fields: tuple[FieldRow, ...]
    anonymised: bool = False

    # ── Scale ─────────────────────────────────────────────────────────────────

    @property
    def field_count(self) -> int:
        return len(self.fields)

    @property
    def grower_count(self) -> int:
        return len({f.grower_id for f in self.fields if f.grower_id})

    @property
    def hectares_under_management(self) -> float:
        return sum(f.hectares or 0.0 for f in self.fields)

    @property
    def hectares_observed(self) -> float:
        """What the system has actually seen. The verification line states this,
        never the figure above it."""
        return sum(f.hectares or 0.0 for f in self.fields if f.is_observed)

    @property
    def observed_fields(self) -> tuple[FieldRow, ...]:
        return tuple(f for f in self.fields if f.is_observed)

    @property
    def unobserved_fields(self) -> tuple[FieldRow, ...]:
        return tuple(f for f in self.fields if not f.is_observed)

    @property
    def stale_fields(self) -> tuple[FieldRow, ...]:
        return tuple(f for f in self.fields if f.is_stale)

    @property
    def average_score(self) -> float | None:
        """Mean across scored fields, or ``None``.

        Unweighted by area, and that is a real limitation rather than an
        oversight: weighting would let one large good field mask a dozen small
        failing ones, which is the opposite of what an attention list is for.
        Stated in the document so nobody reads it as a hectare-weighted figure.
        """
        scores = [f.kurima_score for f in self.observed_fields if f.kurima_score is not None]
        if not scores:
            return None
        return sum(scores) / len(scores)

    # ── Shape ─────────────────────────────────────────────────────────────────

    @property
    def bands(self) -> tuple[BandCount, ...]:
        """Distribution across score bands, worst first. Only scored fields —
        an unscored field has no band, and inventing one would put a field
        nobody has looked at into a credit assessment."""
        counts: dict[str, list[FieldRow]] = {b: [] for b in BAND_ORDER}
        for f in self.observed_fields:
            if f.band in counts:
                counts[f.band].append(f)
        return tuple(
            BandCount(
                band=band,
                fields=len(rows),
                hectares=sum(r.hectares or 0.0 for r in rows),
            )
            for band, rows in counts.items()
            if rows
        )

    @property
    def districts(self) -> tuple[DistrictRow, ...]:
        """Concentration by district — the first thing a lender looks for, since
        a portfolio in one district is one weather event."""
        grouped: dict[str, list[FieldRow]] = {}
        for f in self.fields:
            grouped.setdefault(f.district or "Not recorded", []).append(f)
        rows = [
            DistrictRow(
                district=name,
                fields=len(items),
                hectares=sum(i.hectares or 0.0 for i in items),
                observed_fields=sum(1 for i in items if i.is_observed),
            )
            for name, items in grouped.items()
        ]
        return tuple(sorted(rows, key=lambda r: (-r.hectares, r.district)))

    @property
    def attention(self) -> tuple[FieldRow, ...]:
        """Fields needing action, worst first then largest first.

        Area breaks the tie because two equally urgent fields are not equally
        expensive, and someone reading this is deciding where to send a vehicle.
        """
        return tuple(
            sorted(
                (f for f in self.fields if f.needs_attention),
                key=lambda f: (
                    0 if f.urgency == "critical" else 1,
                    -(f.hectares or 0.0),
                    f.field_name.lower(),
                ),
            )
        )

    # ── Honesty about the above ───────────────────────────────────────────────

    @property
    def qualifications(self) -> tuple[str, ...]:
        """What a reader must know before reading the figures."""
        notes: list[str] = []

        unobserved = len(self.unobserved_fields)
        if unobserved:
            gap = self.hectares_under_management - self.hectares_observed
            notes.append(
                f"{_plural(unobserved, 'field')} ({gap:.0f} ha) "
                f"{'has' if unobserved == 1 else 'have'} no observation yet and "
                f"{'is' if unobserved == 1 else 'are'} excluded from every score "
                f"and band below."
            )

        stale = len(self.stale_fields)
        if stale:
            notes.append(
                f"{_plural(stale, 'field')} "
                f"{'was' if stale == 1 else 'were'} last observed more than "
                f"{STALE_AFTER_DAYS} days ago; those scores describe the last "
                f"clear view, not today."
            )

        if self.average_score is not None:
            notes.append(
                "The average score is unweighted by area — a large healthy field "
                "does not offset several small failing ones."
            )

        if self.anonymised:
            notes.append(
                "Grower and field names have been replaced with labels in this "
                "copy. Figures are unchanged."
            )

        return tuple(notes)


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def anonymise_rows(rows: Iterable[FieldRow]) -> tuple[FieldRow, ...]:
    """
    Replace grower and field names with stable labels, leaving figures alone.

    This exists because of one line in the playbook:

        Never publish grower-level or portfolio data, in any form, without
        written client consent.

    The portfolio report is also the demo shown in a prospect meeting, and the
    predictable accident is someone opening a real client's report in front of a
    different contractor. Anonymising has to be a switch on the generator rather
    than a discipline exercised at the moment of sharing — by then the file
    already exists with the names in it.

    Labels are assigned by first appearance and are stable within one report, so
    "Grower C" is the same grower on page 1 and page 4. They are **not** stable
    across reports, which is deliberate: a label that persisted would become a
    pseudonymous identifier, and correlating two anonymised reports would undo
    the point.

    .. warning::

       **Anonymising is not consent.** The playbook says "in any form", and
       these are still a real client's hectares, districts and scores — a
       contractor shown "Sample portfolio" in a prospect meeting can often work
       out whose book it is from the district mix alone. This function removes
       the *names*; it does not create permission to show the figures. Use it
       for a client's own copy that they intend to circulate internally, and for
       demos built on data you have written consent to use. It is a guard
       against the accident, not a licence.
    """
    grower_labels: dict[str, str] = {}
    out: list[FieldRow] = []

    for index, row in enumerate(rows, start=1):
        if row.grower_id is not None and row.grower_id not in grower_labels:
            grower_labels[row.grower_id] = f"Grower {_letters(len(grower_labels))}"
        out.append(
            FieldRow(
                field_id=row.field_id,
                field_name=f"Field {index}",
                grower_id=row.grower_id,
                grower_name=(
                    grower_labels.get(row.grower_id) if row.grower_id else None
                ),
                district=row.district,
                crop_type=row.crop_type,
                hectares=row.hectares,
                kurima_score=row.kurima_score,
                band=row.band,
                urgency=row.urgency,
                primary_concern=row.primary_concern,
                days_since_observation=row.days_since_observation,
            )
        )
    return tuple(out)


def _letters(index: int) -> str:
    """``A``…``Z``, then ``AA``, ``AB``… — a portfolio can exceed 26 growers."""
    label = ""
    index += 1
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        label = chr(ord("A") + remainder) + label
    return label


def build_portfolio_report(
    *,
    client_name: str,
    coverage_start: date,
    coverage_end: date,
    fields: Sequence[FieldRow],
    anonymise: bool = False,
) -> PortfolioReport:
    """Assemble the report, optionally with names replaced."""
    rows = anonymise_rows(fields) if anonymise else tuple(fields)
    return PortfolioReport(
        client_name="Sample portfolio" if anonymise else client_name,
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        fields=rows,
        anonymised=anonymise,
    )
