"""
Tests for services/reconciliation/compute.py — hand-computed expectations.
"""

import pytest

from services.reconciliation.compute import (
    reconcile_grower,
    summarize,
)


def _rec(contracted, projected, delivered):
    return reconcile_grower("g1", "Tariro", contracted, projected, delivered)


class TestReconcileGrower:
    def test_side_marketing_flag(self):
        # contracted 10, satellite says 10 produced, only 5 delivered → 50% short,
        # corroborated (10 >= 8) → FLAG; side-marketing = 10 - 5 = 5.
        r = _rec(10, 10, 5)
        assert r.expected_volume_tonnes == 10
        assert r.delivery_gap_pct == 50
        assert r.flag == "flag"
        assert r.side_marketing_volume_tonnes == 5
        assert "side-marketing" in r.reasons[0]

    def test_production_shortfall_is_watch_not_flag(self):
        # 60% short BUT satellite-implied (4) is also below contract (< 8) →
        # production shortfall, WATCH, no side-marketing volume.
        r = _rec(10, 4, 4)
        assert r.delivery_gap_pct == 60
        assert r.flag == "watch"
        assert r.side_marketing_volume_tonnes == 0
        assert "production" in r.reasons[0].lower()

    def test_in_line_is_none(self):
        r = _rec(10, 10, 9)  # 10% gap < 20
        assert r.flag == "none"
        assert r.delivery_gap_pct == 10

    def test_watch_band(self):
        # 25% gap, corroborated → watch; side-marketing volume still computed (2.5).
        r = _rec(10, 10, 7.5)
        assert r.delivery_gap_pct == 25
        assert r.flag == "watch"
        assert r.side_marketing_volume_tonnes == 2.5

    def test_no_contract_uses_projection(self):
        r = _rec(0, 8, 8)  # expected = projected = 8, fully delivered
        assert r.expected_volume_tonnes == 8
        assert r.flag == "none"
        assert r.delivery_gap_pct == 0

    def test_no_data(self):
        r = _rec(0, 0, 0)
        assert r.expected_volume_tonnes == 0
        assert r.flag == "none"
        assert "No contract or projection" in r.reasons[0]

    def test_negatives_clamped(self):
        r = _rec(-5, -5, -5)
        assert r.contracted_volume_tonnes == 0
        assert r.flag == "none"


class TestSummarize:
    def test_counts_and_totals(self):
        rows = [
            _rec(10, 10, 5),    # flag, side 5
            _rec(10, 10, 7.5),  # watch, side 2.5
            _rec(10, 10, 9),    # none
            _rec(10, 4, 4),     # watch (shortfall), side 0
        ]
        s = summarize(rows)
        assert s.grower_count == 4
        assert s.flagged_count == 1
        assert s.watch_count == 2
        assert s.total_side_marketing_tonnes == 7.5  # 5 + 2.5

    def test_empty(self):
        s = summarize([])
        assert s.grower_count == 0
        assert s.flagged_count == 0
        assert s.total_side_marketing_tonnes == 0
