"""
Agronomist activities + field assignments (institutional operations, 013)
=========================================================================
The professional field timeline and the operational assignment workflow:

  Activities
  * POST   /fields/{id}/activities          — log a visit / recommendation /
                                              observation / consultation.
  * GET    /fields/{id}/activities          — the field's permanent timeline.
  * PATCH  /activities/{activity_id}        — edit (author or team manager).
  * DELETE /activities/{activity_id}        — delete incorrect records (same).
  * GET    /team/activity                   — tenant-wide recent activity feed.

  Assignments
  * POST   /fields/{id}/assign              — assign / reassign / unassign.
  * GET    /fields/{id}/assignments         — assignment history (active first).
  * GET    /team/workload                   — active field count per member.

Access reuses the canonical `resolve_access` gate (admin / tenant membership /
legacy owner) so consumer AND institutional callers get correct 403-vs-404
behaviour — the same shape as the scouting and soil routes.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.extras import RealDictCursor

from auth_roles import get_authenticated_user, user_can_assign_fields
from database import get_db_connection
from tenancy import arm_rls_gucs
from schemas import (
    AuthenticatedUser, CreateActivityRequest, UpdateActivityRequest,
    FieldActivity, AssignFieldRequest, FieldAssignment,
)
from services.field_state.aggregator import (
    FieldAccessDenied, FieldNotFound, resolve_access,
)

router = APIRouter(tags=["activities"])

_ACTIVITY_COLS = (
    "a.id::text AS id, a.field_id::text AS field_id, a.tenant_id::text AS tenant_id, "
    "a.user_id::text AS user_id, a.activity_type, a.title, a.notes, a.recommendation, "
    "a.visit_date, a.lat, a.lon, a.photo_url, a.created_at, "
    "COALESCE(tm.display_name, p.full_name) AS author_name"
)
_ACTIVITY_JOINS = (
    "LEFT JOIN profiles p ON p.id = a.user_id "
    "LEFT JOIN tenant_members tm ON tm.user_id = a.user_id AND tm.tenant_id = a.tenant_id"
)


def _resolve(field_id: str, user: AuthenticatedUser) -> dict:
    try:
        return resolve_access(
            field_id, user.user_id,
            tenant_ids=user.tenant_ids,
            is_admin=user.role == "admin",
        )
    except FieldNotFound:
        raise HTTPException(status_code=404, detail="Field not found")
    except FieldAccessDenied:
        raise HTTPException(status_code=403, detail="Access denied")


def _scoped_conn(user: AuthenticatedUser, field: Optional[dict] = None):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database unavailable")
    scoped = {str(t) for t in user.tenant_ids}
    if field and field.get("tenant_id"):
        scoped.add(str(field["tenant_id"]))
    arm_rls_gucs(conn, user.user_id, sorted(scoped))
    return conn


def _iso(v):
    return v.isoformat() if hasattr(v, "isoformat") else (str(v) if v else None)


def _activity_from_row(r: dict) -> FieldActivity:
    return FieldActivity(
        id=r["id"], field_id=r["field_id"], tenant_id=r.get("tenant_id"),
        user_id=r["user_id"], author_name=r.get("author_name"),
        activity_type=r["activity_type"], title=r["title"],
        notes=r.get("notes"), recommendation=r.get("recommendation"),
        visit_date=_iso(r.get("visit_date")), lat=r.get("lat"), lon=r.get("lon"),
        photo_url=r.get("photo_url"), created_at=_iso(r.get("created_at")),
        field_name=r.get("field_name"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Activities
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/fields/{field_id}/activities", response_model=FieldActivity, status_code=201)
def create_activity(field_id: str, body: CreateActivityRequest,
                    user: AuthenticatedUser = Depends(get_authenticated_user)):
    field = _resolve(field_id, user)
    conn = _scoped_conn(user, field)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            INSERT INTO field_activities
                (tenant_id, field_id, user_id, activity_type, title, notes,
                 recommendation, visit_date, lat, lon, photo_url)
            VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s,
                    COALESCE(%s::date, CURRENT_DATE), %s, %s, %s)
            RETURNING id::text AS id
            """,
            (field.get("tenant_id"), field_id, user.user_id, body.activity_type,
             body.title, body.notes, body.recommendation, body.visit_date,
             body.lat, body.lon, body.photo_url),
        )
        new_id = cur.fetchone()["id"]
        # Re-read through the author join so the response includes author_name.
        cur.execute(
            f"SELECT {_ACTIVITY_COLS} FROM field_activities a {_ACTIVITY_JOINS} WHERE a.id = %s::uuid",
            (new_id,),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    except HTTPException:
        conn.rollback(); conn.close(); raise
    except Exception as exc:
        conn.rollback(); conn.close()
        raise HTTPException(status_code=500, detail=str(exc))
    else:
        conn.close()
    return _activity_from_row(row)


@router.get("/fields/{field_id}/activities", response_model=List[FieldActivity])
def list_activities(field_id: str,
                    limit: int = Query(default=100, ge=1, le=500),
                    user: AuthenticatedUser = Depends(get_authenticated_user)):
    field = _resolve(field_id, user)
    conn = _scoped_conn(user, field)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"""
            SELECT {_ACTIVITY_COLS} FROM field_activities a {_ACTIVITY_JOINS}
            WHERE a.field_id = %s::uuid
            ORDER BY a.visit_date DESC, a.created_at DESC
            LIMIT %s
            """,
            (field_id, limit),
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()
    return [_activity_from_row(r) for r in rows]


def _load_activity_authorized(cur, activity_id: str, user: AuthenticatedUser) -> dict:
    """Fetch the activity and enforce edit rights: author, tenant owner/admin/
    manager, or platform admin."""
    cur.execute(
        f"SELECT {_ACTIVITY_COLS} FROM field_activities a {_ACTIVITY_JOINS} WHERE a.id = %s::uuid",
        (activity_id,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Activity not found")
    in_tenant = row.get("tenant_id") and str(row["tenant_id"]) in {str(t) for t in user.tenant_ids}
    is_author = str(row["user_id"]) == str(user.user_id)
    if not (user.role == "admin" or is_author or (in_tenant and user_can_assign_fields(user))):
        raise HTTPException(status_code=403, detail="Only the author or a team manager can modify this record")
    return row


@router.patch("/activities/{activity_id}", response_model=FieldActivity)
def update_activity(activity_id: str, body: UpdateActivityRequest,
                    user: AuthenticatedUser = Depends(get_authenticated_user)):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")
    conn = _scoped_conn(user)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        _load_activity_authorized(cur, activity_id, user)
        sets, params = [], []
        for key, val in updates.items():
            if key == "visit_date":
                sets.append("visit_date = %s::date")
            else:
                sets.append(f"{key} = %s")
            params.append(val)
        sets.append("updated_at = NOW()")
        cur.execute(
            f"UPDATE field_activities SET {', '.join(sets)} WHERE id = %s::uuid",
            (*params, activity_id),
        )
        cur.execute(
            f"SELECT {_ACTIVITY_COLS} FROM field_activities a {_ACTIVITY_JOINS} WHERE a.id = %s::uuid",
            (activity_id,),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    except HTTPException:
        conn.rollback(); conn.close(); raise
    except Exception as exc:
        conn.rollback(); conn.close()
        raise HTTPException(status_code=500, detail=str(exc))
    else:
        conn.close()
    return _activity_from_row(row)


@router.delete("/activities/{activity_id}", status_code=204)
def delete_activity(activity_id: str,
                    user: AuthenticatedUser = Depends(get_authenticated_user)):
    conn = _scoped_conn(user)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        _load_activity_authorized(cur, activity_id, user)
        cur.execute("DELETE FROM field_activities WHERE id = %s::uuid", (activity_id,))
        conn.commit()
        cur.close()
    except HTTPException:
        conn.rollback(); conn.close(); raise
    except Exception as exc:
        conn.rollback(); conn.close()
        raise HTTPException(status_code=500, detail=str(exc))
    else:
        conn.close()


@router.get("/team/activity", response_model=List[FieldActivity])
def team_activity_feed(limit: int = Query(default=50, ge=1, le=200),
                       user: AuthenticatedUser = Depends(get_authenticated_user)):
    """Tenant-wide recent professional activity — the team's operational pulse."""
    if not user.tenant_id:
        raise HTTPException(status_code=403, detail="No tenant membership")
    conn = _scoped_conn(user)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"""
            SELECT {_ACTIVITY_COLS}, f.name AS field_name
            FROM field_activities a
            {_ACTIVITY_JOINS}
            LEFT JOIN fields f ON f.id = a.field_id
            WHERE a.tenant_id = ANY(%s::uuid[])
            ORDER BY a.created_at DESC
            LIMIT %s
            """,
            (user.tenant_ids, limit),
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()
    return [_activity_from_row(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# Assignments
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/fields/{field_id}/assign", response_model=Optional[FieldAssignment])
def assign_field(field_id: str, body: AssignFieldRequest,
                 user: AuthenticatedUser = Depends(get_authenticated_user)):
    """Assign (or with assignee_user_id=None, unassign) a field. Reassignment
    closes the previous assignment row, preserving history."""
    if not user_can_assign_fields(user):
        raise HTTPException(status_code=403, detail="Assigning fields requires a manager role")
    field = _resolve(field_id, user)
    conn = _scoped_conn(user, field)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if body.assignee_user_id:
            # The assignee must be an ACTIVE member of the field's tenant.
            cur.execute(
                """
                SELECT 1 FROM tenant_members
                WHERE tenant_id = %s::uuid AND user_id = %s::uuid
                  AND COALESCE(status,'active') = 'active'
                """,
                (field.get("tenant_id"), body.assignee_user_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=400, detail="Assignee is not an active member of your team")

        # Close any current assignment (no-op when there is none).
        cur.execute(
            "UPDATE field_assignments SET unassigned_at = NOW() WHERE field_id = %s::uuid AND unassigned_at IS NULL",
            (field_id,),
        )

        row = None
        if body.assignee_user_id:
            cur.execute(
                """
                INSERT INTO field_assignments
                    (tenant_id, field_id, assignee_user_id, assigned_by_user_id, note)
                VALUES (%s::uuid, %s::uuid, %s::uuid, %s::uuid, %s)
                RETURNING id::text AS id, field_id::text AS field_id,
                          assignee_user_id::text AS assignee_user_id,
                          assigned_by_user_id::text AS assigned_by_user_id,
                          note, assigned_at, unassigned_at
                """,
                (field.get("tenant_id"), field_id, body.assignee_user_id, user.user_id, body.note),
            )
            row = cur.fetchone()
        conn.commit()
        cur.close()
    except HTTPException:
        conn.rollback(); conn.close(); raise
    except Exception as exc:
        conn.rollback(); conn.close()
        raise HTTPException(status_code=500, detail=str(exc))
    else:
        conn.close()

    if not row:
        return None
    return FieldAssignment(
        id=row["id"], field_id=row["field_id"], assignee_user_id=row["assignee_user_id"],
        assigned_by_user_id=row.get("assigned_by_user_id"), note=row.get("note"),
        assigned_at=_iso(row.get("assigned_at")), unassigned_at=_iso(row.get("unassigned_at")),
    )


@router.get("/fields/{field_id}/assignments", response_model=List[FieldAssignment])
def list_assignments(field_id: str,
                     user: AuthenticatedUser = Depends(get_authenticated_user)):
    field = _resolve(field_id, user)
    conn = _scoped_conn(user, field)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT fa.id::text AS id, fa.field_id::text AS field_id,
                   fa.assignee_user_id::text AS assignee_user_id,
                   fa.assigned_by_user_id::text AS assigned_by_user_id,
                   fa.note, fa.assigned_at, fa.unassigned_at,
                   COALESCE(tm.display_name, p.full_name) AS assignee_name
            FROM field_assignments fa
            LEFT JOIN profiles p ON p.id = fa.assignee_user_id
            LEFT JOIN tenant_members tm
                   ON tm.user_id = fa.assignee_user_id AND tm.tenant_id = fa.tenant_id
            WHERE fa.field_id = %s::uuid
            ORDER BY (fa.unassigned_at IS NULL) DESC, fa.assigned_at DESC
            LIMIT 50
            """,
            (field_id,),
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()
    return [FieldAssignment(
        id=r["id"], field_id=r["field_id"], assignee_user_id=r["assignee_user_id"],
        assignee_name=r.get("assignee_name"),
        assigned_by_user_id=r.get("assigned_by_user_id"), note=r.get("note"),
        assigned_at=_iso(r.get("assigned_at")), unassigned_at=_iso(r.get("unassigned_at")),
    ) for r in rows]


@router.get("/team/assignments")
def all_active_assignments(user: AuthenticatedUser = Depends(get_authenticated_user)):
    """Active assignment per field for the tenant — lets the roster filter by
    assignee with one extra request instead of N."""
    if not user.tenant_id:
        raise HTTPException(status_code=403, detail="No tenant membership")
    conn = _scoped_conn(user)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT fa.field_id::text AS field_id,
                   fa.assignee_user_id::text AS assignee_user_id,
                   COALESCE(tm.display_name, p.full_name) AS assignee_name
            FROM field_assignments fa
            LEFT JOIN profiles p ON p.id = fa.assignee_user_id
            LEFT JOIN tenant_members tm
                   ON tm.user_id = fa.assignee_user_id AND tm.tenant_id = fa.tenant_id
            WHERE fa.tenant_id = ANY(%s::uuid[]) AND fa.unassigned_at IS NULL
            """,
            (user.tenant_ids,),
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()
    return {"assignments": [dict(r) for r in rows]}
