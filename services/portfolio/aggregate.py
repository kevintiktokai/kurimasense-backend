"""
Tenant-wide portfolio aggregation (MVP PR 2)
============================================
Builds the payload for the institutional ``GET /portfolio/aggregate`` screen:
tenant info + portfolio summary + a worst-first priority list of every field.

Read-only. **Reuses** the field-state aggregator (``assemble_field_state``, the
pure no-network path) rather than duplicating any scoring. One batched DB read
for all fields + their daily_logs, then assemble per field — fast for 40 fields.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import List, Optional, Tuple

from services.field_state.aggregator import assemble_field_state
from services.field_state import classifiers
from schemas import (
    PortfolioAggregateResponse, PortfolioTenantInfo, PortfolioSummary,
    PortfolioScoreDistribution, PortfolioPriority,
)


class TenantNotFound(Exception):
    """The tenant id does not exist or is not an institutional tenant."""


# urgency sort order (awaiting_data LAST — not actionable yet)
_URGENCY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "awaiting_data": 4}


# ---------------------------------------------------------------------------
# Banding — single source of truth is the aggregator's classifier
# ---------------------------------------------------------------------------
def score_to_band(score: Optional[int]) -> Tuple[Optional[str], Optional[str]]:
    """Return (label, hex_color) for a 0-100 KurimaScore, or (None, None).

    Reuses ``classifiers.label_for_score`` so the portfolio uses the exact same
    band vocabulary/colours as every other screen (no redefinition)."""
    if score is None:
        return (None, None)
    return classifiers.label_for_score(score)


# ---------------------------------------------------------------------------
# Per-field derivations
# ---------------------------------------------------------------------------
def derive_urgency(score: Optional[int]) -> str:
    """Map a KurimaScore to an urgency band. ``None`` (no observations) →
    ``awaiting_data``."""
    if score is None:
        return "awaiting_data"
    if score < 25:
        return "critical"
    if score < 40:
        return "high"
    if score < 55:
        return "medium"
    return "low"


def derive_primary_concern(score: Optional[int], alerts) -> Tuple[str, str]:
    """Return (primary_concern, recommended_action).

    Prefers the field's top alert (headline + its recommended action) from the
    aggregator; otherwise a deterministic score-based message; the awaiting-data
    message when there are no observations yet.
    """
    if score is None:
        return ("Awaiting satellite observations",
                "Field will appear once Sentinel-2 data arrives")
    if alerts:
        top = alerts[0]
        return (top.headline or "Field requires attention",
                top.recommended_action or "Field officer visit recommended")
    if score < 25:
        return ("Critical vegetation stress detected",
                "Field officer visit required within 24 hours")
    if score < 40:
        return ("Significant stress symptoms",
                "Field officer visit recommended within 72 hours")
    if score < 55:
        return ("Below-target field health",
                "Monitor closely; investigate if trend continues")
    if score < 70:
        return ("Field developing within expected range",
                "Routine monitoring sufficient")
    return ("Field performing strongly",
            "No intervention required; maintain current management")


def _parse_district(name: Optional[str]) -> Optional[str]:
    """Best-effort district from a field name like
    ``DEMO_SEED: <first> - <District> - <crop>``. None if not in that shape
    (there is no district column on ``fields``)."""
    if not name:
        return None
    parts = [p.strip() for p in name.split(" - ")]
    return parts[1] if len(parts) >= 3 else None


def _days_since(iso_date: Optional[str], today: date) -> Optional[int]:
    if not iso_date:
        return None
    try:
        d = datetime.strptime(str(iso_date)[:10], "%Y-%m-%d").date()
        return (today - d).days
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
def compute_summary(field_rows: List[dict], states: List[Tuple[Optional[int], list]]) -> PortfolioSummary:
    """Aggregate distribution, alert counts, average score and hectares."""
    dist = PortfolioScoreDistribution()
    with_data = []
    alerts_critical = alerts_high = 0
    for score, alerts in states:
        if score is None:
            dist.awaiting_data += 1
        elif score >= 85:
            dist.thriving += 1
        elif score >= 70:
            dist.strong += 1
        elif score >= 55:
            dist.adequate += 1
        elif score >= 40:
            dist.stressed += 1
        elif score >= 25:
            dist.distressed += 1
        else:
            dist.critical += 1
        if score is not None:
            with_data.append(score)
        if alerts and any(a.severity == "critical" for a in alerts):
            alerts_critical += 1
        if alerts and any(a.severity == "high" for a in alerts):
            alerts_high += 1

    total_hectares = round(sum(float(f.get("size_hectares") or 0) for f in field_rows), 1)
    total_growers = len({f.get("grower_id") for f in field_rows if f.get("grower_id")})
    avg = round(sum(with_data) / len(with_data), 1) if with_data else None
    return PortfolioSummary(
        total_fields=len(field_rows),
        total_growers=total_growers,
        total_hectares=total_hectares,
        score_distribution=dist,
        alerts_critical=alerts_critical,
        alerts_high=alerts_high,
        average_kurima_score=avg,
        fields_with_data=len(with_data),
        fields_awaiting_data=dist.awaiting_data,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
async def compute_portfolio_aggregate(tenant_id: str) -> PortfolioAggregateResponse:
    """
    Build the full portfolio aggregate for an institutional ``tenant_id``.

    Raises :class:`TenantNotFound` if the tenant is missing/not institutional.
    The work is synchronous (one batched read + pure per-field assembly); this is
    ``async`` only to match the endpoint's await call site.
    """
    from database import get_db_connection
    from psycopg2.extras import RealDictCursor

    conn = get_db_connection()
    if not conn:
        raise RuntimeError("Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT id::text AS id, name, institutional_type FROM tenants "
            "WHERE id = %s::uuid AND tenant_type = 'institutional' AND deleted_at IS NULL",
            (tenant_id,),
        )
        trow = cur.fetchone()
        if not trow:
            cur.close()
            raise TenantNotFound(tenant_id)

        cur.execute(
            """
            SELECT f.*, g.name AS grower_name
            FROM fields f
            LEFT JOIN growers g ON g.id = f.grower_id AND g.deleted_at IS NULL
            WHERE f.tenant_id = %s::uuid
            ORDER BY f.created_at ASC
            """,
            (tenant_id,),
        )
        field_rows = [dict(r) for r in cur.fetchall()]
        field_ids = [str(r["id"]) for r in field_rows]

        logs_by_field: dict = {}
        inputs_by_field: dict = {}
        if field_ids:
            cur.execute(
                "SELECT field_id::text AS field_id, log_date, ndvi, evi, soil_moisture, cloud_cover "
                "FROM daily_logs WHERE field_id = ANY(%s::uuid[]) ORDER BY field_id, log_date ASC",
                (field_ids,),
            )
            for r in cur.fetchall():
                logs_by_field.setdefault(r["field_id"], []).append(dict(r))
            cur.execute(
                "SELECT field_id::text AS field_id, count(*) AS n FROM field_inputs "
                "WHERE field_id = ANY(%s::uuid[]) GROUP BY field_id",
                (field_ids,),
            )
            for r in cur.fetchall():
                inputs_by_field[r["field_id"]] = int(r["n"])
        cur.close()
    finally:
        try:
            conn.close()
        except Exception:
            pass

    now = datetime.utcnow()
    today = now.date()
    priorities: List[PortfolioPriority] = []
    states: List[Tuple[Optional[int], list]] = []

    for fr in field_rows:
        fid = str(fr["id"])
        fs = assemble_field_state(
            field_row=fr, requester_id=None,
            daily_logs=logs_by_field.get(fid, []),
            input_record_count=inputs_by_field.get(fid, 0),
            now=now, enforce_owner=False,
        )
        has_data = fs.indices.current.observation_quality != "none"
        score = fs.kurima_score.score if has_data else None
        label, color = (fs.kurima_score.label, fs.kurima_score.color) if has_data else (None, None)
        concern, action = derive_primary_concern(score, fs.alerts)

        priorities.append(PortfolioPriority(
            field_id=fid,
            field_name=fr.get("name") or "Unnamed field",
            grower_id=str(fr["grower_id"]) if fr.get("grower_id") else None,
            grower_name=fr.get("grower_name"),
            district=_parse_district(fr.get("name")),
            natural_region=fr.get("natural_region"),
            crop_type=fr.get("crop_type") or fr.get("crop") or "unknown",
            variety=fr.get("variety"),
            size_hectares=float(fr.get("size_hectares") or 0),
            kurima_score=score,
            kurima_label=label,
            kurima_color=color,
            primary_concern=concern,
            recommended_action=action,
            urgency=derive_urgency(score),
            days_since_observation=_days_since(fs.indices.current.as_of_date, today),
            planting_date=fs.season.planted_date,
            days_since_planting=fs.season.days_since_planted,
        ))
        states.append((score, fs.alerts))

    priorities.sort(key=lambda p: (
        _URGENCY_ORDER.get(p.urgency, 9),
        p.kurima_score if p.kurima_score is not None else 10 ** 9,  # lower score first
        -p.size_hectares,                                            # larger fields first
        p.field_id,                                                  # deterministic tiebreak
    ))

    summary = compute_summary(field_rows, states)
    return PortfolioAggregateResponse(
        tenant=PortfolioTenantInfo(
            id=trow["id"], name=trow["name"], institutional_type=trow.get("institutional_type"),
        ),
        summary=summary,
        priorities=priorities,
        generated_at=now,
    )
