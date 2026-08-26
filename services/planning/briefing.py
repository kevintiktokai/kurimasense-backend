"""
The planning knowledge, rendered for the chat.

Why this exists
---------------
The planner and the chat were answering the same question from different
places. Ask the season planner how to space maize and it computes from
:mod:`.establishment` — a target population for the natural region, a row
spacing, an in-row spacing solved to hit it, a seed rate. Ask the chat the same
question and it improvised from the language model, because ``ai_brain`` knew
about ``crop_profiles`` and nothing about ``services.planning``.

Two surfaces, two answers, and no way for a farmer to tell which one to plant
by. That is precisely what this repo's own convention exists to prevent: a
helper shared by two surfaces so the number on one always matches the number on
the other.

So the chat now reads from the same functions the planner calls. Not a copy of
them, not a prompt describing them — the functions themselves, rendered as
text. If the agronomy changes, both surfaces change together because there is
only one of it.

What this deliberately does not do
----------------------------------
It does not invent an answer for a crop the planner cannot plan. When
``build_establishment_plan`` returns ``None`` for an unsupported crop, this
returns ``None`` too, and the chat falls back to its general knowledge without
a fabricated spacing table in front of it. Declining to answer rather than
guessing is the rule, and it has to hold on the surface where a wrong number is
easiest to state confidently.

.. warning::
   The numbers rendered here come from :mod:`.establishment` and
   :mod:`.fertiliser`, whose targets and rates are compiled from extension
   literature and are pending agronomist sign-off. This module adds no
   agronomy of its own — it changes *where* those numbers are visible, not
   what they say.
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from .curing import build_curing_plan
from .establishment import build_establishment_plan
from .fertiliser import build_fertiliser_programme

#: Steps beyond this are noise in a chat answer — the farmer asked a question,
#: not for the whole season. The planner screen shows the full programme.
_MAX_FERTILISER_STEPS = 4


def _positive(value) -> bool:
    """True for a real, usable quantity — not None and not zero.

    The establishment profiles use 0 to mean "does not apply to this crop"
    (a transplanted crop has no seed rate). Zero is a legitimate stored value
    and a nonsensical thing to show a farmer.
    """
    try:
        return value is not None and float(value) > 0
    except (TypeError, ValueError):
        return False


def _range_text(value) -> str:
    """A (low, high) pair as "5–7", a scalar as itself.

    The establishment profiles express depth as a range because that is what
    the agronomy says. Rendering one end of it as a single number would invent
    a precision the source does not have.
    """
    if isinstance(value, (tuple, list)) and len(value) == 2:
        low, high = value
        if low == high:
            return f"{low:g}"
        return f"{low:g}–{high:g}"
    return f"{value:g}" if isinstance(value, (int, float)) else str(value)


def establishment_briefing(
    crop: str,
    *,
    natural_region: Optional[str] = None,
    irrigated: bool = False,
    area_hectares: Optional[float] = None,
) -> Optional[str]:
    """
    How to plant this crop here, as the planner computes it.

    Returns ``None`` for a crop the planner does not support, so the caller can
    tell "we have nothing" from "we have this" — rather than receiving an empty
    heading that reads like an answer.
    """
    plan = build_establishment_plan(
        crop,
        natural_region=natural_region,
        irrigated=irrigated,
        area_hectares=area_hectares,
    )
    if plan is None:
        return None

    lines: List[str] = [
        "**Establishment plan (computed, not estimated — this is what the "
        "planning screen shows for this field):**",
        f"- Target population: {plan.target_population_per_ha:,} plants/ha"
        f" ({plan.potential_band} potential)",
        f"- Row spacing: {plan.row_spacing_cm:g} cm; "
        f"in-row spacing: {plan.in_row_spacing_cm:g} cm",
    ]

    # Seed depth and seed rate are meaningless for a transplanted crop, and the
    # profiles express that as zero. Rendering it produces
    #
    #     - Planting depth: 0 cm, 1 seed(s) per station
    #     - Seed rate: 0 kg/ha
    #
    # for tobacco — the crop most of this product's farmers actually grow. That
    # is not a fact, it is a broken-looking calculation, and it is the same
    # mistake as a card that renders empty instead of rendering nothing. Say
    # what the crop needs instead: seedlings, not seed.
    direct_seeded = bool(_positive(plan.seed_rate_kg_ha))
    if direct_seeded:
        # planting_depth_cm is a (low, high) range, not a scalar — quoting one
        # end of it as "the" depth would be a fabricated precision.
        lines.append(
            f"- Planting depth: {_range_text(plan.planting_depth_cm)} cm, "
            f"{plan.seeds_per_station} seed(s) per station"
        )
        lines.append(f"- Seed rate: {plan.seed_rate_kg_ha:g} kg/ha")
        if _positive(plan.seed_required_kg):
            lines.append(
                f"- Seed required for this field: {plan.seed_required_kg:g} kg"
            )
    else:
        lines.append(
            f"- Transplanted crop: raise or buy {plan.target_population_per_ha:,} "
            "seedlings per hectare rather than sowing seed in the field. Seed "
            "rate and sowing depth do not apply."
        )
    if plan.thin_at_stage:
        lines.append(f"- Thin at: {plan.thin_at_stage}")
    if plan.field_check:
        lines.append(f"- Field check: {plan.field_check}")
    for reason in plan.rationale or []:
        lines.append(f"- Why: {reason}")
    for warning in plan.warnings or []:
        lines.append(f"- ⚠️ {warning}")

    return "\n".join(lines)


def _when_text(step) -> str:
    """When a step happens, whichever way the programme expressed it.

    ``scheduled_date`` is a date when a planting date was supplied and an ISO
    string in some paths; with no planting date it is absent entirely and the
    programme falls back to "days after planting" prose. All three have to read
    correctly — a chat answer that says "None" for timing is worse than one
    that says nothing.
    """
    scheduled = getattr(step, "scheduled_date", None)
    if scheduled is None:
        return step.timing_text or "timing not set"
    if hasattr(scheduled, "isoformat"):
        return scheduled.isoformat()
    return str(scheduled)


def fertiliser_briefing(
    crop: str,
    *,
    planting_date: Optional[date] = None,
    area_hectares: Optional[float] = None,
    irrigated: bool = False,
    soil_ph: Optional[float] = None,
    soil_texture: Optional[str] = None,
) -> Optional[str]:
    """
    The fertiliser programme the planner would render, trimmed for chat.

    Takes a crop *name* and resolves the profile here, because that is what a
    chat turn has. ``season_lifecycle_routes`` already holds a profile object
    and calls ``build_fertiliser_programme`` directly — same function, same
    numbers, one resolution step apart.

    Notably not wrapped in a bare ``except``: the first draft of this guarded
    the call with ``except TypeError``, got the signature wrong, and produced a
    chat that silently never mentioned fertiliser at all. A defensive catch
    around a call whose shape you have not checked does not make the code
    safer, it makes the mistake invisible.
    """
    # get_crop_profile, NOT get_crop_profile_or_generic. The generic variant
    # returns a maize-shaped fallback for a crop we do not know, and offering a
    # farmer a fertiliser programme for the wrong crop with full confidence is
    # exactly the failure this codebase declines to make.
    from crop_profiles import get_crop_profile

    profile = get_crop_profile(crop)
    if profile is None:
        return None

    programme = build_fertiliser_programme(
        profile,
        planting_date=planting_date,
        area_hectares=area_hectares,
        soil_ph=soil_ph,
        soil_texture=soil_texture,
        irrigated=irrigated,
    )
    if programme is None or not programme.steps:
        return None

    lines: List[str] = [
        "**Fertiliser programme (same schedule as the planning screen):**"
    ]
    for step in programme.steps[:_MAX_FERTILISER_STEPS]:
        when = _when_text(step)
        product = f"{step.product}: " if step.product else ""
        optional = " (optional)" if step.optional else ""
        lines.append(f"- {step.label}{optional} — {product}{step.rate_text} — {when}")
        if step.why:
            lines.append(f"  · {step.why}")

    remaining = len(programme.steps) - _MAX_FERTILISER_STEPS
    if remaining > 0:
        lines.append(
            f"- …and {remaining} further step(s) — the field's planning screen "
            "has the full programme."
        )
    for adjustment in programme.adjustments or []:
        lines.append(f"- Adjusted: {adjustment}")
    for warning in programme.warnings or []:
        lines.append(f"- ⚠️ {warning}")

    return "\n".join(lines)


def curing_briefing(
    crop: Optional[str],
    *,
    area_hectares: Optional[float] = None,
) -> Optional[str]:
    """
    The barn cycle, for a crop that goes into a barn.

    Returns ``None`` for anything that is not flue-cured, which includes burley
    and other air-cured tobacco. That exclusion is the whole reason this goes
    through :func:`~.curing.build_curing_plan` rather than testing the crop
    name here: a chat asked "how do I cure this" will answer, and the flue
    schedule applied to burley destroys the crop.
    """
    plan = build_curing_plan(crop, area_hectares=area_hectares)
    if plan is None:
        return None

    low, high = plan.total_days
    lines: List[str] = [
        f"**Flue-curing (Tobacco Research Board / Kutsaga schedule — "
        f"{low:g}–{high:g} days in the barn):**",
    ]
    for i, stage in enumerate(plan.stages, start=1):
        t_low, t_high = stage.temperature_c
        d_low, d_high = stage.duration_days
        humidity = (
            f", humidity ~{stage.relative_humidity_pct:g}%"
            if stage.relative_humidity_pct is not None
            else ""
        )
        lines.append(
            f"{i}. {stage.name} — {t_low:g}–{t_high:g} °C for "
            f"{d_low:g}–{d_high:g} days{humidity}. {stage.what_happens}"
        )
        lines.append(f"   · Watch for: {stage.watch_for}")

    c_low, c_high = plan.conditioning_moisture_pct
    lines.append(
        f"{len(plan.stages) + 1}. Conditioning — add {c_low:g}–{c_high:g}% "
        "moisture back into the leaf before it comes off the sticks, or it "
        "shatters on handling and the grade goes with it."
    )

    if plan.barn_options:
        lines.append("")
        lines.append("**Barn capacity for this field:**")
        # Not truncated. The first draft capped this at three, which for a 2 ha
        # field cut off the plastic and rocket barns — the two Kutsaga names as
        # suiting "beginners and low-income small-scale growers", which is most
        # of this product's users. Sorting puts fewest-barns-first, so the cap
        # dropped precisely the affordable options and kept the coal ones. There
        # are at most six barn types; there was never enough to save.
        for option in plan.barn_options:
            barn = option.barn
            unit = "barn" if option.count == 1 else "barns"
            fuel = ""
            if barn.fuel_kg_per_kg_cured is not None and barn.fuel:
                fuel = (
                    f" — about {barn.fuel_kg_per_kg_cured:g} kg of {barn.fuel} "
                    "per kg of cured leaf"
                )
            lines.append(
                f"- {option.count} × {barn.name} "
                f"({barn.hectares[0]:g} ha each){fuel}. Suits {barn.suits}."
            )
        # Fuel type decides this, not efficiency, and we do not know what the
        # grower can actually get hold of.
        lines.append(
            "  · Which of these is right depends on the fuel the grower can "
            "actually source, not on which is most efficient."
        )

    for warning in plan.warnings:
        lines.append(f"- ⚠️ {warning}")

    return "\n".join(lines)


def planning_briefing(
    crop: Optional[str],
    *,
    natural_region: Optional[str] = None,
    irrigated: bool = False,
    area_hectares: Optional[float] = None,
    planting_date: Optional[date] = None,
    is_planted: bool = True,
) -> Optional[str]:
    """
    Everything the planner knows about getting this crop into the ground.

    ``is_planted=False`` is the case that prompted this: a field mapped but not
    yet planted has no planting date, so every stage, GDD and yield calculation
    downstream declines to answer — and the farmer sees blank cards with no
    indication that the app has plenty to tell them about the *next* step. For
    that field the establishment and fertiliser plan is the entire useful
    answer, and the chat should lead with it.
    """
    if not crop:
        return None

    sections = [
        establishment_briefing(
            crop,
            natural_region=natural_region,
            irrigated=irrigated,
            area_hectares=area_hectares,
        ),
        fertiliser_briefing(
            crop,
            planting_date=planting_date,
            area_hectares=area_hectares,
            irrigated=irrigated,
        ),
        # Curing is included for a tobacco field from the day it is mapped, not
        # withheld until harvest. A grower decides how many barns to build, and
        # cuts or buys the wood to fire them, months before the first leaf is
        # ready — by reaping time the decision has already been made. Returns
        # None for every other crop, so nothing else carries the weight of it.
        curing_briefing(crop, area_hectares=area_hectares),
    ]
    present = [s for s in sections if s]
    if not present:
        return None

    header = (
        "**This field is mapped but not yet planted.** The farmer is asking "
        "about preparation, so ground the answer in the plan below and do not "
        "state a growth stage, a yield projection or a harvest date for this "
        "field — none of those exist for it yet. Reference material further "
        "down (curing, for instance) is background the farmer may ask about; "
        "it is not a schedule for this field.\n"
        if not is_planted
        else ""
    )
    return header + "\n\n".join(present)
