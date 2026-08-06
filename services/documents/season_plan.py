"""
Season plan — what to do, when, before the season starts.

Pure. Unit-tested in ``tests/test_season_plan.py``.

The only one of the four documents that is **taken into the field**. Everything
else here goes to an inbox; this goes in a pocket, gets rained on, and is read
standing up next to a planter. That drives every decision below:

* **Ordered by when, not by topic.** A farmer reading this in November wants
  planting; in January they want the second top-dress. A document organised by
  subject makes them hunt.
* **Persona-aware.** "Calibrate your planter" is not an instruction to someone
  planting by hand, and "plant two seeds per station and thin at V3" is not one
  you give a 400 ha operation. This changes *which* instructions appear and how
  they are worded — never the agronomy. A target plant population is the same
  number for everyone.
* **Nothing conditional is presented as decided.** A step the engine marked
  optional or conditional says so, because a plan that reads as a set of orders
  gets followed past the point where it stopped applying.

Mirrors ``kurima-sense/lib/persona.ts``. Kept deliberately simple and matched by
tests on both sides rather than shared over the wire — the app has to brand its
screens before any document exists.

.. warning::

   Every rate, date and population here arrives already derived by
   ``services/planning/``, whose constants are pending agronomist review. This
   module chooses what is *said and in what order*; it must not compute
   agronomy, and it must not turn any engine's ``None`` into a figure.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Sequence

#: Personas that mean "has a planter, a spreader and a tape measure".
MECHANISED: frozenset[str] = frozenset({"farmer", "agronomist"})

#: Personas that want the growth-stage code (``V6``) rather than a description.
WANTS_STAGE_CODES: frozenset[str] = frozenset({"farmer", "agronomist"})


def normalise_persona(persona: str | None) -> str:
    """
    Fall back to **smallholder**, never to the commercial profile.

    Getting it wrong in that direction gives someone plain language and paces
    they did not need. The other way tells a person with a hoe to calibrate a
    planter they do not own, which is the failure that makes a document feel
    like it was not written for you.
    """
    key = (persona or "").strip().lower()
    return key if key in {"farmer", "smallholder", "agronomist", "hobbyist"} else "smallholder"


def uses_equipment(persona: str | None) -> bool:
    return normalise_persona(persona) in MECHANISED


def wants_stage_codes(persona: str | None) -> bool:
    return normalise_persona(persona) in WANTS_STAGE_CODES


def stage_label(
    stage_code: str | None, plain: str | None, persona: str | None
) -> str:
    """A growth stage in the register the reader wants."""
    if wants_stage_codes(persona) and stage_code:
        return stage_code
    return plain or stage_code or ""


@dataclass(frozen=True)
class PlanStep:
    """One dated thing to do. Flattened from the planning engines so the
    template can render a single chronological list."""

    key: str
    label: str
    detail: str
    when_text: str
    on_date: date | None = None
    optional: bool = False
    conditional_on: str | None = None

    @property
    def is_committed(self) -> bool:
        """Whether this is a step or a possibility.

        A plan that presents every line as an order gets followed past the point
        where it stopped applying — which, for a conditional top-dress on a dry
        season, means fertiliser spread on a crop that cannot use it.
        """
        return not self.optional and self.conditional_on is None


@dataclass(frozen=True)
class SeasonPlan:
    """The view model a template renders."""

    field_name: str
    crop: str
    persona: str
    coverage_start: date
    coverage_end: date
    planned_planting_date: date | None = None
    hectares: float | None = None
    variety: str | None = None

    establishment: Any | None = None
    steps: tuple[PlanStep, ...] = ()
    warnings: tuple[str, ...] = ()

    # ── Ordering ──────────────────────────────────────────────────────────────

    @property
    def dated_steps(self) -> tuple[PlanStep, ...]:
        """Steps with a date, in date order.

        Undated steps sort after them rather than being dropped: a step the
        engine could not date is still a step, and hiding it because the
        calendar is incomplete would quietly shorten the plan.
        """
        return tuple(
            sorted(self.steps, key=lambda s: (s.on_date is None, s.on_date or date.max))
        )

    @property
    def committed_steps(self) -> tuple[PlanStep, ...]:
        return tuple(s for s in self.dated_steps if s.is_committed)

    @property
    def conditional_steps(self) -> tuple[PlanStep, ...]:
        return tuple(s for s in self.dated_steps if not s.is_committed)

    @property
    def undated_steps(self) -> tuple[PlanStep, ...]:
        return tuple(s for s in self.steps if s.on_date is None)

    # ── Persona-specific instructions ─────────────────────────────────────────

    @property
    def equipment_tips(self) -> tuple[str, ...]:
        """Advice that only applies to a mechanised grower.

        Empty for everyone else — for a smallholder there is genuinely nothing
        here, and padding the page with machinery advice they cannot use is
        exactly what the persona split exists to stop.
        """
        if not uses_equipment(self.persona):
            return ()
        return (
            "Calibrate the planter against the target seed rate before you "
            "start — a plate or belt one size out costs the whole field.",
            "Check singulation and seed depth after the first few rows, not at "
            "the end of the block.",
        )

    @property
    def hand_planting_tips(self) -> tuple[str, ...]:
        """The mirror: real instructions for someone with a hoe and a bucket,
        and nothing at all for a mechanised grower."""
        if uses_equipment(self.persona):
            return ()
        return (
            "Mark your row spacing with a string line or a marked stick so it "
            "stays even down the whole row.",
            "Plant to the same depth every station — seed placed deeper comes "
            "up later and gets shaded out by its neighbours.",
        )

    # ── Honesty ───────────────────────────────────────────────────────────────

    @property
    def qualifications(self) -> tuple[str, ...]:
        notes: list[str] = []

        if self.planned_planting_date is None:
            notes.append(
                "No planting date is set, so nothing below is dated. Set one and "
                "the whole programme moves with it."
            )

        undated = len(self.undated_steps)
        if undated and self.planned_planting_date is not None:
            notes.append(
                f"{_plural(undated, 'step')} could not be dated from the "
                f"planting date and {'is' if undated == 1 else 'are'} listed at "
                f"the end."
            )

        if self.conditional_steps:
            notes.append(
                f"{_plural(len(self.conditional_steps), 'step')} below "
                f"{'is' if len(self.conditional_steps) == 1 else 'are'} "
                f"conditional. Read the condition before acting on them — they "
                f"are not part of the committed programme."
            )

        notes.extend(self.warnings)
        return tuple(notes)


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def steps_from_programme(programme: Any) -> tuple[PlanStep, ...]:
    """Flatten a :class:`~services.planning.fertiliser.FertiliserProgramme`."""
    if programme is None:
        return ()
    raw = programme.to_dict() if hasattr(programme, "to_dict") else dict(programme)
    out: list[PlanStep] = []
    for step in raw.get("steps") or ():
        data = step if isinstance(step, dict) else step.to_dict()
        out.append(
            PlanStep(
                key=data.get("key") or "step",
                label=data.get("label") or "Application",
                detail=" · ".join(
                    part for part in (data.get("product"), data.get("rate_text")) if part
                ),
                when_text=data.get("timing_text") or "",
                on_date=_as_date(data.get("scheduled_date")),
                optional=bool(data.get("optional")),
                conditional_on=data.get("conditional_on"),
            )
        )
    return tuple(out)


def steps_from_windows(windows: Sequence[Any]) -> tuple[PlanStep, ...]:
    """Flatten :class:`~services.planning.windows.ActionWindow` objects."""
    out: list[PlanStep] = []
    for window in windows or ():
        data = window.to_dict() if hasattr(window, "to_dict") else dict(window)
        out.append(
            PlanStep(
                key=data.get("key") or "window",
                label=data.get("label") or "Window",
                detail=data.get("why") or data.get("action") or "",
                when_text=data.get("window_text") or "",
                on_date=_as_date(data.get("closes_on") or data.get("opens_on")),
            )
        )
    return tuple(out)


def _as_date(value: Any) -> date | None:
    if value is None or isinstance(value, date):
        return value if isinstance(value, date) else None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def build_season_plan(
    *,
    field_name: str,
    crop: str,
    coverage_start: date,
    coverage_end: date,
    persona: str | None = None,
    planned_planting_date: date | None = None,
    hectares: float | None = None,
    variety: str | None = None,
    establishment: Any | None = None,
    fertiliser: Any | None = None,
    windows: Sequence[Any] = (),
    warnings: Sequence[str] = (),
) -> SeasonPlan:
    """Assemble the plan from what the planning engines already produced."""
    return SeasonPlan(
        field_name=field_name,
        crop=crop,
        persona=normalise_persona(persona),
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        planned_planting_date=planned_planting_date,
        hectares=hectares,
        variety=variety,
        establishment=establishment,
        steps=steps_from_programme(fertiliser) + steps_from_windows(windows),
        warnings=tuple(warnings),
    )
