"""
Tests for reconciliation_routes: tenant access (403) + cross-tenant isolation.
"""

import pytest

from schemas import AuthenticatedUser


def _user(tid="t1"):
    return AuthenticatedUser(
        user_id="u1", role="institutional", institutional_type="buyer",
        tenant_id=tid, tenant_ids=[tid],
    )


class TestTenantAccess:
    def test_assert_blocks_other_tenant(self):
        from reconciliation_routes import _assert_tenant_access
        with pytest.raises(Exception) as exc:
            _assert_tenant_access("other", _user("t1"))
        assert exc.value.status_code == 403

    def test_assert_allows_own(self):
        from reconciliation_routes import _assert_tenant_access
        _assert_tenant_access("t1", _user("t1"))  # no raise

    def test_assert_allows_admin(self):
        from reconciliation_routes import _assert_tenant_access
        admin = AuthenticatedUser(user_id="a", role="admin", tenant_id=None, tenant_ids=[])
        _assert_tenant_access("any", admin)  # no raise

    def test_endpoint_blocks_cross_tenant(self):
        from reconciliation_routes import get_reconciliation
        with pytest.raises(Exception) as exc:
            get_reconciliation(tenant_id="other", user=_user("t1"))
        assert exc.value.status_code == 403
