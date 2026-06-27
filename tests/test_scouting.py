"""
Tests for scouting_routes (Sprint 3): validation + tenant access (403/404).
"""

from unittest.mock import MagicMock, patch

import pytest

from schemas import AuthenticatedUser


def _user(tid="t1"):
    return AuthenticatedUser(
        user_id="u1", role="institutional", institutional_type="buyer",
        tenant_id=tid, tenant_ids=[tid],
    )


class TestValidation:
    def test_rejects_bad_category(self):
        from schemas import CreateScoutingRequest
        with pytest.raises(Exception):
            CreateScoutingRequest(category="aliens", severity="low")

    def test_rejects_bad_severity(self):
        from schemas import CreateScoutingRequest
        with pytest.raises(Exception):
            CreateScoutingRequest(category="pest", severity="apocalyptic")

    def test_rejects_out_of_range_lat(self):
        from schemas import CreateScoutingRequest
        with pytest.raises(Exception):
            CreateScoutingRequest(category="pest", severity="low", lat=200, lon=0)

    def test_accepts_valid(self):
        from schemas import CreateScoutingRequest
        r = CreateScoutingRequest(category="disease", severity="high", notes="leaf spot", lat=-17.8, lon=31.0)
        assert r.category == "disease"
        assert r.severity == "high"


class TestAccess:
    @patch("scouting_routes.resolve_access")
    def test_create_404_when_field_missing(self, mock_resolve):
        from scouting_routes import create_scouting, _resolve  # noqa
        from services.field_state.aggregator import FieldNotFound
        from schemas import CreateScoutingRequest
        mock_resolve.side_effect = FieldNotFound("f1")
        body = CreateScoutingRequest(category="pest", severity="low")
        with pytest.raises(Exception) as exc:
            create_scouting("f1", body, _user())
        assert exc.value.status_code == 404

    @patch("scouting_routes.resolve_access")
    def test_create_403_when_other_tenant(self, mock_resolve):
        from scouting_routes import create_scouting
        from services.field_state.aggregator import FieldAccessDenied
        from schemas import CreateScoutingRequest
        mock_resolve.side_effect = FieldAccessDenied("f1")
        body = CreateScoutingRequest(category="pest", severity="low")
        with pytest.raises(Exception) as exc:
            create_scouting("f1", body, _user())
        assert exc.value.status_code == 403

    @patch("scouting_routes.get_db_connection")
    @patch("scouting_routes.resolve_access")
    def test_create_inserts_with_resolved_tenant(self, mock_resolve, mock_conn_fn):
        from scouting_routes import create_scouting
        from schemas import CreateScoutingRequest

        mock_resolve.return_value = {"id": "f1", "tenant_id": "t1", "user_id": "u1"}
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {
            "id": "s1", "field_id": "f1", "tenant_id": "t1", "user_id": "u1",
            "category": "pest", "severity": "low", "notes": None, "lat": None,
            "lon": None, "photo_url": None, "diagnosis": None, "observed_at": None,
            "source": "grower_logged", "created_at": None,
        }
        mock_conn.cursor.return_value = mock_cur
        mock_conn_fn.return_value = mock_conn

        body = CreateScoutingRequest(category="pest", severity="low")
        result = create_scouting("f1", body, _user())
        assert result.id == "s1"
        # tenant_id passed to INSERT comes from the resolved field, not the client
        insert_params = mock_cur.execute.call_args.args[1]
        assert insert_params[1] == "t1"  # tenant_id position
