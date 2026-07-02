"""
Tenant-scoping helpers — Workstream 3.5.

Migrates the consumer `fields` endpoints from `user_id` filtering to tenant-aware
filtering, **behavior-preserving**: a consumer (personal tenant, `fields.user_id`
populated) gets identical results, while institutional officers correctly gain
tenant access. The legacy `user_id` fallback is retained in the SQL until
`fields.user_id` is dropped (the final, gated step of Workstream 3.5).

Reuses `auth_roles.fetch_tenant_context` (indexed lookup on `tenant_members`,
degrades to [] so auth never breaks).
"""

from contextlib import contextmanager
from typing import List

from auth_roles import fetch_tenant_context
from database import get_db_connection


def caller_tenant_ids(user_id: str) -> List[str]:
    """All tenant ids the caller belongs to ([] if none / DB unavailable)."""
    _, tenant_ids, _ = fetch_tenant_context(user_id)
    return tenant_ids or []


def _pg_uuid_array_literal(values: List[str]) -> str:
    """Render a list of uuid strings as a Postgres array literal, e.g. '{a,b}'.
    Empty -> '{}'. Values are already uuids from the DB (fetch_tenant_context);
    we still filter falsy entries defensively."""
    return "{" + ",".join(str(v) for v in values if v) + "}"


def arm_rls_gucs(conn, user_id: str, tenant_ids: List[str]) -> None:
    """
    Set `app.tenant_ids` + `app.user_id` transaction-locally on an already
    checked-out connection. This is the raw arming primitive behind
    `tenant_scoped_connection`, exposed for call sites that manage their own
    connection lifecycle (the modular route files' `_conn_or_503` helpers) and
    already hold the caller's tenant ids (e.g. from `AuthenticatedUser`), so no
    second `fetch_tenant_context` round trip is needed.

    Leak-safety is identical to `tenant_scoped_connection`: `is_local => true`
    scopes both GUCs to the current transaction, so they are cleared on the
    handler's commit/rollback (and pool checkin rolls back open transactions),
    never bleeding into the next checkout.

    NOTE: the GUCs die with the first commit/rollback. Handlers that commit
    mid-way and keep querying must re-arm — the wired route files all follow
    the single-commit-at-end pattern, keep it that way.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT set_config('app.tenant_ids', %s, true), "
        "       set_config('app.user_id', %s, true)",
        (_pg_uuid_array_literal(tenant_ids or []), str(user_id)),
    )
    cur.close()


def arm_rls_gucs_all_tenants(conn, service_user: str = "service:global") -> None:
    """
    Arm `app.tenant_ids` with EVERY tenant id — a deliberate global grant for
    the few admin-token-gated service paths that legitimately operate across
    the whole book (e.g. the calibration recompute, which pairs projections
    with actuals across all tenants to compute global model-error stats).

    Works under FORCE because `tenants` is a bootstrap-exempt table (never
    FORCEd — it must be readable to derive tenant context in the first place;
    see docs/rls_force_runbook.md). Only call this from endpoints that are
    already admin-gated; never from a user-facing request path.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT set_config('app.tenant_ids', "
        "       COALESCE((SELECT '{' || string_agg(id::text, ',') || '}' FROM public.tenants), '{}'), "
        "       true), "
        "       set_config('app.user_id', %s, true)",
        (service_user,),
    )
    cur.close()


@contextmanager
def tenant_scoped_connection(user_id: str):
    """
    Yield a DB connection whose `app.tenant_ids` GUC is set to the caller's
    tenant ids for the lifetime of ONE transaction, then commit (or roll back on
    error). This is the enforcement primitive for Sprint 4 Slice 4: the ts_*
    RLS policies (migration 008) read `app_tenant_ids()`, so any query run
    through this context is constrained to the caller's tenants **even against
    the backend owner** once `FORCE ROW LEVEL SECURITY` is enabled.

    Leak-safety: the GUC is set with `set_config(..., is_local => true)`, so it
    is transaction-local and is cleared automatically when the transaction ends.
    It can therefore never bleed into the next request that checks out this same
    pooled connection — a property a plain session-level `SET` would not have.

    Until FORCE RLS is enabled this behaves identically to a normal connection
    (the owner bypasses non-forced RLS), so endpoints can be migrated to it
    incrementally and safely ahead of the FORCE cut-over. See
    docs/rls_force_runbook.md.

    Yields ``(conn, tenant_ids)`` — the tenant ids are surfaced so callers can
    still bind them to explicit `field_scope_sql` params without a second
    `fetch_tenant_context` round trip:

        with tenant_scoped_connection(user_id) as (conn, tenant_ids):
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(f"SELECT ... WHERE {field_scope_sql('f')}", (tenant_ids, user_id))

    Raises ``RuntimeError`` if the database is unavailable (callers that fall
    back to mock/degraded data should catch it).
    """
    tenant_ids = caller_tenant_ids(user_id)
    conn = get_db_connection()
    if conn is None:
        raise RuntimeError("Database unavailable")
    try:
        # app.tenant_ids drives the ts_* tenant policies; app.user_id drives the
        # personal-table policies (farm_tasks / chat_logs / yield_history) added
        # for the FORCE step. Both transaction-local (see arm_rls_gucs).
        arm_rls_gucs(conn, user_id, tenant_ids)
        yield conn, tenant_ids
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()  # returns to pool; SET LOCAL already cleared by txn end


def field_scope_sql(alias: str = "") -> str:
    """
    WHERE fragment scoping a `fields` row to the caller: tenant membership OR the
    legacy `user_id` fallback. Bind params in this order: (tenant_ids, user_id),
    used as ``%s::uuid[]`` then ``%s::uuid``.

        cur.execute(f"... WHERE {field_scope_sql('f')}", (tenant_ids, user_id))
    """
    p = f"{alias}." if alias else ""
    return f"({p}tenant_id = ANY(%s::uuid[]) OR {p}user_id = %s::uuid)"
