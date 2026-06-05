"""
Tests for the Field State Aggregator (Step F).

These exercise the pure, I/O-free assembly path (`assemble_field_state`) plus the
access-control resolver, so they run without a database or network. Heavy
subsystem imports inside the aggregator are lazy, so importing this module never
requires openai/tiktoken/etc.
"""

import time
from datetime import datetime, timedelta

import pytest

from services.field_state import classifiers
from services.field_state.aggregator import (
    assemble_field_state,
    resolve_access,
    FieldNotFound,
    FieldAccessDenied,
)

NOW = datetime(2026, 6, 5, 22, 0, 0)


def _field(**over):
    base = {
        "id": "11111111-1111-1111-1111-111111111111",
        "user_id": "tenant-A",
        "name": "Tomato 1",
        "crop_type": "Maize",
        "variety": "SC727",
        "planting_date": "2026-02-05",
        "size_hectares": 11.69,
        "natural_region": "II",
        "polygon_coordinates": [{"lat": -17.8, "lon": 31.0}, {"lat": -17.81, "lon": 31.01}],
    }
    base.update(over)
    return base


def _logs(ndvi, days=5, start=NOW):
    out = []
    for i in range(days):
        d = (start - timedelta(days=days - i)).date().isoformat()
        out.append({"log_date": d, "ndvi": ndvi, "evi": ndvi - 0.03,
                    "soil_moisture": 40, "cloud_cover": 5})
    return out


# ---------------------------------------------------------------------------
# 1. Happy path — complete data, fully populated, no contradictions
# ---------------------------------------------------------------------------
def test_happy_path_complete_data():
    # planting 70 days before NOW => reproductive phase; healthy NDVI 0.80 well
    # inside the expected band, with a water surplus => clearly a healthy field.
    field = _field(planting_date=(NOW - timedelta(days=70)).date().isoformat())
    fs = assemble_field_state(
        field_row=field, requester_id="tenant-A",
        daily_logs=_logs(0.80), variety_in_database=True, input_record_count=3,
        agri_raw={"water_balance": {"weekly_precipitation": 30, "weekly_et": 22, "balance": 8}},
        now=NOW,
    )
    assert fs.field.id == field["id"]
    assert fs.kurima_score.score >= 55
    assert fs.kurima_score.label in ("Adequate", "Strong", "Thriving")
    # No contradiction: a healthy score must not sit above a "Critical" NDVI label.
    assert fs.indices.current.ndvi_label not in ("Critical", "Distressed")
    assert fs.data_completeness.overall_completeness_pct >= 80
    assert fs.season.days_since_planted == 70
    assert fs.indices.current.observation_quality in ("good", "fair")


# ---------------------------------------------------------------------------
# 2. Sparse data — no recent satellite still returns a FieldState
# ---------------------------------------------------------------------------
def test_sparse_data_flags_not_crash():
    field = _field(variety=None)
    # last pass 40 days ago => stale
    old_logs = _logs(0.5, days=2, start=NOW - timedelta(days=40))
    fs = assemble_field_state(
        field_row=field, requester_id="tenant-A",
        daily_logs=old_logs, variety_in_database=False, input_record_count=0,
        now=NOW,
    )
    assert fs.indices.current.observation_quality == "stale"
    assert fs.data_completeness.has_recent_satellite_pass is False
    assert fs.data_completeness.has_variety_in_database is False
    assert fs.data_completeness.has_input_records is False
    assert any("satellite" in w.lower() for w in fs.meta.stale_data_warnings)
    # Still a valid score (does not crash on sparse data).
    assert 0 <= fs.kurima_score.score <= 100


def test_no_logs_at_all_still_returns_state():
    fs = assemble_field_state(
        field_row=_field(), requester_id="tenant-A", daily_logs=[], now=NOW,
    )
    assert fs.indices.current.observation_quality == "none"
    assert fs.indices.current.ndvi is None
    assert 0 <= fs.kurima_score.score <= 100
    assert fs.indices.trend_30d == []


# ---------------------------------------------------------------------------
# 3. Contradiction resolution — low NDVI at high-expectation stage
# ---------------------------------------------------------------------------
def test_contradiction_low_ndvi_high_stage():
    # 70 days in => reproductive phase where NDVI ~0.55-0.85 expected; feed 0.20.
    field = _field(planting_date=(NOW - timedelta(days=70)).date().isoformat())
    fs = assemble_field_state(
        field_row=field, requester_id="tenant-A",
        daily_logs=_logs(0.20), variety_in_database=True, input_record_count=2,
        now=NOW,
    )
    # The score MUST be low (no "Adequate/Strong/Thriving" over a 0.20 NDVI).
    assert fs.kurima_score.score < 55
    assert fs.kurima_score.label in ("Stressed", "Distressed", "Critical")
    # An alert MUST be generated, consistently with the low score.
    cats = [a.category for a in fs.alerts]
    assert "canopy_stress" in cats
    # And the NDVI label agrees with the score (both read as poor).
    assert fs.indices.current.ndvi_label in ("Critical", "Distressed", "Stressed")


# ---------------------------------------------------------------------------
# 4. Multi-tenant — wrong tenant is denied (403), missing field is 404
# ---------------------------------------------------------------------------
def test_access_denied_for_wrong_tenant():
    with pytest.raises(FieldAccessDenied):
        assemble_field_state(
            field_row=_field(user_id="tenant-A"), requester_id="tenant-B",
            daily_logs=_logs(0.6), now=NOW,
        )


class _FakeCursor:
    def __init__(self, row):
        self._row = row

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return self._row

    def close(self):
        pass


class _FakeConn:
    def __init__(self, row):
        self._row = row

    def cursor(self, *a, **k):
        return _FakeCursor(self._row)

    def close(self):
        pass


def test_resolve_access_403_vs_404(monkeypatch):
    import database

    # Field exists but belongs to tenant-A; tenant-B asks -> 403, not 404.
    row = {"id": "f1", "user_id": "tenant-A", "name": "F"}
    monkeypatch.setattr(database, "get_db_connection", lambda: _FakeConn(row))
    with pytest.raises(FieldAccessDenied):
        resolve_access("f1", "tenant-B")

    # Field truly absent -> 404.
    monkeypatch.setattr(database, "get_db_connection", lambda: _FakeConn(None))
    with pytest.raises(FieldNotFound):
        resolve_access("missing", "tenant-A")


# ---------------------------------------------------------------------------
# 5. Performance — assembly within 500ms for a 90-day history
# ---------------------------------------------------------------------------
def test_performance_90_day_history():
    field = _field(planting_date=(NOW - timedelta(days=90)).date().isoformat())
    logs = _logs(0.6, days=90)
    started = time.time()
    fs = assemble_field_state(
        field_row=field, requester_id="tenant-A", daily_logs=logs,
        variety_in_database=True, input_record_count=4, now=NOW,
    )
    elapsed_ms = (time.time() - started) * 1000
    assert elapsed_ms < 500, f"assembly took {elapsed_ms:.0f}ms"
    # trend is capped at 30 points and uses KurimaScore (0-100), not raw NDVI.
    assert len(fs.indices.trend_30d) == 30
    for pt in fs.indices.trend_30d:
        assert pt.kurima_score is None or 0 <= pt.kurima_score <= 100


# ---------------------------------------------------------------------------
# 6. Unit consistency — no surprise fractional percentages
# ---------------------------------------------------------------------------
def test_confidence_never_fractional():
    # The 0.6% bug: 0.6 fraction must render as 60 (int), never 0.6.
    band, pct = classifiers.confidence_from_fraction(0.6)
    assert (band, pct) == ("medium", 60)
    assert isinstance(pct, int)
    # Defensive: a value already in percent form is clamped, not doubled.
    assert classifiers.confidence_from_fraction(60) == ("medium", 60)


def test_units_are_explicit_and_typed():
    field = _field(planting_date=(NOW - timedelta(days=70)).date().isoformat())
    fs = assemble_field_state(
        field_row=field, requester_id="tenant-A",
        daily_logs=_logs(0.65),
        variety_in_database=True, input_record_count=2,
        yield_raw={"projected_yield": 12.9, "yield_potential": 60.0,
                   "confidence_score": 0.6,
                   "confidence_bands": {"low": 8.2, "high": 16.8},
                   "confidence_factors": ["Late season - high prediction confidence",
                                          "Variety not in database - using estimates"]},
        now=NOW,
    )
    # KurimaScore is an int 0-100.
    assert isinstance(fs.kurima_score.score, int) and 0 <= fs.kurima_score.score <= 100
    # Confidence is band + INTEGER pct everywhere.
    assert isinstance(fs.kurima_score.confidence_pct, int)
    assert isinstance(fs.yield_projection.confidence_pct, int)
    assert fs.yield_projection.confidence_pct == 60
    assert fs.yield_projection.confidence_band == "medium"
    # Yield gap is an int percent 0-100.
    assert fs.yield_projection.yield_gap_pct == 78
    assert fs.yield_projection.unit == "tonnes_per_ha"
    # NDVI within dimensionless range.
    assert -1 <= fs.indices.current.ndvi <= 1
    # Confidence factors were split positive/negative.
    assert any("Late season" in p for p in fs.yield_projection.confidence_factors.positive)
    assert any("Variety not in database" in n for n in fs.yield_projection.confidence_factors.negative)


def test_classifiers_water_balance_and_soil():
    assert classifiers.classify_water_balance(-23.3)[0] == "deficit"
    assert classifiers.classify_water_balance(-23.3)[2] == "high"
    assert classifiers.classify_water_balance(10)[0] == "surplus"
    assert classifiers.classify_soil_moisture("tomato", 13) == "dry"
    assert classifiers.classify_soil_moisture("tomato", 60) == "adequate"
