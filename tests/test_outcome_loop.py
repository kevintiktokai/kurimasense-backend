"""
Tests for the outcome-loop components:
- Snapshot fail-safety (Task 2)
- Harvest validation (Task 3)
- Cross-tenant access (Tasks 3 + 6 regression)
"""

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest


class TestSnapshotFailSafe:
    """Task 2: snapshot_projection must never break field-state."""

    def test_snapshot_returns_none_on_no_yield_raw(self):
        from services.calibration.snapshot import snapshot_projection
        result = snapshot_projection(
            field_row={"id": "abc", "tenant_id": "t1"},
            yield_raw=None,
        )
        assert result is None

    def test_snapshot_returns_none_on_missing_projected(self):
        from services.calibration.snapshot import snapshot_projection
        result = snapshot_projection(
            field_row={"id": "abc", "tenant_id": "t1"},
            yield_raw={"confidence_score": 0.5},
        )
        assert result is None

    @patch("services.calibration.snapshot.threading.Thread")
    def test_snapshot_fires_thread_on_valid_data(self, mock_thread_cls):
        from services.calibration.snapshot import snapshot_projection

        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread

        snapshot_projection(
            field_row={"id": "abc-123", "tenant_id": "t-456"},
            yield_raw={"projected_yield": 5.2, "confidence_score": 0.7},
            daily_logs=[{"ndvi": 0.65}, {"ndvi": 0.68}],
        )

        mock_thread_cls.assert_called_once()
        mock_thread.start.assert_called_once()
        call_kwargs = mock_thread_cls.call_args
        assert call_kwargs.kwargs["daemon"] is True

    @patch("database.get_db_connection", return_value=None)
    def test_do_snapshot_handles_no_connection(self, mock_conn):
        from services.calibration.snapshot import _do_snapshot
        _do_snapshot(
            field_id="abc",
            tenant_id="t1",
            projected_tonnes_per_ha=5.0,
            confidence_band="medium",
            confidence_pct=65,
            model_version="yield-v1",
            season_progress_pct=40,
            inputs_snapshot=None,
            projection_date=date.today(),
        )

    @patch("database.get_db_connection")
    def test_do_snapshot_handles_db_error(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.execute.side_effect = Exception("DB write failed")
        mock_conn.cursor.return_value = mock_cur
        mock_get_conn.return_value = mock_conn

        from services.calibration.snapshot import _do_snapshot
        _do_snapshot(
            field_id="abc",
            tenant_id="t1",
            projected_tonnes_per_ha=5.0,
            confidence_band="medium",
            confidence_pct=65,
            model_version="yield-v1",
            season_progress_pct=40,
            inputs_snapshot=None,
            projection_date=date.today(),
        )
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()


class TestHarvestValidation:
    """Task 3: harvest request validation."""

    def test_rejects_negative_yield(self):
        from schemas import CreateHarvestRequest
        with pytest.raises(Exception):
            CreateHarvestRequest(
                season_year=2025,
                area_harvested_ha=5.0,
                actual_yield_tonnes=-1.0,
            )

    def test_rejects_zero_yield(self):
        from schemas import CreateHarvestRequest
        with pytest.raises(Exception):
            CreateHarvestRequest(
                season_year=2025,
                area_harvested_ha=5.0,
                actual_yield_tonnes=0.0,
            )

    def test_rejects_negative_area(self):
        from schemas import CreateHarvestRequest
        with pytest.raises(Exception):
            CreateHarvestRequest(
                season_year=2025,
                area_harvested_ha=-1.0,
                actual_yield_tonnes=5.0,
            )

    def test_rejects_zero_area(self):
        from schemas import CreateHarvestRequest
        with pytest.raises(Exception):
            CreateHarvestRequest(
                season_year=2025,
                area_harvested_ha=0.0,
                actual_yield_tonnes=5.0,
            )

    def test_accepts_valid_minimal(self):
        from schemas import CreateHarvestRequest
        req = CreateHarvestRequest(
            season_year=2025,
            area_harvested_ha=5.0,
            actual_yield_tonnes=2.5,
        )
        assert req.season_year == 2025
        assert req.area_harvested_ha == 5.0
        assert req.actual_yield_tonnes == 2.5

    def test_accepts_valid_full(self):
        from schemas import CreateHarvestRequest
        req = CreateHarvestRequest(
            season_year=2025,
            area_harvested_ha=10.0,
            actual_yield_tonnes=8.5,
            harvest_date=date(2025, 6, 15),
            quality_grade="A",
            moisture_at_harvest=12.5,
            sale_price_per_tonne=500.0,
            delivered_to_tenant=True,
            notes="Good harvest",
        )
        assert req.quality_grade == "A"
        assert req.delivered_to_tenant is True


class TestCrossTenantAccess:
    """Regression: cross-tenant access must be blocked."""

    @patch("outcome_routes.get_db_connection")
    def test_resolve_field_404_when_not_found(self, mock_conn_fn):
        from outcome_routes import _resolve_field_for_tenant
        from schemas import AuthenticatedUser

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cur
        mock_conn_fn.return_value = mock_conn

        user = AuthenticatedUser(
            user_id="u1", role="institutional",
            institutional_type="buyer",
            tenant_id="t1", tenant_ids=["t1"],
        )
        with pytest.raises(Exception) as exc_info:
            _resolve_field_for_tenant("nonexistent", user)
        assert exc_info.value.status_code == 404

    @patch("outcome_routes.get_db_connection")
    def test_resolve_field_403_when_wrong_tenant(self, mock_conn_fn):
        from outcome_routes import _resolve_field_for_tenant
        from schemas import AuthenticatedUser

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {
            "id": "f1", "tenant_id": "other-tenant",
            "grower_id": None, "crop_type": "tobacco",
            "variety": None, "planting_date": None,
        }
        mock_conn.cursor.return_value = mock_cur
        mock_conn_fn.return_value = mock_conn

        user = AuthenticatedUser(
            user_id="u1", role="institutional",
            institutional_type="buyer",
            tenant_id="t1", tenant_ids=["t1"],
        )
        with pytest.raises(Exception) as exc_info:
            _resolve_field_for_tenant("f1", user)
        assert exc_info.value.status_code == 403

    @patch("outcome_routes.get_db_connection")
    def test_resolve_field_allows_own_tenant(self, mock_conn_fn):
        from outcome_routes import _resolve_field_for_tenant
        from schemas import AuthenticatedUser

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {
            "id": "f1", "tenant_id": "t1",
            "grower_id": "g1", "crop_type": "tobacco",
            "variety": "KRK26R", "planting_date": None,
        }
        mock_conn.cursor.return_value = mock_cur
        mock_conn_fn.return_value = mock_conn

        user = AuthenticatedUser(
            user_id="u1", role="institutional",
            institutional_type="buyer",
            tenant_id="t1", tenant_ids=["t1"],
        )
        field = _resolve_field_for_tenant("f1", user)
        assert field["id"] == "f1"

    @patch("outcome_routes.get_db_connection")
    def test_resolve_field_allows_admin(self, mock_conn_fn):
        from outcome_routes import _resolve_field_for_tenant
        from schemas import AuthenticatedUser

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {
            "id": "f1", "tenant_id": "any-tenant",
            "grower_id": None, "crop_type": "maize",
            "variety": None, "planting_date": None,
        }
        mock_conn.cursor.return_value = mock_cur
        mock_conn_fn.return_value = mock_conn

        user = AuthenticatedUser(
            user_id="admin1", role="admin",
            tenant_id=None, tenant_ids=[],
        )
        field = _resolve_field_for_tenant("f1", user)
        assert field["id"] == "f1"

    def test_calibration_endpoint_blocks_cross_tenant(self):
        from unittest.mock import patch as _patch
        from schemas import AuthenticatedUser

        user = AuthenticatedUser(
            user_id="u1", role="institutional",
            institutional_type="buyer",
            tenant_id="t1", tenant_ids=["t1"],
        )
        with _patch("outcome_routes.get_authenticated_user", return_value=user):
            from outcome_routes import get_calibration
            with pytest.raises(Exception) as exc_info:
                get_calibration(tenant_id="other-tenant", user=user)
            assert exc_info.value.status_code == 403


class TestResolveQuerySchema:
    """Regression: the resolve query must match the real fields schema.
    fields has NO deleted_at column (hard-deleted), and must SELECT user_id
    for the legacy consumer access fallback."""

    @patch("outcome_routes.get_db_connection")
    def test_resolve_query_has_no_deleted_at_and_selects_user_id(self, mock_conn_fn):
        from outcome_routes import _resolve_field_for_tenant
        from schemas import AuthenticatedUser

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {
            "id": "f1", "user_id": "u1", "tenant_id": "t1",
            "grower_id": None, "crop_type": "tobacco",
            "variety": None, "planting_date": None,
        }
        mock_conn.cursor.return_value = mock_cur
        mock_conn_fn.return_value = mock_conn

        user = AuthenticatedUser(
            user_id="u1", role="institutional",
            institutional_type="buyer",
            tenant_id="t1", tenant_ids=["t1"],
        )
        _resolve_field_for_tenant("f1", user)

        executed_sql = mock_cur.execute.call_args.args[0]
        assert "deleted_at" not in executed_sql
        assert "user_id" in executed_sql

    @patch("outcome_routes.get_db_connection")
    def test_resolve_allows_legacy_user_id_owner(self, mock_conn_fn):
        """A consumer whose user_id owns the field (no tenant match) is allowed."""
        from outcome_routes import _resolve_field_for_tenant
        from schemas import AuthenticatedUser

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {
            "id": "f1", "user_id": "consumer-1", "tenant_id": "their-tenant",
            "grower_id": None, "crop_type": "maize",
            "variety": None, "planting_date": None,
        }
        mock_conn.cursor.return_value = mock_cur
        mock_conn_fn.return_value = mock_conn

        user = AuthenticatedUser(
            user_id="consumer-1", role="consumer",
            tenant_id="own-tenant", tenant_ids=["own-tenant"],
        )
        field = _resolve_field_for_tenant("f1", user)
        assert field["id"] == "f1"
