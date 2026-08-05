#!/usr/bin/env python3
"""
Multi-year satellite history backfill for real fields.
======================================================
Fetches Sentinel-2 NDVI/EVI history from the Copernicus Data Space Ecosystem
and writes ``daily_logs`` rows, attributing each to the season that was running
on the day it was captured.

Why this exists
---------------
The season-comparison chart needs two or more observed seasons before it says
anything, and most fields joined the product partway through one. But a field
existed before its farmer signed up, and CDSE holds imagery back to 2015 — so
we can show a farmer three years of their own field's history on day one
without asking them for anything. That is also what makes rotation advice and
yield-gap attribution useful immediately rather than in two seasons' time.

Generalises ``scripts/backfill_demo_fields.py`` (demo fields, 90 days, single
request) to real fields over arbitrary depth, chunked into windows. The
planning logic is pure and unit-tested in ``services/seasons/backfill.py``.

Boundary edits
--------------
History is only valid for the geometry it was sampled from. When a field's
boundary is redrawn, ``--refetch`` deletes its satellite rows and samples the
new shape, so the chart reflects the field as it is now rather than mixing two
geometries in one line.

Env required: DATABASE_URL, SATELLITE_API_CLIENT_ID, SATELLITE_API_CLIENT_SECRET.

Usage:
    # One field, 3 years
    python scripts/backfill_field_history.py --field-id <uuid> --years 3

    # Every field in a tenant, 5 years, dry run first
    python scripts/backfill_field_history.py --tenant-id <uuid> --years 5 --dry-run

    # Re-sample after a boundary edit
    python scripts/backfill_field_history.py --field-id <uuid> --years 3 --refetch
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone

# Ensure the repo root is importable when launched as `python scripts/<this>.py`
# (Python puts scripts/ on sys.path, not the repo root).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import get_crop_health as gch  # noqa: E402
from services.seasons.backfill import (  # noqa: E402
    DEFAULT_WINDOW_DAYS,
    attribute_row_to_season,
    estimate_requests,
    plan_backfill_range,
    plan_windows,
    select_new_rows,
)


def _connect():
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(url)


def _centroid(polygon):
    pts = [p for p in (polygon or []) if isinstance(p, dict) and "lat" in p and "lon" in p]
    if not pts:
        return None
    return (sum(p["lat"] for p in pts) / len(pts), sum(p["lon"] for p in pts) / len(pts))


def _iso_z(d):
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_daily(stats):
    """Yield (log_date, ndvi, evi, cloud_pct) per day. Skips days without NDVI."""
    for interval in stats.get("data", []):
        outputs = interval.get("outputs", {})

        def _mean(name):
            # gch._to_float guards against CDSE returning the string "NaN" for
            # fully clouded intervals.
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


def _load_fields(cur, args):
    if args.field_id:
        cur.execute(
            "SELECT id::text AS id, user_id::text AS user_id, name, polygon_coordinates "
            "FROM fields WHERE id = %s::uuid",
            (args.field_id,),
        )
    elif args.tenant_id:
        cur.execute(
            "SELECT id::text AS id, user_id::text AS user_id, name, polygon_coordinates "
            "FROM fields WHERE tenant_id = %s::uuid ORDER BY name",
            (args.tenant_id,),
        )
    else:
        print("❌ Pass --field-id or --tenant-id.")
        sys.exit(1)
    return cur.fetchall()


def main():
    ap = argparse.ArgumentParser(description="Backfill multi-year Sentinel-2 history.")
    target = ap.add_mutually_exclusive_group(required=True)
    target.add_argument("--field-id")
    target.add_argument("--tenant-id")
    ap.add_argument("--years", type=float, default=3.0, help="History depth (default 3).")
    ap.add_argument("--window-days", type=int, default=DEFAULT_WINDOW_DAYS)
    ap.add_argument("--sleep", type=float, default=1.0, help="Seconds between requests.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report the quota cost and stop, without fetching.")
    ap.add_argument("--refetch", action="store_true",
                    help="Delete existing satellite rows first — use after a boundary edit, "
                         "since history is only valid for the geometry it was sampled from.")
    args = ap.parse_args()

    cid = os.getenv("SATELLITE_API_CLIENT_ID")
    secret = os.getenv("SATELLITE_API_CLIENT_SECRET")
    if not args.dry_run and (not cid or not secret or "your_" in cid):
        print("❌ Satellite credentials missing (SATELLITE_API_CLIENT_ID/SECRET).")
        sys.exit(1)

    conn = _connect()
    from psycopg2.extras import RealDictCursor
    cur = conn.cursor(cursor_factory=RealDictCursor)

    fields = _load_fields(cur, args)
    if not fields:
        print("No matching fields. Nothing to do.")
        return

    # Cost first: a decade across a large tenant should be a deliberate choice.
    sample_start, sample_end = plan_backfill_range(args.years)
    windows_per_field = len(plan_windows(sample_start, sample_end, args.window_days))
    print(
        f"{len(fields)} field(s) · {args.years:g} years · "
        f"~{windows_per_field} requests each · "
        f"~{estimate_requests(windows_per_field, len(fields))} requests total"
    )
    if args.dry_run:
        print("Dry run — nothing fetched.")
        return

    token = gch._get_access_token(cid, secret)
    total_rows = 0

    for i, f in enumerate(fields, 1):
        label = (f["name"] or f["id"])[:42]
        centroid = _centroid(f["polygon_coordinates"])
        if not centroid:
            print(f"  [{i}/{len(fields)}] {label:<42} SKIP (no boundary)")
            continue
        lat, lon = centroid

        # A field's own seasons decide both how far back to go and how each
        # fetched row is attributed.
        cur.execute(
            "SELECT id::text AS id, planting_date FROM seasons "
            "WHERE field_id = %s::uuid AND planting_date IS NOT NULL "
            "ORDER BY planting_date ASC",
            (f["id"],),
        )
        seasons = [dict(r) for r in cur.fetchall()]
        earliest = seasons[0]["planting_date"] if seasons else None

        start, end = plan_backfill_range(args.years, earliest_season_planting=earliest)
        if start is None:
            print(f"  [{i}/{len(fields)}] {label:<42} SKIP (nothing in range)")
            continue

        if args.refetch:
            cur.execute(
                "DELETE FROM daily_logs WHERE field_id = %s::uuid AND source = 'Sentinel-2'",
                (f["id"],),
            )
            conn.commit()

        cur.execute("SELECT log_date::text AS d FROM daily_logs WHERE field_id = %s::uuid", (f["id"],))
        have = [r["d"] for r in cur.fetchall()]

        windows = plan_windows(start, end, args.window_days)
        new_for_field = 0

        for w in windows:
            try:
                req = gch._build_stats_request(
                    gch._build_bbox(lat, lon), _iso_z(w.start), _iso_z(w.end)
                )
                stats = gch._fetch_ndvi_stats(token, req)
            except Exception as exc:
                # One bad window must not abandon the rest of the field's history.
                print(f"      window {w.start}..{w.end} ERROR: {exc}")
                time.sleep(args.sleep)
                continue

            rows = select_new_rows(_parse_daily(stats), have)
            try:
                for day, ndvi, evi, cloud in rows:
                    cur.execute(
                        "INSERT INTO daily_logs "
                        "(field_id, user_id, log_date, ndvi, evi, cloud_cover, source, season_id) "
                        "VALUES (%s::uuid, %s::uuid, %s::date, %s, %s, %s, 'Sentinel-2', "
                        "        NULLIF(%s, '')::uuid)",
                        (f["id"], f["user_id"], day, ndvi, evi, cloud,
                         attribute_row_to_season(day, seasons) or ""),
                    )
                    have.append(day)
                    new_for_field += 1
                conn.commit()
            except Exception as exc:
                conn.rollback()
                print(f"      window {w.start}..{w.end} INSERT ERROR: {exc}")
            time.sleep(args.sleep)

        total_rows += new_for_field
        print(f"  [{i}/{len(fields)}] {label:<42} +{new_for_field} obs "
              f"({start} → {end}, {len(windows)} windows)")

    cur.close()
    conn.close()
    print(f"\n✅ Done. Inserted {total_rows} new daily_logs rows across {len(fields)} field(s).")
    print("Season history reads from GET /fields/{id}/season-history — no extra step.")


if __name__ == "__main__":
    main()
