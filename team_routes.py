"""
Team management routes (institutional operations, migration 013)
================================================================
Organizations manage their own membership here:

  * GET    /team/members                — roster with workload (assigned fields,
                                          recent activity) per member.
  * POST   /team/members                — attach an existing platform user.
  * PATCH  /team/members/{user_id}      — change role, suspend / reactivate.
  * DELETE /team/members/{user_id}      — remove from the tenant.
  * GET    /team/invites                — open + historical invites.
  * POST   /team/invites                — create a code-based invite.
  * DELETE /team/invites/{invite_id}    — revoke an open invite.
  * POST   /team/invites/accept         — any authenticated user redeems a code.

Authorization: management actions need `user_can_manage_team` (tenant owner /
admin, or platform admin). Listing needs any active membership. Safeguards: you
cannot demote/suspend/remove the LAST owner/admin (the tenant would become
unmanageable), and you cannot change your own role (prevents accidental
self-lockout; another admin must do it).

Invites are code-based (no email infrastructure): the admin shares the short
code out-of-band; the teammate signs in and redeems it. This fits the WhatsApp-
first reality of the orgs KurimaSense serves.
"""

from __future__ import annotations

import secrets
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor

from auth_roles import get_authenticated_user, user_can_manage_team
from database import get_db_connection
from tenancy import arm_rls_gucs
from schemas import (
    AuthenticatedUser, TeamMember, AddTeamMemberRequest, UpdateTeamMemberRequest,
    CreateInviteRequest, TeamInvite, AcceptInviteRequest,
)

router = APIRouter(prefix="/team", tags=["team"])

# Roles that keep a tenant manageable; at least one active member must hold one.
_MANAGER_ROLES = ("owner", "admin")


def _require_tenant(user: AuthenticatedUser) -> str:
    if not user.tenant_id:
        raise HTTPException(status_code=403, detail="No tenant membership")
    return user.tenant_id


def _require_manage(user: AuthenticatedUser) -> str:
    tenant_id = _require_tenant(user)
    if not user_can_manage_team(user):
        raise HTTPException(status_code=403, detail="Team management requires an owner or admin role")
    return tenant_id


def _conn_or_503(user: AuthenticatedUser):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database unavailable")
    arm_rls_gucs(conn, user.user_id, user.tenant_ids)
    return conn


def _iso(v) -> str | None:
    return v.isoformat() if hasattr(v, "isoformat") else (str(v) if v else None)


def _manager_count(cur, tenant_id: str, excluding_user_id: str | None = None) -> int:
    """Active owner/admin members, optionally excluding one user."""
    q = """
        SELECT COUNT(*) AS n FROM tenant_members
        WHERE tenant_id = %s::uuid
          AND member_role = ANY(%s)
          AND COALESCE(status, 'active') = 'active'
    """
    params: list = [tenant_id, list(_MANAGER_ROLES)]
    if excluding_user_id:
        q += " AND user_id <> %s::uuid"
        params.append(excluding_user_id)
    cur.execute(q, tuple(params))
    row = cur.fetchone()
    return int(row["n"] if isinstance(row, dict) else row[0])


# ─────────────────────────────────────────────────────────────────────────────
# Members
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/members", response_model=List[TeamMember])
def list_members(user: AuthenticatedUser = Depends(get_authenticated_user)):
    tenant_id = _require_tenant(user)
    conn = _conn_or_503(user)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Roster + workload in one query: active assignment count and 30-day
        # activity count per member (LEFT JOIN LATERAL keeps it index-friendly).
        cur.execute(
            """
            SELECT tm.user_id::text AS user_id, tm.member_role,
                   COALESCE(tm.status, 'active') AS status,
                   tm.display_name, tm.email, tm.joined_at,
                   p.full_name,
                   COALESCE(fa.n, 0) AS assigned_fields,
                   COALESCE(act.n, 0) AS activities_30d
            FROM tenant_members tm
            LEFT JOIN profiles p ON p.id = tm.user_id
            LEFT JOIN LATERAL (
                SELECT COUNT(*) AS n FROM field_assignments
                WHERE assignee_user_id = tm.user_id
                  AND tenant_id = tm.tenant_id
                  AND unassigned_at IS NULL
            ) fa ON true
            LEFT JOIN LATERAL (
                SELECT COUNT(*) AS n FROM field_activities
                WHERE user_id = tm.user_id
                  AND tenant_id = tm.tenant_id
                  AND created_at > NOW() - INTERVAL '30 days'
            ) act ON true
            WHERE tm.tenant_id = %s::uuid
            ORDER BY tm.joined_at ASC
            """,
            (tenant_id,),
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    return [TeamMember(
        user_id=r["user_id"],
        member_role=r["member_role"],
        status=r["status"],
        display_name=r.get("display_name"),
        email=r.get("email"),
        full_name=r.get("full_name"),
        joined_at=_iso(r.get("joined_at")),
        assigned_fields=int(r.get("assigned_fields") or 0),
        activities_30d=int(r.get("activities_30d") or 0),
    ) for r in rows]


@router.post("/members", response_model=TeamMember, status_code=201)
def add_member(body: AddTeamMemberRequest,
               user: AuthenticatedUser = Depends(get_authenticated_user)):
    tenant_id = _require_manage(user)
    conn = _conn_or_503(user)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # The target must exist as a platform profile (they've signed up).
        cur.execute("SELECT id, full_name FROM profiles WHERE id = %s::uuid", (body.user_id,))
        prof = cur.fetchone()
        if not prof:
            raise HTTPException(status_code=404,
                                detail="No user with that ID exists — send them an invite code instead")
        cur.execute(
            """
            INSERT INTO tenant_members (tenant_id, user_id, member_role, status, display_name, email)
            VALUES (%s::uuid, %s::uuid, %s, 'active', %s, %s)
            ON CONFLICT (tenant_id, user_id) DO UPDATE
                SET member_role = EXCLUDED.member_role,
                    status = 'active',
                    display_name = COALESCE(EXCLUDED.display_name, tenant_members.display_name),
                    email = COALESCE(EXCLUDED.email, tenant_members.email)
            RETURNING user_id::text AS user_id, member_role,
                      COALESCE(status,'active') AS status, display_name, email, joined_at
            """,
            (tenant_id, body.user_id, body.member_role, body.display_name, body.email),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    except HTTPException:
        conn.rollback()
        conn.close()
        raise
    except Exception as exc:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(exc))
    else:
        conn.close()

    return TeamMember(
        user_id=row["user_id"], member_role=row["member_role"], status=row["status"],
        display_name=row.get("display_name"), email=row.get("email"),
        full_name=prof.get("full_name"), joined_at=_iso(row.get("joined_at")),
    )


@router.patch("/members/{member_user_id}", response_model=TeamMember)
def update_member(member_user_id: str, body: UpdateTeamMemberRequest,
                  user: AuthenticatedUser = Depends(get_authenticated_user)):
    tenant_id = _require_manage(user)
    if body.member_role is None and body.status is None and body.display_name is None:
        raise HTTPException(status_code=400, detail="Nothing to update")
    # Self-demotion / self-suspension guard: another admin must do it.
    if member_user_id == user.user_id and (body.member_role or body.status == "suspended"):
        raise HTTPException(status_code=400,
                            detail="You cannot change your own role or suspend yourself")

    conn = _conn_or_503(user)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT member_role, COALESCE(status,'active') AS status
            FROM tenant_members WHERE tenant_id = %s::uuid AND user_id = %s::uuid
            """,
            (tenant_id, member_user_id),
        )
        current = cur.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Member not found")

        # Last-manager safeguard: the change must leave at least one other
        # active owner/admin if it strips this member's management standing.
        strips_management = (
            current["member_role"] in _MANAGER_ROLES
            and (
                (body.member_role is not None and body.member_role not in _MANAGER_ROLES)
                or body.status == "suspended"
            )
        )
        if strips_management and _manager_count(cur, tenant_id, excluding_user_id=member_user_id) == 0:
            raise HTTPException(status_code=400,
                                detail="Cannot remove the organisation's last owner/admin")

        sets, params = [], []
        if body.member_role is not None:
            sets.append("member_role = %s"); params.append(body.member_role)
        if body.status is not None:
            sets.append("status = %s"); params.append(body.status)
        if body.display_name is not None:
            sets.append("display_name = %s"); params.append(body.display_name)
        cur.execute(
            f"""
            UPDATE tenant_members SET {', '.join(sets)}
            WHERE tenant_id = %s::uuid AND user_id = %s::uuid
            RETURNING user_id::text AS user_id, member_role,
                      COALESCE(status,'active') AS status, display_name, email, joined_at
            """,
            (*params, tenant_id, member_user_id),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    except HTTPException:
        conn.rollback()
        conn.close()
        raise
    except Exception as exc:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(exc))
    else:
        conn.close()

    return TeamMember(
        user_id=row["user_id"], member_role=row["member_role"], status=row["status"],
        display_name=row.get("display_name"), email=row.get("email"),
        joined_at=_iso(row.get("joined_at")),
    )


@router.delete("/members/{member_user_id}", status_code=204)
def remove_member(member_user_id: str,
                  user: AuthenticatedUser = Depends(get_authenticated_user)):
    tenant_id = _require_manage(user)
    if member_user_id == user.user_id:
        raise HTTPException(status_code=400, detail="You cannot remove yourself — another admin must")

    conn = _conn_or_503(user)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT member_role FROM tenant_members WHERE tenant_id = %s::uuid AND user_id = %s::uuid",
            (tenant_id, member_user_id),
        )
        current = cur.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Member not found")
        if (current["member_role"] in _MANAGER_ROLES
                and _manager_count(cur, tenant_id, excluding_user_id=member_user_id) == 0):
            raise HTTPException(status_code=400,
                                detail="Cannot remove the organisation's last owner/admin")

        # Close any active field assignments so workload numbers stay honest.
        cur.execute(
            """
            UPDATE field_assignments SET unassigned_at = NOW()
            WHERE tenant_id = %s::uuid AND assignee_user_id = %s::uuid AND unassigned_at IS NULL
            """,
            (tenant_id, member_user_id),
        )
        cur.execute(
            "DELETE FROM tenant_members WHERE tenant_id = %s::uuid AND user_id = %s::uuid",
            (tenant_id, member_user_id),
        )
        conn.commit()
        cur.close()
    except HTTPException:
        conn.rollback()
        conn.close()
        raise
    except Exception as exc:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(exc))
    else:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Invites
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/invites", response_model=List[TeamInvite])
def list_invites(user: AuthenticatedUser = Depends(get_authenticated_user)):
    tenant_id = _require_manage(user)
    conn = _conn_or_503(user)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id::text AS id, email, member_role, code, created_at, accepted_at, revoked_at
            FROM team_invites WHERE tenant_id = %s::uuid
            ORDER BY created_at DESC LIMIT 100
            """,
            (tenant_id,),
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()
    return [TeamInvite(
        id=r["id"], email=r.get("email"), member_role=r["member_role"], code=r["code"],
        created_at=_iso(r.get("created_at")), accepted_at=_iso(r.get("accepted_at")),
        revoked_at=_iso(r.get("revoked_at")),
    ) for r in rows]


@router.post("/invites", response_model=TeamInvite, status_code=201)
def create_invite(body: CreateInviteRequest,
                  user: AuthenticatedUser = Depends(get_authenticated_user)):
    tenant_id = _require_manage(user)
    # 8-hex-char code: short enough to read over the phone, 4 billion+ space,
    # single-use, revocable — appropriate for this threat model.
    code = secrets.token_hex(4).upper()
    conn = _conn_or_503(user)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            INSERT INTO team_invites (tenant_id, email, member_role, code, invited_by_user_id)
            VALUES (%s::uuid, %s, %s, %s, %s::uuid)
            RETURNING id::text AS id, email, member_role, code, created_at, accepted_at, revoked_at
            """,
            (tenant_id, body.email, body.member_role, code, user.user_id),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    except Exception as exc:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(exc))
    else:
        conn.close()
    return TeamInvite(
        id=row["id"], email=row.get("email"), member_role=row["member_role"], code=row["code"],
        created_at=_iso(row.get("created_at")),
    )


@router.delete("/invites/{invite_id}", status_code=204)
def revoke_invite(invite_id: str,
                  user: AuthenticatedUser = Depends(get_authenticated_user)):
    tenant_id = _require_manage(user)
    conn = _conn_or_503(user)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            UPDATE team_invites SET revoked_at = NOW()
            WHERE id = %s::uuid AND tenant_id = %s::uuid AND accepted_at IS NULL AND revoked_at IS NULL
            RETURNING id
            """,
            (invite_id, tenant_id),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Open invite not found")
        conn.commit()
        cur.close()
    except HTTPException:
        conn.rollback()
        conn.close()
        raise
    except Exception as exc:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(exc))
    else:
        conn.close()


@router.post("/invites/accept")
def accept_invite(body: AcceptInviteRequest,
                  user: AuthenticatedUser = Depends(get_authenticated_user)):
    """Redeem an invite code — ANY authenticated user (this is how a new
    teammate, who has no tenant yet, joins the organisation)."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        # team_invites is tenant-scoped under RLS, but the redeeming user isn't
        # a member yet. The backend owner connection bypasses RLS (FORCE off);
        # under a future FORCE cutover this lookup moves to a SECURITY DEFINER
        # helper — tracked in the FORCE runbook.
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, tenant_id::text AS tenant_id, member_role, email
            FROM team_invites
            WHERE UPPER(code) = UPPER(%s) AND accepted_at IS NULL AND revoked_at IS NULL
            """,
            (body.code.strip(),),
        )
        invite = cur.fetchone()
        if not invite:
            raise HTTPException(status_code=404, detail="Invalid or already-used invite code")

        cur.execute(
            """
            INSERT INTO tenant_members (tenant_id, user_id, member_role, status, email)
            VALUES (%s::uuid, %s::uuid, %s, 'active', %s)
            ON CONFLICT (tenant_id, user_id) DO UPDATE
                SET member_role = EXCLUDED.member_role, status = 'active'
            """,
            (invite["tenant_id"], user.user_id, invite["member_role"], invite.get("email")),
        )
        cur.execute(
            "UPDATE team_invites SET accepted_at = NOW(), accepted_by_user_id = %s::uuid WHERE id = %s",
            (user.user_id, invite["id"]),
        )
        # Joining an institutional tenant makes the user institutional so the
        # frontend routes them to /portfolio. Preserve admin; only upgrade
        # consumers. institutional_type mirrors the tenant's if present.
        cur.execute(
            """
            UPDATE profiles SET role = 'institutional',
                   institutional_type = COALESCE(institutional_type, (
                       SELECT institutional_type FROM tenants WHERE id = %s::uuid
                   ), 'buyer'),
                   tenant_name = COALESCE(tenant_name, (
                       SELECT name FROM tenants WHERE id = %s::uuid
                   ))
            WHERE id = %s::uuid AND role = 'consumer'
            """,
            (invite["tenant_id"], invite["tenant_id"], user.user_id),
        )
        conn.commit()
        cur.close()
    except HTTPException:
        conn.rollback()
        conn.close()
        raise
    except Exception as exc:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(exc))
    else:
        conn.close()

    return {"status": "success", "tenant_id": invite["tenant_id"], "member_role": invite["member_role"]}
