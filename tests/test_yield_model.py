"""
Unit tests for yield_model.py — focused on the new index-ensemble logic.

Run:
    cd backend
    python -m pytest tests/test_yield_model.py -v
"""
from __future__ import annotations

import os
import sys
from datetime import date
from typing import Any, Dict, List

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crop_constants import (  # noqa: E402
    CROP_INDEX_WEIGHTS,
    DEFAULT_INDEX_WEIGHTS,
    INDEX_NAMES,
    get_index_weights,
)
import yield_model  # noqa: E402
from yield_model import (  # noqa: E402
    _is_optical_sparse,
    _stage_bucket,
    calculate_index_ensemble_factor,
    calculate_ndvi_factor,
)


# --------------------------------------------------------------------------- #
# Stage bucketing
# --------------------------------------------------------------------------- #

def test_stage_bucket_thresholds():
    assert _stage_bucket(0) == "vegetative"
    assert _stage_bucket(39.9) == "vegetative"
    assert _stage_bucket(40.0) == "reproductive"
    assert _stage_bucket(69.9) == "reproductive"
    assert _stage_bucket(70.0) == "grain_fill"
    assert _stage_bucket(100.0) == "grain_fill"


# --------------------------------------------------------------------------- #
# CROP_INDEX_WEIGHTS sanity checks
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("crop", list(CROP_INDEX_WEIGHTS.keys()))
def test_every_crop_stage_weights_sum_to_one(crop):
    for stage, weights in CROP_INDEX_WEIGHTS[crop].items():
        assert set(weights.keys()) == set(INDEX_NAMES), (
            f"{crop}/{stage} weights missing keys"
        )
        assert sum(weights.values()) == pytest.approx(1.0, abs=1e-6), (
            f"{crop}/{stage} weights sum = {sum(weights.values())}"
        )


def test_default_weights_sum_to_one_per_stage():
    for stage, weights in DEFAULT_INDEX_WEIGHTS.items():
        assert sum(weights.values()) == pytest.approx(1.0, abs=1e-6)


def test_get_index_weights_falls_back_for_unknown_crop():
    assert get_index_weights("ZZ_unknown_crop", "vegetative") == DEFAULT_INDEX_WEIGHTS["vegetative"]


def test_tobacco_weights_emphasise_ndre_late_season():
    veg = CROP_INDEX_WEIGHTS["tobacco"]["vegetative"]
    fill = CROP_INDEX_WEIGHTS["tobacco"]["grain_fill"]
    assert fill["ndre"] > veg["ndre"]
    assert fill["ndre"] >= 0.30


def test_maize_weights_emphasise_ndmi_during_grain_fill():
    veg = CROP_INDEX_WEIGHTS["maize"]["vegetative"]
    fill = CROP_INDEX_WEIGHTS["maize"]["grain_fill"]
    assert fill["ndmi"] > veg["ndmi"]
    assert fill["ndmi"] >= 0.30


def test_cotton_weights_keep_ndre_high_consistently():
    cotton = CROP_INDEX_WEIGHTS["cotton"]
    assert cotton["vegetative"]["ndre"] >= 0.20
    assert cotton["reproductive"]["ndre"] >= 0.25
    assert cotton["grain_fill"]["ndre"] >= 0.25


# --------------------------------------------------------------------------- #
# Per-index factor curves
# --------------------------------------------------------------------------- #

def test_ndvi_factor_curve_is_monotonic_across_buckets():
    # Walk through bucket boundaries and verify factor is non-decreasing.
    samples = [0.1, 0.3, 0.5, 0.7, 0.9]
    factors = [yield_model._ndvi_factor(v) for v in samples]
    assert factors == sorted(factors)


def test_ndmi_factor_neutralises_at_saturation():
    # >0.55 NDMI should not get a higher factor than the optimal band.
    optimal = yield_model._ndmi_factor(0.30)
    saturated = yield_model._ndmi_factor(0.70)
    assert saturated <= optimal + 1e-9


def test_sar_factor_handles_none():
    assert yield_model._sar_factor(None) == 1.0


# --------------------------------------------------------------------------- #
# Helpers — building synthetic indices_history
# --------------------------------------------------------------------------- #

def _row(
    log_date: str,
    *,
    ndvi: float = 0.7,
    evi: float = 0.45,
    ndre: float = 0.32,
    ndmi: float = 0.30,
    savi: float = 0.55,
    vv_db: float = -10.0,
    quality: str = "good",
) -> Dict[str, Any]:
    return {
        "log_date": date.fromisoformat(log_date),
        "ndvi": ndvi,
        "indices": {
            "optical": {"ndvi": ndvi, "evi": evi, "ndre": ndre, "ndmi": ndmi, "savi": savi},
            "sar": {"vv_db": vv_db, "vh_db": vv_db - 6},
        },
        "observation_quality": quality,
    }


# --------------------------------------------------------------------------- #
# calculate_index_ensemble_factor
# --------------------------------------------------------------------------- #

def test_ensemble_returns_neutral_factor_for_empty_history():
    factor, explanation, per_index = calculate_index_ensemble_factor(
        indices_history=[], crop="maize", growth_stage_percent=50
    )
    assert factor == 0.85
    assert per_index == {}
    assert "No satellite" in explanation


def test_ensemble_factor_is_in_expected_band_for_healthy_crop():
    history = [_row(f"2026-04-{i:02d}", ndvi=0.75, evi=0.5, ndre=0.35, ndmi=0.30) for i in range(20, 28)]
    factor, explanation, per_index = calculate_index_ensemble_factor(
        indices_history=history, crop="maize", growth_stage_percent=50
    )
    assert 0.95 <= factor <= 1.10
    assert per_index["ndvi"] == pytest.approx(1.0, abs=0.05)
    assert "ndvi" in explanation.lower()


def test_ensemble_factor_drops_for_stressed_crop():
    history = [_row(f"2026-04-{i:02d}", ndvi=0.30, evi=0.20, ndre=0.15, ndmi=0.05) for i in range(20, 28)]
    factor, _, per_index = calculate_index_ensemble_factor(
        indices_history=history, crop="maize", growth_stage_percent=50
    )
    assert factor < 0.9
    assert per_index["ndvi"] < 0.9


def test_ensemble_uses_grain_fill_weights_for_late_season_maize():
    # NDMI=0.40 (high) but NDVI=0.4 (low). Maize grain_fill emphasises NDMI,
    # so the ensemble factor should be pulled up by NDMI vs. the NDVI-only model.
    history = [
        _row(f"2026-04-{i:02d}", ndvi=0.40, evi=0.25, ndre=0.20, ndmi=0.40)
        for i in range(20, 28)
    ]
    ensemble, _, _ = calculate_index_ensemble_factor(
        history, crop="maize", growth_stage_percent=85
    )
    ndvi_only, _ = calculate_ndvi_factor([r["ndvi"] for r in history])
    assert ensemble > ndvi_only


def test_ensemble_uses_ndre_for_tobacco_grain_fill():
    # Tobacco grain_fill weight on NDRE is 0.40 — high NDRE should dominate
    # even when NDVI is mediocre.
    history = [
        _row(f"2026-04-{i:02d}", ndvi=0.50, evi=0.35, ndre=0.45, ndmi=0.20)
        for i in range(20, 28)
    ]
    factor, _, per_index = calculate_index_ensemble_factor(
        history, crop="tobacco", growth_stage_percent=85
    )
    assert per_index["ndre"] >= 1.05  # NDRE 0.45 hits the upper bracket
    assert factor >= 0.97


def test_unknown_crop_falls_back_to_default_weights():
    history = [_row(f"2026-04-{i:02d}") for i in range(20, 28)]
    factor, _, per_index = calculate_index_ensemble_factor(
        history, crop="finger millet", growth_stage_percent=50
    )
    assert factor > 0
    assert "ndvi" in per_index


# --------------------------------------------------------------------------- #
# SAR fallback boost
# --------------------------------------------------------------------------- #

def test_sar_fallback_triggered_when_majority_observations_not_good():
    # 14 obs, 8 partial (>50% non-good). SAR weight should at least double.
    history = []
    for i in range(14):
        q = "partial" if i < 8 else "good"
        history.append(_row(f"2026-04-{i+1:02d}", quality=q, vv_db=-7.0))
    assert _is_optical_sparse(history)


def test_sar_not_triggered_when_majority_good():
    history = [_row(f"2026-04-{i+1:02d}", quality="good") for i in range(14)]
    assert not _is_optical_sparse(history)


def test_sar_fallback_lifts_factor_with_strong_backscatter():
    # When optical is sparse but VV is high (-7 dB), the SAR weight is doubled,
    # so the combined factor must be greater than with default weights.
    sparse_history = []
    for i in range(14):
        q = "partial" if i < 10 else "good"
        sparse_history.append(_row(f"2026-04-{i+1:02d}", quality=q, vv_db=-7.0, ndvi=0.45))

    good_history = [
        _row(f"2026-04-{i+1:02d}", quality="good", vv_db=-7.0, ndvi=0.45) for i in range(14)
    ]

    f_sparse, _, idx_sparse = calculate_index_ensemble_factor(
        sparse_history, crop="maize", growth_stage_percent=50
    )
    f_good, _, idx_good = calculate_index_ensemble_factor(
        good_history, crop="maize", growth_stage_percent=50
    )
    # SAR factor itself unchanged, but its weight is bigger when sparse, so
    # the strong SAR factor pulls the combined value up.
    assert idx_sparse["sar"] == idx_good["sar"]
    assert f_sparse > f_good


# --------------------------------------------------------------------------- #
# Backwards compatibility: ndvi_history-only path still works
# --------------------------------------------------------------------------- #

def test_calculate_ndvi_factor_unchanged():
    # Sanity: legacy NDVI factor still maps to the same buckets.
    f, _ = calculate_ndvi_factor([0.7, 0.72, 0.74, 0.71])
    assert f == 1.0
    f_low, _ = calculate_ndvi_factor([0.15, 0.18, 0.16])
    assert f_low <= 0.6


def test_generate_yield_projection_falls_back_to_ndvi_only(monkeypatch):
    """
    When indices_history is omitted, projection should still work via the legacy
    NDVI path. Patches DB-touching helpers so the call doesn't need a real DB.
    """
    monkeypatch.setattr(yield_model, "get_variety_info", lambda variety: None)

    proj = yield_model.generate_yield_projection(
        field_id="11111111-1111-1111-1111-111111111111",
        crop="Maize",
        variety=None,
        planting_date=date(2026, 1, 15),
        area_ha=2.5,
        coordinates=[{"lat": -17.82, "lon": 31.05}],
        ndvi_history=[0.65, 0.70, 0.72, 0.71, 0.69, 0.73, 0.74],
        cumulative_rainfall_mm=350.0,
        weather_data={"humidity": 60},
    )
    assert proj.projected_yield > 0
    assert "v1.0" in proj.methodology  # legacy methodology label
    assert "index_ensemble_factor" not in proj.adjustment_factors
    assert "per_index_factors" not in proj.adjustment_factors


def test_generate_yield_projection_uses_ensemble_when_provided(monkeypatch):
    monkeypatch.setattr(yield_model, "get_variety_info", lambda variety: None)

    history = [
        _row(f"2026-04-{i:02d}", ndvi=0.72, evi=0.5, ndre=0.35, ndmi=0.30)
        for i in range(20, 28)
    ]
    proj = yield_model.generate_yield_projection(
        field_id="11111111-1111-1111-1111-111111111111",
        crop="Maize",
        variety=None,
        planting_date=date(2026, 1, 15),
        area_ha=2.5,
        coordinates=[{"lat": -17.82, "lon": 31.05}],
        cumulative_rainfall_mm=350.0,
        weather_data={"humidity": 60},
        indices_history=history,
    )
    assert proj.projected_yield > 0
    assert "v1.1" in proj.methodology  # ensemble methodology label
    assert "index_ensemble_factor" in proj.adjustment_factors
    assert "per_index_factors" in proj.adjustment_factors
    assert any("Ensemble indices" in f for f in proj.confidence_factors)
    per_idx = proj.adjustment_factors["per_index_factors"]
    assert {"ndvi", "evi", "ndre", "ndmi", "savi", "sar"}.issubset(per_idx.keys())
