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
from tenancy import arm_rls_gucs, arm_rls_gucs_all_tenants
from schemas import (
    AuthenticatedUser,
    CalibrationEntry,
    CalibrationResponse,
    CreateHarvestRequest,
    HarvestRecord,
)

router = APIRouter(tags=["outcome-loop"])

# Explicit column list with UUID->text casts (matches grower_routes convention).
_HARVEST_COLS = (
    "id::text AS id, field_id::text AS field_id, grower_id::text AS grower_id, "
    "tenant_id::text AS tenant_id, season_year, season_type, crop_type, variety, "
    "planting_date, harvest_date, area_harvested_ha, actual_yield_tonnes, "
    "quality_grade, moisture_at_harvest, sale_price_per_tonne, delivered_to_tenant, "
    "source, notes, created_at"
)


def _resolve_field_for_tenant(field_id: str, user: AuthenticatedUser) -> dict:
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    try:
        # FORCE-ready: under FORCE the unfiltered lookup only sees the caller's
        # tenants (cross-tenant probes become 404; see resolve_access note).
        arm_rls_gucs(conn, user.user_id, [str(t) for t in user.tenant_ids])
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id::text AS id, user_id::text AS user_id,
                   tenant_id::text AS tenant_id, grower_id::text AS grower_id,
                   crop_type, variety, planting_date
            FROM fields WHERE id = %s::uuid
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
    # FORCE-ready: WITH CHECK on harvest_records requires the row's tenant in
    # the GUC — union the resolved field's tenant (covers admin writers).
    scoped = {str(t) for t in user.tenant_ids}
    if field.get("tenant_id"):
        scoped.add(str(field["tenant_id"]))
    arm_rls_gucs(conn, user.user_id, sorted(scoped))
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
            RETURNING """ + _HARVEST_COLS + """
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
    field = _resolve_field_for_tenant(field_id, user)

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    scoped = {str(t) for t in user.tenant_ids}
    if field.get("tenant_id"):
        scoped.add(str(field["tenant_id"]))
    arm_rls_gucs(conn, user.user_id, sorted(scoped))
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT " + _HARVEST_COLS + " FROM harvest_records "
            "WHERE field_id = %s::uuid "
            "ORDER BY season_year DESC, created_at DESC",
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
    # FORCE-ready: harvest_records reads scope by tenant; model_calibration is
    # global (deliberate USING(true) policy, migration 011 — aggregate model
    # stats, no tenant PII).
    arm_rls_gucs(conn, user.user_id, sorted({str(t) for t in user.tenant_ids} | {str(tenant_id)}))
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

        # Latest row per segment within the latest model_version, so repeated
        # recomputes don't surface stale duplicate segments.
        cur.execute(
            """
            SELECT DISTINCT ON
                   (crop_type, natural_region, variety, season_progress_bucket)
                   crop_type, natural_region, variety, season_progress_bucket,
                   model_version, n_observations, mae_pct, rmse, bias_pct, computed_at
            FROM model_calibration
            WHERE model_version = (
                SELECT model_version FROM model_calibration
                ORDER BY computed_at DESC LIMIT 1
            )
            AND (crop_type IS NULL OR crop_type = ANY(%s))
            ORDER BY crop_type, natural_region, variety, season_progress_bucket,
                     computed_at DESC
            """,
            (list(tenant_crops) if tenant_crops else ["__none__"],),
        )
        rows = [dict(r) for r in cur.fetchall()]

        # "Validated" means the calibration is backed by real harvest actuals.
        # All three sources (grower_logged, historical_backfill, institution_recorded)
        # represent real-world records — a contractor's imported book is exactly the
        # historical_backfill path. Demo-seeded fields (name LIKE 'DEMO_SEED:%') are
        # explicitly excluded: fabricated actuals on demo fields must NEVER read as
        # validated (the honesty caveat — demo data must not masquerade as the number).
        cur.execute(
            """
            SELECT EXISTS(
                SELECT 1 FROM harvest_records hr
                JOIN fields f ON f.id = hr.field_id
                WHERE hr.tenant_id = %s::uuid
                  AND hr.actual_yield_tonnes IS NOT NULL
                  AND f.name NOT LIKE 'DEMO_SEED:%%'
            ) AS has_actuals
            """,
            (tenant_id,),
        )
        has_real_actuals = bool(cur.fetchone()["has_actuals"])

        cur.close()
    finally:
        conn.close()

    entries = [CalibrationEntry(**r) for r in rows]

    # Headline = the primary crop's figure at the latest (closest-to-harvest)
    # season-progress bucket. Order buckets explicitly so "unknown" never wins.
    _BUCKET_RANK = {"0-50%": 1, "50-70%": 2, "70-100%": 3, "unknown": 0}
    headline_mae = None
    headline_crop = None
    headline_bucket = None
    if entries:
        best = max(
            entries,
            key=lambda e: (
                _BUCKET_RANK.get(e.season_progress_bucket or "unknown", 0),
                e.n_observations,
            ),
        )
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
    # Global service path (admin-token-gated): calibration pairs projections
    # with actuals across ALL tenants by design — arm the all-tenant grant.
    arm_rls_gucs_all_tenants(conn, service_user="service:calibration_recompute")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT yp.field_id::text, yp.projected_tonnes_per_ha,
                   yp.season_progress_pct,
                   hr.actual_yield_tonnes,
                   f.crop_type, f.natural_region, f.variety
            FROM yield_projections yp
            JOIN harvest_records hr
              ON hr.field_id = yp.field_id
             AND hr.planting_date IS NOT NULL
             AND yp.projection_date >= hr.planting_date
             AND yp.projection_date <= COALESCE(
                     hr.harvest_date, hr.planting_date + INTERVAL '365 days')
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
