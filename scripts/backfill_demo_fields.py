#!/usr/bin/env python3
"""
Demo satellite backfill (MVP PR 1 follow-up) — RUN ON RENDER
============================================================
Server-side, one-shot backfill of real Sentinel-2 history for the demo fields
seeded by ``scripts/seed_demo_fields.py``. Runs where the Sentinel Hub
credentials + DATABASE_URL live (the Render backend shell), so it needs **no
user JWT**.

It does NOT modify the ingestion code — it *reuses* the building blocks in
``tools/get_crop_health`` (token, bbox, stats request/fetch) and parses the
per-day NDVI/EVI series itself, then writes ``daily_logs`` rows. Idempotent:
existing (field_id, log_date) rows are skipped, so it is safe to re-run.

Only operates on fields whose name starts with ``DEMO_SEED:`` in the given
tenant — it will never touch real fields.

Env required (present on Render): DATABASE_URL, SATELLITE_API_CLIENT_ID,
SATELLITE_API_CLIENT_SECRET.

Usage:
    python scripts/backfill_demo_fields.py --tenant-id <uuid>
    python scripts/backfill_demo_fields.py --tenant-id <uuid> --days 90 --sleep 2
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timedelta, timezone

# Ensure the repo root is importable when launched as `python scripts/<this>.py`
# (Python puts scripts/ on sys.path, not the repo root, so `tools` isn't found).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Reuse the existing satellite tool's helpers (no modification to ingestion).
from tools import get_crop_health as gch  # noqa: E402

DEMO_PREFIX = "DEMO_SEED: "


def _connect():
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL not set"); sys.exit(1)
    return psycopg2.connect(url)


def _centroid(polygon):
    """polygon is a JSONB list of {lat, lon}. Returns (lat, lon)."""
    pts = [p for p in (polygon or []) if isinstance(p, dict) and "lat" in p and "lon" in p]
    if not pts:
        return None
    return (sum(p["lat"] for p in pts) / len(pts), sum(p["lon"] for p in pts) / len(pts))


def _iso_z(dt):
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_daily(stats):
    """Yield (log_date, ndvi, evi, cloud_pct) per day from a Sentinel Hub
    statistics response (aggregationInterval P1D). Skips days without NDVI."""
    for interval in stats.get("data", []):
        outputs = interval.get("outputs", {})
        def _mean(name):
            # gch._to_float guards against CDSE returning the string "NaN"
            # for intervals with no valid pixels (fully clouded days).
            return gch._to_float(
                outputs.get(name, {}).get("bands", {}).get("B0", {}).get("stats", {}).get("mean")
            )
        ndvi = _mean("ndvi")
        if ndvi is None:
            continue
        evi = _mean("evi")
        mask = _mean("dataMask")
        cloud = round(max(0.0, 1 - mask) * 100, 2) if mask is not None else None
        day = (interval.get("interval", {}).get("from") or "")[:10]
        if not day:
            continue
        yield day, round(ndvi, 4), (round(evi, 4) if evi is not None else None), cloud


def main():
    ap = argparse.ArgumentParser(description="Backfill Sentinel-2 history for demo fields.")
    ap.add_argument("--tenant-id", required=True)
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--sleep", type=float, default=2.0, help="Seconds between fields (rate limit).")
    args = ap.parse_args()

    cid = os.getenv("SATELLITE_API_CLIENT_ID")
    secret = os.getenv("SATELLITE_API_CLIENT_SECRET")
    if not cid or not secret or "your_" in cid:
        print("❌ Sentinel Hub credentials missing (SATELLITE_API_CLIENT_ID/SECRET).")
        sys.exit(1)

    conn = _connect()
    from psycopg2.extras import RealDictCursor
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT id::text AS id, user_id::text AS user_id, name, polygon_coordinates "
        "FROM fields WHERE tenant_id = %s::uuid AND name LIKE %s ORDER BY name",
        (args.tenant_id, DEMO_PREFIX + "%"),
    )
    fields = cur.fetchall()
    if not fields:
        print(f"No DEMO_SEED fields in tenant {args.tenant_id}. Nothing to do.")
        return
    print(f"Backfilling {len(fields)} demo field(s), {args.days}-day window…")

    token = gch._get_access_token(cid, secret)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=args.days)

    total_rows = 0
    for i, f in enumerate(fields, 1):
        c = _centroid(f["polygon_coordinates"])
        if not c:
            print(f"  [{i}/{len(fields)}] {f['name'][:42]:<42} SKIP (no polygon)")
            continue
        lat, lon = c
        try:
            req = gch._build_stats_request(gch._build_bbox(lat, lon), _iso_z(start), _iso_z(end))
            stats = gch._fetch_ndvi_stats(token, req)
        except Exception as exc:
            print(f"  [{i}/{len(fields)}] {f['name'][:42]:<42} ERROR: {exc}")
            time.sleep(args.sleep)
            continue

        # parse + insert; one bad field must never abort the whole batch
        try:
            # existing dates for idempotency
            cur.execute("SELECT log_date::text FROM daily_logs WHERE field_id = %s::uuid", (f["id"],))
            have = {r["log_date"] for r in cur.fetchall()}

            new = 0
            for day, ndvi, evi, cloud in _parse_daily(stats):
                if day in have:
                    continue
                cur.execute(
                    "INSERT INTO daily_logs (field_id, user_id, log_date, ndvi, evi, cloud_cover, source) "
                    "VALUES (%s::uuid, %s::uuid, %s::date, %s, %s, %s, 'Sentinel-2')",
                    (f["id"], f["user_id"], day, ndvi, evi, cloud),
                )
                new += 1
            conn.commit()
        except Exception as exc:
            conn.rollback()
            print(f"  [{i}/{len(fields)}] {f['name'][:42]:<42} ERROR: {exc}")
            time.sleep(args.sleep)
            continue
        total_rows += new
        print(f"  [{i}/{len(fields)}] {f['name'][:42]:<42} +{new} obs")
        time.sleep(args.sleep)

    cur.close()
    conn.close()
    print(f"\n✅ Done. Inserted {total_rows} new daily_logs rows across {len(fields)} fields.")
    print("KurimaScores compute on-the-fly from GET /field/{id}/state — no extra step.")


if __name__ == "__main__":
    main()
