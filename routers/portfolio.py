"""
B2B portfolio API.

All endpoints require an X-API-Key header. The key is parsed, looked up
in api_keys (by key_id_hex), and bcrypt-verified; the resolved
ApiKeyContext.tenant_id must equal the tenant_id in the URL — see
services.auth.api_key_auth.get_api_key_context for the full flow.

Pure-Python helpers (e.g. risk classification, anomaly diff math) live in
this module so tests can exercise them without spinning up FastAPI.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, status
from psycopg2.extras import RealDictCursor

from database import get_db_connection
from crop_constants import DEFAULT_YIELDS
from schemas import (
    ConfidenceBand,
    DistrictForecast,
    FieldAlert,
    FieldAnomaly,
    FieldRiskScore,
    IndicesHistoryPoint,
    IndicesHistoryResponse,
    PortfolioAnomaliesResponse,
    PortfolioRiskSummaryResponse,
    PortfolioYieldForecastResponse,
    RiskDistribution,
    RiskScoreRequest,
    RiskScoreResponse,
)
from services.auth import ApiKeyContext, get_api_key_context

logger = logging.getLogger(__name__)

router = APIRouter(tags=["portfolio"])


# --------------------------------------------------------------------------- #
# Auth — wrap the shared dependency with a tenant-id path-match check
# --------------------------------------------------------------------------- #

def require_tenant_match(
    tenant_id: str = Path(..., description="Tenant UUID this key must be bound to"),
    ctx: ApiKeyContext = Depends(get_api_key_context),
) -> ApiKeyContext:
    """Enforces that the key's tenant matches the tenant_id in the URL."""
    if str(ctx.tenant_id) != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key does not match tenant",
        )
    return ctx


# --------------------------------------------------------------------------- #
# Pure helpers (testable without FastAPI / DB)
# --------------------------------------------------------------------------- #

def classify_risk(ndvi: Optional[float], health_score: Optional[float]) -> Tuple[str, str]:
    """
    Map a field's recent NDVI and health_score to a risk bucket and the
    headline reason.

    Buckets: low / medium / high / critical.
    """
    if ndvi is None and health_score is None:
        return "high", "No recent satellite or health data"

    # Health score is 0-100 in this codebase; normalize.
    h = (health_score / 100.0) if health_score is not None and health_score > 1 else health_score
    n = ndvi

    if n is not None and n < 0.25:
        return "critical", f"Severe NDVI deficit ({n:.2f})"
    if h is not None and h < 0.3:
        return "critical", f"Health score critically low ({h:.0%})"
    if n is not None and n < 0.40:
        return "high", f"Stressed canopy (NDVI {n:.2f})"
    if h is not None and h < 0.5:
        return "high", f"Low health score ({h:.0%})"
    if (n is not None and n < 0.55) or (h is not None and h < 0.7):
        return "medium", "Moderate vigour — monitor closely"
    return "low", "Healthy crop trajectory"


def compute_field_risk_score(
    *,
    ndvi: Optional[float],
    ndmi: Optional[float],
    cloud_pct: Optional[float],
    health_score: Optional[float],
) -> Tuple[float, List[str]]:
    """
    Returns (score in [0, 1], factor list). Higher score = higher risk.

    Combines:
      - NDVI deviation from healthy baseline (0.7)
      - NDMI deviation from healthy baseline (0.30)
      - Health score (0-100 or 0-1)
      - Heavy cloud cover degrades confidence
    """
    factors: List[str] = []
    components: List[Tuple[str, float, float]] = []  # (label, weight, contribution)

    if ndvi is not None:
        # 0.7 healthy → 0 risk; 0.2 → 1 risk.
        risk = max(0.0, min(1.0, (0.7 - ndvi) / 0.5))
        components.append(("ndvi", 0.45, risk))
        if risk >= 0.4:
            factors.append(f"Low NDVI ({ndvi:.2f})")
    if ndmi is not None:
        # 0.30 healthy → 0; 0.0 → 1.
        risk = max(0.0, min(1.0, (0.30 - ndmi) / 0.30))
        components.append(("ndmi", 0.25, risk))
        if risk >= 0.5:
            factors.append(f"Low NDMI ({ndmi:.2f}) — water stress")
    if health_score is not None:
        h = (health_score / 100.0) if health_score > 1 else health_score
        risk = max(0.0, min(1.0, 1.0 - h))
        components.append(("health", 0.20, risk))
        if risk >= 0.5:
            factors.append(f"Health score {h:.0%}")
    if cloud_pct is not None and cloud_pct > 50:
        components.append(("cloud", 0.10, min(1.0, (cloud_pct - 50) / 50)))
        factors.append(f"Heavy cloud cover ({cloud_pct:.0f}%)")

    if not components:
        return 0.6, ["No data — conservative estimate"]

    weight_sum = sum(w for _, w, _ in components) or 1.0
    score = sum(w * r for _, w, r in components) / weight_sum
    if not factors:
        factors.append("All indicators within healthy range")
    return round(min(1.0, max(0.0, score)), 3), factors


def detect_anomaly(
    points: List[Dict[str, Any]], index_name: str, threshold: float, days_back: int
) -> Optional[FieldAnomaly]:
    """
    Compare the mean of the first 3 points to the mean of the last 3 points
    for the given index. If the recent mean has dropped by more than
    `threshold`, return a FieldAnomaly.

    `points` is a list of indices_history rows ordered oldest → newest.
    """
    values = [p.get(index_name) for p in points if p.get(index_name) is not None]
    if len(values) < 4:
        return None
    earlier = values[:3]
    recent = values[-3:]
    earlier_mean = sum(earlier) / len(earlier)
    recent_mean = sum(recent) / len(recent)
    drop = earlier_mean - recent_mean
    if drop > threshold:
        return FieldAnomaly(
            field_id="",  # caller fills this in
            index=index_name,
            days_back=days_back,
            earlier_mean=round(earlier_mean, 4),
            recent_mean=round(recent_mean, 4),
            drop=round(drop, 4),
        )
    return None


def project_yield_for_field(
    *,
    crop_type: Optional[str],
    size_hectares: Optional[float],
    recent_ndvi: Optional[float],
) -> Tuple[float, float]:
    """
    Lightweight per-field projection used by the portfolio aggregator.
    Returns (projected_yield_tonnes_per_ha, confidence_score).
    """
    crop_key = (crop_type or "maize").lower().strip()
    base = DEFAULT_YIELDS.get(crop_key, 5.0)
    if recent_ndvi is None:
        return round(base * 0.85, 2), 0.4
    # Same buckets as yield_model.calculate_ndvi_factor.
    if recent_ndvi < 0.2:
        f = 0.6
    elif recent_ndvi < 0.4:
        f = 0.75
    elif recent_ndvi < 0.6:
        f = 0.9
    elif recent_ndvi < 0.8:
        f = 1.0
    else:
        f = 1.1
    return round(base * f, 2), 0.75


# --------------------------------------------------------------------------- #
# DB queries
# --------------------------------------------------------------------------- #

def _fetch_tenant_fields(
    cursor, tenant_id: str, crop_filter: Optional[str]
) -> List[Dict[str, Any]]:
    cursor.execute(
        """
        SELECT f.id, f.crop_type, f.size_hectares, f.health_score,
               COALESCE(NULLIF(f.natural_region, ''), 'Unknown') AS district,
               (SELECT AVG(ndvi)::float
                  FROM daily_logs
                  WHERE field_id = f.id
                    AND ndvi IS NOT NULL
                    AND log_date >= (NOW() - INTERVAL '7 days')) AS recent_ndvi,
               (SELECT AVG((indices->'optical'->>'ndmi')::float)
                  FROM daily_logs
                  WHERE field_id = f.id
                    AND indices IS NOT NULL
                    AND log_date >= (NOW() - INTERVAL '7 days')) AS recent_ndmi,
               (SELECT AVG(cloud_pct)::float
                  FROM daily_logs
                  WHERE field_id = f.id
                    AND log_date >= (NOW() - INTERVAL '7 days')) AS recent_cloud_pct
        FROM fields f
        WHERE f.user_id = %s::uuid
          AND (%s IS NULL OR f.crop_type ILIKE %s)
        """,
        (tenant_id, crop_filter, crop_filter),
    )
    return list(cursor.fetchall())


def _fetch_field_indices_history(
    cursor, field_id: str, start_date: date, end_date: date
) -> List[Dict[str, Any]]:
    cursor.execute(
        """
        SELECT log_date, ndvi, evi, indices, cloud_pct, observation_quality
        FROM daily_logs
        WHERE field_id = %s::uuid
          AND log_date BETWEEN %s AND %s
        ORDER BY log_date ASC
        """,
        (field_id, start_date, end_date),
    )
    return list(cursor.fetchall())


def _fetch_fields_for_anomaly(cursor, tenant_id: str, days_back: int) -> List[Dict[str, Any]]:
    cursor.execute(
        """
        SELECT id FROM fields WHERE user_id = %s::uuid
        """,
        (tenant_id,),
    )
    return list(cursor.fetchall())


def _row_to_history_point(row: Dict[str, Any]) -> IndicesHistoryPoint:
    indices = row.get("indices") or {}
    optical = indices.get("optical") if isinstance(indices, dict) else None
    sar = indices.get("sar") if isinstance(indices, dict) else None
    optical = optical or {}
    sar = sar or {}

    def _val(d: Dict[str, Any], k: str) -> Optional[float]:
        v = d.get(k)
        if isinstance(v, dict):
            v = v.get("mean")
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    return IndicesHistoryPoint(
        log_date=row["log_date"],
        ndvi=_val({"v": row.get("ndvi")}, "v") or _val(optical, "ndvi"),
        evi=_val({"v": row.get("evi")}, "v") or _val(optical, "evi"),
        ndre=_val(optical, "ndre"),
        ndmi=_val(optical, "ndmi"),
        savi=_val(optical, "savi"),
        vv_db=_val(sar, "vv_db"),
        vh_db=_val(sar, "vh_db"),
        cloud_pct=row.get("cloud_pct"),
        observation_quality=row.get("observation_quality"),
    )


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

@router.get(
    "/portfolio/{tenant_id}/yield_forecast",
    response_model=PortfolioYieldForecastResponse,
)
def yield_forecast(
    tenant_id: str = Path(...),
    crop: Optional[str] = Query(default=None),
    as_of_date: Optional[date] = Query(default=None),
    _ctx: ApiKeyContext = Depends(require_tenant_match),
) -> PortfolioYieldForecastResponse:
    """Aggregate per-district yield projection for a tenant."""
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(503, "Database unavailable")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        rows = _fetch_tenant_fields(cursor, tenant_id, crop)
        cursor.close()
    finally:
        conn.close()

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        grouped[r["district"]].append(r)

    districts: List[DistrictForecast] = []
    for district, fields in sorted(grouped.items()):
        n = len(fields)
        total_area = sum(float(f.get("size_hectares") or 0.0) for f in fields)
        per_field: List[Tuple[float, float, float]] = []  # (yield_per_ha, conf, area)
        for f in fields:
            y, c = project_yield_for_field(
                crop_type=f.get("crop_type"),
                size_hectares=float(f.get("size_hectares") or 0.0),
                recent_ndvi=f.get("recent_ndvi"),
            )
            per_field.append((y, c, float(f.get("size_hectares") or 1.0)))

        weight_sum = sum(a for _, _, a in per_field) or 1.0
        weighted_yield = sum(y * a for y, _, a in per_field) / weight_sum
        avg_conf = sum(c for _, c, _ in per_field) / len(per_field) if per_field else 0.0
        districts.append(
            DistrictForecast(
                district_name=district,
                n_fields=n,
                total_area_ha=round(total_area, 2),
                projected_yield_tonnes_per_ha=round(weighted_yield, 2),
                confidence_score=round(avg_conf, 2),
                confidence_band=ConfidenceBand(
                    low=round(weighted_yield * 0.9, 2),
                    mid=round(weighted_yield, 2),
                    high=round(weighted_yield * 1.1, 2),
                ),
            )
        )

    return PortfolioYieldForecastResponse(
        tenant_id=tenant_id,
        crop=crop or "all",
        districts=districts,
    )


@router.get(
    "/portfolio/{tenant_id}/risk_summary",
    response_model=PortfolioRiskSummaryResponse,
)
def risk_summary(
    tenant_id: str = Path(...),
    _ctx: ApiKeyContext = Depends(require_tenant_match),
) -> PortfolioRiskSummaryResponse:
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(503, "Database unavailable")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        rows = _fetch_tenant_fields(cursor, tenant_id, None)
        cursor.close()
    finally:
        conn.close()

    distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    alerts: List[FieldAlert] = []
    for r in rows:
        level, concern = classify_risk(r.get("recent_ndvi"), r.get("health_score"))
        distribution[level] += 1
        if level in ("high", "critical"):
            alerts.append(
                FieldAlert(
                    field_id=str(r["id"]),
                    risk_level=level,
                    primary_concern=concern,
                )
            )

    return PortfolioRiskSummaryResponse(
        tenant_id=tenant_id,
        total_fields=len(rows),
        risk_distribution=RiskDistribution(**distribution),
        fields_with_alerts=alerts,
    )


@router.get(
    "/portfolio/{tenant_id}/anomalies",
    response_model=PortfolioAnomaliesResponse,
)
def anomalies(
    tenant_id: str = Path(...),
    days_back: int = Query(default=14, ge=2, le=90),
    threshold: float = Query(default=0.15, gt=0.0, le=1.0),
    _ctx: ApiKeyContext = Depends(require_tenant_match),
) -> PortfolioAnomaliesResponse:
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(503, "Database unavailable")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT id FROM fields WHERE user_id = %s::uuid", (tenant_id,)
        )
        field_rows = list(cursor.fetchall())
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)

        flagged: List[FieldAnomaly] = []
        for fr in field_rows:
            fid = str(fr["id"])
            history = _fetch_field_indices_history(cursor, fid, start_date, end_date)
            points = [_row_to_history_point(h).model_dump() for h in history]
            for index_name in ("ndvi", "ndre", "ndmi", "evi", "savi"):
                anomaly = detect_anomaly(points, index_name, threshold, days_back)
                if anomaly is not None:
                    flagged.append(anomaly.model_copy(update={"field_id": fid}))
        cursor.close()
    finally:
        conn.close()

    return PortfolioAnomaliesResponse(
        tenant_id=tenant_id,
        threshold=threshold,
        days_back=days_back,
        anomalies=flagged,
    )


@router.get(
    "/field/{field_id}/indices_history",
    response_model=IndicesHistoryResponse,
)
def field_indices_history(
    field_id: str = Path(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    ctx: ApiKeyContext = Depends(get_api_key_context),
) -> IndicesHistoryResponse:
    """
    Field endpoint isn't tenant-scoped in the URL, so we authenticate via
    the shared dependency and then require that the field belongs to the
    key's tenant before returning any data.
    """
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(503, "Database unavailable")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT user_id FROM fields WHERE id = %s::uuid",
            (field_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(404, "Field not found")
        if str(row["user_id"]) != str(ctx.tenant_id):
            raise HTTPException(403, "Field does not belong to API key tenant")

        rows = _fetch_field_indices_history(cursor, field_id, start_date, end_date)
        cursor.close()
    finally:
        conn.close()

    points = [_row_to_history_point(r) for r in rows]
    return IndicesHistoryResponse(
        field_id=field_id,
        start_date=start_date,
        end_date=end_date,
        points=points,
    )


@router.post(
    "/portfolio/{tenant_id}/risk_score",
    response_model=RiskScoreResponse,
)
def risk_score(
    body: RiskScoreRequest,
    tenant_id: str = Path(...),
    _ctx: ApiKeyContext = Depends(require_tenant_match),
) -> RiskScoreResponse:
    """Per-field risk scores for a list of field IDs (bank-facing)."""
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(503, "Database unavailable")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT f.id, f.user_id, f.health_score,
                   (SELECT AVG(ndvi)::float
                      FROM daily_logs
                      WHERE field_id = f.id
                        AND ndvi IS NOT NULL
                        AND log_date >= (NOW() - INTERVAL '14 days')) AS recent_ndvi,
                   (SELECT AVG((indices->'optical'->>'ndmi')::float)
                      FROM daily_logs
                      WHERE field_id = f.id
                        AND indices IS NOT NULL
                        AND log_date >= (NOW() - INTERVAL '14 days')) AS recent_ndmi,
                   (SELECT AVG(cloud_pct)::float
                      FROM daily_logs
                      WHERE field_id = f.id
                        AND log_date >= (NOW() - INTERVAL '14 days')) AS recent_cloud_pct
            FROM fields f
            WHERE f.id = ANY(%s::uuid[])
            """,
            (body.field_ids,),
        )
        rows = list(cursor.fetchall())
        cursor.close()
    finally:
        conn.close()

    scores: Dict[str, FieldRiskScore] = {}
    requested_ids = set(str(fid) for fid in body.field_ids)
    seen_ids: set = set()
    for r in rows:
        fid = str(r["id"])
        seen_ids.add(fid)
        # Reject fields that belong to a different tenant.
        if str(r.get("user_id")) != str(tenant_id):
            scores[fid] = FieldRiskScore(score=1.0, primary_factors=["Field not in tenant"])
            continue
        score, factors = compute_field_risk_score(
            ndvi=r.get("recent_ndvi"),
            ndmi=r.get("recent_ndmi"),
            cloud_pct=r.get("recent_cloud_pct"),
            health_score=r.get("health_score"),
        )
        scores[fid] = FieldRiskScore(score=score, primary_factors=factors)

    for fid in requested_ids - seen_ids:
        scores[fid] = FieldRiskScore(
            score=1.0, primary_factors=["Field not found"]
        )

    return RiskScoreResponse(tenant_id=tenant_id, scores=scores)
