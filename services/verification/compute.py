"""
Verification engine — pure, no I/O.

Checks whether a logged input (fertilizer/chemical, self-reported per field)
produced a satellite canopy response: did NDVI rise in the weeks after the
application? An input claimed but with no NDVI response is a flag — the input may
not have been applied (or was diverted). Evidence for input-verification.

Never recomputes a KurimaScore/label — it reads the raw NDVI series (Hard Rule 1).
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional, Tuple

# Tunable v1 windows/thresholds (documented; revisit with field agronomy).
PRE_DAYS = 14          # baseline window before the application
POST_MIN_DAYS = 14     # response window opens (canopy takes ~2 weeks)
POST_MAX_DAYS = 35     # response window closes
MIN_RESPONSE = 0.02    # NDVI delta considered a real canopy response

Status = str  # 'verified' | 'flagged' | 'unknown'


@dataclass
class InputEvent:
    input_date: date
    input_type: Optional[str] = None


@dataclass
class NdviPoint:
    obs_date: date
    ndvi: float


@dataclass
class InputVerification:
    input_date: date
    input_type: Optional[str]
    ndvi_before: Optional[float]
    ndvi_after: Optional[float]
    response_delta: Optional[float]
    status: Status
    reason: str


@dataclass
class FieldVerification:
    n_inputs: int
    n_verified: int
    n_flagged: int
    n_unknown: int
    verification_pct: Optional[float]  # verified / judgeable * 100 (None if none judgeable)
    inputs: List[InputVerification] = field(default_factory=list)


def _mean_window(series: List[NdviPoint], start: date, end: date) -> Tuple[Optional[float], int]:
    vals = [p.ndvi for p in series if p.ndvi is not None and start <= p.obs_date <= end]
    if not vals:
        return None, 0
    return sum(vals) / len(vals), len(vals)


def verify_input(event: InputEvent, series: List[NdviPoint]) -> InputVerification:
    pre_mean, pre_n = _mean_window(
        series, event.input_date - timedelta(days=PRE_DAYS), event.input_date
    )
    post_mean, post_n = _mean_window(
        series,
        event.input_date + timedelta(days=POST_MIN_DAYS),
        event.input_date + timedelta(days=POST_MAX_DAYS),
    )

    if pre_mean is None or post_mean is None:
        return InputVerification(
            input_date=event.input_date,
            input_type=event.input_type,
            ndvi_before=round(pre_mean, 3) if pre_mean is not None else None,
            ndvi_after=round(post_mean, 3) if post_mean is not None else None,
            response_delta=None,
            status="unknown",
            reason="Not enough satellite coverage around this input to verify.",
        )

    delta = post_mean - pre_mean
    if delta >= MIN_RESPONSE:
        status: Status = "verified"
        reason = f"NDVI rose {delta:+.2f} after application — canopy responded."
    else:
        status = "flagged"
        reason = (
            f"NDVI changed {delta:+.2f} after application — little/no canopy "
            f"response; verify the input was actually applied."
        )

    return InputVerification(
        input_date=event.input_date,
        input_type=event.input_type,
        ndvi_before=round(pre_mean, 3),
        ndvi_after=round(post_mean, 3),
        response_delta=round(delta, 3),
        status=status,
        reason=reason,
    )


def verify_field(events: List[InputEvent], series: List[NdviPoint]) -> FieldVerification:
    results = [verify_input(e, series) for e in events]
    nv = sum(1 for r in results if r.status == "verified")
    nf = sum(1 for r in results if r.status == "flagged")
    nu = sum(1 for r in results if r.status == "unknown")
    judgeable = nv + nf
    pct = round(nv / judgeable * 100, 1) if judgeable else None
    return FieldVerification(
        n_inputs=len(results),
        n_verified=nv,
        n_flagged=nf,
        n_unknown=nu,
        verification_pct=pct,
        inputs=results,
    )


@dataclass
class PortfolioVerificationRollup:
    field_count: int
    fields_with_flagged: int      # fields with >=1 unverified (flagged) input
    total_flagged_inputs: int
    total_inputs: int


def rollup_portfolio(per_field: List[FieldVerification]) -> PortfolioVerificationRollup:
    """Aggregate per-field verification into a portfolio attention summary."""
    return PortfolioVerificationRollup(
        field_count=len(per_field),
        fields_with_flagged=sum(1 for f in per_field if f.n_flagged > 0),
        total_flagged_inputs=sum(f.n_flagged for f in per_field),
        total_inputs=sum(f.n_inputs for f in per_field),
    )
