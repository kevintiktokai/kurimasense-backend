"""
Pre-plant and in-season planning services.

Pure agronomy modules (no DB, no network) that turn a farmer's intent — crop,
place, date — into executable field instructions:

* :mod:`.establishment` — target plant population, row/in-row spacing, seed
  quantity, the field check, and the post-emergence Stand Check assessment.
* :mod:`.fertiliser` — a crop profile's fertiliser schedule rendered as a
  dated, quantified, soil-adjusted programme.
"""

from .establishment import (
    CropEstablishment,
    EstablishmentPlan,
    StandAssessment,
    assess_stand,
    build_establishment_plan,
    get_establishment_profile,
    in_row_spacing_for,
    normalise_crop,
    population_for,
    population_from_stand_count,
    potential_band,
    seed_rate_kg_ha,
    stand_check_row_length_m,
)
from .fertiliser import (
    FertiliserProgramme,
    FertiliserStep,
    build_fertiliser_programme,
    parse_days_after_planting,
    parse_rate,
)

__all__ = [
    "CropEstablishment",
    "EstablishmentPlan",
    "StandAssessment",
    "assess_stand",
    "build_establishment_plan",
    "get_establishment_profile",
    "in_row_spacing_for",
    "normalise_crop",
    "population_for",
    "population_from_stand_count",
    "potential_band",
    "seed_rate_kg_ha",
    "stand_check_row_length_m",
    "FertiliserProgramme",
    "FertiliserStep",
    "build_fertiliser_programme",
    "parse_days_after_planting",
    "parse_rate",
]
