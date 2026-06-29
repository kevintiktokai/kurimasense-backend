"""
Tests for services/verification/compute.py — hand-computed expectations.
"""

from datetime import date, timedelta

import pytest

from services.verification.compute import (
    InputEvent,
    NdviPoint,
    verify_field,
    verify_input,
)

D0 = date(2024, 1, 15)


def _series(points):
    return [NdviPoint(obs_date=D0 + timedelta(days=d), ndvi=v) for d, v in points]


class TestVerifyInput:
    def test_verified_when_ndvi_rises(self):
        # before ~0.40 (days -10,-5), after ~0.55 (days 20,30) → +0.15
        series = _series([(-10, 0.40), (-5, 0.40), (20, 0.55), (30, 0.55)])
        r = verify_input(InputEvent(D0, "Compound D"), series)
        assert r.status == "verified"
        assert r.ndvi_before == 0.40
        assert r.ndvi_after == 0.55
        assert r.response_delta == 0.15

    def test_flagged_when_no_response(self):
        # before 0.50, after 0.49 → -0.01 (< MIN_RESPONSE) → flagged
        series = _series([(-7, 0.50), (25, 0.49)])
        r = verify_input(InputEvent(D0, "Urea"), series)
        assert r.status == "flagged"
        assert r.response_delta == -0.01
        assert "verify the input" in r.reason

    def test_unknown_when_no_post_window_data(self):
        series = _series([(-7, 0.5)])  # nothing in the response window
        r = verify_input(InputEvent(D0), series)
        assert r.status == "unknown"
        assert r.response_delta is None

    def test_unknown_when_no_pre_window_data(self):
        series = _series([(25, 0.6)])  # only post data
        r = verify_input(InputEvent(D0), series)
        assert r.status == "unknown"

    def test_response_exactly_at_threshold_verified(self):
        series = _series([(-5, 0.50), (20, 0.52)])  # +0.02 == MIN_RESPONSE
        r = verify_input(InputEvent(D0), series)
        assert r.status == "verified"

    def test_window_means_average_multiple_points(self):
        # pre mean (0.4,0.5)=0.45 ; post mean (0.6,0.7)=0.65 → +0.20
        series = _series([(-10, 0.4), (-3, 0.5), (18, 0.6), (33, 0.7)])
        r = verify_input(InputEvent(D0), series)
        assert r.ndvi_before == 0.45
        assert r.ndvi_after == 0.65
        assert r.response_delta == 0.20


class TestVerifyField:
    def test_aggregates_statuses(self):
        series = _series([
            (-10, 0.40), (-5, 0.40), (20, 0.55), (30, 0.55),  # supports event A (verified)
        ])
        events = [
            InputEvent(D0, "Compound D"),               # verified
            InputEvent(date(2024, 6, 1), "Urea"),       # no NDVI nearby → unknown
        ]
        fv = verify_field(events, series)
        assert fv.n_inputs == 2
        assert fv.n_verified == 1
        assert fv.n_unknown == 1
        assert fv.n_flagged == 0
        assert fv.verification_pct == 100.0  # 1 verified / 1 judgeable

    def test_pct_none_when_nothing_judgeable(self):
        fv = verify_field([InputEvent(D0)], [])
        assert fv.verification_pct is None
        assert fv.n_unknown == 1

    def test_empty(self):
        fv = verify_field([], [])
        assert fv.n_inputs == 0
        assert fv.verification_pct is None


class TestRollupPortfolio:
    def test_aggregates_counts(self):
        from services.verification.compute import rollup_portfolio
        verified_series = _series([(-10, 0.40), (-5, 0.40), (20, 0.55), (30, 0.55)])
        flat_series = _series([(-7, 0.50), (25, 0.49)])
        f_ok = verify_field([InputEvent(D0)], verified_series)   # 1 verified
        f_flag = verify_field([InputEvent(D0)], flat_series)     # 1 flagged
        f_none = verify_field([], [])                            # no inputs
        roll = rollup_portfolio([f_ok, f_flag, f_none])
        assert roll.field_count == 3
        assert roll.fields_with_flagged == 1
        assert roll.total_flagged_inputs == 1
        assert roll.total_inputs == 2

    def test_empty(self):
        from services.verification.compute import rollup_portfolio
        roll = rollup_portfolio([])
        assert roll.field_count == 0
        assert roll.fields_with_flagged == 0
        assert roll.total_flagged_inputs == 0
