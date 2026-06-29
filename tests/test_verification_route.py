"""
Tests for verification_routes: tenant access (403/404).
"""

from unittest.mock import patch

import pytest

from schemas import AuthenticatedUser


def _user(tid="t1"):
    return AuthenticatedUser(
        user_id="u1", role="institutional", institutional_type="buyer",
        tenant_id=tid, tenant_ids=[tid],
    )


class TestAccess:
    @patch("verification_routes.resolve_access")
    def test_404_when_field_missing(self, mock_resolve):
        from verification_routes import get_field_verification
        from services.field_state.aggregator import FieldNotFound
        mock_resolve.side_effect = FieldNotFound("f1")
        with pytest.raises(Exception) as exc:
            get_field_verification("f1", _user())
        assert exc.value.status_code == 404

    @patch("verification_routes.resolve_access")
    def test_403_when_other_tenant(self, mock_resolve):
        from verification_routes import get_field_verification
        from services.field_state.aggregator import FieldAccessDenied
        mock_resolve.side_effect = FieldAccessDenied("f1")
        with pytest.raises(Exception) as exc:
            get_field_verification("f1", _user())
        assert exc.value.status_code == 403

    def test_portfolio_rollup_blocks_cross_tenant(self):
        from verification_routes import get_portfolio_verification
        with pytest.raises(Exception) as exc:
            get_portfolio_verification("other-tenant", _user("t1"))
        assert exc.value.status_code == 403

    def test_portfolio_rollup_assert_allows_own_and_admin(self):
        from verification_routes import _assert_tenant_access
        _assert_tenant_access("t1", _user("t1"))  # no raise
        admin = AuthenticatedUser(user_id="a", role="admin", tenant_id=None, tenant_ids=[])
        _assert_tenant_access("any", admin)  # no raise
