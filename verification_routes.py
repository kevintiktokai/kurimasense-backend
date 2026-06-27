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
from schemas import AuthenticatedUser, FieldVerificationResponse, InputVerificationOut
from services.field_state.aggregator import (
    FieldAccessDenied,
    FieldNotFound,
    resolve_access,
)

router = APIRouter(tags=["verification"])


@router.get("/fields/{field_id}/verification", response_model=FieldVerificationResponse)
def get_field_verification(
    field_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    try:
        resolve_access(
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
