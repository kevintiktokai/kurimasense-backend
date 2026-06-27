"""
Reconciliation engine — pure, no I/O.

Compares, per grower-season:
  contracted volume  (the delivery obligation)
  satellite-implied  (the model's projected production from NDVI — Sprint 1)
  delivered volume   (actual deliveries — Sprint 2)

to surface **side-marketing**: a grower the satellite says produced the crop but
who under-delivered to the contracting buyer. This is the evidence base for the
delivery-risk / side-selling accountability claim (and premium pricing).

The engine never recomputes a projection — it reads the persisted/aggregated
projected volume passed in (Hard Rule 1).
"""

from dataclasses import dataclass, field
from typing import List, Optional

# Tunable v1 thresholds (documented; revisit with real books).
WATCH_GAP_PCT = 20.0          # delivery gap that warrants watching
FLAG_GAP_PCT = 40.0           # delivery gap that warrants a flag
PRODUCTION_CORROBORATION = 0.8  # projected >= expected*this ⇒ satellite says they grew it

Flag = str  # 'none' | 'watch' | 'flag'


@dataclass
class GrowerReconciliation:
    grower_id: str
    grower_name: Optional[str]
    contracted_volume_tonnes: float
    projected_volume_tonnes: float       # satellite-implied
    delivered_volume_tonnes: float
    expected_volume_tonnes: float        # the comparison basis
    delivery_gap_pct: float              # (expected - delivered)/expected*100, >=0
    side_marketing_volume_tonnes: float  # produced-but-undelivered (only when corroborated)
    flag: Flag
    reasons: List[str] = field(default_factory=list)


@dataclass
class ReconciliationSummary:
    grower_count: int
    flagged_count: int
    watch_count: int
    total_side_marketing_tonnes: float
    growers: List[GrowerReconciliation] = field(default_factory=list)


def _round(x: float) -> float:
    return round(x, 2)


def reconcile_grower(
    grower_id: str,
    grower_name: Optional[str],
    contracted: float,
    projected: float,
    delivered: float,
) -> GrowerReconciliation:
    contracted = max(0.0, contracted or 0.0)
    projected = max(0.0, projected or 0.0)
    delivered = max(0.0, delivered or 0.0)

    # Expected = the obligation when contracted; else what satellite implies.
    expected = contracted if contracted > 0 else projected
    gap_pct = ((expected - delivered) / expected * 100) if expected > 0 else 0.0
    gap_pct = max(0.0, gap_pct)

    corroborated = projected >= expected * PRODUCTION_CORROBORATION and projected > 0
    # Volume the satellite says was produced but not delivered — only meaningful
    # once there's an actual delivery gap (watch/flag), never for in-line delivery.
    produced_undelivered = max(0.0, min(projected, expected) - delivered) if corroborated else 0.0
    side_marketing = 0.0

    reasons: List[str] = []
    flag: Flag = "none"

    if expected <= 0:
        reasons.append("No contract or projection to reconcile against.")
    elif gap_pct >= FLAG_GAP_PCT:
        if corroborated:
            flag = "flag"
            side_marketing = produced_undelivered
            reasons.append(
                f"Delivered {delivered:.1f}t of an expected {expected:.1f}t "
                f"({gap_pct:.0f}% short) while satellite-implied production was "
                f"{projected:.1f}t — possible side-marketing."
            )
        else:
            flag = "watch"
            reasons.append(
                f"Delivered {gap_pct:.0f}% short, but satellite-implied production "
                f"({projected:.1f}t) is also below contract — likely a production "
                f"shortfall, not diversion."
            )
    elif gap_pct >= WATCH_GAP_PCT:
        flag = "watch"
        side_marketing = produced_undelivered
        reasons.append(f"Delivery {gap_pct:.0f}% below expected — monitor.")
    else:
        reasons.append("Deliveries in line with expectation.")

    return GrowerReconciliation(
        grower_id=grower_id,
        grower_name=grower_name,
        contracted_volume_tonnes=_round(contracted),
        projected_volume_tonnes=_round(projected),
        delivered_volume_tonnes=_round(delivered),
        expected_volume_tonnes=_round(expected),
        delivery_gap_pct=_round(gap_pct),
        side_marketing_volume_tonnes=_round(side_marketing),
        flag=flag,
        reasons=reasons,
    )


def summarize(rows: List[GrowerReconciliation]) -> ReconciliationSummary:
    return ReconciliationSummary(
        grower_count=len(rows),
        flagged_count=sum(1 for r in rows if r.flag == "flag"),
        watch_count=sum(1 for r in rows if r.flag == "watch"),
        total_side_marketing_tonnes=_round(sum(r.side_marketing_volume_tonnes for r in rows)),
        growers=rows,
    )
