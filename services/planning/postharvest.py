"""
Post-harvest phase — drying, storage and the losses that happen after the
combine leaves. Pure, no I/O.

Why this exists
---------------
For the model, harvest closes the loop. For the farmer it opens the riskiest
window of the year: developing-country storage losses run **20-30%**, mostly to
post-harvest pests. In Zimbabwe the named threats are the **larger grain borer**
(*Prostephanus truncatus*) and the **maize weevil** (*Sitophilus zeamais*), with
LGB explicitly more damaging in small-scale on-farm storage. Drying losses on
raised platforms alone run ~4.5%.

A farmer can execute a flawless season and lose a quarter of it in the shed, and
until now the app went quiet at exactly the moment that risk began.

Everything here is rendered from knowledge the crop profiles already carry —
``harvest_moisture``, ``storage_conditions`` and ``post_harvest_notes`` are on
every ``CropProfile`` and no screen has ever displayed them. The work is parsing
them into checkable numbers and staging them into an order of operations.

.. warning::
   Moisture targets are read from the crop profiles; the storage-protection
   guidance is compiled from FAO/regional extension material and is pending
   agronomist sign-off before farmer-facing release.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional, Tuple

# Grain at or below this is safe from mould for long storage; above it, fungal
# growth and aflatoxin risk climb quickly. Used only when a crop profile gives
# no explicit figure.
DEFAULT_SAFE_MOISTURE_PCT = 12.5

# Fumigants such as phosphine need the grain dry enough to hold the gas; wet
# grain both absorbs it and keeps respiring.
FUMIGATION_MAX_MOISTURE_PCT = 13.0

# "<13%", "13%", "12.5 %", "8%", and ranges like "20-25%" where only the upper
# bound carries the sign. Both bounds are captured so a range is not silently
# read as its maximum. Note this matches percentages only — "<25°C" in the same
# sentence is a temperature and must not be mistaken for a moisture reading.
_PCT_RE = re.compile(
    r"<?\s*(\d{1,2}(?:\.\d)?)\s*(?:[-–]\s*(\d{1,2}(?:\.\d)?)\s*)?%"
)

# Crops where the profiles flag aflatoxin explicitly. Mould on these is a food
# safety problem, not just a quality one.
_AFLATOXIN_KEYWORDS = ("aflatoxin",)


@dataclass
class PostHarvestStep:
    key: str
    title: str
    detail: str
    why: str
    target_moisture_pct: Optional[float] = None
    order: int = 0
    critical: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "detail": self.detail,
            "why": self.why,
            "target_moisture_pct": self.target_moisture_pct,
            "order": self.order,
            "critical": self.critical,
        }


@dataclass
class PostHarvestPlan:
    crop: str
    harvest_moisture_text: str = ""
    storage_moisture_pct: Optional[float] = None
    fumigation_possible: bool = False
    aflatoxin_risk: bool = False
    steps: List[PostHarvestStep] = dc_field(default_factory=list)
    warnings: List[str] = dc_field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crop": self.crop,
            "harvest_moisture_text": self.harvest_moisture_text,
            "storage_moisture_pct": self.storage_moisture_pct,
            "fumigation_possible": self.fumigation_possible,
            "aflatoxin_risk": self.aflatoxin_risk,
            "steps": [s.to_dict() for s in self.steps],
            "warnings": self.warnings,
        }


def extract_moisture_targets(text: Optional[str]) -> List[float]:
    """Every moisture percentage mentioned, in order of appearance.

    Range bounds are both returned, so "20-25%" reads as two figures rather
    than silently collapsing to its maximum.
    """
    if not text:
        return []
    out: List[float] = []
    for low, high in _PCT_RE.findall(str(text)):
        out.append(float(low))
        if high:
            out.append(float(high))
    return out


def safe_storage_moisture(
    harvest_moisture: Optional[str],
    storage_conditions: Optional[str],
) -> Optional[float]:
    """The moisture a crop must reach before it is safe to store.

    Takes the **lowest** figure mentioned across both fields. The profiles quote
    a harvest range and a storage ceiling in the same prose ("harvest at 20-25%,
    shell-dry to <13%"), and it is the storage ceiling that matters here —
    picking the higher number would tell a farmer to bag grain that will mould.
    """
    values = extract_moisture_targets(storage_conditions) + extract_moisture_targets(harvest_moisture)
    # Discard implausible readings: percentages above ~30 in this prose are
    # almost always something else (temperature, protein, oil content).
    values = [v for v in values if 0 < v <= 30]
    return min(values) if values else None


def _mentions_aflatoxin(profile: Any) -> bool:
    blob = " ".join(
        str(getattr(profile, attr, "") or "")
        for attr in ("post_harvest_notes", "storage_conditions", "harvest_moisture")
    ).lower()
    return any(k in blob for k in _AFLATOXIN_KEYWORDS)


def build_post_harvest_plan(profile: Any) -> PostHarvestPlan:
    """Stage a crop's post-harvest knowledge into an order of operations."""
    crop = getattr(profile, "crop_name", "") or ""
    harvest_moisture = str(getattr(profile, "harvest_moisture", "") or "")
    storage_conditions = str(getattr(profile, "storage_conditions", "") or "")
    notes = str(getattr(profile, "post_harvest_notes", "") or "")

    target = safe_storage_moisture(harvest_moisture, storage_conditions)
    plan = PostHarvestPlan(
        crop=crop,
        harvest_moisture_text=harvest_moisture,
        storage_moisture_pct=target,
        aflatoxin_risk=_mentions_aflatoxin(profile),
    )
    plan.fumigation_possible = target is not None and target <= FUMIGATION_MAX_MOISTURE_PCT

    if not (harvest_moisture or storage_conditions or notes):
        plan.warnings.append(
            f"No post-harvest guidance is recorded for {crop or 'this crop'} yet."
        )
        return plan

    order = 0

    if harvest_moisture:
        order += 1
        plan.steps.append(PostHarvestStep(
            key="harvest_timing",
            title="Harvest at the right moisture",
            detail=harvest_moisture,
            why=(
                "Harvesting too wet invites mould in the heap; too dry and the crop "
                "shatters and cracks in handling, which is loss you never see in a "
                "yield figure."
            ),
            order=order,
            critical=True,
        ))

    order += 1
    dry_target = target if target is not None else DEFAULT_SAFE_MOISTURE_PCT
    plan.steps.append(PostHarvestStep(
        key="drying",
        title=f"Dry down to {dry_target}%",
        detail=(
            f"Dry on a raised, ventilated platform or crib — never directly on bare "
            f"ground. Keep drying until the crop reaches {dry_target}% moisture; that "
            f"number is the difference between grain that keeps and grain that moulds."
        ),
        why=(
            "This is the single controlling variable in storage. Drying losses on "
            "raised platforms run about 4.5%, but grain stored wet can lose far more "
            "to mould and insects over a season."
        ),
        target_moisture_pct=dry_target,
        order=order,
        critical=True,
    ))

    if notes:
        order += 1
        plan.steps.append(PostHarvestStep(
            key="grading",
            title="Sort and grade",
            detail=notes,
            why=(
                "Damaged and mouldy grain contaminates the rest of the bag and is "
                "what buyers reject on first inspection."
            ),
            order=order,
            critical=plan.aflatoxin_risk,
        ))

    if storage_conditions:
        order += 1
        plan.steps.append(PostHarvestStep(
            key="storage",
            title="Store it properly",
            detail=storage_conditions,
            why=(
                "Storage losses in the region run 20-30%, mostly to insects. The "
                "larger grain borer is the worst of them in on-farm storage and it "
                "bores into sound grain, not just damaged grain — so a clean crop is "
                "not protection on its own."
            ),
            order=order,
            critical=True,
        ))

    order += 1
    plan.steps.append(PostHarvestStep(
        key="monitoring",
        title="Check the store monthly",
        detail=(
            "Open the store each month. Look for fine dust under the bags, live "
            "insects, warm patches in the heap, or a musty smell — all of them mean "
            "the crop is being eaten or is going out of condition."
        ),
        why=(
            "An infestation caught in its first month costs a re-treatment; the same "
            "infestation found at selling time has already eaten the margin."
        ),
        order=order,
    ))

    if plan.aflatoxin_risk:
        plan.warnings.append(
            "Mould on this crop is a food-safety problem, not just a quality one — "
            "aflatoxin is not removed by cooking, and contaminated grain should not "
            "be eaten or sold. Reject discoloured or mouldy grain rather than "
            "blending it in."
        )
    if target is not None and not plan.fumigation_possible:
        plan.warnings.append(
            f"At {target}% this crop is stored drier than fumigants need. Rely on "
            f"hermetic storage (sealed bags or a metal silo) rather than chemical "
            f"treatment."
        )
    if target is None:
        plan.warnings.append(
            "No specific storage moisture is recorded for this crop, so the general "
            f"{DEFAULT_SAFE_MOISTURE_PCT}% guideline is shown."
        )

    return plan
