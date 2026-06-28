"""
Tests for tenancy.py (Workstream 3.5) + the migrated /fields list endpoint.
"""

from unittest.mock import patch

from tenancy import caller_tenant_ids, field_scope_sql


class TestFieldScopeSql:
    def test_includes_tenant_and_user_fallback(self):
        sql = field_scope_sql("f")
        assert "f.tenant_id = ANY(%s::uuid[])" in sql
        assert "f.user_id = %s::uuid" in sql
        assert " OR " in sql

    def test_no_alias(self):
        sql = field_scope_sql()
        assert "tenant_id = ANY(%s::uuid[])" in sql
        assert "user_id = %s::uuid" in sql


class TestCallerTenantIds:
    @patch("tenancy.fetch_tenant_context", return_value=("t1", ["t1", "t2"], "owner"))
    def test_returns_list(self, _m):
        assert caller_tenant_ids("u1") == ["t1", "t2"]

    @patch("tenancy.fetch_tenant_context", return_value=(None, [], None))
    def test_empty_when_none(self, _m):
        assert caller_tenant_ids("u1") == []

# NOTE: endpoint-level verification of the migrated /fields query (that it filters
# by tenant_id with the user_id fallback) requires importing app.py, which pulls
# in cryptography/PyJWT — broken in this sandbox (pyo3/_cffi_backend), same reason
# test_create_field_tenant.py is excluded. Run that assertion in a full env.
