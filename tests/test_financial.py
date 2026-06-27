"""
Tests for financial / exposure routes (Sprint 2):
- request validation
- tenant access control (403)
- grower verification (403/404)
- delivery value computation
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from schemas import AuthenticatedUser


def _inst_user(tid="t1"):
    return AuthenticatedUser(
        user_id="u1", role="institutional", institutional_type="buyer",
        tenant_id=tid, tenant_ids=[tid],
    )


class TestValidation:
    def test_contract_rejects_nonpositive_volume(self):
        from schemas import CreateContractRequest
        with pytest.raises(Exception):
            CreateContractRequest(
                grower_id="g1", season_year=2025,
                contracted_volume_tonnes=0, contract_price_per_tonne=200,
                input_credit_value=1000,
            )

    def test_contract_rejects_negative_price(self):
        from schemas import CreateContractRequest
        with pytest.raises(Exception):
            CreateContractRequest(
                grower_id="g1", season_year=2025,
                contracted_volume_tonnes=10, contract_price_per_tonne=-1,
                input_credit_value=1000,
            )

    def test_contract_accepts_zero_credit(self):
        from schemas import CreateContractRequest
        req = CreateContractRequest(
            grower_id="g1", season_year=2025,
            contracted_volume_tonnes=10, contract_price_per_tonne=200,
            input_credit_value=0,
        )
        assert req.input_credit_value == 0

    def test_disbursement_rejects_nonpositive_credit(self):
        from schemas import CreateDisbursementRequest
        with pytest.raises(Exception):
            CreateDisbursementRequest(grower_id="g1", credit_value=0)

    def test_delivery_rejects_nonpositive_volume(self):
        from schemas import CreateDeliveryRequest
        with pytest.raises(Exception):
            CreateDeliveryRequest(grower_id="g1", volume_tonnes=0)


class TestTenantAccess:
    def test_assert_tenant_access_blocks_other_tenant(self):
        from financial_routes import _assert_tenant_access
        with pytest.raises(Exception) as exc:
            _assert_tenant_access("other", _inst_user("t1"))
        assert exc.value.status_code == 403

    def test_assert_tenant_access_allows_own(self):
        from financial_routes import _assert_tenant_access
        _assert_tenant_access("t1", _inst_user("t1"))  # no raise

    def test_assert_tenant_access_allows_admin(self):
        from financial_routes import _assert_tenant_access
        admin = AuthenticatedUser(user_id="a", role="admin", tenant_id=None, tenant_ids=[])
        _assert_tenant_access("any-tenant", admin)  # no raise

    def test_exposure_blocks_cross_tenant(self):
        from financial_routes import get_exposure
        with pytest.raises(Exception) as exc:
            get_exposure(tenant_id="other", user=_inst_user("t1"))
        assert exc.value.status_code == 403

    def test_list_contracts_blocks_cross_tenant(self):
        from financial_routes import list_contracts
        with pytest.raises(Exception) as exc:
            list_contracts(tenant_id="other", user=_inst_user("t1"))
        assert exc.value.status_code == 403


class TestVerifyGrower:
    def test_404_when_grower_missing(self):
        from financial_routes import _verify_grower
        cur = MagicMock()
        cur.fetchone.return_value = None
        with pytest.raises(Exception) as exc:
            _verify_grower(cur, "g1", "t1")
        assert exc.value.status_code == 404

    def test_403_when_grower_other_tenant(self):
        from financial_routes import _verify_grower
        cur = MagicMock()
        cur.fetchone.return_value = {"tenant_id": "other-tenant"}
        with pytest.raises(Exception) as exc:
            _verify_grower(cur, "g1", "t1")
        assert exc.value.status_code == 403

    def test_ok_when_grower_in_tenant(self):
        from financial_routes import _verify_grower
        cur = MagicMock()
        cur.fetchone.return_value = {"tenant_id": "t1"}
        _verify_grower(cur, "g1", "t1")  # no raise


class TestCreateDeliveryValue:
    @patch("financial_routes.get_db_connection")
    def test_value_usd_computed_from_price(self, mock_conn_fn):
        from financial_routes import create_delivery
        from schemas import CreateDeliveryRequest

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        # _verify_grower lookup, then INSERT RETURNING
        mock_cur.fetchone.side_effect = [
            {"tenant_id": "t1"},  # grower verify
            {  # returned delivery row
                "id": "d1", "tenant_id": "t1", "grower_id": "g1",
                "contract_id": None, "field_id": None,
                "delivery_date": date(2024, 4, 1), "volume_tonnes": 5.0,
                "price_per_tonne": 200.0, "quality_grade": "A",
                "value_usd": 1000.0, "created_at": None,
            },
        ]
        mock_conn.cursor.return_value = mock_cur
        mock_conn_fn.return_value = mock_conn

        body = CreateDeliveryRequest(grower_id="g1", volume_tonnes=5.0, price_per_tonne=200.0)
        result = create_delivery("t1", body, _inst_user("t1"))

        # Assert the INSERT was called with value_usd = 5*200 = 1000
        insert_call = [c for c in mock_cur.execute.call_args_list
                       if "INSERT INTO deliveries" in c.args[0]][0]
        params = insert_call.args[1]
        assert params[-1] == pytest.approx(1000.0)  # value_usd is last param
        assert result.value_usd == pytest.approx(1000.0)
