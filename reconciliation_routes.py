"""
Reconciliation read API (Sprint 4): GET /tenants/{id}/reconciliation.

Joins contracted volume (grower_contracts), satellite-implied production (latest
live yield_projections × area), and delivered volume (deliveries) per grower, and
runs the pure reconciliation engine to surface side-marketing. Tenant-scoped.
"""

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor

from auth_roles import get_authenticated_user
from database import get_db_connection
from schemas import (
    AuthenticatedUser,
    GrowerReconciliationOut,
    ReconciliationResponse,
)

router = APIRouter(tags=["reconciliation"])


def _assert_tenant_access(tenant_id: str, user: AuthenticatedUser) -> None:
    if user.role == "admin" or tenant_id in {str(t) for t in user.tenant_ids}:
        return
    raise HTTPException(status_code=403, detail="Access denied")


@router.get("/tenants/{tenant_id}/reconciliation", response_model=ReconciliationResponse)
def get_reconciliation(
    tenant_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    _assert_tenant_access(tenant_id, user)

    from services.reconciliation.compute import reconcile_grower, summarize

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            "SELECT id::text AS id, name FROM growers "
            "WHERE tenant_id = %s::uuid AND deleted_at IS NULL",
            (tenant_id,),
        )
        names: Dict[str, str] = {r["id"]: r["name"] for r in cur.fetchall()}

        # Contracted volume per grower (latest season).
        cur.execute(
            """
            SELECT DISTINCT ON (grower_id)
                   grower_id::text AS grower_id, contracted_volume_tonnes
            FROM grower_contracts
            WHERE tenant_id = %s::uuid
            ORDER BY grower_id, season_year DESC, created_at DESC
            """,
            (tenant_id,),
        )
        contracted: Dict[str, float] = {
            r["grower_id"]: float(r["contracted_volume_tonnes"] or 0) for r in cur.fetchall()
        }

        # Delivered volume per grower.
        cur.execute(
            "SELECT grower_id::text AS grower_id, COALESCE(SUM(volume_tonnes),0) AS vol "
            "FROM deliveries WHERE tenant_id = %s::uuid GROUP BY grower_id",
            (tenant_id,),
        )
        delivered: Dict[str, float] = {r["grower_id"]: float(r["vol"]) for r in cur.fetchall()}

        # Satellite-implied production per grower: latest live projection per field × area.
        cur.execute(
            """
            SELECT f.grower_id::text AS grower_id,
                   COALESCE(SUM(latest.projected_tonnes_per_ha * f.size_hectares), 0) AS projected
            FROM fields f
            JOIN LATERAL (
                SELECT yp.projected_tonnes_per_ha
                FROM yield_projections yp
                WHERE yp.field_id = f.id AND yp.is_backtest = FALSE
                  AND yp.projected_tonnes_per_ha IS NOT NULL
                ORDER BY yp.projection_date DESC
                LIMIT 1
            ) latest ON TRUE
            WHERE f.tenant_id = %s::uuid AND f.grower_id IS NOT NULL
            GROUP BY f.grower_id
            """,
            (tenant_id,),
        )
        projected: Dict[str, float] = {r["grower_id"]: float(r["projected"]) for r in cur.fetchall()}

        cur.close()
    finally:
        conn.close()

    # Reconcile every grower that has any financial/production signal.
    grower_ids = set(contracted) | set(delivered) | set(projected)
    rows = [
        reconcile_grower(
            grower_id=gid,
            grower_name=names.get(gid),
            contracted=contracted.get(gid, 0.0),
            projected=projected.get(gid, 0.0),
            delivered=delivered.get(gid, 0.0),
        )
        for gid in grower_ids
    ]
    # Most concerning first: flag > watch > none, then by gap.
    order = {"flag": 0, "watch": 1, "none": 2}
    rows.sort(key=lambda r: (order.get(r.flag, 3), -r.delivery_gap_pct))

    summary = summarize(rows)

    return ReconciliationResponse(
        tenant_id=tenant_id,
        grower_count=summary.grower_count,
        flagged_count=summary.flagged_count,
        watch_count=summary.watch_count,
        total_side_marketing_tonnes=summary.total_side_marketing_tonnes,
        growers=[GrowerReconciliationOut(**vars(r)) for r in rows],
    )
