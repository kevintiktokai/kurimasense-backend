"""
Exposure engine — pure, no I/O.

Per-grower:  net_exposure = input_credit_value − (projected_volume × price × repayment_likelihood)
Positive net_exposure = capital at risk (credit extended exceeds expected recoverable delivery value).

repayment_likelihood is a v1 heuristic of KurimaScore + historical delivery performance.
All score reads come from the field-state aggregator upstream — this module never
recomputes a KurimaScore or NDVI label (Hard Rule 1).
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def repayment_likelihood(
    score: Optional[float],
    delivery_ratio: Optional[float] = None,
) -> float:
    """
    v1 repayment likelihood in [0, 1].

    score: KurimaScore 0–100 (read from field state). None → neutral 0.5 fraction.
    delivery_ratio: historical Σdelivered / Σcontracted (prior seasons). None → no history.

    With delivery history: 0.6*min(1, delivery_ratio) + 0.4*score_fraction.
    Without history: score_fraction alone.
    """
    score_fraction = 0.5 if score is None else _clamp(score / 100.0)
    if delivery_ratio is None:
        return round(_clamp(score_fraction), 4)
    dr = _clamp(delivery_ratio)  # cap at 1.0; over-delivery doesn't exceed certainty
    return round(_clamp(0.6 * dr + 0.4 * score_fraction), 4)


def grower_net_exposure(
    input_credit_value: float,
    projected_volume_tonnes: float,
    price_per_tonne: float,
    likelihood: float,
) -> float:
    """net_exposure = input_credit_value − (projected_volume × price × repayment_likelihood)."""
    expected_recoverable = projected_volume_tonnes * price_per_tonne * likelihood
    return round(input_credit_value - expected_recoverable, 2)


@dataclass
class GrowerExposure:
    grower_id: str
    grower_name: Optional[str]
    input_credit_value: float
    projected_volume_tonnes: float
    price_per_tonne: float
    repayment_likelihood: float
    net_exposure: float
    expected_harvest_date: Optional[date] = None
    kurima_score: Optional[float] = None
    field_count: int = 0


@dataclass
class WeeklyExposure:
    week_start: date          # Monday of the ISO week
    total_net_exposure: float
    grower_count: int


@dataclass
class PortfolioExposure:
    total_net_exposure: float
    total_input_credit: float
    total_expected_recoverable: float
    grower_count: int
    growers: List[GrowerExposure] = field(default_factory=list)
    weekly: List[WeeklyExposure] = field(default_factory=list)


def _week_start(d: date) -> date:
    """Monday of the ISO week containing d."""
    return d - timedelta(days=d.weekday())


def portfolio_weekly(growers: List[GrowerExposure]) -> List[WeeklyExposure]:
    """Bucket grower net_exposure by the ISO-week of expected harvest (when exposure resolves)."""
    buckets: Dict[date, List[GrowerExposure]] = {}
    for g in growers:
        if g.expected_harvest_date is None:
            continue
        wk = _week_start(g.expected_harvest_date)
        buckets.setdefault(wk, []).append(g)
    out = [
        WeeklyExposure(
            week_start=wk,
            total_net_exposure=round(sum(g.net_exposure for g in gs), 2),
            grower_count=len(gs),
        )
        for wk, gs in buckets.items()
    ]
    out.sort(key=lambda w: w.week_start)
    return out


def build_portfolio_exposure(growers: List[GrowerExposure]) -> PortfolioExposure:
    """Roll up per-grower exposures into a portfolio total + weekly distribution."""
    total_net = round(sum(g.net_exposure for g in growers), 2)
    total_credit = round(sum(g.input_credit_value for g in growers), 2)
    total_recoverable = round(
        sum(g.projected_volume_tonnes * g.price_per_tonne * g.repayment_likelihood for g in growers),
        2,
    )
    return PortfolioExposure(
        total_net_exposure=total_net,
        total_input_credit=total_credit,
        total_expected_recoverable=total_recoverable,
        grower_count=len(growers),
        growers=growers,
        weekly=portfolio_weekly(growers),
    )
