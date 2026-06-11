"""
Validation suite for crop_profiles/tobacco_flue_cured/tobacco_math.py (Phase 2).

Covers: known-input scenarios, edge cases, range invariants, consistency/
monotonicity invariants, and side-marketing detection. Run:

    pytest tests/test_tobacco_math.py -v
"""

from __future__ import annotations

import os
import sys
from datetime import date

import pytest

# Make the repo root importable when pytest is run from elsewhere.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crop_profiles.tobacco_flue_cured import tobacco_math as tm  # noqa: E402

TP = date(2024, 10, 1)  # canonical transplant date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _indices(ndvi=0.7, evi=0.55, ndre=0.4, ndmi=0.3, n=6):
    return [{"NDVI": ndvi, "EVI": evi, "NDRE": ndre, "NDMI": ndmi} for _ in range(n)]


def _full_mgmt(**over):
    base = dict(
        plant_population_per_ha=16000,
        basal_fertilizer_rate_kg_ha=800.0,
        basal_fertilizer_product="Compound C",
        topdressing_schedule_completion=1.0,
        topping_days_after_transplant=62,
        spray_applications_count=6,
        sucker_control_applied=True,
        variety_code="K326",
        stage="REPRODUCTIVE",
    )
    base.update(over)
    return base


# ===========================================================================
# 1. KNOWN-INPUT SCENARIOS  (bands hard-coded from Phase 1 research)
# ===========================================================================


def test_scenario_healthy_k326_region_ii_strong():
    """Healthy K326, Region II, reproductive, near-optimal mgmt -> 75-90 (Strong/Thriving)."""
    idx = _indices(ndvi=0.74, evi=0.58, ndre=0.46, ndmi=0.30, n=6)
    sat = tm.compute_satellite_component(idx, "REPRODUCTIVE", "K326", "II")
    mgt = tm.compute_management_component(
        16000, 800.0, "Compound C", 0.9, 65, 6, True, "K326", "REPRODUCTIVE"
    )
    env = tm.compute_environmental_component(
        {"ESTABLISHMENT": 45, "VEGETATIVE": 165, "REPRODUCTIVE": 90}, {}, 0, "II", "REPRODUCTIVE"
    )
    out = tm.compute_kurima_score(sat, mgt, env, "REPRODUCTIVE")
    assert 75 <= out["score"] <= 90, out
    assert out["label"] in {"Strong", "Thriving"}


def test_scenario_dryland_region_iii_poor_drought_distressed():
    """Dryland Region III, poor fertilisation, drought -> 20-45 (Distressed/Stressed)."""
    idx = _indices(ndvi=0.50, evi=0.35, ndre=0.27, ndmi=0.08, n=4)
    sat = tm.compute_satellite_component(idx, "REPRODUCTIVE", "KRK26R", "III")
    mgt = tm.compute_management_component(
        10000, None, None, 0.2, 82, 1, False, "KRK26R", "REPRODUCTIVE"
    )
    env = tm.compute_environmental_component(
        {"ESTABLISHMENT": 20, "VEGETATIVE": 60, "REPRODUCTIVE": 25},
        {"VEGETATIVE": 15, "REPRODUCTIVE": 12},
        2,
        "III",
        "REPRODUCTIVE",
    )
    out = tm.compute_kurima_score(sat, mgt, env, "REPRODUCTIVE")
    assert 20 <= out["score"] <= 45, out
    assert out["label"] in {"Stressed", "Distressed"}


def test_scenario_optimal_region_v_capped_adequate():
    """Optimal management in marginal Region V -> 50-70 (Adequate) due to region limit."""
    # Region-limited (heat-constrained) canopy is genuinely thinner even when well managed.
    idx = _indices(ndvi=0.62, evi=0.46, ndre=0.36, ndmi=0.22, n=6)
    sat = tm.compute_satellite_component(idx, "REPRODUCTIVE", "T75", "V")
    mgt = tm.compute_management_component(
        16000, 800.0, "Compound C", 1.0, 62, 6, True, "T75", "REPRODUCTIVE"
    )
    env = tm.compute_environmental_component(
        {"ESTABLISHMENT": 45, "VEGETATIVE": 165, "REPRODUCTIVE": 90}, {}, 1, "V", "REPRODUCTIVE"
    )
    out = tm.compute_kurima_score(sat, mgt, env, "REPRODUCTIVE")
    assert 50 <= out["score"] <= 70, out
    assert out["label"] == "Adequate"


def test_project_yield_healthy_region_ii_reasonable():
    """Optimal K326 in NR II projects a strong, in-range cured yield under the ceiling."""
    out = tm.project_yield(
        "K326", "II", TP, date(2024, 12, 3), 16000, _indices(0.78, 0.62, 0.50, 0.36),
        _full_mgmt(), {"rainfall_mm_per_stage": {"ESTABLISHMENT": 45, "VEGETATIVE": 170, "REPRODUCTIVE": 95}},
    )
    assert 2500 <= out["projected_yield_kg_ha"] <= 4500
    ci = out["confidence_interval"]
    assert ci["low"] < out["projected_yield_kg_ha"] < ci["high"]


# ===========================================================================
# 2. EDGE CASES
# ===========================================================================


def test_pre_transplant_sentinel():
    assert tm.detect_stage("K326", TP, date(2024, 9, 1)) == "PRE_TRANSPLANT"


def test_post_harvest_sentinel():
    assert tm.detect_stage("K326", TP, date(2025, 6, 1)) == "POST_HARVEST"


def test_unknown_variety_raises_detect_stage():
    with pytest.raises(tm.UnknownVarietyError):
        tm.detect_stage("NOT_A_VARIETY", TP, date(2024, 11, 1))


def test_unknown_variety_raises_components():
    with pytest.raises(tm.UnknownVarietyError):
        tm.compute_satellite_component(_indices(), "VEGETATIVE", "ZZZ999", "II")
    with pytest.raises(tm.UnknownVarietyError):
        tm.compute_management_component(16000, 800, "Compound C", 1.0, 62, 6, True, "ZZZ999", "VEGETATIVE")


def test_empty_indices_history_neutral_and_low_confidence():
    sat = tm.compute_satellite_component([], "VEGETATIVE", "K326", "II")
    assert sat == pytest.approx(0.5)
    _, band = tm.compute_confidence([], progress=0.1)
    assert band == "low"


def test_all_zero_indices_low_satellite_no_div_zero():
    idx = _indices(ndvi=0.0, evi=0.0, ndre=0.0, ndmi=0.0)
    sat = tm.compute_satellite_component(idx, "VEGETATIVE", "K326", "II")
    assert 0.0 <= sat <= 0.2  # low but finite, no exception


def test_plant_population_edge_values():
    variety = tm.get_variety("K326")
    assert tm._population_score(0, variety) == 0.0
    assert tm._population_score(-500, variety) == 0.0
    # absurdly high handled gracefully, stays within [0.5, 1.0]
    high = tm._population_score(200000, variety)
    assert 0.5 <= high <= 1.0
    # None -> neutral
    assert tm._population_score(None, variety) == pytest.approx(0.70)


def test_management_handles_all_none_optional_inputs():
    val = tm.compute_management_component(None, None, None, None, None, None, None, "K326", "ESTABLISHMENT")
    assert 0.0 <= val <= 1.0


def test_region_iia_iib_normalise():
    # IIa / IIb fold onto II without error.
    env_a = tm.compute_environmental_component({"ESTABLISHMENT": 45}, {}, 0, "IIa", "ESTABLISHMENT")
    env_b = tm.compute_environmental_component({"ESTABLISHMENT": 45}, {}, 0, "IIb", "ESTABLISHMENT")
    assert env_a == env_b


# ===========================================================================
# 3. RANGE INVARIANTS
# ===========================================================================


@pytest.mark.parametrize("stage", list(tm.STAGES))
def test_components_in_unit_interval(stage):
    idx = _indices(0.6, 0.45, 0.35, 0.25)
    sat = tm.compute_satellite_component(idx, stage, "K326", "II")
    mgt = tm.compute_management_component(15000, 700, "Compound C", 0.8, 60, 5, True, "K326", stage)
    env = tm.compute_environmental_component({"VEGETATIVE": 100}, {"VEGETATIVE": 3}, 1, "III", stage)
    for v in (sat, mgt, env):
        assert 0.0 <= v <= 1.0


def test_kurima_score_bounds_extremes():
    for sat in (0.0, 0.5, 1.0):
        for mgt in (0.0, 0.5, 1.0):
            for env in (0.0, 0.5, 1.0):
                for stage in tm.STAGES:
                    out = tm.compute_kurima_score(sat, mgt, env, stage)
                    assert 0 <= out["score"] <= 100
                    assert out["label"] in {
                        "Thriving", "Strong", "Adequate", "Stressed", "Distressed", "Critical",
                    }
                    assert out["color"].startswith("#")


def test_yield_projection_positive_and_ordered():
    out = tm.project_yield(
        "KRK26R", "IV", TP, date(2024, 12, 20), 12000, _indices(0.3, 0.25, 0.2, 0.05),
        _full_mgmt(variety_code="KRK26R", stage="REAPING"),
        {"rainfall_mm_per_stage": {"VEGETATIVE": 40}, "drought_days_per_stage": {"VEGETATIVE": 20}},
    )
    assert out["projected_yield_kg_ha"] > 0
    ci = out["confidence_interval"]
    assert ci["low"] < out["projected_yield_kg_ha"] < ci["high"]


def test_factors_within_mandated_window():
    out = tm.project_yield(
        "K326", "II", TP, date(2024, 12, 3), 16000, _indices(0.8, 0.65, 0.52, 0.38),
        _full_mgmt(), {"rainfall_mm_per_stage": {"ESTABLISHMENT": 45, "VEGETATIVE": 170, "REPRODUCTIVE": 95}},
    )
    for name, val in out["contributing_factors"].items():
        if name.endswith("_factor") or name.endswith("_calibration"):
            assert 0.0 <= val <= 1.5, (name, val)


# ===========================================================================
# 4. CONSISTENCY / MONOTONICITY INVARIANTS
# ===========================================================================


def test_determinism_100_runs():
    idx = _indices(0.7, 0.55, 0.42, 0.3)
    args = ("K326", "II", TP, date(2024, 12, 3), 16000, idx, _full_mgmt(),
            {"rainfall_mm_per_stage": {"VEGETATIVE": 150, "REPRODUCTIVE": 90}})
    first = tm.project_yield(*args)
    for _ in range(100):
        assert tm.project_yield(*args) == first


def test_monotonic_better_management_higher_score():
    poor = tm.compute_management_component(9000, None, None, 0.1, 95, 0, False, "K326", "REPRODUCTIVE")
    good = tm.compute_management_component(16000, 800, "Compound C", 1.0, 62, 6, True, "K326", "REPRODUCTIVE")
    assert good > poor


def test_monotonic_better_satellite_higher_component():
    low = tm.compute_satellite_component(_indices(0.35, 0.25, 0.2, 0.1), "VEGETATIVE", "K326", "II")
    high = tm.compute_satellite_component(_indices(0.78, 0.62, 0.48, 0.38), "VEGETATIVE", "K326", "II")
    assert high > low


def test_monotonic_worse_rainfall_lower_environment():
    wet = tm.compute_environmental_component(
        {"ESTABLISHMENT": 45, "VEGETATIVE": 170}, {}, 0, "II", "VEGETATIVE"
    )
    dry = tm.compute_environmental_component(
        {"ESTABLISHMENT": 10, "VEGETATIVE": 40}, {}, 0, "II", "VEGETATIVE"
    )
    assert wet > dry


def test_monotonic_more_drought_lower_environment():
    none = tm.compute_environmental_component({"VEGETATIVE": 120}, {}, 0, "II", "VEGETATIVE")
    some = tm.compute_environmental_component({"VEGETATIVE": 120}, {"VEGETATIVE": 25}, 0, "II", "VEGETATIVE")
    assert none > some


def test_kurima_score_monotonic_in_components():
    base = tm.compute_kurima_score(0.5, 0.5, 0.5, "VEGETATIVE")["score"]
    for better in ((0.7, 0.5, 0.5), (0.5, 0.7, 0.5), (0.5, 0.5, 0.7)):
        assert tm.compute_kurima_score(*better, "VEGETATIVE")["score"] >= base


# ===========================================================================
# 5. SIDE-MARKETING DETECTION
# ===========================================================================


def test_side_marketing_delivered_equals_predicted_low():
    out = tm.detect_side_marketing_signal(2500, 2500, 300, "high")
    assert out["flag_severity"] == "LOW"


def test_side_marketing_high_flag_with_confidence():
    # delivered = predicted - 2.5 * std_dev, high confidence -> HIGH
    out = tm.detect_side_marketing_signal(2500 - 2.5 * 300, 2500, 300, "high")
    assert out["flag_severity"] == "HIGH"
    assert out["deviation_std_devs"] == pytest.approx(2.5, abs=0.01)


def test_side_marketing_high_deviation_low_confidence_not_high():
    out = tm.detect_side_marketing_signal(2500 - 2.5 * 300, 2500, 300, "low")
    assert out["flag_severity"] != "HIGH"
    assert out["flag_severity"] == "MEDIUM"


def test_side_marketing_medium_band():
    out = tm.detect_side_marketing_signal(2500 - 1.3 * 300, 2500, 300, "medium")
    assert out["flag_severity"] == "MEDIUM"


def test_side_marketing_std_dev_floor_no_div_zero():
    # std_dev below floor (150) must not blow up; tiny deviation still LOW.
    out = tm.detect_side_marketing_signal(2490, 2500, 0.0, "high")
    assert out["flag_severity"] == "LOW"
    assert isinstance(out["deviation_std_devs"], float)


# ===========================================================================
# 6. DRIVER LOGIC  (>=12 branches exercised)
# ===========================================================================


def test_driver_hail():
    d, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.4, "management": 0.8, "environmental": 0.8},
        {"ndvi_abrupt_drop": 0.25}, "REPRODUCTIVE",
    )
    assert "hail" in d.lower() or "acute" in d.lower()


def test_driver_bacterial_wilt():
    d, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.35, "management": 0.8, "environmental": 0.7},
        {"spatial_patchiness": "high"}, "REPRODUCTIVE",
    )
    assert "wilt" in d.lower()


def test_driver_waterlogging():
    d, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.4, "management": 0.8, "environmental": 0.5, "waterlogging": True},
        {}, "VEGETATIVE",
    )
    assert "waterlog" in d.lower()


def test_driver_drought():
    d, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.45, "management": 0.7, "environmental": 0.45},
        {"ndmi_trend": -0.08}, "VEGETATIVE",
    )
    assert "water stress" in d.lower() or "drought" in d.lower()


def test_driver_nitrogen_deficiency():
    d, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.5, "management": 0.5, "environmental": 0.7, "fert_score": 0.3},
        {"ndre_trend": -0.05}, "VEGETATIVE",
    )
    assert "nitrogen" in d.lower()


def test_driver_late_topping():
    d, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.6, "management": 0.6, "environmental": 0.7, "topping_score": 0.3},
        {"ndvi_trend": 0.01}, "TOPPING_RIPENING",
    )
    assert "ripening" in d.lower() or "topping" in d.lower()


def test_driver_sucker_breakthrough():
    d, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.6, "management": 0.6, "environmental": 0.7, "sucker_score": 0.4, "topping_score": 0.9},
        {"ndvi_trend": 0.05}, "REAPING",
    )
    assert "sucker" in d.lower()


def test_driver_low_population():
    d, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.6, "management": 0.6, "environmental": 0.7, "pop_score": 0.3, "topping_score": 0.9},
        {}, "ESTABLISHMENT",
    )
    assert "stand" in d.lower() or "population" in d.lower()


def test_driver_poor_establishment():
    d, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.4, "management": 0.7, "environmental": 0.6, "pop_score": 0.9, "topping_score": 0.9},
        {}, "ESTABLISHMENT",
    )
    assert "establish" in d.lower()


def test_driver_blue_mould_and_angular():
    d_blue, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.5, "management": 0.7, "environmental": 0.7, "disease_type": "blue_mould"},
        {"ndvi_trend": -0.03}, "VEGETATIVE",
    )
    assert "blue mould" in d_blue.lower()
    d_ang, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.5, "management": 0.7, "environmental": 0.7, "disease_type": "angular_leaf_spot"},
        {"ndvi_trend": -0.03}, "REPRODUCTIVE",
    )
    assert "angular" in d_ang.lower()


def test_driver_general_disease():
    d, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.5, "management": 0.7, "environmental": 0.4},
        {"ndvi_trend": -0.04}, "REAPING",
    )
    assert "disease" in d.lower() or "pest" in d.lower()


def test_driver_management_gap_and_environmental_and_ontrack():
    gap, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.6, "management": 0.3, "environmental": 0.7}, {}, "VEGETATIVE"
    )
    assert "management" in gap.lower()
    env, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.6, "management": 0.7, "environmental": 0.3}, {}, "VEGETATIVE"
    )
    assert "environmental" in env.lower()
    ok, _, _ = tm.interpret_primary_driver(
        {"satellite": 0.8, "management": 0.85, "environmental": 0.85}, {}, "VEGETATIVE"
    )
    assert "track" in ok.lower()


# ===========================================================================
# 7. CONFIDENCE BANDS
# ===========================================================================


def test_confidence_increases_with_data():
    sparse, b_sparse = tm.compute_confidence(_indices(n=1), progress=0.2)
    rich, b_rich = tm.compute_confidence(_indices(n=8), progress=0.8)
    assert rich > sparse
    assert b_rich == "high"


def test_confidence_band_values_valid():
    for n, prog in ((0, 0.05), (2, 0.3), (8, 0.9)):
        _, band = tm.compute_confidence(_indices(n=n), progress=prog)
        assert band in {"high", "medium", "low"}


# ===========================================================================
# 8. OUTPUT STRUCTURE
# ===========================================================================


def test_kurima_score_output_structure():
    out = tm.compute_kurima_score(0.7, 0.6, 0.65, "VEGETATIVE", as_of_date="2024-12-01")
    for key in (
        "score", "label", "color", "component_breakdown", "primary_driver",
        "likely_cause", "recommended_action", "yield_implication",
        "confidence_band", "stage", "as_of_date",
    ):
        assert key in out
    assert set(out["component_breakdown"]) == {"satellite", "management", "environmental"}
    assert out["as_of_date"] == "2024-12-01"


def test_nr_baselines_best_practice_within_sanity_band():
    """Phase 2 gap-(b) amendment: every region's best_practice sits in a sane band
    and a separate genetic_ceiling_kg_ha (>= best_practice) is present."""
    regions = tm.NATURAL_REGION_BASELINES["natural_regions"]
    for code, data in regions.items():
        yb = data["yield_baselines_kg_ha"]
        assert 1500 <= yb["best_practice"] <= 3500, (code, yb)
        assert yb["genetic_ceiling_kg_ha"] >= yb["best_practice"], (code, yb)
    # NR II specifically must be inside the audit's 2,500-3,500 sanity band.
    assert 2500 <= regions["II"]["yield_baselines_kg_ha"]["best_practice"] <= 3500


def test_project_yield_clamps_to_genetic_ceiling_not_best_practice():
    """A maximal crop may exceed operational best_practice but never the genetic ceiling."""
    yb = tm.NATURAL_REGION_BASELINES["natural_regions"]["II"]["yield_baselines_kg_ha"]
    out = tm.project_yield(
        "K RK66", "II", TP, date(2024, 12, 3), 16000,
        _indices(0.85, 0.70, 0.54, 0.40),
        _full_mgmt(variety_code="K RK66"),
        {"rainfall_mm_per_stage": {"ESTABLISHMENT": 45, "VEGETATIVE": 175, "REPRODUCTIVE": 95}},
    )
    assert out["projected_yield_kg_ha"] <= yb["genetic_ceiling_kg_ha"]


def test_project_yield_output_structure():
    out = tm.project_yield(
        "K326", "II", TP, date(2024, 12, 3), 16000, _indices(), _full_mgmt(),
        {"rainfall_mm_per_stage": {"VEGETATIVE": 150}},
    )
    for key in (
        "projected_yield_kg_ha", "confidence_interval", "confidence_band",
        "contributing_factors", "stage", "kurima_score",
    ):
        assert key in out
    assert set(out["confidence_interval"]) == {"low", "high"}
