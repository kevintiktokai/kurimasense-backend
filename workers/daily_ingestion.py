"""
Daily satellite ingestion worker.

Run via cron:
    python workers/daily_ingestion.py [--dry-run] [--field-id UUID] [--batch-size N]

For each active field (not retired, has at least one coordinate, last successful
ingestion older than 12h), the worker:
  - Resolves the AOI via services.satellite.field_aoi.get_field_aoi
  - Calls the Sentinel Hub Statistical API for S2 optical indices and S1 SAR
    backscatter over the last 7 days
  - For each observation date, builds the indices JSONB blob, classifies
    observation_quality from cloud_pct (good <10, partial 10-30, rejected >30
    which is dropped), and UPSERTs into daily_logs
  - Syncs the top-level ndvi column from indices.optical.ndvi

Logs are emitted as one JSON object per line for production aggregation.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

# Make the repo root importable when the script runs from `workers/`.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from database import get_db_connection
from services.satellite.field_aoi import get_field_aoi
from services.satellite.indices import (
    EVALSCRIPT_S1_SAR_BACKSCATTER,
    EVALSCRIPT_S2_OPTICAL_INDICES,
)
from services.satellite.sentinel_hub_client import (
    SentinelHubClient,
    SentinelHubError,
    SentinelHubQuotaError,
)

logger = logging.getLogger("workers.daily_ingestion")

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

DEFAULT_BATCH_SIZE = 50
LOOKBACK_DAYS = 7
MIN_HOURS_SINCE_INGESTION = 12

S2_COLLECTION = "sentinel-2-l2a"
S1_COLLECTION = "sentinel-1-grd"

CLOUD_GOOD_MAX = 10.0   # cloud_pct < 10 → good
CLOUD_PARTIAL_MAX = 30.0  # cloud_pct < 30 → partial; otherwise rejected


# --------------------------------------------------------------------------- #
# JSON logging
# --------------------------------------------------------------------------- #

class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        # Anything attached via logger.info(..., extra={"k": v}) lands in __dict__.
        for k, v in record.__dict__.items():
            if k in payload or k.startswith("_"):
                continue
            if k in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module",
                "msecs", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName",
                "taskName",
            ):
                continue
            try:
                json.dumps(v)
                payload[k] = v
            except (TypeError, ValueError):
                payload[k] = repr(v)
        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    # Replace any existing handlers so JSON formatting is the only output.
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)


# --------------------------------------------------------------------------- #
# Stats
# --------------------------------------------------------------------------- #

@dataclass
class IngestionStats:
    fields_processed: int = 0
    fields_skipped: int = 0
    fields_failed: int = 0
    upserts: int = 0
    rejected_observations: int = 0
    pu_consumed: float = 0.0
    failures: List[Dict[str, str]] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# DB helpers
# --------------------------------------------------------------------------- #

def _has_column(cursor, table: str, column: str) -> bool:
    cursor.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        LIMIT 1
        """,
        (table, column),
    )
    return cursor.fetchone() is not None


def select_active_fields(
    cursor,
    *,
    field_id_filter: Optional[str] = None,
    min_hours_since_ingestion: int = MIN_HOURS_SINCE_INGESTION,
) -> List[Dict[str, Any]]:
    """
    Return rows of (id, user_id) for fields that are eligible for ingestion.

    A field is eligible when:
      - polygon_coordinates is non-empty (≥ 1 vertex)
      - it is not retired (uses is_retired or retired_at if those columns exist;
        otherwise the predicate is omitted gracefully)
      - the latest daily_logs row for it is older than min_hours_since_ingestion
        hours, or there are no daily_logs rows at all
    """
    not_retired_clause = ""
    if _has_column(cursor, "fields", "is_retired"):
        not_retired_clause = "AND COALESCE(f.is_retired, FALSE) = FALSE"
    elif _has_column(cursor, "fields", "retired_at"):
        not_retired_clause = "AND f.retired_at IS NULL"

    field_filter_sql = ""
    params: Tuple[Any, ...] = ()
    if field_id_filter is not None:
        field_filter_sql = "AND f.id = %s::uuid"
        params = (field_id_filter,)

    sql = f"""
        SELECT f.id, f.user_id
        FROM fields f
        LEFT JOIN LATERAL (
            SELECT MAX(created_at) AS last_ingested
            FROM daily_logs dl
            WHERE dl.field_id = f.id
        ) last_log ON TRUE
        WHERE f.polygon_coordinates IS NOT NULL
          AND jsonb_array_length(f.polygon_coordinates) >= 1
          {not_retired_clause}
          {field_filter_sql}
          AND (
              last_log.last_ingested IS NULL
              OR last_log.last_ingested < (NOW() - (%s::int * INTERVAL '1 hour'))
          )
        ORDER BY f.id
    """
    cursor.execute(sql, params + (min_hours_since_ingestion,))
    return list(cursor.fetchall())


def upsert_daily_log(
    cursor,
    *,
    field_id: str,
    user_id: Optional[str],
    log_date: date,
    indices: Dict[str, Any],
    satellite_source: str,
    cloud_pct: Optional[float],
    observation_quality: str,
) -> None:
    ndvi = (indices.get("optical") or {}).get("ndvi")
    evi = (indices.get("optical") or {}).get("evi")
    cursor.execute(
        """
        INSERT INTO daily_logs (
            field_id, user_id, log_date, ndvi, evi,
            indices, satellite_source, cloud_pct, observation_quality, source
        )
        VALUES (
            %s::uuid, %s, %s, %s, %s,
            %s::jsonb, %s, %s, %s, %s
        )
        ON CONFLICT (field_id, log_date) DO UPDATE SET
            ndvi = EXCLUDED.ndvi,
            evi = COALESCE(EXCLUDED.evi, daily_logs.evi),
            indices = EXCLUDED.indices,
            satellite_source = EXCLUDED.satellite_source,
            cloud_pct = EXCLUDED.cloud_pct,
            observation_quality = EXCLUDED.observation_quality
        """,
        (
            field_id,
            user_id,
            log_date,
            ndvi,
            evi,
            json.dumps(indices),
            satellite_source,
            cloud_pct,
            observation_quality,
            satellite_source,
        ),
    )


# --------------------------------------------------------------------------- #
# Sentinel Hub response parsing
# --------------------------------------------------------------------------- #

def _parse_iso_date(s: str) -> date:
    # Accepts both "YYYY-MM-DD" and full ISO datetimes.
    if "T" in s:
        s = s.split("T", 1)[0]
    return datetime.strptime(s, "%Y-%m-%d").date()


def _stat_mean(outputs: Dict[str, Any], output_id: str) -> Optional[float]:
    """
    Pull bands.B0.stats.mean for the given output id from a Statistical
    API interval. Returns None if missing.
    """
    out = outputs.get(output_id)
    if not isinstance(out, dict):
        return None
    bands = out.get("bands") or {}
    # Sentinel Hub returns either {"B0": {...}} or {"<name>": {...}} for
    # single-band outputs; read the first band.
    if not bands:
        return None
    band = next(iter(bands.values()))
    stats = (band or {}).get("stats") or {}
    mean = stats.get("mean")
    if mean is None:
        return None
    try:
        return float(mean)
    except (TypeError, ValueError):
        return None


def parse_optical_intervals(payload: Dict[str, Any]) -> Dict[date, Dict[str, Any]]:
    """
    Produce {date: {"ndvi": .., "evi": .., "ndre": .., "ndmi": .., "savi": ..,
                    "cloud_pct": ..}} from a Statistical API response.

    cloud_pct is derived from the dataMask output: dataMask=1 for valid pixels,
    0 for masked (cloud/shadow). Cloud fraction = (1 - mean(dataMask)) * 100.
    """
    out: Dict[date, Dict[str, Any]] = {}
    for entry in payload.get("data", []):
        interval = entry.get("interval") or {}
        from_str = interval.get("from")
        if not from_str:
            continue
        try:
            d = _parse_iso_date(from_str)
        except ValueError:
            continue
        outputs = entry.get("outputs") or {}
        data_mask_mean = _stat_mean(outputs, "dataMask")
        if data_mask_mean is None or data_mask_mean <= 0:
            cloud_pct: Optional[float] = 100.0
        else:
            cloud_pct = max(0.0, min(100.0, (1.0 - data_mask_mean) * 100.0))
        out[d] = {
            "ndvi": _stat_mean(outputs, "ndvi"),
            "evi": _stat_mean(outputs, "evi"),
            "ndre": _stat_mean(outputs, "ndre"),
            "ndmi": _stat_mean(outputs, "ndmi"),
            "savi": _stat_mean(outputs, "savi"),
            "cloud_pct": cloud_pct,
        }
    return out


def parse_sar_intervals(payload: Dict[str, Any]) -> Dict[date, Dict[str, Any]]:
    """Produce {date: {"vv_db": .., "vh_db": ..}} from a Statistical API response."""
    out: Dict[date, Dict[str, Any]] = {}
    for entry in payload.get("data", []):
        interval = entry.get("interval") or {}
        from_str = interval.get("from")
        if not from_str:
            continue
        try:
            d = _parse_iso_date(from_str)
        except ValueError:
            continue
        outputs = entry.get("outputs") or {}
        out[d] = {
            "vv_db": _stat_mean(outputs, "vv_db"),
            "vh_db": _stat_mean(outputs, "vh_db"),
        }
    return out


def classify_observation_quality(cloud_pct: Optional[float]) -> str:
    """good <10, partial 10-30, rejected >30. None ⇒ rejected."""
    if cloud_pct is None:
        return "rejected"
    if cloud_pct < CLOUD_GOOD_MAX:
        return "good"
    if cloud_pct < CLOUD_PARTIAL_MAX:
        return "partial"
    return "rejected"


def merge_observation(
    optical: Optional[Dict[str, Any]], sar: Optional[Dict[str, Any]]
) -> Tuple[Dict[str, Any], str, Optional[float]]:
    """
    Combine S2 + S1 readings for a single date into the indices blob,
    determine satellite_source, and surface cloud_pct.
    """
    indices: Dict[str, Any] = {}
    if optical:
        indices["optical"] = {
            "ndvi": optical.get("ndvi"),
            "evi": optical.get("evi"),
            "ndre": optical.get("ndre"),
            "ndmi": optical.get("ndmi"),
            "savi": optical.get("savi"),
        }
    if sar:
        indices["sar"] = {"vv_db": sar.get("vv_db"), "vh_db": sar.get("vh_db")}
    cloud_pct = optical.get("cloud_pct") if optical else None
    if optical and sar:
        source = "merged"
    elif optical:
        source = "s2-l2a"
    elif sar:
        source = "s1-grd"
    else:
        source = "s2-l2a"
    return indices, source, cloud_pct


# --------------------------------------------------------------------------- #
# Per-field orchestration
# --------------------------------------------------------------------------- #

async def process_field(
    *,
    cursor,
    sh_client: SentinelHubClient,
    field_id: str,
    user_id: Optional[str],
    aoi_resolver: Callable[[str], Dict[str, Any]],
    time_range: Tuple[date, date],
    dry_run: bool,
    stats: IngestionStats,
) -> None:
    aoi = aoi_resolver(field_id)
    geometry = {"type": aoi["type"], "coordinates": aoi["coordinates"]}

    optical_payload = await sh_client.statistical_request(
        geometry, time_range, EVALSCRIPT_S2_OPTICAL_INDICES, S2_COLLECTION
    )
    sar_payload = await sh_client.statistical_request(
        geometry, time_range, EVALSCRIPT_S1_SAR_BACKSCATTER, S1_COLLECTION
    )

    optical_by_date = parse_optical_intervals(optical_payload)
    sar_by_date = parse_sar_intervals(sar_payload)
    all_dates = sorted(set(optical_by_date) | set(sar_by_date))

    for d in all_dates:
        optical = optical_by_date.get(d)
        sar = sar_by_date.get(d)
        indices, source, cloud_pct = merge_observation(optical, sar)
        if source == "s1-grd":
            # SAR is cloud-immune; classify by data presence, not cloud_pct.
            quality = "good"
        else:
            quality = classify_observation_quality(cloud_pct)
        if quality == "rejected":
            stats.rejected_observations += 1
            logger.info(
                "ingestion.observation_rejected",
                extra={
                    "field_id": field_id,
                    "log_date": d.isoformat(),
                    "cloud_pct": cloud_pct,
                },
            )
            continue
        if dry_run:
            logger.info(
                "ingestion.dry_run_upsert",
                extra={
                    "field_id": field_id,
                    "log_date": d.isoformat(),
                    "satellite_source": source,
                    "cloud_pct": cloud_pct,
                    "observation_quality": quality,
                },
            )
        else:
            upsert_daily_log(
                cursor,
                field_id=field_id,
                user_id=user_id,
                log_date=d,
                indices=indices,
                satellite_source=source,
                cloud_pct=cloud_pct,
                observation_quality=quality,
            )
        stats.upserts += 1


# --------------------------------------------------------------------------- #
# Top-level entry
# --------------------------------------------------------------------------- #

async def run_ingestion(
    *,
    dry_run: bool = False,
    field_id_filter: Optional[str] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    sh_client: Optional[SentinelHubClient] = None,
    aoi_resolver: Callable[[str], Dict[str, Any]] = get_field_aoi,
    now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    db_factory: Callable[[], Any] = get_db_connection,
) -> IngestionStats:
    stats = IngestionStats()
    today = now_fn().date()
    time_range = (today - timedelta(days=LOOKBACK_DAYS), today)

    conn = db_factory()
    if conn is None:
        raise RuntimeError("Database unavailable — aborting ingestion run")

    owns_client = sh_client is None
    if sh_client is None:
        sh_client = SentinelHubClient()

    try:
        from psycopg2.extras import RealDictCursor

        select_cursor = conn.cursor(cursor_factory=RealDictCursor)
        fields = select_active_fields(
            select_cursor, field_id_filter=field_id_filter
        )
        select_cursor.close()
        logger.info(
            "ingestion.run_started",
            extra={
                "candidate_fields": len(fields),
                "batch_size": batch_size,
                "dry_run": dry_run,
                "field_id_filter": field_id_filter,
            },
        )

        for batch_start in range(0, len(fields), batch_size):
            batch = fields[batch_start : batch_start + batch_size]
            for row in batch:
                fid = str(row["id"])
                uid = str(row["user_id"]) if row.get("user_id") else None
                t0 = time.monotonic()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                try:
                    await process_field(
                        cursor=cursor,
                        sh_client=sh_client,
                        field_id=fid,
                        user_id=uid,
                        aoi_resolver=aoi_resolver,
                        time_range=time_range,
                        dry_run=dry_run,
                        stats=stats,
                    )
                    if not dry_run:
                        conn.commit()
                    else:
                        conn.rollback()
                    stats.fields_processed += 1
                    logger.info(
                        "ingestion.field_done",
                        extra={
                            "field_id": fid,
                            "elapsed_s": round(time.monotonic() - t0, 3),
                        },
                    )
                except SentinelHubQuotaError as e:
                    conn.rollback()
                    logger.error(
                        "ingestion.quota_exceeded",
                        extra={"field_id": fid, "error": str(e)},
                    )
                    stats.failures.append({"field_id": fid, "error": str(e)})
                    stats.fields_failed += 1
                    raise
                except (SentinelHubError, Exception) as e:  # noqa: BLE001
                    conn.rollback()
                    stats.fields_failed += 1
                    stats.failures.append({"field_id": fid, "error": str(e)})
                    logger.warning(
                        "ingestion.field_failed",
                        extra={"field_id": fid, "error": str(e)},
                        exc_info=True,
                    )
                finally:
                    cursor.close()

        stats.pu_consumed = sh_client.pu_consumed_this_month
        logger.info(
            "ingestion.run_completed",
            extra={
                "fields_processed": stats.fields_processed,
                "upserts": stats.upserts,
                "skipped": stats.fields_skipped,
                "failed": stats.fields_failed,
                "rejected_observations": stats.rejected_observations,
                "pu_consumed": stats.pu_consumed,
                "dry_run": dry_run,
            },
        )
        return stats
    finally:
        if owns_client:
            await sh_client.aclose()
        conn.close()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Daily satellite ingestion worker.")
    p.add_argument("--dry-run", action="store_true", help="Don't write to daily_logs.")
    p.add_argument(
        "--field-id",
        default=None,
        help="Process a single field by UUID (useful for debugging).",
    )
    p.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Fields per batch (default: {DEFAULT_BATCH_SIZE}).",
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    configure_logging()
    try:
        stats = asyncio.run(
            run_ingestion(
                dry_run=args.dry_run,
                field_id_filter=args.field_id,
                batch_size=args.batch_size,
            )
        )
    except SentinelHubQuotaError:
        return 2
    except Exception:  # noqa: BLE001
        logger.exception("ingestion.run_crashed")
        return 1
    # Exit code 0 even if some fields failed — those will retry next run.
    if stats.fields_failed and stats.fields_processed == 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
