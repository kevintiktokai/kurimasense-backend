"""
Execution quality — whether an operation was done in a way that worked.
Pure computation, no I/O.

Why this exists
---------------
``farm_tasks`` records that a job was done. ``field_inputs`` records what went
on and how much. Neither records **how**, and for nitrogen the how is most of
the outcome:

* Urea broadcast onto dry soil and left on the surface can lose a large share
  of its nitrogen to ammonia volatilisation before the crop ever sees it. The
  farmer paid for the bag, applied it on the right day, ticked the task — and
  fed the air.
* The same urea, banded or incorporated, or followed within a couple of days by
  moderate rain, reaches the roots.
* The same urea again, followed by a downpour on sandy soil, leaches past the
  roots. Zimbabwean sandy loams lose 29-40 kg N/ha from the top 40 cm within
  two weeks of heavy rain.

Three identical task ticks; three completely different seasons. Capturing the
difference is what turns outcome data from "what happened" into "what worked",
and it is the only way the calibration loop can learn anything about management
rather than about weather.

What this module does NOT do
---------------------------
It does not grade a farmer. Every assessment names what would have been better
**next time**, and losses are described as risks to the nitrogen rather than
mistakes — a farmer who feels marked will stop logging, and then there is no
data at all.

.. warning::
   Loss fractions are compiled from extension research and are pending
   agronomist sign-off before farmer-facing release.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional

# Application methods, best to worst for keeping nitrogen in the soil.
METHOD_INCORPORATED = "incorporated"     # worked into the soil
METHOD_BANDED = "banded"                 # placed in a band beside the row
METHOD_BROADCAST = "broadcast"           # spread on the surface
METHOD_FERTIGATION = "fertigation"       # through irrigation water

# Rain in the 48 hours after application, in mm.
#   Below this, surface-applied urea sits and volatilises.
RAIN_TOO_LITTLE_MM = 5.0
#   Above this on a leaching soil, nitrogen moves past the root zone.
RAIN_TOO_MUCH_MM = 40.0

# Indicative share of applied nitrogen at risk, by failure mode.
VOLATILISATION_LOSS = 0.25      # surface urea, dry, unincorporated
LEACHING_LOSS = 0.30            # heavy rain on sand soon after application

_UREA_KEYWORDS = ("urea",)
_NITROGEN_KEYWORDS = ("urea", "an", "ammonium nitrate", "can", "uan", "nitrogen")
_LEACHING_TEXTURES = ("sand", "sandy", "loamy sand", "sandy loam", "kaolinitic")


@dataclass
class ExecutionAssessment:
    """How well one application is likely to have worked."""
    quality: str                      # 'good' | 'reduced' | 'poor' | 'unknown'
    effective_fraction: float         # share of the input likely to reach the crop
    went_well: List[str] = dc_field(default_factory=list)
    at_risk: List[str] = dc_field(default_factory=list)
    next_time: List[str] = dc_field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality": self.quality,
            "effective_fraction": self.effective_fraction,
            "went_well": self.went_well,
            "at_risk": self.at_risk,
            "next_time": self.next_time,
            "summary": self.summary,
        }


def _matches(text: Optional[str], keywords) -> bool:
    if not text:
        return False
    t = str(text).strip().lower()
    tokens = {tok.strip(" .,-") for tok in t.replace("-", " ").split()}
    for k in keywords:
        if " " in k:
            if k in t:
                return True
        elif k in tokens:
            return True
    return False


def is_nitrogen(input_type: Optional[str], product: Optional[str] = None) -> bool:
    """Whether this application carries nitrogen worth assessing for losses."""
    return _matches(input_type, _NITROGEN_KEYWORDS) or _matches(product, _NITROGEN_KEYWORDS)


def is_urea(input_type: Optional[str], product: Optional[str] = None) -> bool:
    """Urea specifically — it is the form that volatilises on the surface."""
    return _matches(input_type, _UREA_KEYWORDS) or _matches(product, _UREA_KEYWORDS)


def is_leaching_soil(soil_texture: Optional[str]) -> bool:
    if not soil_texture:
        return False
    t = str(soil_texture).strip().lower()
    return any(k in t for k in _LEACHING_TEXTURES)


def assess_application(
    *,
    input_type: Optional[str],
    product: Optional[str] = None,
    method: Optional[str] = None,
    incorporated: Optional[bool] = None,
    rain_mm_48h: Optional[float] = None,
    soil_texture: Optional[str] = None,
) -> ExecutionAssessment:
    """Assess one nitrogen application against how it was actually put on.

    Returns ``quality='unknown'`` when there is not enough recorded to judge —
    an application with no method and no rainfall record cannot be assessed, and
    guessing would put a verdict on a farmer's work that the data does not
    support.
    """
    if not is_nitrogen(input_type, product):
        return ExecutionAssessment(
            quality="unknown",
            effective_fraction=1.0,
            summary="Execution quality is only assessed for nitrogen applications.",
        )

    if method is None and rain_mm_48h is None:
        return ExecutionAssessment(
            quality="unknown",
            effective_fraction=1.0,
            summary="Not enough was recorded about this application to assess it.",
            next_time=[
                "Logging how you applied it and whether rain followed turns this "
                "into something the season review can learn from."
            ],
        )

    m = (method or "").strip().lower()
    leaching_soil = is_leaching_soil(soil_texture)
    urea = is_urea(input_type, product)

    effective = 1.0
    went_well: List[str] = []
    at_risk: List[str] = []
    next_time: List[str] = []

    # --- Placement ---------------------------------------------------------
    if m in (METHOD_INCORPORATED, METHOD_BANDED) or incorporated is True:
        went_well.append(
            "It went into the soil rather than sitting on the surface, which is "
            "what keeps nitrogen where the roots can reach it."
        )
    elif m == METHOD_FERTIGATION:
        went_well.append("Applied through irrigation, so it went in with the water.")
    elif m == METHOD_BROADCAST:
        # Broadcasting is only a problem when nothing moves it in.
        if urea and (rain_mm_48h is not None and rain_mm_48h < RAIN_TOO_LITTLE_MM):
            effective *= (1 - VOLATILISATION_LOSS)
            at_risk.append(
                f"Urea spread on the surface with little rain behind it loses "
                f"nitrogen to the air — up to about "
                f"{int(VOLATILISATION_LOSS * 100)}% of what you applied."
            )
            next_time.append(
                "Band it, work it in, or put it on just ahead of rain. Surface "
                "urea on dry soil is the one application most likely to be wasted."
            )
        elif urea and rain_mm_48h is None:
            at_risk.append(
                "Surface-applied urea depends on rain within a day or two to wash "
                "it in; without a rainfall record we cannot tell whether it did."
            )

    # --- Timing against rain ------------------------------------------------
    if rain_mm_48h is not None:
        if rain_mm_48h > RAIN_TOO_MUCH_MM and leaching_soil:
            effective *= (1 - LEACHING_LOSS)
            at_risk.append(
                f"{rain_mm_48h:.0f} mm fell within two days on sandy soil, which "
                f"moves nitrogen down past the roots. On these soils that can be "
                f"29-40 kg N/ha gone."
            )
            next_time.append(
                "On sand, split the nitrogen into smaller doses and avoid applying "
                "just before heavy rain is forecast — the aim is steady rain, not "
                "a downpour."
            )
        elif RAIN_TOO_LITTLE_MM <= rain_mm_48h <= RAIN_TOO_MUCH_MM:
            went_well.append(
                f"{rain_mm_48h:.0f} mm followed within two days — enough to move "
                f"the nitrogen into the root zone without washing it through."
            )
        elif rain_mm_48h < RAIN_TOO_LITTLE_MM and not at_risk:
            at_risk.append(
                "Very little rain followed, so the nitrogen may still be sitting "
                "near the surface waiting to be moved in."
            )

    effective = round(effective, 3)
    if effective >= 0.95:
        quality = "good"
    elif effective >= 0.75:
        quality = "reduced"
    else:
        quality = "poor"

    if quality == "good":
        summary = "This application was put on in a way that should have worked."
    else:
        summary = (
            f"Roughly {int(effective * 100)}% of this application is likely to have "
            f"reached the crop."
        )

    return ExecutionAssessment(
        quality=quality,
        effective_fraction=effective,
        went_well=went_well,
        at_risk=at_risk,
        next_time=next_time,
        summary=summary,
    )


def summarise_season_execution(
    assessments: List[ExecutionAssessment],
) -> Dict[str, Any]:
    """Roll a season's applications into one read on how well inputs were used.

    Only assessable applications count toward the average — an unknown is not a
    good one, and averaging it in as 1.0 would quietly reward not recording
    anything.
    """
    scored = [a for a in assessments if a.quality != "unknown"]
    if not scored:
        return {
            "applications_assessed": 0,
            "average_effective_fraction": None,
            "summary": (
                "No applications had enough recorded to assess. Logging how each "
                "one went on is what makes this useful next season."
            ),
        }

    avg = round(sum(a.effective_fraction for a in scored) / len(scored), 3)
    lost = round((1 - avg) * 100)
    return {
        "applications_assessed": len(scored),
        "average_effective_fraction": avg,
        "summary": (
            "Your fertiliser went on well this season."
            if avg >= 0.95 else
            f"About {lost}% of the fertiliser you paid for is likely to have been "
            f"lost to how or when it was applied, rather than to the crop."
        ),
    }
