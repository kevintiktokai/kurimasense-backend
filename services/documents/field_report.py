"""
Field report — one field, one season, everything known about it.

Pure. Unit-tested in ``tests/test_field_report.py``. Takes already-assembled
pieces (zone diagnosis, retrospective, stand check, input execution) and decides
what the document says.

Unlike the evidence pack and the portfolio report, this one is read by someone
who was *there*. An agronomist or a commercial farmer already knows the field
looked patchy on the west edge; what they want is which of the things they did
explains it. So the report is ordered by **what can still be acted on**, and it
says plainly when it cannot explain something.

Sections render only when they have content — the same rule the app's cards
follow. There is one deliberate exception, and it is the finding this whole body
of work started from.

.. warning::

   Nothing here computes agronomy. Every number arrives already derived by
   ``services/planning/``, ``services/zones/`` or ``services/seasons/``, each of
   which carries its own pending-review warning. This module decides what is
   *said*, and it must not turn any of those engines' ``None`` into a figure.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import date
from typing import Any, Sequence

#: A zone this far below the field mean is worth naming in a document. Matches
#: the threshold ``services/zones/diagnosis.py`` uses for 'problem', so a report
#: and the app never disagree about which zones are a problem.
ZONE_REPORT_SEVERITIES: frozenset[str] = frozenset({"problem", "watch"})


@dataclass(frozen=True)
class StandCheck:
    """What the farmer counted, against what was planned."""

    checked_on: date
    target_population_per_ha: float | None
    established_population_per_ha: float | None

    @property
    def achieved_share(self) -> float | None:
        """Established as a share of target, or ``None`` if either is unknown."""
        target = self.target_population_per_ha
        established = self.established_population_per_ha
        if not target or established is None:
            return None
        return established / target


@dataclass(frozen=True)
class ZoneFinding:
    """One zone the report names."""

    label: str
    severity: str
    summary: str
    causes: tuple[str, ...] = ()
    action: str = ""

    @property
    def is_explained(self) -> bool:
        """Whether anything corroborates the zone being weak.

        The zone engine names a cause only when something supports it. A zone
        with no causes is not a zone with no problem — it is a problem with no
        explanation, and saying so is more useful than picking the likeliest.
        """
        return bool(self.causes)


@dataclass(frozen=True)
class FieldReport:
    """The view model a template renders."""

    field_name: str
    grower_name: str | None
    district: str | None
    hectares: float | None
    crop_type: str | None
    variety: str | None
    season_label: str | None
    coverage_start: date
    coverage_end: date

    stand_check: StandCheck | None = None
    zones: tuple[ZoneFinding, ...] = ()
    retrospective: Any | None = None
    #: Free-form notes from the execution summary, already phrased by
    #: ``services/planning/execution.py``.
    execution_notes: tuple[str, ...] = ()

    # ── What the report can show ──────────────────────────────────────────────

    @property
    def reportable_zones(self) -> tuple[ZoneFinding, ...]:
        """Zones worth a reader's attention, weakest first.

        Healthy zones are omitted. A document listing twelve zones of which ten
        say "ok" buries the two that matter — and a farmer reading this has
        already walked the field.
        """
        order = {"problem": 0, "watch": 1}
        return tuple(
            sorted(
                (z for z in self.zones if z.severity in ZONE_REPORT_SEVERITIES),
                key=lambda z: (order.get(z.severity, 9), z.label),
            )
        )

    @property
    def unexplained_zones(self) -> tuple[ZoneFinding, ...]:
        """Zones that are weak with nothing corroborating why."""
        return tuple(z for z in self.reportable_zones if not z.is_explained)

    @property
    def has_content(self) -> bool:
        """Whether there is anything to report beyond the field's identity.

        A report with nothing in it should not be issued. Generating one anyway
        produces a document with a verification line and no findings, which
        reads as a clean bill of health for a field nobody looked at.
        """
        return bool(
            self.stand_check
            or self.reportable_zones
            or self.retrospective
            or self.execution_notes
        )

    # ── The one thing whose absence is stated ─────────────────────────────────

    @property
    def stand_check_gap(self) -> str | None:
        """
        Why this report is weaker without a stand check, or ``None`` if there
        is one.

        This is the exception to "sections render only when they have content",
        and it is the finding the whole planning body of work began with:
        satellite NDVI cannot separate a **thin healthy stand** from a **full
        stressed one**. Both read as low canopy. Without a plant count, every
        zone finding below is ambiguous in exactly that way, and a reader who
        does not know that will read them as stress.

        A farmer can also still act on it — a stand check next season is cheap,
        and it is the single thing that most improves what this document can
        say. Silence would hide both facts.
        """
        if self.stand_check is not None:
            return None
        return (
            "No stand check was recorded for this season. Satellite imagery "
            "cannot tell a thin healthy stand from a full stressed one — both "
            "look like low canopy — so the zone findings below cannot "
            "distinguish a spacing problem from a stress problem. A plant count "
            "early next season resolves it."
        )

    @property
    def qualifications(self) -> tuple[str, ...]:
        """What a reader must know before reading the findings."""
        notes: list[str] = []

        gap = self.stand_check_gap
        if gap:
            notes.append(gap)

        unexplained = len(self.unexplained_zones)
        if unexplained:
            notes.append(
                f"{_plural(unexplained, 'zone')} "
                f"{'is' if unexplained == 1 else 'are'} behind the field average "
                f"with nothing in the record to explain why. "
                f"{'It is' if unexplained == 1 else 'They are'} named below "
                f"rather than attributed to a likely cause."
            )

        if self.stand_check is not None and self.stand_check.achieved_share is None:
            notes.append(
                "A stand check was recorded but without both a target and an "
                "achieved population, so establishment cannot be scored."
            )

        return tuple(notes)


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def zone_findings(zones: Sequence[Any]) -> tuple[ZoneFinding, ...]:
    """
    Adapt ``services.zones.diagnosis.ZoneDiagnosis`` objects (or their dicts).

    Accepts either so a route can pass what it already has without a round-trip
    through JSON — and so tests can build findings directly.
    """
    out: list[ZoneFinding] = []
    for zone in zones:
        data = zone.to_dict() if hasattr(zone, "to_dict") else dict(zone)
        out.append(
            ZoneFinding(
                label=data.get("label") or "Zone",
                severity=data.get("severity") or "unknown",
                summary=data.get("summary") or "",
                causes=tuple(data.get("causes") or ()),
                action=data.get("action") or "",
            )
        )
    return tuple(out)


def build_field_report(
    *,
    field_name: str,
    coverage_start: date,
    coverage_end: date,
    grower_name: str | None = None,
    district: str | None = None,
    hectares: float | None = None,
    crop_type: str | None = None,
    variety: str | None = None,
    season_label: str | None = None,
    stand_check: StandCheck | None = None,
    zones: Sequence[Any] = (),
    retrospective: Any | None = None,
    execution_notes: Sequence[str] = (),
) -> FieldReport:
    """Assemble the report from pieces the callers already hold."""
    return FieldReport(
        field_name=field_name,
        grower_name=grower_name,
        district=district,
        hectares=hectares,
        crop_type=crop_type,
        variety=variety,
        season_label=season_label,
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        stand_check=stand_check,
        zones=zone_findings(zones),
        retrospective=retrospective,
        execution_notes=tuple(execution_notes),
    )
