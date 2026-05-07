"""
Unit tests for workers/daily_ingestion.py.

Run:
    cd backend
    python -m pytest tests/test_daily_ingestion.py -v

The Sentinel Hub client and DB layer are both faked. No network or real
database is touched.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers import daily_ingestion  # noqa: E402
from workers.daily_ingestion import (  # noqa: E402
    classify_observation_quality,
    main,
    merge_observation,
    parse_optical_intervals,
    parse_sar_intervals,
    run_ingestion,
)


# --------------------------------------------------------------------------- #
# Fake Sentinel Hub client
# --------------------------------------------------------------------------- #

class FakeSentinelClient:
    """
    Returns canned Statistical API payloads. Records every call so tests
    can assert on geometry, time range, and which evalscript was used.
    """

    def __init__(
        self,
        optical_payload: Dict[str, Any],
        sar_payload: Dict[str, Any],
        pu_per_call: float = 1.0,
    ) -> None:
        self.optical_payload = optical_payload
        self.sar_payload = sar_payload
        self.calls: List[Dict[str, Any]] = []
        self._pu = 0.0
        self._pu_per_call = pu_per_call

    async def statistical_request(
        self,
        geometry: Dict[str, Any],
        time_range: Tuple[date, date],
        evalscript: str,
        collection: str,
    ) -> Dict[str, Any]:
        self.calls.append(
            {
                "geometry": geometry,
                "time_range": time_range,
                "collection": collection,
                "evalscript_kind": "s2" if "B08" in evalscript else "s1",
            }
        )
        self._pu += self._pu_per_call
        if collection == "sentinel-2-l2a":
            return self.optical_payload
        if collection == "sentinel-1-grd":
            return self.sar_payload
        return {"data": []}

    @property
    def pu_consumed_this_month(self) -> float:
        return self._pu

    async def aclose(self) -> None:
        pass


# --------------------------------------------------------------------------- #
# Fake DB
# --------------------------------------------------------------------------- #

@dataclass
class _FieldRow:
    id: str
    user_id: str
    polygon_coordinates: List[Dict[str, float]]
    last_ingested_hours_ago: Optional[float] = None  # None ⇒ never ingested


class FakeDB:
    """In-memory fake of the slice of psycopg2 the worker uses."""

    def __init__(self, fields_rows: List[_FieldRow]) -> None:
        self.fields = fields_rows
        self.daily_logs: List[Dict[str, Any]] = []
        self.committed = 0
        self.rolled_back = 0
        # Schema fingerprints tested by _has_column.
        self.columns = {
            ("fields", "id"),
            ("fields", "user_id"),
            ("fields", "polygon_coordinates"),
            ("daily_logs", "field_id"),
        }

    def connect(self):
        return _FakeConn(self)


class _FakeConn:
    def __init__(self, db: FakeDB) -> None:
        self._db = db

    def cursor(self, cursor_factory=None) -> "_FakeCursor":
        return _FakeCursor(self._db)

    def commit(self) -> None:
        self._db.committed += 1

    def rollback(self) -> None:
        self._db.rolled_back += 1

    def close(self) -> None:
        pass


class _FakeCursor:
    def __init__(self, db: FakeDB) -> None:
        self._db = db
        self._last: Any = None

    def execute(self, sql: str, params: tuple = ()) -> None:
        sql_norm = " ".join(sql.split())
        if "FROM information_schema.columns" in sql_norm:
            table, column = params
            self._last = (1,) if (table, column) in self._db.columns else None
        elif "FROM fields f" in sql_norm:
            # Eligibility: never ingested, OR last ingestion > N hours ago.
            min_hours = params[-1]
            field_filter = params[0] if len(params) > 1 else None
            rows: List[Dict[str, Any]] = []
            for f in self._db.fields:
                if field_filter is not None and f.id != field_filter:
                    continue
                eligible = (
                    f.last_ingested_hours_ago is None
                    or f.last_ingested_hours_ago > min_hours
                )
                if eligible:
                    rows.append({"id": f.id, "user_id": f.user_id})
            self._last = rows
        elif "INSERT INTO daily_logs" in sql_norm:
            (
                field_id,
                user_id,
                log_date,
                ndvi,
                evi,
                indices_json,
                satellite_source,
                cloud_pct,
                observation_quality,
                source,
            ) = params
            import json as _json

            existing = next(
                (
                    r for r in self._db.daily_logs
                    if r["field_id"] == field_id and r["log_date"] == log_date
                ),
                None,
            )
            row = {
                "field_id": field_id,
                "user_id": user_id,
                "log_date": log_date,
                "ndvi": ndvi,
                "evi": evi,
                "indices": _json.loads(indices_json),
                "satellite_source": satellite_source,
                "cloud_pct": cloud_pct,
                "observation_quality": observation_quality,
                "source": source,
            }
            if existing is None:
                self._db.daily_logs.append(row)
            else:
                existing.update(row)
            self._last = None
        else:
            self._last = None

    def fetchone(self):
        if isinstance(self._last, list):
            return self._last[0] if self._last else None
        return self._last

    def fetchall(self):
        if isinstance(self._last, list):
            return self._last
        return []

    def __iter__(self):
        return iter(self.fetchall())

    def close(self) -> None:
        pass


# --------------------------------------------------------------------------- #
# Payload builders
# --------------------------------------------------------------------------- #

def _stat_block(value: Optional[float]) -> Dict[str, Any]:
    return {"bands": {"B0": {"stats": {"mean": value}}}}


def make_optical_payload(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """observations: list of {"date": "YYYY-MM-DD", "ndvi": .., "data_mask": ..}."""
    data = []
    for o in observations:
        outputs = {
            "ndvi": _stat_block(o.get("ndvi")),
            "evi": _stat_block(o.get("evi", 0.4)),
            "ndre": _stat_block(o.get("ndre", 0.3)),
            "ndmi": _stat_block(o.get("ndmi", 0.2)),
            "savi": _stat_block(o.get("savi", 0.5)),
            "dataMask": _stat_block(o["data_mask"]),
        }
        data.append({"interval": {"from": f"{o['date']}T00:00:00Z"}, "outputs": outputs})
    return {"data": data}


def make_sar_payload(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    data = []
    for o in observations:
        outputs = {
            "vv_db": _stat_block(o.get("vv_db", -9.0)),
            "vh_db": _stat_block(o.get("vh_db", -16.0)),
        }
        data.append({"interval": {"from": f"{o['date']}T00:00:00Z"}, "outputs": outputs})
    return {"data": data}


# --------------------------------------------------------------------------- #
# Pure parsing / classification
# --------------------------------------------------------------------------- #

def test_classify_observation_quality_buckets():
    assert classify_observation_quality(0.0) == "good"
    assert classify_observation_quality(9.99) == "good"
    assert classify_observation_quality(10.0) == "partial"
    assert classify_observation_quality(29.99) == "partial"
    assert classify_observation_quality(30.0) == "rejected"
    assert classify_observation_quality(80.0) == "rejected"
    assert classify_observation_quality(None) == "rejected"


def test_parse_optical_derives_cloud_pct_from_data_mask():
    payload = make_optical_payload(
        [
            {"date": "2026-05-01", "ndvi": 0.7, "data_mask": 1.0},   # 0% cloud
            {"date": "2026-05-02", "ndvi": 0.6, "data_mask": 0.8},   # 20% cloud
            {"date": "2026-05-03", "ndvi": 0.5, "data_mask": 0.0},   # 100% cloud
        ]
    )
    parsed = parse_optical_intervals(payload)
    assert parsed[date(2026, 5, 1)]["cloud_pct"] == pytest.approx(0.0)
    assert parsed[date(2026, 5, 2)]["cloud_pct"] == pytest.approx(20.0)
    assert parsed[date(2026, 5, 3)]["cloud_pct"] == pytest.approx(100.0)


def test_parse_sar_extracts_means():
    payload = make_sar_payload([{"date": "2026-05-01", "vv_db": -7.5, "vh_db": -14.5}])
    parsed = parse_sar_intervals(payload)
    assert parsed[date(2026, 5, 1)] == {"vv_db": -7.5, "vh_db": -14.5}


def test_merge_observation_source_resolution():
    optical = {"ndvi": 0.6, "evi": 0.4, "ndre": 0.3, "ndmi": 0.2, "savi": 0.5, "cloud_pct": 5.0}
    sar = {"vv_db": -9.0, "vh_db": -16.0}
    indices, source, cp = merge_observation(optical, sar)
    assert source == "merged"
    assert cp == 5.0
    assert indices["optical"]["ndvi"] == 0.6
    assert indices["sar"]["vv_db"] == -9.0

    indices, source, cp = merge_observation(optical, None)
    assert source == "s2-l2a"
    assert "sar" not in indices

    indices, source, cp = merge_observation(None, sar)
    assert source == "s1-grd"
    assert "optical" not in indices
    assert cp is None


# --------------------------------------------------------------------------- #
# End-to-end run_ingestion
# --------------------------------------------------------------------------- #

@pytest.fixture
def aoi_resolver():
    def _resolve(field_id: str) -> Dict[str, Any]:
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
    return _resolve


def _fixed_now():
    return datetime(2026, 5, 7, 12, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_full_flow_upserts_good_and_partial_skips_rejected(aoi_resolver):
    db = FakeDB([
        _FieldRow(
            id="11111111-1111-1111-1111-111111111111",
            user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            polygon_coordinates=[{"lat": -17.8, "lon": 31.0}] * 4,
        ),
    ])
    optical = make_optical_payload([
        {"date": "2026-05-01", "ndvi": 0.72, "data_mask": 1.0},   # good
        {"date": "2026-05-03", "ndvi": 0.55, "data_mask": 0.85},  # partial (15% cloud)
        {"date": "2026-05-05", "ndvi": 0.40, "data_mask": 0.5},   # rejected (50% cloud)
    ])
    sar = make_sar_payload([
        {"date": "2026-05-01", "vv_db": -8.1, "vh_db": -15.2},
        {"date": "2026-05-04", "vv_db": -8.4, "vh_db": -15.8},
    ])
    sh = FakeSentinelClient(optical, sar, pu_per_call=2.5)

    stats = await run_ingestion(
        sh_client=sh,
        aoi_resolver=aoi_resolver,
        now_fn=_fixed_now,
        db_factory=db.connect,
    )

    # 2026-05-01: merged (S2 good + S1) ⇒ upsert.
    # 2026-05-03: S2 only, 15% cloud ⇒ partial ⇒ upsert.
    # 2026-05-04: S1 only ⇒ good (SAR is cloud-immune) ⇒ upsert.
    # 2026-05-05: S2 only, 50% cloud ⇒ rejected.
    assert stats.fields_processed == 1
    assert stats.upserts == 3
    assert stats.rejected_observations == 1
    assert stats.fields_failed == 0
    assert stats.pu_consumed == pytest.approx(5.0)  # two SH calls × 2.5 PU
    assert db.committed >= 1
    assert len(db.daily_logs) == 3

    by_date = {row["log_date"].isoformat(): row for row in db.daily_logs}
    r1 = by_date["2026-05-01"]
    assert r1["satellite_source"] == "merged"
    assert r1["observation_quality"] == "good"
    assert r1["ndvi"] == pytest.approx(0.72)
    assert r1["indices"]["optical"]["ndvi"] == pytest.approx(0.72)
    assert r1["indices"]["sar"]["vv_db"] == pytest.approx(-8.1)
    r3 = by_date["2026-05-03"]
    assert r3["satellite_source"] == "s2-l2a"
    assert r3["observation_quality"] == "partial"
    r4 = by_date["2026-05-04"]
    assert r4["satellite_source"] == "s1-grd"
    assert r4["observation_quality"] == "good"
    assert r4["indices"].get("optical") is None
    assert r4["indices"]["sar"]["vv_db"] == pytest.approx(-8.4)
    assert "2026-05-05" not in by_date


@pytest.mark.asyncio
async def test_dry_run_does_not_write(aoi_resolver):
    db = FakeDB([
        _FieldRow(
            id="11111111-1111-1111-1111-111111111111",
            user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            polygon_coordinates=[{"lat": -17.8, "lon": 31.0}] * 4,
        ),
    ])
    optical = make_optical_payload([{"date": "2026-05-01", "ndvi": 0.7, "data_mask": 1.0}])
    sar = make_sar_payload([{"date": "2026-05-01", "vv_db": -8.0, "vh_db": -15.0}])
    sh = FakeSentinelClient(optical, sar)

    stats = await run_ingestion(
        sh_client=sh,
        aoi_resolver=aoi_resolver,
        now_fn=_fixed_now,
        db_factory=db.connect,
        dry_run=True,
    )

    assert stats.upserts == 1
    assert db.daily_logs == []
    assert db.committed == 0


@pytest.mark.asyncio
async def test_field_id_filter_processes_only_one_field(aoi_resolver):
    rows = [
        _FieldRow(id=f"{i:08x}-1111-1111-1111-111111111111", user_id="u", polygon_coordinates=[{"lat": -17.8, "lon": 31.0}] * 4)
        for i in range(3)
    ]
    db = FakeDB(rows)
    sh = FakeSentinelClient(
        make_optical_payload([{"date": "2026-05-01", "ndvi": 0.7, "data_mask": 1.0}]),
        make_sar_payload([{"date": "2026-05-01", "vv_db": -8.0, "vh_db": -15.0}]),
    )

    stats = await run_ingestion(
        sh_client=sh,
        aoi_resolver=aoi_resolver,
        now_fn=_fixed_now,
        db_factory=db.connect,
        field_id_filter=rows[1].id,
    )

    assert stats.fields_processed == 1
    assert all(r["field_id"] == rows[1].id for r in db.daily_logs)


@pytest.mark.asyncio
async def test_recently_ingested_field_is_excluded(aoi_resolver):
    rows = [
        _FieldRow(
            id="11111111-1111-1111-1111-111111111111",
            user_id="u",
            polygon_coordinates=[{"lat": -17.8, "lon": 31.0}] * 4,
            last_ingested_hours_ago=1.0,  # <12h ⇒ not eligible
        ),
        _FieldRow(
            id="22222222-2222-2222-2222-222222222222",
            user_id="u",
            polygon_coordinates=[{"lat": -17.8, "lon": 31.0}] * 4,
            last_ingested_hours_ago=24.0,  # >12h ⇒ eligible
        ),
    ]
    db = FakeDB(rows)
    sh = FakeSentinelClient(
        make_optical_payload([{"date": "2026-05-01", "ndvi": 0.7, "data_mask": 1.0}]),
        make_sar_payload([{"date": "2026-05-01", "vv_db": -8.0, "vh_db": -15.0}]),
    )

    stats = await run_ingestion(
        sh_client=sh,
        aoi_resolver=aoi_resolver,
        now_fn=_fixed_now,
        db_factory=db.connect,
    )

    assert stats.fields_processed == 1
    assert {r["field_id"] for r in db.daily_logs} == {rows[1].id}


@pytest.mark.asyncio
async def test_field_failure_is_isolated(aoi_resolver):
    rows = [
        _FieldRow(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", user_id="u", polygon_coordinates=[{"lat": -17.8, "lon": 31.0}] * 4),
        _FieldRow(id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", user_id="u", polygon_coordinates=[{"lat": -17.8, "lon": 31.0}] * 4),
    ]
    db = FakeDB(rows)

    class FailFirstClient(FakeSentinelClient):
        """Raises on the first S2 call, so the first field fails entirely."""

        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.s2_seen = 0

        async def statistical_request(self, geometry, time_range, evalscript, collection):
            if collection == "sentinel-2-l2a":
                self.s2_seen += 1
                if self.s2_seen == 1:
                    raise RuntimeError("boom")
            return await super().statistical_request(geometry, time_range, evalscript, collection)

    sh = FailFirstClient(
        make_optical_payload([{"date": "2026-05-01", "ndvi": 0.7, "data_mask": 1.0}]),
        make_sar_payload([{"date": "2026-05-01", "vv_db": -8.0, "vh_db": -15.0}]),
    )

    stats = await run_ingestion(
        sh_client=sh,
        aoi_resolver=aoi_resolver,
        now_fn=_fixed_now,
        db_factory=db.connect,
    )

    assert stats.fields_failed == 1
    assert stats.fields_processed == 1
    assert len(db.daily_logs) == 1
    assert db.daily_logs[0]["field_id"] == rows[1].id


# --------------------------------------------------------------------------- #
# JSON logging
# --------------------------------------------------------------------------- #

def test_json_formatter_emits_valid_single_line_json(capsys):
    daily_ingestion.configure_logging()
    daily_ingestion.logger.info(
        "ingestion.test", extra={"field_id": "abc", "n": 7}
    )
    out = capsys.readouterr().out.strip()
    assert "\n" not in out
    import json as _json
    parsed = _json.loads(out)
    assert parsed["message"] == "ingestion.test"
    assert parsed["field_id"] == "abc"
    assert parsed["n"] == 7
    assert parsed["level"] == "INFO"
    assert "ts" in parsed


# --------------------------------------------------------------------------- #
# CLI argument parsing
# --------------------------------------------------------------------------- #

def test_cli_parser_defaults():
    args = daily_ingestion._parse_args([])
    assert args.dry_run is False
    assert args.field_id is None
    assert args.batch_size == daily_ingestion.DEFAULT_BATCH_SIZE


def test_cli_parser_flags():
    args = daily_ingestion._parse_args(["--dry-run", "--field-id", "abc", "--batch-size", "10"])
    assert args.dry_run is True
    assert args.field_id == "abc"
    assert args.batch_size == 10
