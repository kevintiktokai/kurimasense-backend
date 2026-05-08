"""
Unit tests for workers/backfill_ingestion.py.

Run:
    cd backend
    python -m pytest tests/test_backfill_ingestion.py -v

The Earth Engine layer and DB connection are both faked. No GEE auth or
real database is touched.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2.extras  # noqa: E402

from workers import backfill_ingestion  # noqa: E402
from workers.backfill_ingestion import (  # noqa: E402
    BackfillStats,
    IndexStats,
    Observation,
    _months_to_date_range,
    bulk_upsert_observations,
    run_backfill,
)


# --------------------------------------------------------------------------- #
# Patch psycopg2.extras.execute_values so it doesn't reach into cur.connection.
# Replacement just calls cursor.execute(sql, row) once per row, which our fake
# cursor handles directly via its INSERT-INTO-daily_logs branch.
# --------------------------------------------------------------------------- #

@pytest.fixture(autouse=True)
def _patch_execute_values(monkeypatch):
    def _fake_execute_values(cur, sql, argslist, template=None, page_size=100, fetch=False):
        for row in argslist:
            cur.execute("INSERT INTO daily_logs (faked) VALUES (...)", row)
    monkeypatch.setattr(psycopg2.extras, "execute_values", _fake_execute_values)
    yield


# --------------------------------------------------------------------------- #
# Fake DB
# --------------------------------------------------------------------------- #

@dataclass
class _FieldRow:
    id: str
    user_id: str
    polygon_coordinates: List[Dict[str, float]] = field(default_factory=list)


class FakeDB:
    def __init__(self, fields_rows: List[_FieldRow]) -> None:
        self.fields = fields_rows
        self.daily_logs: List[Dict[str, Any]] = []
        self.committed = 0
        self.rolled_back = 0

    def connect(self):
        return _FakeConn(self)


class _FakeConn:
    encoding = "UTF8"

    def __init__(self, db: FakeDB) -> None:
        self._db = db

    def cursor(self, cursor_factory=None) -> "_FakeCursor":
        return _FakeCursor(self._db, self)

    def commit(self) -> None:
        self._db.committed += 1

    def rollback(self) -> None:
        self._db.rolled_back += 1

    def close(self) -> None:
        pass


class _FakeCursor:
    def __init__(self, db: FakeDB, conn: _FakeConn) -> None:
        self._db = db
        self.connection = conn
        self._last: Any = None

    def execute(self, sql: str, params: Any = None) -> None:
        sql_norm = " ".join(sql.split())
        if "INSERT INTO daily_logs" in sql_norm:
            (
                fid, uid, log_date, ndvi, evi, indices_json,
                sat_source, cloud_pct, quality, source,
            ) = params
            import json as _json
            existing = next(
                (
                    r for r in self._db.daily_logs
                    if r["field_id"] == fid and r["log_date"] == log_date
                ),
                None,
            )
            stored = {
                "field_id": fid,
                "user_id": uid,
                "log_date": log_date,
                "ndvi": ndvi,
                "evi": evi,
                "indices": _json.loads(indices_json),
                "satellite_source": sat_source,
                "cloud_pct": cloud_pct,
                "observation_quality": quality,
                "source": source,
            }
            if existing is None:
                self._db.daily_logs.append(stored)
            else:
                existing.update(stored)
            self._last = None
            return

        if "FROM fields" in sql_norm and "WHERE id = %s::uuid" in sql_norm:
            target_id = params[0]
            self._last = [
                {"id": f.id, "user_id": f.user_id}
                for f in self._db.fields if f.id == target_id
            ]
        elif "FROM fields" in sql_norm and "user_id = %s::uuid" in sql_norm:
            tenant = params[0]
            self._last = [
                {"id": f.id, "user_id": f.user_id}
                for f in self._db.fields if f.user_id == tenant
            ]
        elif "FROM fields" in sql_norm:
            self._last = [{"id": f.id, "user_id": f.user_id} for f in self._db.fields]
        else:
            self._last = None

    def fetchall(self):
        return self._last or []

    def fetchone(self):
        if isinstance(self._last, list):
            return self._last[0] if self._last else None
        return self._last

    def __iter__(self):
        return iter(self.fetchall())

    def close(self) -> None:
        pass


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _stats(mean: float, std: float = 0.05, p10: Optional[float] = None, p90: Optional[float] = None) -> IndexStats:
    if p10 is None:
        p10 = mean - 0.05
    if p90 is None:
        p90 = mean + 0.05
    return IndexStats(mean=mean, p10=p10, p90=p90, std=std)


def _make_obs(d: str, cloud_pct: float, ndvi: float = 0.7) -> Observation:
    return Observation(
        log_date=date.fromisoformat(d),
        cloud_pct=cloud_pct,
        indices={
            "ndvi": _stats(ndvi),
            "evi": _stats(ndvi - 0.2),
            "ndre": _stats(ndvi - 0.3),
            "ndmi": _stats(ndvi - 0.4),
            "savi": _stats(ndvi - 0.1),
        },
    )


def _aoi_resolver(field_id: str) -> Dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [31.00, -17.80],
                [31.01, -17.80],
                [31.01, -17.79],
                [31.00, -17.79],
                [31.00, -17.80],
            ]
        ],
        "bbox": [31.00, -17.80, 31.01, -17.79],
        "area_ha": 100.0,
    }


def _fixed_now():
    return datetime(2026, 5, 7, 12, 0, tzinfo=timezone.utc)


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #

def test_months_to_date_range_uses_30_day_approx():
    today = date(2026, 5, 7)
    start, end = _months_to_date_range(6, today)
    assert end == today
    assert start == today - timedelta(days=180)


def test_observation_to_indices_jsonb_includes_mean_and_distribution_keys():
    obs = _make_obs("2026-05-01", cloud_pct=2.0, ndvi=0.72)
    blob = obs.to_indices_jsonb()
    optical = blob["optical"]
    assert optical["ndvi"] == pytest.approx(0.72)
    assert "ndvi_p10" in optical and "ndvi_p90" in optical and "ndvi_std" in optical
    for name in ("evi", "ndre", "ndmi", "savi"):
        assert name in optical
        assert f"{name}_p10" in optical


# --------------------------------------------------------------------------- #
# bulk_upsert_observations
# --------------------------------------------------------------------------- #

def test_bulk_upsert_drops_rejected_observations_and_returns_written_count():
    db = FakeDB([])
    cursor = _FakeCursor(db, _FakeConn(db))
    observations = [
        _make_obs("2026-05-01", cloud_pct=2.0),    # good
        _make_obs("2026-05-02", cloud_pct=15.0),   # partial
        _make_obs("2026-05-03", cloud_pct=80.0),   # rejected
    ]
    written = bulk_upsert_observations(
        cursor, field_id="abc", user_id="u1", observations=observations
    )
    assert written == 2
    assert len(db.daily_logs) == 2
    qualities = sorted(r["observation_quality"] for r in db.daily_logs)
    assert qualities == ["good", "partial"]


def test_bulk_upsert_chunks_large_payloads():
    db = FakeDB([])
    cursor = _FakeCursor(db, _FakeConn(db))
    observations = [
        Observation(
            log_date=date(2026, 1, 1) + timedelta(days=i),
            cloud_pct=1.0,
            indices={"ndvi": _stats(0.5)},
        )
        for i in range(50)
    ]
    written = bulk_upsert_observations(
        cursor, field_id="abc", user_id=None, observations=observations, chunk_size=10,
    )
    assert written == 50
    assert len(db.daily_logs) == 50


def test_bulk_upsert_no_rows_returns_zero():
    db = FakeDB([])
    cursor = _FakeCursor(db, _FakeConn(db))
    written = bulk_upsert_observations(
        cursor, field_id="abc", user_id=None, observations=[]
    )
    assert written == 0
    assert db.daily_logs == []


# --------------------------------------------------------------------------- #
# Field selection branches
# --------------------------------------------------------------------------- #

def test_field_id_selector_only_processes_matching_field():
    rows = [
        _FieldRow(id="11111111-1111-1111-1111-111111111111", user_id="t1"),
        _FieldRow(id="22222222-2222-2222-2222-222222222222", user_id="t1"),
    ]
    db = FakeDB(rows)

    def fake_fetch(geometry, start, end):
        return [_make_obs("2026-05-01", cloud_pct=2.0)]

    stats = run_backfill(
        months=6,
        field_id=rows[1].id,
        init_ee=lambda: None,
        fetch_observations=fake_fetch,
        aoi_resolver=_aoi_resolver,
        db_factory=db.connect,
        now_fn=_fixed_now,
        progress_factory=lambda iterable, **kw: iterable,
    )
    assert stats.fields_total == 1
    assert stats.fields_succeeded == 1
    assert {r["field_id"] for r in db.daily_logs} == {rows[1].id}


def test_tenant_id_selector_processes_all_fields_for_tenant():
    rows = [
        _FieldRow(id="11111111-1111-1111-1111-111111111111", user_id="t1"),
        _FieldRow(id="22222222-2222-2222-2222-222222222222", user_id="t1"),
        _FieldRow(id="33333333-3333-3333-3333-333333333333", user_id="t2"),
    ]
    db = FakeDB(rows)

    def fake_fetch(geometry, start, end):
        return [_make_obs("2026-05-01", cloud_pct=2.0)]

    stats = run_backfill(
        months=6,
        tenant_id="t1",
        init_ee=lambda: None,
        fetch_observations=fake_fetch,
        aoi_resolver=_aoi_resolver,
        db_factory=db.connect,
        now_fn=_fixed_now,
        progress_factory=lambda iterable, **kw: iterable,
    )
    assert stats.fields_total == 2
    field_ids = {r["field_id"] for r in db.daily_logs}
    assert field_ids == {rows[0].id, rows[1].id}


def test_all_selector_processes_every_field():
    rows = [
        _FieldRow(id="11111111-1111-1111-1111-111111111111", user_id="t1"),
        _FieldRow(id="22222222-2222-2222-2222-222222222222", user_id="t2"),
    ]
    db = FakeDB(rows)

    stats = run_backfill(
        months=6,
        all_fields=True,
        init_ee=lambda: None,
        fetch_observations=lambda g, s, e: [_make_obs("2026-05-01", cloud_pct=2.0)],
        aoi_resolver=_aoi_resolver,
        db_factory=db.connect,
        now_fn=_fixed_now,
        progress_factory=lambda iterable, **kw: iterable,
    )
    assert stats.fields_total == 2
    assert stats.fields_succeeded == 2


def test_no_selector_raises_value_error():
    db = FakeDB([])
    with pytest.raises(ValueError):
        run_backfill(
            months=6,
            init_ee=lambda: None,
            fetch_observations=lambda *a, **k: [],
            aoi_resolver=_aoi_resolver,
            db_factory=db.connect,
            now_fn=_fixed_now,
        )


# --------------------------------------------------------------------------- #
# Full flow
# --------------------------------------------------------------------------- #

def test_full_flow_inserts_rows_with_correct_indices_blob():
    rows = [_FieldRow(id="11111111-1111-1111-1111-111111111111", user_id="t1")]
    db = FakeDB(rows)
    fetched_args: Dict[str, Any] = {}

    def fake_fetch(geometry, start, end):
        fetched_args["geometry"] = geometry
        fetched_args["start"] = start
        fetched_args["end"] = end
        return [
            _make_obs("2026-04-01", cloud_pct=3.0, ndvi=0.55),
            _make_obs("2026-04-15", cloud_pct=18.0, ndvi=0.65),  # partial
            _make_obs("2026-05-01", cloud_pct=80.0),             # rejected
        ]

    stats = run_backfill(
        months=6,
        field_id=rows[0].id,
        init_ee=lambda: None,
        fetch_observations=fake_fetch,
        aoi_resolver=_aoi_resolver,
        db_factory=db.connect,
        now_fn=_fixed_now,
        progress_factory=lambda iterable, **kw: iterable,
    )

    assert stats.fields_total == 1
    assert stats.fields_succeeded == 1
    assert stats.observations_inserted == 2
    assert stats.observations_rejected == 1

    assert fetched_args["start"] == date(2026, 5, 7) - timedelta(days=180)
    assert fetched_args["end"] == date(2026, 5, 7)
    assert fetched_args["geometry"]["type"] == "Polygon"

    by_date = {r["log_date"].isoformat(): r for r in db.daily_logs}
    r1 = by_date["2026-04-01"]
    assert r1["satellite_source"] == "s2-l2a"
    assert r1["observation_quality"] == "good"
    assert r1["ndvi"] == pytest.approx(0.55)
    optical = r1["indices"]["optical"]
    assert optical["ndvi"] == pytest.approx(0.55)
    assert optical["ndvi_p10"] == pytest.approx(0.50)
    assert optical["ndvi_std"] == pytest.approx(0.05)
    r2 = by_date["2026-04-15"]
    assert r2["observation_quality"] == "partial"
    assert "2026-05-01" not in by_date


def test_field_failure_isolated_does_not_block_others():
    rows = [
        _FieldRow(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", user_id="t1"),
        _FieldRow(id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", user_id="t1"),
    ]
    db = FakeDB(rows)
    seen: List[str] = []

    def flaky_fetch(geometry, start, end):
        seen.append("call")
        if len(seen) == 1:
            raise RuntimeError("EE quota exhausted on first call")
        return [_make_obs("2026-05-01", cloud_pct=2.0)]

    stats = run_backfill(
        months=6,
        all_fields=True,
        init_ee=lambda: None,
        fetch_observations=flaky_fetch,
        aoi_resolver=_aoi_resolver,
        db_factory=db.connect,
        now_fn=_fixed_now,
        progress_factory=lambda iterable, **kw: iterable,
    )

    assert stats.fields_total == 2
    assert stats.fields_succeeded == 1
    assert stats.fields_failed == 1
    assert len(db.daily_logs) == 1


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def test_cli_requires_a_selector():
    with pytest.raises(SystemExit):
        backfill_ingestion._parse_args(["--months", "6"])


def test_cli_field_id_and_months():
    args = backfill_ingestion._parse_args(
        ["--field-id", "abc", "--months", "3"]
    )
    assert args.field_id == "abc"
    assert args.months == 3
    assert args.tenant_id is None
    assert args.all is False


def test_cli_all_flag():
    args = backfill_ingestion._parse_args(["--all", "--months", "6"])
    assert args.all is True
    assert args.months == 6


def test_cli_tenant_id():
    args = backfill_ingestion._parse_args(["--tenant-id", "t1"])
    assert args.tenant_id == "t1"
    assert args.months == 12  # default


def test_cli_selectors_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        backfill_ingestion._parse_args(["--field-id", "a", "--all"])
