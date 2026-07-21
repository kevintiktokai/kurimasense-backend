"""
Zone-level field analysis (field sections).

    GET  /fields/{field_id}/sections            — zones + latest per-zone NDVI
    POST /fields/{field_id}/sections/analyze    — sample satellite per zone

Splits the field polygon into a grid of walkable zones (default 2×2 with
compass names) and samples crop health at each zone's centroid, so analysis
says WHERE the problem is, not just that there is one. Light router in the
season_routes mold: principal dependency + aggregator ``resolve_access`` for
field access (404 unknown / 403 denied). Zone geometry is pure
(``field_sections.py``); persistence is one row per zone per batch in
``field_section_analysis``.
"""

from __future__ import annotations

import json
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from psycopg2.extras import RealDictCursor

from field_sections import compute_sections
from season_routes import get_principal
from services.field_state.aggregator import (
    resolve_access, FieldNotFound, FieldAccessDenied,
)

router = APIRouter(tags=["sections"])

MAX_GRID = 3  # 2 → 4 zones (default), 3 → 9 zones; beyond that zones stop being walkable guidance


def _resolve_field(field_id: str, principal: dict) -> dict:
    try:
        return resolve_access(
            field_id, principal["requester_id"],
            tenant_ids=principal.get("tenant_ids"),
            is_admin=principal.get("is_admin", False),
        )
    except FieldNotFound:
        raise HTTPException(status_code=404, detail="Field not found")
    except FieldAccessDenied:
        raise HTTPException(status_code=403, detail="Access denied")


def _polygon_of(field: dict) -> list:
    coords = field.get("polygon_coordinates")
    if isinstance(coords, str):
        try:
            coords = json.loads(coords)
        except (ValueError, TypeError):
            coords = []
    return coords if isinstance(coords, list) else []


@router.get("/fields/{field_id}/sections")
def get_field_sections(
    field_id: str,
    grid: int = Query(2, ge=1, le=MAX_GRID),
    principal: dict = Depends(get_principal),
):
    """Zones for the field plus the most recent per-zone analysis (if any).

    Always returns the zone geometry — a field that has never been
    zone-analyzed still renders its grid in the UI, with ``ndvi: null``.
    """
    field = _resolve_field(field_id, principal)
    sections = compute_sections(_polygon_of(field), grid=grid)
    if not sections:
        raise HTTPException(status_code=422, detail="Field has no usable boundary polygon")

    latest: dict = {}
    analyzed_at = None
    from database import get_db_connection
    conn = get_db_connection()
    if conn:
        try:
            from tenancy import arm_rls_gucs
            arm_rls_gucs(conn, principal["requester_id"],
                         [str(field["tenant_id"])] if field.get("tenant_id") else [])
            cur = conn.cursor(cursor_factory=RealDictCursor)
            # Latest batch for this field+grid = rows sharing the newest batch_id.
            cur.execute(
                """
                SELECT section_index, ndvi, evi, cloud_cover, status, error,
                       created_at
                FROM field_section_analysis
                WHERE field_id = %s::uuid AND grid_size = %s
                  AND batch_id = (
                      SELECT batch_id FROM field_section_analysis
                      WHERE field_id = %s::uuid AND grid_size = %s
                      ORDER BY created_at DESC LIMIT 1
                  )
                """,
                (field_id, grid, field_id, grid),
            )
            for row in cur.fetchall():
                latest[row["section_index"]] = row
                if row["created_at"] and (analyzed_at is None or row["created_at"] > analyzed_at):
                    analyzed_at = row["created_at"]
            cur.close()
        except Exception as e:
            print(f"[sections] latest-batch read failed (serving geometry only): {e}")
        finally:
            conn.close()

    out = []
    for s in sections:
        row = latest.get(s["index"], {})
        out.append({
            **s,
            "ndvi": float(row["ndvi"]) if row.get("ndvi") is not None else None,
            "evi": float(row["evi"]) if row.get("evi") is not None else None,
            "cloud_cover": row.get("cloud_cover"),
            "status": row.get("status"),
            "sampled_at": row["created_at"].isoformat() if row.get("created_at") else None,
        })

    return {
        "field_id": field_id,
        "grid": grid,
        "analyzed_at": analyzed_at.isoformat() if analyzed_at else None,
        "sections": out,
    }


def _run_section_analysis(field_id: str, tenant_id: Optional[str],
                          sections: list, grid: int):
    """Background task: sample crop health at each zone centroid and persist
    one batch. Mirrors trigger_sentinel_analysis' service posture (RLS armed
    with the already-authorized field's tenant)."""
    from database import get_db_connection
    from tools.get_crop_health import run as run_crop_health

    conn = get_db_connection()
    if not conn:
        print(f"[sections] analysis skipped for {field_id}: database unavailable")
        return
    try:
        from tenancy import arm_rls_gucs, arm_rls_gucs_all_tenants
        if tenant_id:
            arm_rls_gucs(conn, "service:section_analysis", [str(tenant_id)])
        else:
            arm_rls_gucs_all_tenants(conn, service_user="service:section_analysis")

        batch_id = str(uuid.uuid4())
        cur = conn.cursor(cursor_factory=RealDictCursor)
        for s in sections:
            c = s.get("centroid") or {}
            ndvi = evi = cloud = None
            status, error = "ok", None
            try:
                result = run_crop_health(c["lat"], c["lon"])
                if result.get("status") == "error":
                    status, error = "error", str(result.get("error_message"))[:300]
                else:
                    data = result.get("data", {})
                    ndvi = data.get("ndvi_mean")
                    evi = data.get("evi_mean")
                    cloud = data.get("cloud_cover_pct")
            except Exception as e:
                status, error = "error", str(e)[:300]

            cur.execute(
                """
                INSERT INTO field_section_analysis
                    (field_id, tenant_id, batch_id, grid_size, section_index,
                     section_label, polygon, centroid, area_share,
                     ndvi, evi, cloud_cover, status, error)
                VALUES (%s::uuid, %s, %s::uuid, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s)
                """,
                (field_id, tenant_id, batch_id, grid, s["index"], s["label"],
                 json.dumps(s["polygon"]), json.dumps(s.get("centroid")),
                 s.get("area_share"), ndvi, evi, cloud, status, error),
            )
        conn.commit()
        cur.close()
        print(f"[sections] batch {batch_id} complete for field {field_id} ({len(sections)} zones)")
    except Exception as e:
        print(f"[sections] analysis failed for {field_id}: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()


@router.post("/fields/{field_id}/sections/analyze", status_code=202)
def analyze_field_sections(
    field_id: str,
    background_tasks: BackgroundTasks,
    grid: int = Query(2, ge=1, le=MAX_GRID),
    principal: dict = Depends(get_principal),
):
    """Kick off per-zone satellite sampling (background; ~seconds per zone).
    Client polls GET /fields/{id}/sections until ``analyzed_at`` advances."""
    field = _resolve_field(field_id, principal)
    sections = compute_sections(_polygon_of(field), grid=grid)
    if not sections:
        raise HTTPException(status_code=422, detail="Field has no usable boundary polygon")

    tenant_id = str(field["tenant_id"]) if field.get("tenant_id") else None
    background_tasks.add_task(_run_section_analysis, field_id, tenant_id, sections, grid)
    return {"status": "started", "zones": len(sections), "grid": grid}
