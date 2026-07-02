"""
Verification read API (Sprint 4): GET /fields/{id}/verification.

Checks each logged input (field_inputs) against the field's NDVI trajectory
(daily_logs) to confirm a canopy response — flagging inputs that show none.
Tenant-scoped via the canonical resolve_access pattern (403-vs-404).
"""

from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor

from auth_roles import get_authenticated_user
from database import get_db_connection
from tenancy import arm_rls_gucs
from schemas import (
    AuthenticatedUser,
    FieldVerificationResponse,
    FieldVerificationSummary,
    InputVerificationOut,
    PortfolioVerificationResponse,
)
from services.field_state.aggregator import (
    FieldAccessDenied,
    FieldNotFound,
    resolve_access,
)

router = APIRouter(tags=["verification"])


def _assert_tenant_access(tenant_id: str, user: AuthenticatedUser) -> None:
    if user.role == "admin" or tenant_id in {str(t) for t in user.tenant_ids}:
        return
    raise HTTPException(status_code=403, detail="Access denied")


@router.get("/fields/{field_id}/verification", response_model=FieldVerificationResponse)
def get_field_verification(
    field_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    try:
        field_row = resolve_access(
            field_id, user.user_id,
            tenant_ids=user.tenant_ids, is_admin=user.role == "admin",
        )
    except FieldNotFound:
        raise HTTPException(status_code=404, detail="Field not found")
    except FieldAccessDenied:
        raise HTTPException(status_code=403, detail="Access denied")

    from services.verification.compute import InputEvent, NdviPoint, verify_field

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    # Arm the RLS GUCs (FORCE-ready): field_inputs/daily_logs policies scope
    # through the parent field's tenant, so union the resolved field's tenant in
    # (covers admins who aren't members of that tenant).
    scoped = {str(t) for t in user.tenant_ids}
    if field_row.get("tenant_id"):
        scoped.add(str(field_row["tenant_id"]))
    arm_rls_gucs(conn, user.user_id, sorted(scoped))
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT input_type, input_date FROM field_inputs "
            "WHERE field_id = %s::uuid AND input_date IS NOT NULL ORDER BY input_date",
            (field_id,),
        )
        events = [
            InputEvent(input_date=r["input_date"], input_type=r.get("input_type"))
            for r in cur.fetchall()
        ]
        cur.execute(
            "SELECT log_date, ndvi FROM daily_logs "
            "WHERE field_id = %s::uuid AND ndvi IS NOT NULL ORDER BY log_date",
            (field_id,),
        )
        series = [NdviPoint(obs_date=r["log_date"], ndvi=float(r["ndvi"])) for r in cur.fetchall()]
        cur.close()
    finally:
        conn.close()

    fv = verify_field(events, series)
    return FieldVerificationResponse(
        field_id=field_id,
        n_inputs=fv.n_inputs,
        n_verified=fv.n_verified,
        n_flagged=fv.n_flagged,
        n_unknown=fv.n_unknown,
        verification_pct=fv.verification_pct,
        inputs=[InputVerificationOut(**vars(i)) for i in fv.inputs],
    )


@router.get("/tenants/{tenant_id}/verification", response_model=PortfolioVerificationResponse)
def get_portfolio_verification(
    tenant_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Attention-allocation rollup: which fields have unverified inputs across the
    whole book. Batch-loads inputs + NDVI for the tenant's fields and runs the
    verification engine per field (no per-field round trips)."""
    _assert_tenant_access(tenant_id, user)

    from services.verification.compute import (
        InputEvent,
        NdviPoint,
        rollup_portfolio,
        verify_field,
    )

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    # Arm the RLS GUCs (FORCE-ready); path tenant already authorized above.
    arm_rls_gucs(conn, user.user_id, sorted({str(t) for t in user.tenant_ids} | {str(tenant_id)}))
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT f.id::text AS id, f.name, g.name AS grower_name
            FROM fields f
            LEFT JOIN growers g ON g.id = f.grower_id AND g.deleted_at IS NULL
            WHERE f.tenant_id = %s::uuid
            """,
            (tenant_id,),
        )
        field_rows = cur.fetchall()
        field_ids = [r["id"] for r in field_rows]

        inputs_by_field: dict = {}
        ndvi_by_field: dict = {}
        if field_ids:
            cur.execute(
                "SELECT field_id::text AS field_id, input_type, input_date FROM field_inputs "
                "WHERE field_id = ANY(%s::uuid[]) AND input_date IS NOT NULL",
                (field_ids,),
            )
            for r in cur.fetchall():
                inputs_by_field.setdefault(r["field_id"], []).append(
                    InputEvent(input_date=r["input_date"], input_type=r.get("input_type"))
                )
            cur.execute(
                "SELECT field_id::text AS field_id, log_date, ndvi FROM daily_logs "
                "WHERE field_id = ANY(%s::uuid[]) AND ndvi IS NOT NULL ORDER BY log_date",
                (field_ids,),
            )
            for r in cur.fetchall():
                ndvi_by_field.setdefault(r["field_id"], []).append(
                    NdviPoint(obs_date=r["log_date"], ndvi=float(r["ndvi"]))
                )
        cur.close()
    finally:
        conn.close()

    summaries = []
    per_field = []
    for fr in field_rows:
        fid = fr["id"]
        events = inputs_by_field.get(fid, [])
        if not events:
            continue  # only surface fields that have logged inputs
        fv = verify_field(events, ndvi_by_field.get(fid, []))
        per_field.append(fv)
        summaries.append(FieldVerificationSummary(
            field_id=fid,
            field_name=fr.get("name"),
            grower_name=fr.get("grower_name"),
            n_inputs=fv.n_inputs,
            n_verified=fv.n_verified,
            n_flagged=fv.n_flagged,
            n_unknown=fv.n_unknown,
            verification_pct=fv.verification_pct,
        ))

    # Most flagged first (attention allocation).
    summaries.sort(key=lambda s: (-s.n_flagged, -(s.n_inputs)))
    roll = rollup_portfolio(per_field)

    return PortfolioVerificationResponse(
        tenant_id=tenant_id,
        field_count=roll.field_count,
        fields_with_flagged=roll.fields_with_flagged,
        total_flagged_inputs=roll.total_flagged_inputs,
        total_inputs=roll.total_inputs,
        fields=summaries,
    )
