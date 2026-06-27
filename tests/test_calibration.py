"""
Tests for services/calibration/compute.py — hand-computed expectations.
"""

import math
import pytest

from services.calibration.compute import (
    CalibrationPair,
    CalibrationResult,
    absolute_pct_error,
    calibrate,
    segment,
)


class TestAbsolutePctError:
    def test_exact_match(self):
        assert absolute_pct_error(5.0, 5.0) == 0.0

    def test_over_prediction(self):
        assert absolute_pct_error(6.0, 5.0) == pytest.approx(20.0)

    def test_under_prediction(self):
        assert absolute_pct_error(4.0, 5.0) == pytest.approx(20.0)

    def test_zero_actual_raises(self):
        with pytest.raises(ValueError, match="actual must be > 0"):
            absolute_pct_error(5.0, 0.0)

    def test_negative_actual_raises(self):
        with pytest.raises(ValueError, match="actual must be > 0"):
            absolute_pct_error(5.0, -1.0)


class TestCalibrate:
    def test_over_predicting_set(self):
        # All projections 20% above actual
        # proj=6, actual=5 → |6-5|/5*100 = 20%, bias = +20%
        # proj=12, actual=10 → |12-10|/10*100 = 20%, bias = +20%
        pairs = [
            CalibrationPair(projected=6.0, actual=5.0),
            CalibrationPair(projected=12.0, actual=10.0),
        ]
        result = calibrate(pairs)
        assert result.n == 2
        assert result.mae_pct == pytest.approx(20.0)
        assert result.bias_pct == pytest.approx(20.0)  # positive = over
        # RMSE: sqrt(((6-5)^2 + (12-10)^2) / 2) = sqrt((1+4)/2) = sqrt(2.5)
        assert result.rmse == pytest.approx(round(math.sqrt(2.5), 3))

    def test_under_predicting_set(self):
        # proj=4, actual=5 → |4-5|/5*100 = 20%, bias = -20%
        # proj=8, actual=10 → |8-10|/10*100 = 20%, bias = -20%
        pairs = [
            CalibrationPair(projected=4.0, actual=5.0),
            CalibrationPair(projected=8.0, actual=10.0),
        ]
        result = calibrate(pairs)
        assert result.n == 2
        assert result.mae_pct == pytest.approx(20.0)
        assert result.bias_pct == pytest.approx(-20.0)  # negative = under

    def test_mixed_set(self):
        # proj=6, actual=5 → 20% error, +20% bias
        # proj=4, actual=5 → 20% error, -20% bias
        pairs = [
            CalibrationPair(projected=6.0, actual=5.0),
            CalibrationPair(projected=4.0, actual=5.0),
        ]
        result = calibrate(pairs)
        assert result.n == 2
        assert result.mae_pct == pytest.approx(20.0)
        assert result.bias_pct == pytest.approx(0.0)  # symmetric

    def test_zero_actual_excluded(self):
        pairs = [
            CalibrationPair(projected=6.0, actual=5.0),
            CalibrationPair(projected=3.0, actual=0.0),  # excluded
        ]
        result = calibrate(pairs)
        assert result.n == 1
        assert result.mae_pct == pytest.approx(20.0)

    def test_negative_actual_excluded(self):
        pairs = [
            CalibrationPair(projected=6.0, actual=5.0),
            CalibrationPair(projected=3.0, actual=-1.0),  # excluded
        ]
        result = calibrate(pairs)
        assert result.n == 1

    def test_all_zero_actuals(self):
        pairs = [
            CalibrationPair(projected=5.0, actual=0.0),
            CalibrationPair(projected=3.0, actual=0.0),
        ]
        result = calibrate(pairs)
        assert result.n == 0
        assert result.mae_pct == 0.0

    def test_empty_input(self):
        result = calibrate([])
        assert result.n == 0


class TestSegment:
    def test_segments_by_crop_region_variety_progress(self):
        pairs = [
            CalibrationPair(projected=6.0, actual=5.0, crop_type="tobacco",
                            natural_region="II", variety="KRK26R", season_progress_pct=40),
            CalibrationPair(projected=12.0, actual=10.0, crop_type="tobacco",
                            natural_region="II", variety="KRK26R", season_progress_pct=45),
            CalibrationPair(projected=3.0, actual=2.5, crop_type="maize",
                            natural_region="III", variety=None, season_progress_pct=80),
        ]
        results = segment(pairs)
        assert len(results) == 2

        tobacco_key = ("tobacco", "II", "KRK26R", "0-50%")
        assert tobacco_key in results
        assert results[tobacco_key].n == 2
        assert results[tobacco_key].mae_pct == pytest.approx(20.0)

        maize_key = ("maize", "III", None, "70-100%")
        assert maize_key in results
        assert results[maize_key].n == 1

    def test_progress_buckets(self):
        pairs = [
            CalibrationPair(projected=5.5, actual=5.0, season_progress_pct=30),
            CalibrationPair(projected=5.5, actual=5.0, season_progress_pct=60),
            CalibrationPair(projected=5.5, actual=5.0, season_progress_pct=90),
            CalibrationPair(projected=5.5, actual=5.0, season_progress_pct=None),
        ]
        results = segment(pairs)
        buckets = {key[3] for key in results.keys()}
        assert buckets == {"0-50%", "50-70%", "70-100%", "unknown"}
