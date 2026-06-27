"""
Tests for services/exposure/compute.py — hand-computed expectations.
"""

from datetime import date

import pytest

from services.exposure.compute import (
    GrowerExposure,
    PortfolioExposure,
    WeeklyExposure,
    build_portfolio_exposure,
    grower_net_exposure,
    portfolio_weekly,
    repayment_likelihood,
)


class TestRepaymentLikelihood:
    def test_score_only_no_history(self):
        # 80/100 = 0.8
        assert repayment_likelihood(80, None) == pytest.approx(0.8)

    def test_with_delivery_history(self):
        # 0.6*0.9 + 0.4*0.8 = 0.54 + 0.32 = 0.86
        assert repayment_likelihood(80, 0.9) == pytest.approx(0.86)

    def test_none_score_neutral(self):
        assert repayment_likelihood(None, None) == pytest.approx(0.5)

    def test_over_delivery_capped(self):
        # delivery_ratio 1.5 capped to 1.0; score 100 → 0.6*1 + 0.4*1 = 1.0
        assert repayment_likelihood(100, 1.5) == pytest.approx(1.0)

    def test_worst_case(self):
        assert repayment_likelihood(0, 0.0) == pytest.approx(0.0)

    def test_clamped_to_unit_interval(self):
        v = repayment_likelihood(100, 1.0)
        assert 0.0 <= v <= 1.0


class TestGrowerNetExposure:
    def test_break_even(self):
        # credit 1000, 10t * 200 * 0.5 = 1000 recoverable → net 0
        assert grower_net_exposure(1000, 10, 200, 0.5) == pytest.approx(0.0)

    def test_over_covered_negative(self):
        # credit 1000, 10t * 200 * 0.8 = 1600 → net -600 (no capital at risk)
        assert grower_net_exposure(1000, 10, 200, 0.8) == pytest.approx(-600.0)

    def test_at_risk_positive(self):
        # credit 2000, 5t * 200 * 0.5 = 500 → net 1500 at risk
        assert grower_net_exposure(2000, 5, 200, 0.5) == pytest.approx(1500.0)

    def test_zero_projection_full_exposure(self):
        # no expected delivery → entire credit at risk
        assert grower_net_exposure(1500, 0, 200, 0.9) == pytest.approx(1500.0)


def _ge(grower_id, net, harvest=None, credit=0.0, vol=0.0, price=0.0, like=0.0):
    return GrowerExposure(
        grower_id=grower_id, grower_name=None,
        input_credit_value=credit, projected_volume_tonnes=vol,
        price_per_tonne=price, repayment_likelihood=like,
        net_exposure=net, expected_harvest_date=harvest,
    )


class TestPortfolioWeekly:
    def test_buckets_by_iso_week_monday(self):
        # 2024-03-20 is a Wednesday → Monday 2024-03-18
        weekly = portfolio_weekly([_ge("g1", 1000.0, date(2024, 3, 20))])
        assert len(weekly) == 1
        assert weekly[0].week_start == date(2024, 3, 18)
        assert weekly[0].total_net_exposure == pytest.approx(1000.0)
        assert weekly[0].grower_count == 1

    def test_same_week_summed(self):
        # 2024-03-18 (Mon) and 2024-03-22 (Fri) → same week
        weekly = portfolio_weekly([
            _ge("g1", 1000.0, date(2024, 3, 18)),
            _ge("g2", 500.0, date(2024, 3, 22)),
        ])
        assert len(weekly) == 1
        assert weekly[0].total_net_exposure == pytest.approx(1500.0)
        assert weekly[0].grower_count == 2

    def test_different_weeks_sorted(self):
        weekly = portfolio_weekly([
            _ge("g2", 500.0, date(2024, 4, 1)),
            _ge("g1", 1000.0, date(2024, 3, 18)),
        ])
        assert [w.week_start for w in weekly] == [date(2024, 3, 18), date(2024, 4, 1)]

    def test_missing_harvest_date_excluded(self):
        weekly = portfolio_weekly([_ge("g1", 1000.0, None)])
        assert weekly == []


class TestBuildPortfolioExposure:
    def test_totals(self):
        growers = [
            GrowerExposure("g1", "Alpha", input_credit_value=2000, projected_volume_tonnes=5,
                           price_per_tonne=200, repayment_likelihood=0.5, net_exposure=1500.0,
                           expected_harvest_date=date(2024, 3, 18)),
            GrowerExposure("g2", "Beta", input_credit_value=1000, projected_volume_tonnes=10,
                           price_per_tonne=200, repayment_likelihood=0.8, net_exposure=-600.0,
                           expected_harvest_date=date(2024, 3, 20)),
        ]
        p = build_portfolio_exposure(growers)
        assert isinstance(p, PortfolioExposure)
        assert p.grower_count == 2
        assert p.total_input_credit == pytest.approx(3000.0)
        assert p.total_net_exposure == pytest.approx(900.0)  # 1500 + (-600)
        # recoverable: 5*200*0.5=500 ; 10*200*0.8=1600 ; total 2100
        assert p.total_expected_recoverable == pytest.approx(2100.0)
        # both harvest in week of 2024-03-18
        assert len(p.weekly) == 1
        assert p.weekly[0].total_net_exposure == pytest.approx(900.0)

    def test_empty(self):
        p = build_portfolio_exposure([])
        assert p.grower_count == 0
        assert p.total_net_exposure == 0
        assert p.weekly == []
