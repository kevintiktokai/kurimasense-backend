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

from typing import List

from auth_roles import fetch_tenant_context


def caller_tenant_ids(user_id: str) -> List[str]:
    """All tenant ids the caller belongs to ([] if none / DB unavailable)."""
    _, tenant_ids, _ = fetch_tenant_context(user_id)
    return tenant_ids or []


def field_scope_sql(alias: str = "") -> str:
    """
    WHERE fragment scoping a `fields` row to the caller: tenant membership OR the
    legacy `user_id` fallback. Bind params in this order: (tenant_ids, user_id),
    used as ``%s::uuid[]`` then ``%s::uuid``.

        cur.execute(f"... WHERE {field_scope_sql('f')}", (tenant_ids, user_id))
    """
    p = f"{alias}." if alias else ""
    return f"({p}tenant_id = ANY(%s::uuid[]) OR {p}user_id = %s::uuid)"
