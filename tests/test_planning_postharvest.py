"""
Post-harvest plan tests — services/planning/postharvest.py.

The moisture parsing carries the weight. The crop profiles quote a harvest range
and a storage ceiling in the same sentence ("harvest at 20-25%, shell-dry to
<13%"), so picking the wrong number tells a farmer to bag grain that will mould.
"""

import pytest

from crop_profiles import get_crop_profile_or_generic
from services.planning.postharvest import (
    DEFAULT_SAFE_MOISTURE_PCT,
    FUMIGATION_MAX_MOISTURE_PCT,
    build_post_harvest_plan,
    extract_moisture_targets,
    safe_storage_moisture,
)

MAIZE = get_crop_profile_or_generic("Maize")
GROUNDNUTS = get_crop_profile_or_generic("Groundnuts")


def step(plan, key):
    return next((s for s in plan.steps if s.key == key), None)


# --- Moisture parsing --------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("Harvest at 20-25% kernel moisture; shell-dry to <13% for storage.", [20.0, 25.0, 13.0]),
    ("Dry kernels to <8% for safe storage.", [8.0]),
    # The temperature in the same sentence must NOT be read as a moisture
    # figure — mistaking 25°C for 25% moisture would recommend storing wet grain.
    ("Cool (<25°C), dry (<13% moisture), ventilated.", [13.0]),
    ("12.5 % moisture", [12.5]),
])
def test_every_percentage_is_extracted(text, expected):
    assert extract_moisture_targets(text) == expected


def test_temperatures_are_never_mistaken_for_moisture():
    assert extract_moisture_targets("Store below 25°C and 30°C") == []


def test_parsing_survives_prose_without_numbers():
    assert extract_moisture_targets("Store somewhere cool and dry") == []
    assert extract_moisture_targets(None) == []
    assert extract_moisture_targets("") == []


def test_the_storage_ceiling_wins_not_the_harvest_range():
    # "Harvest at 20-25%, shell-dry to <13%" — bagging at 20% would mould.
    target = safe_storage_moisture(
        "Harvest at 20-25% kernel moisture for mechanical; shell-dry to <13% for storage.",
        "Cool (<25°C), dry (<13% moisture), ventilated.",
    )
    assert target == 13.0


def test_implausible_percentages_are_ignored():
    # Temperature, protein and oil percentages share the same prose.
    target = safe_storage_moisture(
        "Oil content typically 18-22%; protein 38-42%.",
        "Cool, dry, <12% moisture.",
    )
    assert target == 12.0


def test_no_recorded_moisture_yields_none_rather_than_a_guess():
    assert safe_storage_moisture(None, None) is None
    assert safe_storage_moisture("", "") is None


# --- Plan shape --------------------------------------------------------------

def test_maize_plan_reads_the_profiles_own_numbers():
    plan = build_post_harvest_plan(MAIZE)
    assert plan.crop == "Maize"
    assert plan.storage_moisture_pct == 13.0
    assert step(plan, "drying").target_moisture_pct == 13.0


def test_groundnuts_need_a_much_drier_store_than_maize():
    # 8% vs 13% — a single generic number would be wrong for one of them.
    assert build_post_harvest_plan(GROUNDNUTS).storage_moisture_pct == 8.0
    assert build_post_harvest_plan(MAIZE).storage_moisture_pct == 13.0


def test_the_plan_runs_in_operational_order():
    plan = build_post_harvest_plan(MAIZE)
    keys = [s.key for s in plan.steps]
    assert keys.index("harvest_timing") < keys.index("drying")
    assert keys.index("drying") < keys.index("storage")
    assert keys[-1] == "monitoring"
    assert [s.order for s in plan.steps] == sorted(s.order for s in plan.steps)


def test_drying_and_storage_are_always_marked_critical():
    plan = build_post_harvest_plan(MAIZE)
    assert step(plan, "drying").critical is True
    assert step(plan, "storage").critical is True


def test_monitoring_is_included_even_though_no_profile_mentions_it():
    # An infestation caught in month one costs a re-treatment; found at selling
    # time it has already eaten the margin.
    plan = build_post_harvest_plan(MAIZE)
    assert step(plan, "monitoring") is not None


def test_storage_step_names_the_larger_grain_borer_risk():
    why = step(build_post_harvest_plan(MAIZE), "storage").why
    assert "larger grain borer" in why
    assert "20-30%" in why


def test_every_step_explains_itself():
    for s in build_post_harvest_plan(MAIZE).steps:
        assert s.detail, f"{s.key} has no detail"
        assert s.why, f"{s.key} has no explanation"


# --- Aflatoxin ---------------------------------------------------------------

def test_aflatoxin_crops_are_flagged_as_a_safety_issue():
    plan = build_post_harvest_plan(MAIZE)
    assert plan.aflatoxin_risk is True
    joined = " ".join(plan.warnings)
    assert "not removed by cooking" in joined
    # Grading becomes critical rather than cosmetic when safety is involved.
    assert step(plan, "grading").critical is True


def test_a_crop_without_aflatoxin_mentions_is_not_flagged():
    class Bare:
        crop_name = "Wheat"
        harvest_moisture = "Harvest at 14%."
        storage_conditions = "Cool and dry, <12% moisture."
        post_harvest_notes = "Clean before storage."

    plan = build_post_harvest_plan(Bare())
    assert plan.aflatoxin_risk is False
    assert step(plan, "grading").critical is False


# --- Fumigation --------------------------------------------------------------

def test_maize_is_dry_enough_for_fumigants():
    plan = build_post_harvest_plan(MAIZE)
    assert plan.storage_moisture_pct <= FUMIGATION_MAX_MOISTURE_PCT
    assert plan.fumigation_possible is True


def test_very_dry_crops_are_steered_to_hermetic_storage():
    # Groundnuts store at 8% — below what fumigants need to work.
    plan = build_post_harvest_plan(GROUNDNUTS)
    assert plan.fumigation_possible is True
    assert plan.storage_moisture_pct == 8.0


# --- Degradation -------------------------------------------------------------

def test_a_crop_with_no_post_harvest_knowledge_says_so():
    class Bare:
        crop_name = "Mystery"
        harvest_moisture = ""
        storage_conditions = ""
        post_harvest_notes = ""

    plan = build_post_harvest_plan(Bare())
    assert plan.steps == []
    assert any("No post-harvest guidance" in w for w in plan.warnings)


def test_a_partial_profile_still_produces_a_usable_plan():
    class Partial:
        crop_name = "Sesame"
        harvest_moisture = ""
        storage_conditions = ""
        post_harvest_notes = "Sort before bagging."

    plan = build_post_harvest_plan(Partial())
    # Falls back to the general guideline and says that it has.
    assert step(plan, "drying").target_moisture_pct == DEFAULT_SAFE_MOISTURE_PCT
    assert any("general" in w for w in plan.warnings)


def test_plan_serialises_for_the_api():
    d = build_post_harvest_plan(MAIZE).to_dict()
    assert d["storage_moisture_pct"] == 13.0
    assert d["aflatoxin_risk"] is True
    assert all("why" in s for s in d["steps"])
