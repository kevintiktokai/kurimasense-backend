"""
Unit tests for services/satellite/indices.py.

Run:
    cd backend
    python -m pytest tests/test_indices.py -v
"""
from __future__ import annotations

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.satellite.indices import (  # noqa: E402
    EVALSCRIPT_S1_SAR_BACKSCATTER,
    EVALSCRIPT_S2_OPTICAL_INDICES,
    compute_evi,
    compute_ndmi,
    compute_ndre,
    compute_ndvi,
    compute_sar_ratio_db,
    compute_savi,
)


# --------------------------------------------------------------------------- #
# NDVI
# --------------------------------------------------------------------------- #

def test_ndvi_healthy_vegetation():
    # Strong NIR vs. weak red ⇒ high NDVI.
    assert compute_ndvi(nir=0.6, red=0.1) == pytest.approx((0.6 - 0.1) / (0.6 + 0.1))


def test_ndvi_bare_soil_near_zero():
    # NIR ≈ red ⇒ NDVI ≈ 0.
    assert compute_ndvi(nir=0.2, red=0.2) == pytest.approx(0.0)


def test_ndvi_water_negative():
    # Water has higher red than NIR ⇒ negative NDVI.
    val = compute_ndvi(nir=0.05, red=0.15)
    assert val == pytest.approx(-0.5)
    assert val < 0


def test_ndvi_zero_inputs_returns_zero():
    assert compute_ndvi(0.0, 0.0) == 0.0


def test_ndvi_bounds_within_minus_one_to_one():
    for nir, red in [(1.0, 0.0), (0.0, 1.0), (0.5, 0.3), (0.1, 0.9)]:
        v = compute_ndvi(nir, red)
        assert -1.0 <= v <= 1.0


# --------------------------------------------------------------------------- #
# EVI
# --------------------------------------------------------------------------- #

def test_evi_known_value():
    # NIR=0.5, RED=0.1, BLUE=0.05
    # numerator = 2.5 * (0.5 - 0.1) = 1.0
    # denom = 0.5 + 6*0.1 - 7.5*0.05 + 1 = 0.5 + 0.6 - 0.375 + 1 = 1.725
    expected = 1.0 / 1.725
    assert compute_evi(nir=0.5, red=0.1, blue=0.05) == pytest.approx(expected)


def test_evi_zero_division_returns_zero():
    # Construct nir, red, blue so denom = 0:
    # nir + 6*red - 7.5*blue + 1 = 0  →  pick nir=0, red=0, blue = 1/7.5
    blue = 1.0 / 7.5
    assert compute_evi(nir=0.0, red=0.0, blue=blue) == 0.0


def test_evi_zero_inputs_returns_value_using_constant_one():
    # With all zeros, denom = 1, num = 0 → EVI = 0.
    assert compute_evi(0.0, 0.0, 0.0) == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# NDRE
# --------------------------------------------------------------------------- #

def test_ndre_known_value():
    # (0.5 - 0.3) / (0.5 + 0.3) = 0.25
    assert compute_ndre(nir=0.5, red_edge=0.3) == pytest.approx(0.25)


def test_ndre_zero_division_returns_zero():
    assert compute_ndre(0.0, 0.0) == 0.0


# --------------------------------------------------------------------------- #
# NDMI
# --------------------------------------------------------------------------- #

def test_ndmi_known_value():
    # (0.4 - 0.2) / (0.4 + 0.2) = 1/3
    assert compute_ndmi(nir=0.4, swir1=0.2) == pytest.approx(1.0 / 3.0)


def test_ndmi_dry_negative():
    # SWIR1 > NIR ⇒ negative (dry).
    assert compute_ndmi(nir=0.2, swir1=0.4) == pytest.approx(-1.0 / 3.0)


def test_ndmi_zero_division_returns_zero():
    assert compute_ndmi(0.0, 0.0) == 0.0


# --------------------------------------------------------------------------- #
# SAVI
# --------------------------------------------------------------------------- #

def test_savi_known_value_default_L():
    # (1+0.5)*(0.5-0.1)/(0.5+0.1+0.5) = 1.5*0.4/1.1 = 0.6/1.1
    assert compute_savi(nir=0.5, red=0.1) == pytest.approx(0.6 / 1.1)


def test_savi_with_L_zero_equals_ndvi():
    # SAVI with L=0 reduces to NDVI.
    nir, red = 0.6, 0.2
    assert compute_savi(nir, red, L=0.0) == pytest.approx(compute_ndvi(nir, red))


def test_savi_zero_division_returns_zero():
    # nir + red + L = 0 → use L = -1, nir=red=0.5 ⇒ 0.5+0.5-1 = 0
    assert compute_savi(nir=0.5, red=0.5, L=-1.0) == 0.0


def test_savi_custom_L():
    # L=1: (1+1)*(NIR-RED)/(NIR+RED+1)
    nir, red, L = 0.4, 0.1, 1.0
    expected = 2.0 * (nir - red) / (nir + red + L)
    assert compute_savi(nir, red, L=L) == pytest.approx(expected)


# --------------------------------------------------------------------------- #
# SAR ratio
# --------------------------------------------------------------------------- #

def test_sar_ratio_db_simple_subtraction():
    # 10*log10(VV/VH) = VV_db - VH_db
    assert compute_sar_ratio_db(-8.0, -15.0) == pytest.approx(7.0)


def test_sar_ratio_db_equal_inputs_zero():
    assert compute_sar_ratio_db(-12.0, -12.0) == 0.0


def test_sar_ratio_db_negative_when_vh_stronger():
    assert compute_sar_ratio_db(-20.0, -10.0) == pytest.approx(-10.0)


def test_sar_ratio_db_nan_returns_zero():
    assert compute_sar_ratio_db(float("nan"), -10.0) == 0.0
    assert compute_sar_ratio_db(-10.0, float("nan")) == 0.0


def test_sar_ratio_db_inf_returns_zero():
    assert compute_sar_ratio_db(float("inf"), -10.0) == 0.0
    assert compute_sar_ratio_db(-10.0, float("-inf")) == 0.0


# --------------------------------------------------------------------------- #
# Evalscript constants
# --------------------------------------------------------------------------- #

def test_s2_evalscript_contains_required_bands_and_outputs():
    s = EVALSCRIPT_S2_OPTICAL_INDICES
    assert "//VERSION=3" in s
    for band in ["B02", "B04", "B05", "B08", "B11", "SCL"]:
        assert band in s
    for output in ["ndvi", "evi", "ndre", "ndmi", "savi"]:
        assert output in s
    # SCL cloud-mask classes referenced.
    for cls in ["3", "8", "9", "10"]:
        assert cls in s


def test_s1_evalscript_contains_vv_vh_and_db_conversion():
    s = EVALSCRIPT_S1_SAR_BACKSCATTER
    assert "//VERSION=3" in s
    assert "VV" in s and "VH" in s
    assert "vv_db" in s and "vh_db" in s
    # 10 * log10 for dB conversion (Math.log / Math.LN10).
    assert "Math.LN10" in s
