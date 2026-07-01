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
        cur = conn.cursor()
        # is_local => true: scoped to this transaction only (auto-cleared on end).
        cur.execute(
            "SELECT set_config('app.tenant_ids', %s, true)",
            (_pg_uuid_array_literal(tenant_ids),),
        )
        cur.close()
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
