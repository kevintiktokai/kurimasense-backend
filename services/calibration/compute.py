"""
Calibration math — pure, no I/O.
Computes forecast accuracy metrics from paired (projected, actual) yield data.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class CalibrationPair:
    projected: float
    actual: float
    crop_type: Optional[str] = None
    natural_region: Optional[str] = None
    variety: Optional[str] = None
    season_progress_pct: Optional[int] = None


@dataclass
class CalibrationResult:
    n: int
    mae_pct: float
    rmse: float
    bias_pct: float


def absolute_pct_error(projected: float, actual: float) -> float:
    if actual <= 0:
        raise ValueError("actual must be > 0")
    return abs(projected - actual) / actual * 100


def calibrate(pairs: List[CalibrationPair]) -> CalibrationResult:
    valid = [p for p in pairs if p.actual > 0]
    if not valid:
        return CalibrationResult(n=0, mae_pct=0.0, rmse=0.0, bias_pct=0.0)

    pct_errors = [abs(p.projected - p.actual) / p.actual * 100 for p in valid]
    signed_pct = [(p.projected - p.actual) / p.actual * 100 for p in valid]
    sq_errors = [(p.projected - p.actual) ** 2 for p in valid]

    n = len(valid)
    mae_pct = round(sum(pct_errors) / n, 2)
    rmse = round(math.sqrt(sum(sq_errors) / n), 3)
    bias_pct = round(sum(signed_pct) / n, 2)

    return CalibrationResult(n=n, mae_pct=mae_pct, rmse=rmse, bias_pct=bias_pct)


def _progress_bucket(pct: Optional[int]) -> str:
    if pct is None:
        return "unknown"
    if pct <= 50:
        return "0-50%"
    if pct <= 70:
        return "50-70%"
    return "70-100%"


SegmentKey = Tuple[Optional[str], Optional[str], Optional[str], str]


def segment(
    pairs: List[CalibrationPair],
) -> Dict[SegmentKey, CalibrationResult]:
    buckets: Dict[SegmentKey, List[CalibrationPair]] = {}
    for p in pairs:
        key: SegmentKey = (
            p.crop_type,
            p.natural_region,
            p.variety,
            _progress_bucket(p.season_progress_pct),
        )
        buckets.setdefault(key, []).append(p)

    return {key: calibrate(group) for key, group in buckets.items()}
