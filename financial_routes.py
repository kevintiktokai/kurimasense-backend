"""
Financial / exposure routes (Sprint 2).
Contracts, disbursements, deliveries (tenant-scoped CRUD) + the exposure engine read.
All queries filter by tenant_id from get_authenticated_user; 403-vs-404 enforced.
"""

from datetime import date, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor

from auth_roles import get_authenticated_user
from database import get_db_connection
from tenancy import arm_rls_gucs
from schemas import (
    AuthenticatedUser,
    Contract,
    CreateContractRequest,
    CreateDeliveryRequest,
    CreateDisbursementRequest,
    Delivery,
    Disbursement,
    ExposureResponse,
    GrowerExposureOut,
    WeeklyExposureOut,
)

router = APIRouter(tags=["financial"])

_CONTRACT_COLS = (
    "id::text AS id, tenant_id::text AS tenant_id, grower_id::text AS grower_id, "
    "season_year, crop_type, contracted_volume_tonnes, contract_price_per_tonne, "
    "input_credit_value, status, created_at"
)
_DISBURSE_COLS = (
    "id::text AS id, tenant_id::text AS tenant_id, grower_id::text AS grower_id, "
    "contract_id::text AS contract_id, disbursement_date, input_type, quantity, "
    "unit, credit_value, created_at"
)
_DELIVERY_COLS = (
    "id::text AS id, tenant_id::text AS tenant_id, grower_id::text AS grower_id, "
    "contract_id::text AS contract_id, field_id::text AS field_id, delivery_date, "
    "volume_tonnes, price_per_tonne, quality_grade, value_usd, created_at"
)


def _assert_tenant_access(tenant_id: str, user: AuthenticatedUser) -> None:
    if user.role == "admin":
        return
    if tenant_id in {str(t) for t in user.tenant_ids}:
        return
    raise HTTPException(status_code=403, detail="Access denied")


def _conn_or_503(user: AuthenticatedUser, tenant_id: str):
    """Checked-out connection with the RLS GUCs armed (FORCE-ready).

    `tenant_id` is the path tenant, ALREADY authorized by `_assert_tenant_access`;
    it is unioned in so admins (who may not be members) keep access under FORCE.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    scoped = {str(t) for t in user.tenant_ids} | {str(tenant_id)}
    arm_rls_gucs(conn, user.user_id, sorted(scoped))
    return conn


def _verify_grower(cur, grower_id: str, tenant_id: str) -> None:
    """404 if grower doesn't exist, 403 if it belongs to another tenant."""
    cur.execute(
        "SELECT tenant_id::text AS tenant_id FROM growers "
        "WHERE id = %s::uuid AND deleted_at IS NULL",
        (grower_id,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Grower not found")
    if str(row["tenant_id"]) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Grower belongs to another tenant")


# --------------------------------------------------------------------------
# Contracts
# --------------------------------------------------------------------------
@router.post("/tenants/{tenant_id}/contracts", response_model=Contract, status_code=201)
def create_contract(
    tenant_id: str,
    body: CreateContractRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    _assert_tenant_access(tenant_id, user)
    conn = _conn_or_503(user, tenant_id)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        _verify_grower(cur, body.grower_id, tenant_id)
        cur.execute(
            "INSERT INTO grower_contracts "
            "(tenant_id, grower_id, season_year, crop_type, contracted_volume_tonnes, "
            " contract_price_per_tonne, input_credit_value, status) "
            "VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s) "
            "RETURNING " + _CONTRACT_COLS,
            (tenant_id, body.grower_id, body.season_year, body.crop_type,
             body.contracted_volume_tonnes, body.contract_price_per_tonne,
             body.input_credit_value, body.status or "active"),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()
    return Contract(**dict(row))


@router.get("/tenants/{tenant_id}/contracts", response_model=List[Contract])
def list_contracts(
    tenant_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    _assert_tenant_access(tenant_id, user)
    conn = _conn_or_503(user, tenant_id)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT " + _CONTRACT_COLS + " FROM grower_contracts "
            "WHERE tenant_id = %s::uuid ORDER BY season_year DESC, created_at DESC",
            (tenant_id,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
    finally:
        conn.close()
    return [Contract(**r) for r in rows]


# --------------------------------------------------------------------------
# Disbursements
# --------------------------------------------------------------------------
@router.post("/tenants/{tenant_id}/disbursements", response_model=Disbursement, status_code=201)
def create_disbursement(
    tenant_id: str,
    body: CreateDisbursementRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    _assert_tenant_access(tenant_id, user)
    conn = _conn_or_503(user, tenant_id)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        _verify_grower(cur, body.grower_id, tenant_id)
        cur.execute(
            "INSERT INTO input_disbursements "
            "(tenant_id, grower_id, contract_id, disbursement_date, input_type, "
            " quantity, unit, credit_value) "
            "VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s, %s) "
            "RETURNING " + _DISBURSE_COLS,
            (tenant_id, body.grower_id, body.contract_id, body.disbursement_date,
             body.input_type, body.quantity, body.unit, body.credit_value),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()
    return Disbursement(**dict(row))


@router.get("/tenants/{tenant_id}/disbursements", response_model=List[Disbursement])
def list_disbursements(
    tenant_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    _assert_tenant_access(tenant_id, user)
    conn = _conn_or_503(user, tenant_id)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT " + _DISBURSE_COLS + " FROM input_disbursements "
            "WHERE tenant_id = %s::uuid ORDER BY disbursement_date DESC, created_at DESC",
            (tenant_id,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
    finally:
        conn.close()
    return [Disbursement(**r) for r in rows]


# --------------------------------------------------------------------------
# Deliveries
# --------------------------------------------------------------------------
@router.post("/tenants/{tenant_id}/deliveries", response_model=Delivery, status_code=201)
def create_delivery(
    tenant_id: str,
    body: CreateDeliveryRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    _assert_tenant_access(tenant_id, user)
    value_usd = None
    if body.price_per_tonne is not None:
        value_usd = round(body.volume_tonnes * body.price_per_tonne, 2)
    conn = _conn_or_503(user, tenant_id)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        _verify_grower(cur, body.grower_id, tenant_id)
        cur.execute(
            "INSERT INTO deliveries "
            "(tenant_id, grower_id, contract_id, field_id, delivery_date, "
            " volume_tonnes, price_per_tonne, quality_grade, value_usd) "
            "VALUES (%s::uuid, %s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s, %s) "
            "RETURNING " + _DELIVERY_COLS,
            (tenant_id, body.grower_id, body.contract_id, body.field_id,
             body.delivery_date, body.volume_tonnes, body.price_per_tonne,
             body.quality_grade, value_usd),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    except HTTPException:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()
    return Delivery(**dict(row))


@router.get("/tenants/{tenant_id}/deliveries", response_model=List[Delivery])
def list_deliveries(
    tenant_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    _assert_tenant_access(tenant_id, user)
    conn = _conn_or_503(user, tenant_id)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT " + _DELIVERY_COLS + " FROM deliveries "
            "WHERE tenant_id = %s::uuid ORDER BY delivery_date DESC, created_at DESC",
            (tenant_id,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
    finally:
        conn.close()
    return [Delivery(**r) for r in rows]


# --------------------------------------------------------------------------
# Exposure read (the engine)
# --------------------------------------------------------------------------
def _days_to_maturity(variety: Optional[str], crop: Optional[str]) -> int:
    try:
        from proactive_intelligence import get_variety_info
        info = get_variety_info(variety) if variety else None
        if info and info.get("days_to_maturity"):
            return int(info["days_to_maturity"])
    except Exception:
        pass
    return 140


@router.get("/tenants/{tenant_id}/exposure", response_model=ExposureResponse)
def get_exposure(
    tenant_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    _assert_tenant_access(tenant_id, user)

    from datetime import datetime
    from services.calibration import MODEL_VERSION
    from services.exposure.compute import (
        GrowerExposure,
        build_portfolio_exposure,
        grower_net_exposure,
        repayment_likelihood,
    )
    from services.field_state.aggregator import _fetch_yield, assemble_field_state

    conn = _conn_or_503(user, tenant_id)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Growers in this tenant.
        cur.execute(
            "SELECT id::text AS id, name FROM growers "
            "WHERE tenant_id = %s::uuid AND deleted_at IS NULL",
            (tenant_id,),
        )
        growers = {r["id"]: r["name"] for r in cur.fetchall()}

        # Fields (+ their grower) for this tenant.
        cur.execute(
            "SELECT f.*, f.id::text AS id, f.grower_id::text AS grower_id "
            "FROM fields f WHERE f.tenant_id = %s::uuid",
            (tenant_id,),
        )
        field_rows = [dict(r) for r in cur.fetchall()]
        field_ids = [str(r["id"]) for r in field_rows]

        logs_by_field: Dict[str, list] = {}
        if field_ids:
            cur.execute(
                "SELECT field_id::text AS field_id, log_date, ndvi, evi, soil_moisture, cloud_cover "
                "FROM daily_logs WHERE field_id = ANY(%s::uuid[]) ORDER BY field_id, log_date ASC",
                (field_ids,),
            )
            for r in cur.fetchall():
                logs_by_field.setdefault(r["field_id"], []).append(dict(r))

        # Contracts (price + contracted volume) per grower for the latest season.
        cur.execute(
            "SELECT grower_id::text AS grower_id, season_year, crop_type, "
            "contracted_volume_tonnes, contract_price_per_tonne, input_credit_value "
            "FROM grower_contracts WHERE tenant_id = %s::uuid "
            "ORDER BY grower_id, season_year DESC",
            (tenant_id,),
        )
        contracts_by_grower: Dict[str, list] = {}
        for r in cur.fetchall():
            contracts_by_grower.setdefault(r["grower_id"], []).append(dict(r))

        # Disbursed credit per grower.
        cur.execute(
            "SELECT grower_id::text AS grower_id, COALESCE(SUM(credit_value),0) AS credit "
            "FROM input_disbursements WHERE tenant_id = %s::uuid GROUP BY grower_id",
            (tenant_id,),
        )
        disbursed_by_grower = {r["grower_id"]: float(r["credit"]) for r in cur.fetchall()}

        # Delivered volume per grower (history, for repayment likelihood).
        cur.execute(
            "SELECT grower_id::text AS grower_id, COALESCE(SUM(volume_tonnes),0) AS vol "
            "FROM deliveries WHERE tenant_id = %s::uuid GROUP BY grower_id",
            (tenant_id,),
        )
        delivered_by_grower = {r["grower_id"]: float(r["vol"]) for r in cur.fetchall()}

        cur.close()
    finally:
        conn.close()

    now = datetime.utcnow()

    # Per-grower projected volume + score from field state (read, never recompute).
    proj_volume_by_grower: Dict[str, float] = {}
    score_sum_by_grower: Dict[str, float] = {}
    score_n_by_grower: Dict[str, int] = {}
    field_count_by_grower: Dict[str, int] = {}
    harvest_by_grower: Dict[str, Optional[date]] = {}

    for fr in field_rows:
        gid = fr.get("grower_id")
        if not gid:
            continue
        fid = str(fr["id"])
        logs = logs_by_field.get(fid, [])
        yield_raw = _fetch_yield(fr, logs)
        fs = assemble_field_state(
            field_row=fr, requester_id=None, daily_logs=logs,
            yield_raw=yield_raw, now=now, enforce_owner=False,
        )
        size_ha = float(fr.get("size_hectares") or 0)
        tph = fs.yield_projection.projected_tonnes_per_ha
        if tph is not None:
            proj_volume_by_grower[gid] = proj_volume_by_grower.get(gid, 0.0) + tph * size_ha

        has_data = fs.indices.current.observation_quality != "none"
        if has_data and fs.kurima_score.score is not None:
            score_sum_by_grower[gid] = score_sum_by_grower.get(gid, 0.0) + fs.kurima_score.score
            score_n_by_grower[gid] = score_n_by_grower.get(gid, 0) + 1

        field_count_by_grower[gid] = field_count_by_grower.get(gid, 0) + 1

        # Earliest expected harvest across a grower's fields = when exposure first resolves.
        planting = fr.get("planting_date")
        if planting:
            if isinstance(planting, str):
                try:
                    planting = date.fromisoformat(planting)
                except ValueError:
                    planting = None
        if planting:
            dtm = _days_to_maturity(fr.get("variety"), fr.get("crop_type"))
            harvest = planting + timedelta(days=dtm)
            cur_h = harvest_by_grower.get(gid)
            if cur_h is None or harvest < cur_h:
                harvest_by_grower[gid] = harvest

    # Only growers with a financial relationship (contract or disbursement) carry exposure.
    relevant = set(contracts_by_grower) | set(disbursed_by_grower)

    grower_exposures: List[GrowerExposure] = []
    for gid in relevant:
        contracts = contracts_by_grower.get(gid, [])
        latest = contracts[0] if contracts else None
        price = float(latest["contract_price_per_tonne"]) if latest and latest.get("contract_price_per_tonne") else 0.0
        contracted_total = sum(float(c.get("contracted_volume_tonnes") or 0) for c in contracts)

        # input_credit_value: actual disbursements, fallback to contract credit value.
        credit = disbursed_by_grower.get(gid, 0.0)
        if credit == 0.0 and latest and latest.get("input_credit_value"):
            credit = float(latest["input_credit_value"])

        projected_volume = proj_volume_by_grower.get(gid, 0.0)

        n = score_n_by_grower.get(gid, 0)
        avg_score = (score_sum_by_grower[gid] / n) if n else None

        delivered = delivered_by_grower.get(gid, 0.0)
        delivery_ratio = (delivered / contracted_total) if contracted_total > 0 else None

        likelihood = repayment_likelihood(avg_score, delivery_ratio)
        net = grower_net_exposure(credit, projected_volume, price, likelihood)

        grower_exposures.append(GrowerExposure(
            grower_id=gid,
            grower_name=growers.get(gid),
            input_credit_value=round(credit, 2),
            projected_volume_tonnes=round(projected_volume, 2),
            price_per_tonne=price,
            repayment_likelihood=likelihood,
            net_exposure=net,
            expected_harvest_date=harvest_by_grower.get(gid),
            kurima_score=avg_score,
            field_count=field_count_by_grower.get(gid, 0),
        ))

    portfolio = build_portfolio_exposure(grower_exposures)

    return ExposureResponse(
        tenant_id=tenant_id,
        total_net_exposure=portfolio.total_net_exposure,
        total_input_credit=portfolio.total_input_credit,
        total_expected_recoverable=portfolio.total_expected_recoverable,
        grower_count=portfolio.grower_count,
        model_version=MODEL_VERSION,
        growers=[GrowerExposureOut(**vars(g)) for g in portfolio.growers],
        weekly=[WeeklyExposureOut(**vars(w)) for w in portfolio.weekly],
    )
