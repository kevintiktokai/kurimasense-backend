"""
Establishment planning tests — the pure agronomy in services/planning/establishment.py.

Covers the spacing maths (which must round-trip exactly), the region/irrigation
→ population logic, seed rate derivation, and the Stand Check assessment.
"""

import pytest

from services.planning.establishment import (
    EstablishmentPlan,
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


# --- Crop resolution ---------------------------------------------------------
@pytest.mark.parametrize("raw,expected", [
    ("Maize", "maize"),
    ("corn", "maize"),
    ("MEALIES", "maize"),
    ("Soya Beans", "soybean"),
    ("soybeans", "soybean"),
    ("groundnut", "groundnuts"),
    ("flue-cured tobacco", "tobacco"),
    ("tobacco_flue_cured", "tobacco"),
])
def test_normalise_crop_handles_aliases_and_case(raw, expected):
    assert normalise_crop(raw) == expected


def test_unknown_crop_returns_none_rather_than_guessing():
    # A wrong population is worse than no population — the farmer acts on it.
    assert normalise_crop("dragonfruit") is None
    assert get_establishment_profile("dragonfruit") is None
    assert build_establishment_plan("dragonfruit") is None


def test_normalise_crop_handles_none_and_blank():
    assert normalise_crop(None) is None
    assert normalise_crop("") is None


# --- Spacing maths -----------------------------------------------------------
def test_in_row_spacing_matches_worked_example():
    # 44,000 plants/ha at 90 cm rows -> a plant every ~25 cm.
    assert in_row_spacing_for(44_000, 90.0) == pytest.approx(25.3, abs=0.1)


def test_spacing_and_population_round_trip():
    for pop in (30_000, 44_000, 60_000, 350_000):
        for row in (45.0, 75.0, 90.0):
            in_row = in_row_spacing_for(pop, row)
            assert population_for(row, in_row) == pytest.approx(pop, rel=0.01)


def test_narrower_rows_need_wider_in_row_spacing_for_same_population():
    wide = in_row_spacing_for(44_000, 90.0)
    narrow = in_row_spacing_for(44_000, 75.0)
    assert narrow > wide


@pytest.mark.parametrize("pop,row", [(0, 90.0), (-1, 90.0), (44_000, 0), (44_000, -5)])
def test_spacing_rejects_non_positive_inputs(pop, row):
    with pytest.raises(ValueError):
        in_row_spacing_for(pop, row)


# --- Potential band ----------------------------------------------------------
def test_region_drives_potential_band():
    assert potential_band("I") == "high"
    assert potential_band("IIb") == "moderate"
    assert potential_band("IV") == "low"
    assert potential_band("V") == "very_low"


def test_irrigation_overrides_region():
    # Under a pivot the rainfall constraint is gone, so Region V behaves like
    # the best land on the farm.
    assert potential_band("V", irrigated=True) == "very_high"


def test_dry_outlook_steps_the_band_down_and_wet_steps_up():
    assert potential_band("IIb", seasonal_rainfall_outlook="below_normal") == "low"
    assert potential_band("IIb", seasonal_rainfall_outlook="above_normal") == "high"


def test_band_stepping_clamps_at_the_extremes():
    assert potential_band("V", seasonal_rainfall_outlook="dry") == "very_low"
    assert potential_band("V", irrigated=True, seasonal_rainfall_outlook="wet") == "very_high"


def test_unknown_region_falls_back_to_moderate():
    assert potential_band("Narnia") == "moderate"
    assert potential_band(None) == "moderate"


# --- Seed rate ---------------------------------------------------------------
def test_seed_rate_inflates_for_germination_and_field_loss():
    # Perfect germination + no loss is the floor; real conditions need more.
    perfect = seed_rate_kg_ha(44_000, 330.0, germination_pct=100, field_loss_pct=0)
    realistic = seed_rate_kg_ha(44_000, 330.0, germination_pct=90, field_loss_pct=10)
    assert realistic > perfect


def test_seed_rate_scales_with_seed_size():
    small = seed_rate_kg_ha(44_000, 250.0)
    large = seed_rate_kg_ha(44_000, 400.0)
    assert large > small


@pytest.mark.parametrize("germ,loss", [(0, 10), (-5, 10), (101, 10), (90, 100), (90, -1)])
def test_seed_rate_rejects_out_of_range_percentages(germ, loss):
    with pytest.raises(ValueError):
        seed_rate_kg_ha(44_000, 330.0, germination_pct=germ, field_loss_pct=loss)


# --- Stand check geometry ----------------------------------------------------
def test_stand_check_row_length_sweeps_one_thousandth_of_a_hectare():
    # 10 m^2 at 90 cm rows -> 11.11 m of row.
    assert stand_check_row_length_m(90.0) == pytest.approx(11.11, abs=0.01)


def test_stand_count_inverts_the_sample_geometry():
    row, length = 90.0, stand_check_row_length_m(90.0)
    # A perfectly on-target count should read back as the target.
    on_target = round(44_000 / 1000)
    assert population_from_stand_count(on_target, row, length) == pytest.approx(44_000, rel=0.02)


def test_stand_count_rejects_bad_geometry():
    with pytest.raises(ValueError):
        population_from_stand_count(-1, 90.0, 11.0)
    with pytest.raises(ValueError):
        population_from_stand_count(40, 90.0, 0)


# --- Full plan ---------------------------------------------------------------
def test_maize_plan_in_region_iib_is_coherent():
    plan = build_establishment_plan("Maize", natural_region="IIb", area_hectares=2.4)
    assert isinstance(plan, EstablishmentPlan)
    assert plan.crop == "maize"
    assert plan.target_population_per_ha == 44_000
    assert plan.row_spacing_cm == 90.0
    assert plan.in_row_spacing_cm == pytest.approx(25.3, abs=0.1)
    # Spacing must actually deliver the stated population.
    assert population_for(plan.row_spacing_cm, plan.in_row_spacing_cm) == pytest.approx(
        plan.target_population_per_ha, rel=0.01
    )
    # Seed for the whole field, not just a per-hectare rate.
    assert plan.seed_required_kg == pytest.approx(plan.seed_rate_kg_ha * 2.4, abs=0.2)
    # Maize is stationed two-up and thinned.
    assert plan.seeds_per_station == 2
    assert plan.thin_at_stage == "V3"


def test_plan_always_carries_a_countable_field_check():
    plan = build_establishment_plan("Maize", natural_region="IIb")
    assert "paces" in plan.field_check
    # The check must name a real number of plants to count.
    assert any(ch.isdigit() for ch in plan.field_check)


def test_irrigated_field_gets_a_denser_target_than_dryland():
    dry = build_establishment_plan("Maize", natural_region="IV")
    irrigated = build_establishment_plan("Maize", natural_region="IV", irrigated=True)
    assert irrigated.target_population_per_ha > dry.target_population_per_ha


def test_custom_row_spacing_is_honoured_and_in_row_compensates():
    plan = build_establishment_plan("Maize", natural_region="IIb", row_spacing_cm=75.0)
    assert plan.row_spacing_cm == 75.0
    assert population_for(75.0, plan.in_row_spacing_cm) == pytest.approx(44_000, rel=0.01)


def test_unusual_row_spacing_warns_but_still_plans():
    plan = build_establishment_plan("Maize", natural_region="IIb", row_spacing_cm=150.0)
    assert plan is not None
    assert any("outside the usual" in w for w in plan.warnings)


def test_override_wins_over_the_region_default():
    plan = build_establishment_plan(
        "Maize", natural_region="IIb", target_population_override=52_000
    )
    assert plan.target_population_per_ha == 52_000


def test_plan_explains_itself():
    # Rationale is not decoration: unexplainable advice reads as a sales pitch.
    plan = build_establishment_plan("Maize", natural_region="IV", irrigated=True)
    assert plan.rationale
    assert any("Irrigated" in r for r in plan.rationale)


def test_plan_serialises_for_the_api():
    d = build_establishment_plan("Maize", natural_region="IIb", area_hectares=1.0).to_dict()
    assert d["target_population_per_ha"] == 44_000
    assert d["planting_depth_cm"]["min"] == 5.0
    assert "field_check" in d


# --- Stand assessment --------------------------------------------------------
def _count_for(pop, row=90.0):
    """Plants to count over the standard sample to represent ``pop`` plants/ha."""
    return round(pop / 1000)


def test_on_target_stand_reads_good_with_no_yield_penalty():
    a = assess_stand(_count_for(44_000), 90.0, stand_check_row_length_m(90.0), 44_000)
    assert a.verdict == "good"
    assert a.yield_ceiling_factor == 1.0
    assert "on target" in a.recommendation.lower()


def test_slightly_below_target_is_acceptable_and_does_not_trigger_replant():
    a = assess_stand(_count_for(38_000), 90.0, stand_check_row_length_m(90.0), 44_000)
    assert a.verdict == "acceptable"
    assert "not replant" in a.recommendation.lower()


def test_thin_stand_within_the_window_recommends_gap_filling():
    a = assess_stand(
        _count_for(31_000), 90.0, stand_check_row_length_m(90.0), 44_000,
        days_after_emergence=8,
    )
    assert a.verdict == "thin"
    assert "gap-fill" in a.recommendation.lower()


def test_thin_stand_past_the_window_says_accept_and_stop_spending():
    a = assess_stand(
        _count_for(31_000), 90.0, stand_check_row_length_m(90.0), 44_000,
        days_after_emergence=30,
    )
    assert a.verdict == "thin"
    assert "too late" in a.recommendation.lower()
    # The key agronomic point: don't feed a stand that can't convert it.
    assert any("nitrogen cannot buy back" in r for r in a.rationale)


def test_ceiling_is_not_linear_in_population():
    # A 70% stand must not be modelled as 70% yield — surviving plants
    # compensate, and over-penalising pushes farmers into losing replants.
    a = assess_stand(_count_for(30_800), 90.0, stand_check_row_length_m(90.0), 44_000)
    assert a.achieved_pct == pytest.approx(70, abs=2)
    assert a.yield_ceiling_factor > 0.8


def test_poor_emergence_uniformity_costs_more_than_the_count_alone():
    even = assess_stand(
        _count_for(38_000), 90.0, stand_check_row_length_m(90.0), 44_000,
        emergence_uniformity="uniform",
    )
    uneven = assess_stand(
        _count_for(38_000), 90.0, stand_check_row_length_m(90.0), 44_000,
        emergence_uniformity="poor",
    )
    assert uneven.yield_ceiling_factor < even.yield_ceiling_factor
    assert any("shaded out" in r for r in uneven.rationale)


def test_severely_thin_stand_is_flagged():
    a = assess_stand(
        _count_for(20_000), 90.0, stand_check_row_length_m(90.0), 44_000,
        days_after_emergence=5,
    )
    assert a.verdict == "severely_thin"
    assert a.yield_ceiling_factor < 0.85


def test_assessment_serialises_and_reports_the_measurement():
    a = assess_stand(_count_for(40_000), 90.0, stand_check_row_length_m(90.0), 44_000)
    d = a.to_dict()
    assert d["target_population_per_ha"] == 44_000
    assert d["rationale"]
    # First line is the raw measurement, so the farmer can check our arithmetic.
    assert "Counted" in d["rationale"][0]
