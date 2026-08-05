"""
Establishment planning — pure agronomy, no I/O.

Turns "what are you planting, where, and when" into the numbers a farmer can
actually execute in a field: **target plant population, row spacing, in-row
spacing, seed quantity, and a countable field check**.

Why this module exists
----------------------
Plant population is the highest-leverage yield lever the farmer fully controls,
it is locked in during week one, it is unrecoverable by roughly week three, and
it is *invisible to satellites* — NDVI cannot tell a thin healthy stand from a
full stressed one, and those two demand opposite actions. Before this module the
codebase mentioned spacing 231 times across ``crop_profiles/`` as advice prose
and zero times in any service: we told farmers to check their plant population
and never captured, scored or verified it.
See ``docs/farmer_growth_cycle_research.md`` §2.

Design
------
* **Pure.** No DB, no network, no FastAPI. Fully unit-testable.
* **Deterministic and auditable.** Every recommendation carries a ``rationale``.
  The ranking/derivation is rule-driven on purpose — farmers discount advice
  they can't interrogate, and an unexplainable number reads as a sales pitch.
* **Honest about units.** ``44,000 plants/ha`` is unactionable holding a hoe.
  The output is row spacing, in-row spacing, and "count this many plants in
  this many paces".

.. warning::
   The population tables below are compiled from Zimbabwe/Southern-Africa
   extension guidance (Seed Co grower guides, natural-region convention) and are
   **pending agronomist sign-off** before farmer-facing release. Farmers spend
   real money on this. Treat the numbers as reviewable defaults, not gospel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field as dc_field
from typing import Dict, List, Optional, Tuple

# A walking pace, metres. Used only for the human-readable field check — the
# arithmetic is always done in metres.
PACE_M = 0.75

# Square metres in a hectare.
SQM_PER_HA = 10_000.0

# The classic stand-count sample: 1/1000 ha = 10 m². Count the plants in the
# row length that sweeps 10 m² at the field's row spacing, multiply by 1000,
# and you have plants/ha. This is the method farmers already know.
STAND_SAMPLE_FRACTION = 1000.0


# ---------------------------------------------------------------------------
# Crop establishment parameters
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CropEstablishment:
    """Structured establishment agronomy for one crop.

    ``population_by_potential`` maps a yield-potential band (see
    :func:`potential_band`) to a target final stand in plants/ha.
    """
    crop: str
    population_by_potential: Dict[str, int]
    default_row_spacing_cm: float
    row_spacing_options_cm: Tuple[float, ...]
    thousand_seed_weight_g: float
    planting_depth_cm: Tuple[float, float]   # (min, max)
    seeds_per_station: int = 1
    thin_at_stage: Optional[str] = None
    notes: str = ""


# Yield-potential bands. Driven by natural region + irrigation, because the
# same crop wants a very different stand in Region V dryland than under a pivot.
POTENTIAL_BANDS = ("very_low", "low", "moderate", "high", "very_high")

# Zimbabwe natural region → rainfed potential band.
#   I    Eastern Highlands, >1000 mm
#   IIa/IIb  750-1000 mm, intensive
#   III  650-800 mm, semi-intensive
#   IV   450-650 mm, semi-extensive
#   V    <450 mm, extensive
_REGION_BAND = {
    "I": "high",
    "IIA": "high",
    "IIB": "moderate",
    "II": "moderate",
    "III": "moderate",
    "IV": "low",
    "V": "very_low",
}

_CROPS: Dict[str, CropEstablishment] = {
    "maize": CropEstablishment(
        crop="maize",
        # Seed Co / regional guidance: 37-44k dryland in low-rainfall areas,
        # 50-60k under irrigation or high potential. 36-60k overall envelope.
        population_by_potential={
            "very_low": 30_000,
            "low": 37_000,
            "moderate": 44_000,
            "high": 50_000,
            "very_high": 55_000,
        },
        default_row_spacing_cm=90.0,
        row_spacing_options_cm=(75.0, 90.0),
        thousand_seed_weight_g=330.0,
        planting_depth_cm=(5.0, 7.0),
        seeds_per_station=2,
        thin_at_stage="V3",
        notes=(
            "Plant two seeds per station and thin to one at V3 — insurance "
            "against gappy emergence, which costs more yield than uneven spacing."
        ),
    ),
    "soybean": CropEstablishment(
        crop="soybean",
        population_by_potential={
            "very_low": 250_000,
            "low": 300_000,
            "moderate": 350_000,
            "high": 400_000,
            "very_high": 450_000,
        },
        default_row_spacing_cm=45.0,
        row_spacing_options_cm=(30.0, 45.0, 75.0),
        thousand_seed_weight_g=150.0,
        planting_depth_cm=(3.0, 5.0),
        notes="Narrow rows close canopy sooner and suppress weeds.",
    ),
    "groundnuts": CropEstablishment(
        crop="groundnuts",
        population_by_potential={
            "very_low": 130_000,
            "low": 160_000,
            "moderate": 200_000,
            "high": 250_000,
            "very_high": 280_000,
        },
        default_row_spacing_cm=45.0,
        row_spacing_options_cm=(30.0, 45.0, 60.0),
        thousand_seed_weight_g=450.0,
        planting_depth_cm=(5.0, 7.0),
    ),
    "sorghum": CropEstablishment(
        crop="sorghum",
        population_by_potential={
            "very_low": 60_000,
            "low": 90_000,
            "moderate": 130_000,
            "high": 170_000,
            "very_high": 200_000,
        },
        default_row_spacing_cm=75.0,
        row_spacing_options_cm=(45.0, 75.0, 90.0),
        thousand_seed_weight_g=30.0,
        planting_depth_cm=(2.0, 4.0),
    ),
    "cotton": CropEstablishment(
        crop="cotton",
        population_by_potential={
            "very_low": 30_000,
            "low": 40_000,
            "moderate": 50_000,
            "high": 60_000,
            "very_high": 70_000,
        },
        default_row_spacing_cm=90.0,
        row_spacing_options_cm=(90.0, 100.0),
        thousand_seed_weight_g=100.0,
        planting_depth_cm=(3.0, 5.0),
        seeds_per_station=2,
        thin_at_stage="4-leaf",
    ),
    "sugar_beans": CropEstablishment(
        crop="sugar_beans",
        population_by_potential={
            "very_low": 150_000,
            "low": 180_000,
            "moderate": 220_000,
            "high": 250_000,
            "very_high": 280_000,
        },
        default_row_spacing_cm=45.0,
        row_spacing_options_cm=(30.0, 45.0),
        thousand_seed_weight_g=350.0,
        planting_depth_cm=(3.0, 5.0),
    ),
    "wheat": CropEstablishment(
        crop="wheat",
        population_by_potential={
            "very_low": 1_200_000,
            "low": 1_600_000,
            "moderate": 2_000_000,
            "high": 2_400_000,
            "very_high": 2_800_000,
        },
        default_row_spacing_cm=20.0,
        row_spacing_options_cm=(17.5, 20.0, 25.0),
        thousand_seed_weight_g=40.0,
        planting_depth_cm=(3.0, 5.0),
        notes="Drilled, not stationed — in-row spacing is nominal.",
    ),
    "tobacco": CropEstablishment(
        crop="tobacco",
        population_by_potential={
            "very_low": 12_000,
            "low": 14_000,
            "moderate": 16_000,
            "high": 18_000,
            "very_high": 20_000,
        },
        default_row_spacing_cm=120.0,
        row_spacing_options_cm=(110.0, 120.0),
        thousand_seed_weight_g=0.08,
        planting_depth_cm=(0.0, 0.0),
        notes="Transplanted — seed rate is not the operative number; count seedlings.",
    ),
}

# Crop-name aliases → canonical key.
_ALIASES = {
    "maize": "maize", "corn": "maize", "mealies": "maize",
    "soybean": "soybean", "soybeans": "soybean", "soya": "soybean", "soya beans": "soybean",
    "groundnut": "groundnuts", "groundnuts": "groundnuts", "peanut": "groundnuts", "peanuts": "groundnuts",
    "sorghum": "sorghum",
    "cotton": "cotton",
    "sugar beans": "sugar_beans", "sugar_beans": "sugar_beans", "beans": "sugar_beans",
    "wheat": "wheat",
    "tobacco": "tobacco", "flue-cured tobacco": "tobacco",
    "flue cured tobacco": "tobacco", "tobacco_flue_cured": "tobacco",
}


def normalise_crop(crop: Optional[str]) -> Optional[str]:
    """Map a free-text crop name to a canonical establishment key, else None."""
    if not crop:
        return None
    key = str(crop).strip().lower().replace("-", " ")
    if key in _ALIASES:
        return _ALIASES[key]
    return _ALIASES.get(key.replace(" ", "_"))


def get_establishment_profile(crop: Optional[str]) -> Optional[CropEstablishment]:
    """Structured establishment agronomy for ``crop``, or None if unknown.

    Returning None (rather than a generic guess) is deliberate: a wrong
    population is worse than no population, because the farmer acts on it.
    """
    key = normalise_crop(crop)
    return _CROPS.get(key) if key else None


def potential_band(
    natural_region: Optional[str] = None,
    irrigated: bool = False,
    seasonal_rainfall_outlook: Optional[str] = None,
) -> str:
    """Yield-potential band from region, irrigation and rainfall outlook.

    Irrigation removes the rainfall constraint, so it dominates the region.
    A ``'below_normal'`` outlook steps the band down one and ``'above_normal'``
    steps it up — a dry-season forecast is a reason to plant a thinner stand,
    which is precisely the kind of adjustment a farmer cannot easily make alone.
    """
    if irrigated:
        band = "very_high"
    else:
        region_key = (natural_region or "").strip().upper().replace(" ", "")
        band = _REGION_BAND.get(region_key, "moderate")

    outlook = (seasonal_rainfall_outlook or "").strip().lower()
    if outlook in ("below_normal", "below", "dry"):
        band = _step_band(band, -1)
    elif outlook in ("above_normal", "above", "wet"):
        band = _step_band(band, +1)
    return band


def _step_band(band: str, delta: int) -> str:
    try:
        idx = POTENTIAL_BANDS.index(band)
    except ValueError:
        return band
    return POTENTIAL_BANDS[max(0, min(len(POTENTIAL_BANDS) - 1, idx + delta))]


# ---------------------------------------------------------------------------
# Core spacing maths
# ---------------------------------------------------------------------------
def in_row_spacing_for(target_population_per_ha: int, row_spacing_cm: float) -> float:
    """In-row spacing (cm) that yields ``target_population_per_ha``.

    ``plants/ha = 10,000 / (row_m * in_row_m)``  ⇒  ``in_row_m = 10,000 / (pop * row_m)``
    """
    if target_population_per_ha <= 0 or row_spacing_cm <= 0:
        raise ValueError("population and row spacing must be positive")
    row_m = row_spacing_cm / 100.0
    in_row_m = SQM_PER_HA / (target_population_per_ha * row_m)
    return round(in_row_m * 100.0, 1)


def population_for(row_spacing_cm: float, in_row_spacing_cm: float) -> int:
    """Plants/ha implied by a row × in-row spacing. Inverse of the above."""
    if row_spacing_cm <= 0 or in_row_spacing_cm <= 0:
        raise ValueError("spacings must be positive")
    row_m = row_spacing_cm / 100.0
    in_row_m = in_row_spacing_cm / 100.0
    return int(round(SQM_PER_HA / (row_m * in_row_m)))


def seed_rate_kg_ha(
    target_population_per_ha: int,
    thousand_seed_weight_g: float,
    germination_pct: float = 90.0,
    field_loss_pct: float = 10.0,
) -> float:
    """Seed needed per hectare to *establish* the target stand.

    Works back from the final stand the farmer wants, inflating for germination
    below 100% and for seedlings lost between sowing and establishment. This is
    the right direction of travel: the target is a stand, not a bag count.
    """
    if not 0 < germination_pct <= 100:
        raise ValueError("germination_pct must be in (0, 100]")
    if not 0 <= field_loss_pct < 100:
        raise ValueError("field_loss_pct must be in [0, 100)")
    seeds = target_population_per_ha / (germination_pct / 100.0) / (1 - field_loss_pct / 100.0)
    return round(seeds * thousand_seed_weight_g / 1_000_000.0, 2)


def stand_check_row_length_m(row_spacing_cm: float,
                             sample_fraction: float = STAND_SAMPLE_FRACTION) -> float:
    """Row length whose swept area is 1/``sample_fraction`` of a hectare.

    Count the plants along this length, multiply by ``sample_fraction``, and the
    result is plants/ha. Six metres of tape and a minute of walking replaces the
    single biggest blind spot in the season.
    """
    if row_spacing_cm <= 0:
        raise ValueError("row spacing must be positive")
    area_m2 = SQM_PER_HA / sample_fraction
    return round(area_m2 / (row_spacing_cm / 100.0), 2)


def population_from_stand_count(counted_plants: int, row_spacing_cm: float,
                                row_length_m: float) -> int:
    """Plants/ha from a raw field count over a measured row length."""
    if counted_plants < 0:
        raise ValueError("counted_plants cannot be negative")
    if row_length_m <= 0 or row_spacing_cm <= 0:
        raise ValueError("row length and spacing must be positive")
    area_m2 = row_length_m * (row_spacing_cm / 100.0)
    return int(round(counted_plants * SQM_PER_HA / area_m2))


# ---------------------------------------------------------------------------
# The plan
# ---------------------------------------------------------------------------
@dataclass
class EstablishmentPlan:
    crop: str
    target_population_per_ha: int
    potential_band: str
    row_spacing_cm: float
    in_row_spacing_cm: float
    planting_depth_cm: Tuple[float, float]
    seeds_per_station: int
    thin_at_stage: Optional[str]
    seed_rate_kg_ha: float
    seed_required_kg: Optional[float]
    field_check: str
    stand_check_row_length_m: float
    rationale: List[str] = dc_field(default_factory=list)
    warnings: List[str] = dc_field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "crop": self.crop,
            "target_population_per_ha": self.target_population_per_ha,
            "potential_band": self.potential_band,
            "row_spacing_cm": self.row_spacing_cm,
            "in_row_spacing_cm": self.in_row_spacing_cm,
            "planting_depth_cm": {
                "min": self.planting_depth_cm[0], "max": self.planting_depth_cm[1],
            },
            "seeds_per_station": self.seeds_per_station,
            "thin_at_stage": self.thin_at_stage,
            "seed_rate_kg_ha": self.seed_rate_kg_ha,
            "seed_required_kg": self.seed_required_kg,
            "field_check": self.field_check,
            "stand_check_row_length_m": self.stand_check_row_length_m,
            "rationale": self.rationale,
            "warnings": self.warnings,
        }


def _field_check_sentence(in_row_spacing_cm: float, paces: int = 4) -> str:
    """A countable check in walking units — the form advice has to take to be used."""
    distance_m = paces * PACE_M
    plants = max(1, int(round(distance_m / (in_row_spacing_cm / 100.0))))
    return (
        f"Walk {paces} paces (about {distance_m:.1f} m) along a row — "
        f"you should count roughly {plants} plants."
    )


def build_establishment_plan(
    crop: str,
    *,
    natural_region: Optional[str] = None,
    irrigated: bool = False,
    seasonal_rainfall_outlook: Optional[str] = None,
    area_hectares: Optional[float] = None,
    row_spacing_cm: Optional[float] = None,
    germination_pct: float = 90.0,
    target_population_override: Optional[int] = None,
) -> Optional[EstablishmentPlan]:
    """Build a full establishment plan, or None for an unsupported crop.

    ``row_spacing_cm`` lets a farmer pin the spacing their equipment or ridging
    already dictates; in-row spacing is then solved to hit the target population.
    That ordering matters — row width is usually a constraint, plant spacing is
    the free variable.
    """
    profile = get_establishment_profile(crop)
    if profile is None:
        return None

    band = potential_band(natural_region, irrigated, seasonal_rainfall_outlook)
    target = target_population_override or profile.population_by_potential[band]

    row = row_spacing_cm if row_spacing_cm else profile.default_row_spacing_cm
    in_row = in_row_spacing_for(target, row)

    rate = seed_rate_kg_ha(target, profile.thousand_seed_weight_g, germination_pct)
    required = round(rate * area_hectares, 1) if area_hectares else None

    rationale: List[str] = []
    if irrigated:
        rationale.append(
            "Irrigated, so water is not the limit — a denser stand converts the "
            "extra water into yield."
        )
    elif natural_region:
        rationale.append(
            f"Natural Region {natural_region} is a '{band.replace('_', ' ')}' "
            f"potential environment, which sets the target stand."
        )
    outlook = (seasonal_rainfall_outlook or "").strip().lower()
    if outlook in ("below_normal", "below", "dry"):
        rationale.append(
            "The seasonal outlook is drier than normal, so the target is stepped "
            "down — a thick stand in a dry year competes with itself for water."
        )
    elif outlook in ("above_normal", "above", "wet"):
        rationale.append(
            "The seasonal outlook is wetter than normal, so the target is stepped up."
        )
    rationale.append(
        f"{target:,} plants/ha at {row:.0f} cm rows means a plant every "
        f"{in_row:.0f} cm along the row."
    )
    if profile.notes:
        rationale.append(profile.notes)

    warnings: List[str] = []
    if row not in profile.row_spacing_options_cm:
        warnings.append(
            f"{row:.0f} cm rows are outside the usual "
            f"{'/'.join(f'{o:.0f}' for o in profile.row_spacing_options_cm)} cm "
            f"for {profile.crop} — in-row spacing has been adjusted to keep the "
            f"population on target."
        )
    if in_row < 5:
        warnings.append(
            "The in-row spacing needed is very tight; consider narrower rows instead."
        )

    return EstablishmentPlan(
        crop=profile.crop,
        target_population_per_ha=target,
        potential_band=band,
        row_spacing_cm=row,
        in_row_spacing_cm=in_row,
        planting_depth_cm=profile.planting_depth_cm,
        seeds_per_station=profile.seeds_per_station,
        thin_at_stage=profile.thin_at_stage,
        seed_rate_kg_ha=rate,
        seed_required_kg=required,
        field_check=_field_check_sentence(in_row),
        stand_check_row_length_m=stand_check_row_length_m(row),
        rationale=rationale,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# The Stand Check — verification after emergence
# ---------------------------------------------------------------------------
@dataclass
class StandAssessment:
    established_population_per_ha: int
    target_population_per_ha: int
    achieved_pct: float
    verdict: str            # 'good' | 'acceptable' | 'thin' | 'severely_thin'
    yield_ceiling_factor: float
    recommendation: str
    rationale: List[str] = dc_field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "established_population_per_ha": self.established_population_per_ha,
            "target_population_per_ha": self.target_population_per_ha,
            "achieved_pct": self.achieved_pct,
            "verdict": self.verdict,
            "yield_ceiling_factor": self.yield_ceiling_factor,
            "recommendation": self.recommendation,
            "rationale": self.rationale,
        }


def assess_stand(
    counted_plants: int,
    row_spacing_cm: float,
    row_length_m: float,
    target_population_per_ha: int,
    *,
    days_after_emergence: Optional[int] = None,
    emergence_uniformity: Optional[str] = None,
) -> StandAssessment:
    """Turn a field count into a verdict, a revised ceiling, and a decision.

    The yield-ceiling factor is deliberately *not* linear in population. A stand
    at 70% of target does not yield 70% — surviving plants compensate with
    bigger ears and more tillers. Over-penalising a thin stand would push
    farmers into replants that cost more than they recover, which is the
    documented failure mode of seed-company replant advice.
    """
    established = population_from_stand_count(counted_plants, row_spacing_cm, row_length_m)
    achieved = round(established / target_population_per_ha * 100.0, 1) if target_population_per_ha else 0.0

    rationale: List[str] = []

    # Compensation curve: full yield at/above target, then a shallow decline.
    if achieved >= 95:
        verdict, ceiling = "good", 1.0
    elif achieved >= 80:
        verdict, ceiling = "acceptable", 0.95
    elif achieved >= 65:
        verdict, ceiling = "thin", 0.87
    else:
        verdict, ceiling = "severely_thin", 0.75

    # Uneven emergence is worse than a uniformly thin stand: late plants are
    # out-competed by early neighbours and often end up barren. Extension data
    # puts a 3-week emergence spread at 20%+ yield loss on its own.
    if emergence_uniformity == "poor":
        ceiling = round(ceiling * 0.85, 3)
        rationale.append(
            "Emergence was uneven. Late plants are shaded out by their earlier "
            "neighbours and many will not carry a full head — that costs more "
            "than the plant count alone suggests."
        )
    elif emergence_uniformity == "moderate":
        ceiling = round(ceiling * 0.93, 3)
        rationale.append("Emergence was somewhat uneven, which trims the ceiling further.")

    # Gap-filling only helps while the replacements can still catch up.
    gap_fill_open = days_after_emergence is not None and days_after_emergence <= 14

    if verdict == "good":
        recommendation = "Stand is on target. No action needed — manage as planned."
    elif verdict == "acceptable":
        recommendation = (
            "Stand is slightly below target but within the range where surviving "
            "plants compensate. Do not replant."
        )
    elif verdict == "thin":
        if gap_fill_open:
            recommendation = (
                "Stand is thin. Gap-fill the worst patches now — a replacement "
                "planted within about two weeks of emergence can still catch up. "
                "A full replant is not justified at this level."
            )
        else:
            recommendation = (
                "Stand is thin and it is now too late for replacements to catch "
                "up. Accept the stand and protect what is there — the ceiling is "
                "set, so avoid over-investing in inputs this crop cannot convert."
            )
    else:
        if gap_fill_open:
            recommendation = (
                "Stand is severely thin. Compare a full replant against gap-filling: "
                "replanting costs seed and roughly two weeks of season, so it only "
                "pays if the calendar still allows a full-length crop."
            )
        else:
            recommendation = (
                "Stand is severely thin and too late to replant into. Accept the "
                "reduced ceiling and cut input spend to match it."
            )

    rationale.insert(0, (
        f"Counted {counted_plants} plants over {row_length_m:.1f} m of "
        f"{row_spacing_cm:.0f} cm rows → about {established:,} plants/ha, "
        f"{achieved:.0f}% of the {target_population_per_ha:,} target."
    ))
    if verdict in ("thin", "severely_thin"):
        rationale.append(
            "A thin stand is not a hungry stand. This field's ceiling is now set "
            "by plant numbers, not nutrition — extra nitrogen cannot buy back "
            "plants that were never established."
        )

    return StandAssessment(
        established_population_per_ha=established,
        target_population_per_ha=target_population_per_ha,
        achieved_pct=achieved,
        verdict=verdict,
        yield_ceiling_factor=ceiling,
        recommendation=recommendation,
        rationale=rationale,
    )
