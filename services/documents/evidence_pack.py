"""
Season Evidence Pack — assembling what the pack is allowed to claim.

Pure. Unit-tested in ``tests/test_evidence_pack.py``. Takes already-fetched rows
and returns a view model; the SQL lives in a repository and the wiring in a
route, per this repo's split.

The pack is the artefact a contractor forwards to a leaf buyer. Everything in
this module is therefore about **coverage** — not about presenting data well,
which is the template's job, but about establishing what the data actually
covers and refusing to overstate it.

Three rules drive the whole file:

1. **A grower without a TIMB number is reported, but not counted as traceable.**
   The pack's headline claim is grower-level traceability keyed to TIMB numbers.
   A grower with no number appears in the table with the gap visible, and is
   excluded from the traceable count. Quietly counting them would make the
   headline figure a lie that nobody could see.

2. **Coverage hectares are observed hectares, not contracted hectares.** A field
   the satellite never saw is not covered, however many hectares the contract
   says it is. The verification line is generated from this figure, so getting
   it wrong is the failure mode that matters most.

3. **A theme with no evidence says so.** The STP themes each report their own
   completeness rather than being silently omitted — a buyer must be able to
   tell "we checked and it's fine" from "we didn't check".

.. warning::

   The thresholds below decide what the pack presents as adequate coverage.
   They are judgement calls compiled from the Sustainable Tobacco Programme's
   published theme list, not agreed with a leaf buyer. Before a pack goes to a
   real multinational, these need signing off by someone who has seen a real
   STP submission.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import date
from typing import Iterable, Sequence

from .grower_number import comparison_key, normalise_grower_number

#: The four themes the Sustainable Tobacco Programme covers, in the order a pack
#: presents them. Land use leads because it is the one a buyer's compliance team
#: reads first — deforestation is the reputational exposure.
STP_THEMES: tuple[str, ...] = (
    "land_use",
    "soil",
    "crop_protection",
    "good_agricultural_practice",
)

THEME_LABELS: dict[str, str] = {
    "land_use": "Land use and deforestation",
    "soil": "Soil",
    "crop_protection": "Crop protection agent usage",
    "good_agricultural_practice": "Good agricultural practice",
}

#: Below this share of a theme's fields carrying evidence, the pack reports the
#: theme as partial rather than covered. Not a standard — a judgement, pending
#: sign-off (see the module warning).
THEME_ADEQUATE_SHARE = 0.8


@dataclass(frozen=True)
class FieldEvidence:
    """One field's contribution to the pack, already fetched."""

    field_id: str
    field_name: str
    hectares: float | None
    crop: str | None
    #: Whether the field was actually observed in the coverage window. A field
    #: with no observation contributes nothing to covered hectares regardless of
    #: what the contract says.
    observed: bool
    #: Which STP themes this field has evidence for.
    themes: frozenset[str] = dc_field(default_factory=frozenset)


@dataclass(frozen=True)
class GrowerEvidence:
    """One grower and their fields."""

    grower_id: str
    grower_name: str
    timb_grower_number: str | None
    fields: tuple[FieldEvidence, ...] = ()

    @property
    def is_traceable(self) -> bool:
        """Whether this grower can be reconciled against TIMB's register."""
        return normalise_grower_number(self.timb_grower_number) is not None

    @property
    def covered_hectares(self) -> float:
        return sum(f.hectares or 0.0 for f in self.fields if f.observed)

    @property
    def total_hectares(self) -> float:
        return sum(f.hectares or 0.0 for f in self.fields)

    @property
    def unobserved_fields(self) -> tuple[FieldEvidence, ...]:
        return tuple(f for f in self.fields if not f.observed)


@dataclass(frozen=True)
class ThemeCoverage:
    """How completely one STP theme is evidenced across the pack."""

    theme: str
    fields_with_evidence: int
    fields_total: int

    @property
    def label(self) -> str:
        return THEME_LABELS.get(self.theme, self.theme)

    @property
    def share(self) -> float | None:
        """``None`` when there are no fields — not zero. No fields means the
        question was not asked, which is different from asking and finding
        nothing."""
        if self.fields_total == 0:
            return None
        return self.fields_with_evidence / self.fields_total

    @property
    def status(self) -> str:
        """``covered`` | ``partial`` | ``absent`` | ``not_applicable``."""
        share = self.share
        if share is None:
            return "not_applicable"
        if share == 0:
            return "absent"
        if share >= THEME_ADEQUATE_SHARE:
            return "covered"
        return "partial"


@dataclass(frozen=True)
class EvidencePack:
    """The view model a template renders. Every claim on the page comes from
    here, so that what the pack asserts is decided in tested code rather than in
    a template."""

    client_name: str
    coverage_start: date
    coverage_end: date
    growers: tuple[GrowerEvidence, ...]
    themes: tuple[ThemeCoverage, ...]

    # ── The headline claims ───────────────────────────────────────────────────

    @property
    def covered_hectares(self) -> float:
        """Observed hectares. This is the figure the verification line states,
        so it counts only ground the system actually saw."""
        return sum(g.covered_hectares for g in self.growers)

    @property
    def total_hectares(self) -> float:
        return sum(g.total_hectares for g in self.growers)

    @property
    def grower_count(self) -> int:
        return len(self.growers)

    @property
    def traceable_growers(self) -> tuple[GrowerEvidence, ...]:
        return tuple(g for g in self.growers if g.is_traceable)

    @property
    def untraceable_growers(self) -> tuple[GrowerEvidence, ...]:
        """Growers with no TIMB number. Reported in full, never hidden — the gap
        is the actionable finding, and a pack that omits them looks complete
        while being less complete than it appears."""
        return tuple(g for g in self.growers if not g.is_traceable)

    @property
    def field_count(self) -> int:
        return sum(len(g.fields) for g in self.growers)

    @property
    def unobserved_fields(self) -> tuple[FieldEvidence, ...]:
        return tuple(f for g in self.growers for f in g.unobserved_fields)

    @property
    def duplicate_grower_numbers(self) -> tuple[str, ...]:
        """TIMB numbers appearing on more than one grower.

        Not blocked on write — someone registering a hundred growers before a
        deadline should not be stopped by a typo — so it surfaces here, where it
        can be fixed before the pack is sent rather than after a buyer finds it.
        """
        seen: dict[str, list[str]] = {}
        for g in self.growers:
            key = comparison_key(g.timb_grower_number)
            if key is None:
                continue
            seen.setdefault(key, []).append(g.grower_id)
        return tuple(
            sorted(k for k, ids in seen.items() if len(ids) > 1)
        )

    # ── Honesty about the above ───────────────────────────────────────────────

    @property
    def is_complete(self) -> bool:
        """Whether the pack has nothing to qualify.

        Used to decide whether the cover carries a plain claim or a caveat. It
        is deliberately strict: any untraceable grower, any unobserved field, or
        any theme short of covered makes the pack incomplete. A pack that
        rounds itself up to complete is the one a buyer stops trusting.
        """
        return not self.qualifications

    @property
    def qualifications(self) -> tuple[str, ...]:
        """Everything a reader must know to read the rest correctly.

        Stated on the cover, not buried. The playbook's position is that one
        data controversy ends the company; the defence is that the pack said so
        itself, first.
        """
        notes: list[str] = []

        untraceable = len(self.untraceable_growers)
        if untraceable:
            has = "has" if untraceable == 1 else "have"
            notes.append(
                f"{untraceable} of {self.grower_count} growers {has} no TIMB "
                f"number recorded and {'is' if untraceable == 1 else 'are'} not "
                f"included in the traceability count."
            )

        unobserved = len(self.unobserved_fields)
        if unobserved:
            missing_ha = self.total_hectares - self.covered_hectares
            notes.append(
                f"{_plural(unobserved, 'field')} ({missing_ha:.0f} ha) "
                f"{'was' if unobserved == 1 else 'were'} not observed in this "
                f"period and {'is' if unobserved == 1 else 'are'} excluded from "
                f"covered hectares."
            )

        for theme in self.themes:
            if theme.status == "covered":
                continue
            if theme.status == "not_applicable":
                notes.append(f"{theme.label}: no fields in scope.")
            elif theme.status == "absent":
                notes.append(f"{theme.label}: no evidence recorded.")
            else:
                notes.append(
                    f"{theme.label}: evidence for "
                    f"{theme.fields_with_evidence} of {theme.fields_total} fields."
                )

        duplicates = len(self.duplicate_grower_numbers)
        if duplicates:
            notes.append(
                f"{_plural(duplicates, 'TIMB number')} "
                f"{'appears' if duplicates == 1 else 'appear'} on more than one "
                f"grower and {'needs' if duplicates == 1 else 'need'} resolving "
                f"before this pack is sent."
            )

        return tuple(notes)


def _plural(count: int, noun: str) -> str:
    """``1 field`` / ``3 fields``.

    Trivial, and worth having: "1 fields were not observed" on a document going
    to a multinational reads as software nobody proofread, and a reader who
    doubts the care taken over the sentence doubts the care taken over the
    number.
    """
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def build_theme_coverage(
    fields: Iterable[FieldEvidence], themes: Sequence[str] = STP_THEMES
) -> tuple[ThemeCoverage, ...]:
    """Coverage per theme across every field in the pack.

    Counts against *all* fields rather than only observed ones: a field nobody
    looked at is a field with no soil evidence, and counting only what was
    observed would make a pack covering a tenth of the ground report full
    coverage of every theme.
    """
    all_fields = tuple(fields)
    return tuple(
        ThemeCoverage(
            theme=theme,
            fields_with_evidence=sum(1 for f in all_fields if theme in f.themes),
            fields_total=len(all_fields),
        )
        for theme in themes
    )


def build_evidence_pack(
    *,
    client_name: str,
    coverage_start: date,
    coverage_end: date,
    growers: Sequence[GrowerEvidence],
) -> EvidencePack:
    """
    Assemble the pack.

    Growers are sorted with the untraceable ones **first**. That is deliberate
    and the opposite of flattering: the gaps are the part someone can act on
    before sending, and a list sorted alphabetically buries them on page four.
    """
    ordered = tuple(
        sorted(growers, key=lambda g: (g.is_traceable, g.grower_name.lower()))
    )
    all_fields = [f for g in ordered for f in g.fields]
    return EvidencePack(
        client_name=client_name,
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        growers=ordered,
        themes=build_theme_coverage(all_fields),
    )
