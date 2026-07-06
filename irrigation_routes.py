"""
Irrigation recommendation API — the surface of services/irrigation.

  GET  /fields/{field_id}/irrigation/recommendation   full explainable recommendation
  GET  /irrigation/recommendations                    all my fields (planner/climatology dashboards)
  POST /fields/{field_id}/irrigation/apply            materialise as an AI planner task

Supersedes the informational ``/agro/irrigation/{field_id}`` heuristic (kept for
backward compatibility): this engine adds soil capacity, forecast netting,
planner history, amounts/durations and reasoning.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.extras import RealDictCursor
from starlette.concurrency import run_in_threadpool

from deps import verify_token
from services.irrigation import service as irrigation_service
from services.irrigation.models import IRRIGATION_METHOD_RATES_MM_PER_HOUR
from tenancy import field_scope_sql, tenant_scoped_connection

router = APIRouter(tags=["irrigation"])

_FIELD_COLUMNS = "id, user_id, name, crop_type, planting_date, polygon_coordinates"


def _load_field(field_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    with tenant_scoped_connection(user_id) as (conn, tenant_ids):
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            f"SELECT {_FIELD_COLUMNS} FROM fields WHERE id = %s AND " + field_scope_sql(),
            (field_id, tenant_ids, user_id),
        )
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None


def _load_fields(user_id: str, limit: int) -> List[Dict[str, Any]]:
    with tenant_scoped_connection(user_id) as (conn, tenant_ids):
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            f"""SELECT {_FIELD_COLUMNS} FROM fields
                WHERE planting_date IS NOT NULL AND {field_scope_sql()}
                ORDER BY created_at DESC LIMIT %s""",
            (tenant_ids, user_id, limit),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [dict(r) for r in rows]


def _validated_method(method: Optional[str]) -> Optional[str]:
    if method is None:
        return None
    if method not in IRRIGATION_METHOD_RATES_MM_PER_HOUR:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown irrigation method. Supported: {sorted(IRRIGATION_METHOD_RATES_MM_PER_HOUR)}",
        )
    return method


@router.get("/fields/{field_id}/irrigation/recommendation")
async def field_irrigation_recommendation(
    field_id: str,
    method: Optional[str] = Query(default=None, description="Irrigation method for duration estimates"),
    user_id: str = Depends(verify_token),
):
    method = _validated_method(method)
    field = await run_in_threadpool(_load_field, field_id, user_id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    rec = await irrigation_service.recommendation_for_field_row(field, method=method)
    if rec is None:
        return {
            "available": False,
            "reason": "This field needs a crop and planting date before irrigation can be modelled.",
        }
    return {"available": True, "recommendation": rec.to_dict()}


@router.get("/irrigation/recommendations")
async def my_irrigation_recommendations(
    method: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=25),
    user_id: str = Depends(verify_token),
):
    """Recommendations across the caller's planted fields — the climatology
    decision-support and planner surfaces. Fields are evaluated concurrently;
    one field failing never hides the others."""
    method = _validated_method(method)
    fields = await run_in_threadpool(_load_fields, user_id, limit)

    async def evaluate(field: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            rec = await irrigation_service.recommendation_for_field_row(field, method=method)
            return rec.to_dict() if rec else None
        except Exception as e:
            print(f"[irrigation] recommendation failed for field {field.get('id')}: {e}")
            return None

    results = await asyncio.gather(*(evaluate(f) for f in fields))
    recommendations = [r for r in results if r]
    order = {"irrigate_now": 0, "irrigate_soon": 1, "delay_rain_expected": 2, "monitor": 3, "not_needed": 4}
    recommendations.sort(key=lambda r: order.get(r["action"], 9))
    return {
        "recommendations": recommendations,
        "evaluated_fields": len(fields),
        "actionable": sum(1 for r in recommendations if r["action"] in ("irrigate_now", "irrigate_soon")),
    }


@router.post("/fields/{field_id}/irrigation/apply")
async def apply_irrigation_recommendation(
    field_id: str,
    method: Optional[str] = Query(default=None),
    user_id: str = Depends(verify_token),
):
    """Recompute the recommendation and add it to the planner as an
    AI-generated irrigation task (idempotent per field/day)."""
    method = _validated_method(method)
    field = await run_in_threadpool(_load_field, field_id, user_id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    rec = await irrigation_service.recommendation_for_field_row(field, method=method)
    if rec is None:
        raise HTTPException(status_code=422, detail="Field has no crop/planting date to model")
    if rec.action not in ("irrigate_now", "irrigate_soon"):
        return {"applied": False, "reason": rec.headline, "recommendation": rec.to_dict()}
    # The task belongs to the caller even when fields.user_id is stale/empty.
    field = {**field, "user_id": field.get("user_id") or user_id}
    task = await run_in_threadpool(irrigation_service.ensure_planner_task, field, rec)
    if not task:
        raise HTTPException(status_code=500, detail="Could not create planner task")
    return {"applied": True, "task": task, "recommendation": rec.to_dict()}
