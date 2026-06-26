"""
Outcome-loop routes (Sprint 1): harvest CRUD + calibration read + admin recompute.
Tenant-scoped via get_authenticated_user; 403-vs-404 access pattern.
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from psycopg2.extras import RealDictCursor

from auth_roles import get_authenticated_user
from database import get_db_connection
from schemas import (
    AuthenticatedUser,
    CalibrationEntry,
    CalibrationResponse,
    CreateHarvestRequest,
    HarvestRecord,
)

router = APIRouter(tags=["outcome-loop"])


def _resolve_field_for_tenant(field_id: str, user: AuthenticatedUser) -> dict:
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id::text, tenant_id::text, grower_id::text,
                   crop_type, variety, planting_date
            FROM fields WHERE id = %s::uuid AND deleted_at IS NULL
            """,
            (field_id,),
        )
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Field not found")

    field_tenant = row.get("tenant_id")
    allowed = (
        user.role == "admin"
        or (field_tenant is not None and str(field_tenant) in {str(t) for t in user.tenant_ids})
        or str(row.get("user_id", "")) == user.user_id
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")
    return dict(row)


@router.post("/fields/{field_id}/harvest", response_model=HarvestRecord, status_code=201)
def create_harvest(
    field_id: str,
    body: CreateHarvestRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    field = _resolve_field_for_tenant(field_id, user)

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            INSERT INTO harvest_records
                (field_id, grower_id, tenant_id, season_year, crop_type, variety,
                 planting_date, harvest_date, area_harvested_ha, actual_yield_tonnes,
                 quality_grade, moisture_at_harvest, sale_price_per_tonne,
                 delivered_to_tenant, source, notes)
            VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, 'grower_logged', %s)
            RETURNING *,
                id::text AS id,
                field_id::text AS field_id,
                grower_id::text AS grower_id,
                tenant_id::text AS tenant_id
            """,
            (
                field_id,
                field.get("grower_id"),
                field.get("tenant_id"),
                body.season_year,
                field.get("crop_type"),
                field.get("variety"),
                field.get("planting_date"),
                body.harvest_date,
                body.area_harvested_ha,
                body.actual_yield_tonnes,
                body.quality_grade,
                body.moisture_at_harvest,
                body.sale_price_per_tonne,
                body.delivered_to_tenant,
                body.notes,
            ),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    except HTTPException:
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()

    return HarvestRecord(**dict(row))


@router.get("/fields/{field_id}/harvest", response_model=List[HarvestRecord])
def list_harvests(
    field_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    _resolve_field_for_tenant(field_id, user)

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT *, id::text AS id, field_id::text AS field_id,
                   grower_id::text AS grower_id, tenant_id::text AS tenant_id
            FROM harvest_records
            WHERE field_id = %s::uuid
            ORDER BY season_year DESC, created_at DESC
            """,
            (field_id,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
    finally:
        conn.close()

    return [HarvestRecord(**r) for r in rows]


@router.get("/tenants/{tenant_id}/calibration", response_model=CalibrationResponse)
def get_calibration(
    tenant_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    allowed = (
        user.role == "admin"
        or tenant_id in {str(t) for t in user.tenant_ids}
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Access denied")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT DISTINCT mc.crop_type
            FROM model_calibration mc
            JOIN harvest_records hr ON hr.crop_type = mc.crop_type
                                   AND hr.tenant_id = %s::uuid
            WHERE mc.model_version = (
                SELECT model_version FROM model_calibration
                ORDER BY computed_at DESC LIMIT 1
            )
            """,
            (tenant_id,),
        )
        tenant_crops = {r["crop_type"] for r in cur.fetchall()}

        cur.execute(
            """
            SELECT * FROM model_calibration
            WHERE model_version = (
                SELECT model_version FROM model_calibration
                ORDER BY computed_at DESC LIMIT 1
            )
            AND (crop_type IS NULL OR crop_type = ANY(%s))
            ORDER BY crop_type, season_progress_bucket
            """,
            (list(tenant_crops) if tenant_crops else ["__none__"],),
        )
        rows = [dict(r) for r in cur.fetchall()]

        has_real_actuals = False
        if tenant_crops:
            cur.execute(
                """
                SELECT EXISTS(
                    SELECT 1 FROM harvest_records
                    WHERE tenant_id = %s::uuid
                      AND source != 'historical_backfill'
                      AND actual_yield_tonnes IS NOT NULL
                )
                """,
                (tenant_id,),
            )
            has_real_actuals = cur.fetchone()["exists"]

        cur.close()
    finally:
        conn.close()

    entries = [CalibrationEntry(**r) for r in rows]

    headline_mae = None
    headline_crop = None
    headline_bucket = None
    if entries:
        best = max(entries, key=lambda e: (e.season_progress_bucket or "", e.n_observations))
        headline_mae = best.mae_pct
        headline_crop = best.crop_type
        headline_bucket = best.season_progress_bucket

    return CalibrationResponse(
        headline_mae_pct=headline_mae,
        headline_crop=headline_crop,
        headline_progress_bucket=headline_bucket,
        is_validated=has_real_actuals,
        entries=entries,
    )


@router.post("/admin/calibration/recompute", status_code=200)
def admin_recompute_calibration(
    x_admin_token: str = Header(..., alias="X-Admin-Token"),
):
    import os
    expected = os.environ.get("ADMIN_TOKEN", "")
    if not expected or x_admin_token != expected:
        raise HTTPException(status_code=403, detail="Invalid admin token")

    from services.calibration.compute import calibrate, segment, CalibrationPair
    from services.calibration import MODEL_VERSION

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT yp.field_id::text, yp.projected_tonnes_per_ha,
                   yp.season_progress_pct,
                   hr.actual_yield_tonnes,
                   f.crop_type, f.natural_region, f.variety
            FROM yield_projections yp
            JOIN harvest_records hr ON hr.field_id = yp.field_id
                                   AND hr.season_year = EXTRACT(YEAR FROM yp.projection_date)
            JOIN fields f ON f.id = yp.field_id
            WHERE yp.projected_tonnes_per_ha IS NOT NULL
              AND hr.actual_yield_tonnes IS NOT NULL
              AND hr.actual_yield_tonnes > 0
            """
        )
        rows = [dict(r) for r in cur.fetchall()]

        if not rows:
            cur.close()
            return {"status": "no_data", "message": "No paired projection/actual data found"}

        pairs = [
            CalibrationPair(
                projected=float(r["projected_tonnes_per_ha"]),
                actual=float(r["actual_yield_tonnes"]),
                crop_type=r.get("crop_type"),
                natural_region=r.get("natural_region"),
                variety=r.get("variety"),
                season_progress_pct=r.get("season_progress_pct"),
            )
            for r in rows
        ]

        segments = segment(pairs)
        written = 0
        for key, result in segments.items():
            crop, region, variety, bucket = key
            cur.execute(
                """
                INSERT INTO model_calibration
                    (crop_type, natural_region, variety, season_progress_bucket,
                     model_version, n_observations, mae_pct, rmse, bias_pct)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (crop, region, variety, bucket,
                 MODEL_VERSION, result.n, result.mae_pct, result.rmse, result.bias_pct),
            )
            written += 1

        conn.commit()
        cur.close()
    except HTTPException:
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()

    return {"status": "ok", "segments_written": written}
