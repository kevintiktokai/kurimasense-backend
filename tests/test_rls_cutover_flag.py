"""
Tests for the RLS_TENANT_ONLY cut-over flag (Step C prep).

The flag lets the `fields.user_id` fallback be dropped via a config flip:
  * OFF (default): field scoping SQL is byte-identical to the legacy literal, so
    deploying this change is a no-op.
  * ON: scoping is tenant-only and references no `fields.user_id` column, yet the
    param binding is unchanged — so call sites never change and the column can be
    dropped.
"""

import tenancy


def test_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("RLS_TENANT_ONLY", raising=False)
    assert tenancy.rls_tenant_only() is False


def test_flag_parses_truthy_values(monkeypatch):
    for v in ("true", "True", "1", "yes"):
        monkeypatch.setenv("RLS_TENANT_ONLY", v)
        assert tenancy.rls_tenant_only() is True
    for v in ("false", "0", "no", ""):
        monkeypatch.setenv("RLS_TENANT_ONLY", v)
        assert tenancy.rls_tenant_only() is False


def test_scope_sql_off_is_legacy_literal(monkeypatch):
    monkeypatch.delenv("RLS_TENANT_ONLY", raising=False)
    assert tenancy.field_scope_sql() == "(tenant_id = ANY(%s::uuid[]) OR user_id = %s::uuid)"
    assert tenancy.field_scope_sql("f") == "(f.tenant_id = ANY(%s::uuid[]) OR f.user_id = %s::uuid)"


def test_scope_sql_on_is_tenant_only_and_columnless(monkeypatch):
    monkeypatch.setenv("RLS_TENANT_ONLY", "true")
    for alias in ("", "f"):
        sql = tenancy.field_scope_sql(alias)
        # References tenant_id but NOT the user_id column (column-drop ready).
        assert "tenant_id = ANY(%s::uuid[])" in sql
        assert "user_id" not in sql


def test_param_count_is_stable_across_flag(monkeypatch):
    # Both modes have exactly two %s placeholders, so every call site's
    # (tenant_ids, user_id) binding stays valid without change.
    monkeypatch.delenv("RLS_TENANT_ONLY", raising=False)
    off = tenancy.field_scope_sql("f")
    monkeypatch.setenv("RLS_TENANT_ONLY", "true")
    on = tenancy.field_scope_sql("f")
    assert off.count("%s") == on.count("%s") == 2
