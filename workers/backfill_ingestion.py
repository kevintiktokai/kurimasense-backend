"""
On-demand satellite backfill worker (Google Earth Engine).

Bulk historical ingestion lives here because GEE is free and handles long
date ranges efficiently. The daily worker (workers/daily_ingestion.py) keeps
using Sentinel Hub for fresh, low-latency observations.

Usage:
    python workers/backfill_ingestion.py --field-id <UUID>  --months 12
    python workers/backfill_ingestion.py --tenant-id <UUID> --months 12
    python workers/backfill_ingestion.py --all              --months 6

For each field:
  1. Resolve AOI via services.satellite.field_aoi.get_field_aoi
  2. Filter Sentinel-2 SR Harmonized by date and field bounds
  3. Mask clouds using SCL (with a QA60 fallback)
  4. Compute NDVI, EVI, NDRE, NDMI, SAVI per image
  5. Reduce each image to {mean, p10, p90, std} over the field polygon and
     compute cloud_pct from the mask
  6. Bulk-UPSERT into daily_logs using execute_values (chunked)

Authenticate via service account key at GEE_SERVICE_ACCOUNT_KEY (path to JSON).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field as dc_field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

# Make the repo root importable when run as `python workers/backfill_ingestion.py`.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from database import get_db_connection
from services.satellite.field_aoi import get_field_aoi
from workers.daily_ingestion import (
    CLOUD_GOOD_MAX,
    CLOUD_PARTIAL_MAX,
    classify_observation_quality,
    configure_logging,
)

logger = logging.getLogger("workers.backfill_ingestion")

S2_SR_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
DEFAULT_BULK_INSERT_CHUNK = 500
GEE_SCALE_M = 10  # Sentinel-2 native resolution for visible/NIR bands.


# --------------------------------------------------------------------------- #
# Observation record
# --------------------------------------------------------------------------- #

@dataclass
class IndexStats:
    mean: Optional[float] = None
    p10: Optional[float] = None
    p90: Optional[float] = None
    std: Optional[float] = None

    def to_dict(self) -> Dict[str, Optional[float]]:
        return {"mean": self.mean, "p10": self.p10, "p90": self.p90, "std": self.std}


@dataclass
class Observation:
    log_date: date
    cloud_pct: float
    indices: Dict[str, IndexStats]  # keyed by lowercase index name

    def to_indices_jsonb(self) -> Dict[str, Any]:
        """
        Build the indices JSONB structure used in daily_logs. The mean is
        stored as the top-level scalar (matching the daily worker) with
        _p10/_p90/_std siblings for distribution stats.
        """
        optical: Dict[str, Optional[float]] = {}
        for name, stats in self.indices.items():
            optical[name] = stats.mean
            optical[f"{name}_p10"] = stats.p10
            optical[f"{name}_p90"] = stats.p90
            optical[f"{name}_std"] = stats.std
        return {"optical": optical}


# --------------------------------------------------------------------------- #
# Backfill stats
# --------------------------------------------------------------------------- #

@dataclass
class BackfillStats:
    fields_total: int = 0
    fields_succeeded: int = 0
    fields_failed: int = 0
    observations_inserted: int = 0
    observations_rejected: int = 0
    failures: List[Dict[str, str]] = dc_field(default_factory=list)


# --------------------------------------------------------------------------- #
# Earth Engine client (lazy import + monkeypatch seam)
# --------------------------------------------------------------------------- #

def init_earth_engine(service_account_key_path: Optional[str] = None) -> None:
    """
    Authenticate the earthengine-api with a service account key.
    Reads GEE_SERVICE_ACCOUNT_KEY if no path is provided.
    """
    key_path = service_account_key_path or os.environ.get("GEE_SERVICE_ACCOUNT_KEY")
    if not key_path:
        raise RuntimeError(
            "GEE_SERVICE_ACCOUNT_KEY env var (or service_account_key_path) "
            "is required for backfill ingestion."
        )
    if not os.path.exists(key_path):
        raise RuntimeError(f"Service account key file not found: {key_path}")

    import ee  # noqa: WPS433 - lazy import; heavy dep only needed for real runs.

    with open(key_path, "r") as f:
        creds_data = json.load(f)
    credentials = ee.ServiceAccountCredentials(creds_data["client_email"], key_path)
    ee.Initialize(credentials)
    logger.info(
        "backfill.ee_initialised",
        extra={"service_account": creds_data.get("client_email")},
    )


def fetch_gee_observations(
    geometry: Dict[str, Any],
    start_date: date,
    end_date: date,
) -> List[Observation]:
    """
    Query Earth Engine for S2-SR observations over the given polygon and
    date range. Returns one Observation per image that passed cloud masking.

    This function is the integration seam. Tests monkey-patch this to inject
    canned results without touching the network.
    """
    import ee  # noqa: WPS433

    aoi = ee.Geometry(geometry)
    collection = (
        ee.ImageCollection(S2_SR_COLLECTION)
        .filterBounds(aoi)
        .filterDate(start_date.isoformat(), end_date.isoformat())
    )

    # SCL classes treated as unusable: 3=cloud shadow, 8=cloud medium prob,
    # 9=cloud high prob, 10=thin cirrus.
    bad_scl = ee.List([3, 8, 9, 10])

    def _process(image):
        scl = image.select("SCL")
        cloud_mask = scl.remap(bad_scl, ee.List([1, 1, 1, 1]), 0).rename("cloud")
        valid_mask = cloud_mask.eq(0)

        scaled = image.select(["B02", "B04", "B05", "B08", "B11"]).divide(10000)
        b02 = scaled.select("B02")
        b04 = scaled.select("B04")
        b05 = scaled.select("B05")
        b08 = scaled.select("B08")
        b11 = scaled.select("B11")

        ndvi = b08.subtract(b04).divide(b08.add(b04)).rename("ndvi")
        evi = (
            b08.subtract(b04)
            .multiply(2.5)
            .divide(b08.add(b04.multiply(6)).subtract(b02.multiply(7.5)).add(1))
            .rename("evi")
        )
        ndre = b08.subtract(b05).divide(b08.add(b05)).rename("ndre")
        ndmi = b08.subtract(b11).divide(b08.add(b11)).rename("ndmi")
        savi = (
            b08.subtract(b04)
            .multiply(1.5)
            .divide(b08.add(b04).add(0.5))
            .rename("savi")
        )

        masked = (
            ee.Image.cat([ndvi, evi, ndre, ndmi, savi])
            .updateMask(valid_mask)
        )

        reducer = (
            ee.Reducer.mean()
            .combine(ee.Reducer.percentile([10, 90]), sharedInputs=True)
            .combine(ee.Reducer.stdDev(), sharedInputs=True)
        )
        stats = masked.reduceRegion(
            reducer=reducer, geometry=aoi, scale=GEE_SCALE_M, maxPixels=1e9, bestEffort=True
        )
        cloud_stats = cloud_mask.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi, scale=GEE_SCALE_M,
            maxPixels=1e9, bestEffort=True,
        )

        return ee.Feature(
            None,
            stats.combine(
                ee.Dictionary({
                    "cloud_pct": ee.Number(cloud_stats.get("cloud", 0)).multiply(100),
                    "log_date": image.date().format("YYYY-MM-dd"),
                })
            ),
        )

    fc = collection.map(_process)
    raw = fc.getInfo()  # Single round trip — list of Features.

    observations: List[Observation] = []
    for feat in raw.get("features", []):
        props = feat.get("properties") or {}
        log_date_str = props.get("log_date")
        if not log_date_str:
            continue
        try:
            log_date = datetime.strptime(log_date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        cloud_pct = float(props.get("cloud_pct") or 0.0)
        indices: Dict[str, IndexStats] = {}
        for name in ("ndvi", "evi", "ndre", "ndmi", "savi"):
            indices[name] = IndexStats(
                mean=_safe_float(props.get(f"{name}_mean")),
                p10=_safe_float(props.get(f"{name}_p10")),
                p90=_safe_float(props.get(f"{name}_p90")),
                std=_safe_float(props.get(f"{name}_stdDev")),
            )
        observations.append(
            Observation(log_date=log_date, cloud_pct=cloud_pct, indices=indices)
        )
    return observations


def _safe_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# Field selection
# --------------------------------------------------------------------------- #

def select_fields(
    cursor,
    *,
    field_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    all_fields: bool = False,
) -> List[Dict[str, Any]]:
    if field_id:
        cursor.execute(
            "SELECT id, user_id FROM fields WHERE id = %s::uuid",
            (field_id,),
        )
    elif tenant_id:
        cursor.execute(
            "SELECT id, user_id FROM fields WHERE user_id = %s::uuid "
            "AND polygon_coordinates IS NOT NULL",
            (tenant_id,),
        )
    elif all_fields:
        cursor.execute(
            "SELECT id, user_id FROM fields WHERE polygon_coordinates IS NOT NULL"
        )
    else:
        return []
    return list(cursor.fetchall())


# --------------------------------------------------------------------------- #
# DB writes
# --------------------------------------------------------------------------- #

def bulk_upsert_observations(
    cursor,
    *,
    field_id: str,
    user_id: Optional[str],
    observations: List[Observation],
    chunk_size: int = DEFAULT_BULK_INSERT_CHUNK,
) -> int:
    """
    UPSERT a list of observations into daily_logs in batches.
    Returns the number of rows actually written (rejected ones are dropped).
    """
    from psycopg2.extras import execute_values

    rows: List[Tuple[Any, ...]] = []
    for obs in observations:
        quality = classify_observation_quality(obs.cloud_pct)
        if quality == "rejected":
            continue
        indices_blob = obs.to_indices_jsonb()
        ndvi = indices_blob["optical"].get("ndvi")
        evi = indices_blob["optical"].get("evi")
        rows.append((
            field_id,
            user_id,
            obs.log_date,
            ndvi,
            evi,
            json.dumps(indices_blob),
            "s2-l2a",
            obs.cloud_pct,
            quality,
            "s2-l2a",
        ))

    if not rows:
        return 0

    written = 0
    sql = """
        INSERT INTO daily_logs (
            field_id, user_id, log_date, ndvi, evi,
            indices, satellite_source, cloud_pct, observation_quality, source
        )
        VALUES %s
        ON CONFLICT (field_id, log_date) DO UPDATE SET
            ndvi = EXCLUDED.ndvi,
            evi = COALESCE(EXCLUDED.evi, daily_logs.evi),
            indices = EXCLUDED.indices,
            satellite_source = EXCLUDED.satellite_source,
            cloud_pct = EXCLUDED.cloud_pct,
            observation_quality = EXCLUDED.observation_quality
    """
    template = "(%s::uuid, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)"
    for start in range(0, len(rows), chunk_size):
        chunk = rows[start : start + chunk_size]
        execute_values(cursor, sql, chunk, template=template)
        written += len(chunk)
    return written


# --------------------------------------------------------------------------- #
# Top-level orchestration
# --------------------------------------------------------------------------- #

def _months_to_date_range(months: int, today: date) -> Tuple[date, date]:
    # Approximate: 30 days * months. Earth Engine doesn't care about exact
    # calendar months for filtering and a few extra days won't hurt.
    return (today - timedelta(days=30 * months), today)


def run_backfill(
    *,
    months: int,
    field_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    all_fields: bool = False,
    init_ee: Callable[[], None] = init_earth_engine,
    fetch_observations: Callable[..., List[Observation]] = fetch_gee_observations,
    aoi_resolver: Callable[[str], Dict[str, Any]] = get_field_aoi,
    db_factory: Callable[[], Any] = get_db_connection,
    now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    progress_factory: Optional[Callable[..., Any]] = None,
) -> BackfillStats:
    if not (field_id or tenant_id or all_fields):
        raise ValueError("One of --field-id, --tenant-id, or --all is required")

    today = now_fn().date()
    start, end = _months_to_date_range(months, today)
    stats = BackfillStats()

    init_ee()

    conn = db_factory()
    if conn is None:
        raise RuntimeError("Database unavailable — aborting backfill")

    if progress_factory is None:
        try:
            from tqdm import tqdm as _tqdm  # noqa: WPS433
            progress_factory = _tqdm
        except ImportError:
            progress_factory = lambda iterable, **kw: iterable

    try:
        from psycopg2.extras import RealDictCursor

        select_cursor = conn.cursor(cursor_factory=RealDictCursor)
        fields = select_fields(
            select_cursor, field_id=field_id, tenant_id=tenant_id, all_fields=all_fields
        )
        select_cursor.close()
        stats.fields_total = len(fields)
        logger.info(
            "backfill.run_started",
            extra={
                "fields_total": stats.fields_total,
                "months": months,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "selection": "field" if field_id else ("tenant" if tenant_id else "all"),
            },
        )

        iterator = progress_factory(fields, desc="Fields", unit="field")
        for row in iterator:
            fid = str(row["id"])
            uid = str(row["user_id"]) if row.get("user_id") else None
            try:
                aoi = aoi_resolver(fid)
                geometry = {"type": aoi["type"], "coordinates": aoi["coordinates"]}
                observations = fetch_observations(geometry, start, end)
                rejected = sum(
                    1 for o in observations
                    if classify_observation_quality(o.cloud_pct) == "rejected"
                )
                stats.observations_rejected += rejected

                cursor = conn.cursor(cursor_factory=RealDictCursor)
                try:
                    written = bulk_upsert_observations(
                        cursor,
                        field_id=fid,
                        user_id=uid,
                        observations=observations,
                    )
                    conn.commit()
                    stats.observations_inserted += written
                    stats.fields_succeeded += 1
                    logger.info(
                        "backfill.field_done",
                        extra={
                            "field_id": fid,
                            "fetched": len(observations),
                            "inserted": written,
                            "rejected": rejected,
                        },
                    )
                finally:
                    cursor.close()
            except Exception as e:  # noqa: BLE001
                conn.rollback()
                stats.fields_failed += 1
                stats.failures.append({"field_id": fid, "error": str(e)})
                logger.warning(
                    "backfill.field_failed",
                    extra={"field_id": fid, "error": str(e)},
                    exc_info=True,
                )

        logger.info(
            "backfill.run_completed",
            extra={
                "fields_total": stats.fields_total,
                "fields_succeeded": stats.fields_succeeded,
                "fields_failed": stats.fields_failed,
                "observations_inserted": stats.observations_inserted,
                "observations_rejected": stats.observations_rejected,
            },
        )
        # Human-readable summary printed to stdout for interactive runs;
        # JSON-formatted log lines above remain the canonical record.
        print(
            f"Backfill complete: {stats.fields_succeeded}/{stats.fields_total} "
            f"fields, {stats.observations_inserted} observations inserted, "
            f"{stats.observations_rejected} rejected, {stats.fields_failed} failed."
        )
        return stats
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Backfill historical satellite observations via Google Earth Engine."
    )
    selector = p.add_mutually_exclusive_group(required=True)
    selector.add_argument("--field-id", help="Single field UUID to backfill.")
    selector.add_argument("--tenant-id", help="Backfill all fields for a tenant (user_id).")
    selector.add_argument(
        "--all", action="store_true", help="Backfill every field with a polygon."
    )
    p.add_argument(
        "--months",
        type=int,
        default=12,
        help="How many months of history to fetch (default: 12).",
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    configure_logging()
    try:
        stats = run_backfill(
            months=args.months,
            field_id=args.field_id,
            tenant_id=args.tenant_id,
            all_fields=args.all,
        )
    except Exception:  # noqa: BLE001
        logger.exception("backfill.run_crashed")
        return 1
    if stats.fields_failed and stats.fields_succeeded == 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
