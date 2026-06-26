#!/usr/bin/env python3
"""
Backtest harness for the KurimaSense yield model (Sprint 1, Task 5).

For each historical field with a known polygon, season, crop, variety, planting_date,
and actual_yield_tonnes (from harvest_records where source='historical_backfill'):

  At each checkpoint (default 40%, 60%, 80% of season):
    1. Fetch historical Sentinel-2 NDVI/EVI series up to that as-of date
    2. Run the existing yield model on that truncated data
    3. Write a yield_projections row (is_backtest=TRUE)
    4. Pair with the known actual, run calibration, write model_calibration rows

HONESTY CAVEAT
==============
The demo tenant has real satellite history but FICTIONAL growers and NO real
harvest actuals. Running this harness against demo data yields mae_pct against
fabricated actuals — a PIPELINE TEST, not a sales artifact.
All output from demo/sample data is flagged:
    ⚠ SAMPLE / NOT FOR EXTERNAL USE

A defensible mae_pct is produced only after a real contractor's historical book
is imported via scripts/import_historical_book.py.

Usage:
  python scripts/backtest_yield_model.py --tenant-id UUID
  python scripts/backtest_yield_model.py --tenant-id UUID --checkpoints 40,60,80 --dry-run

Requires: DATABASE_URL, SATELLITE_API_CLIENT_ID, SATELLITE_API_CLIENT_SECRET
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

SAMPLE_BANNER = "⚠ SAMPLE / NOT FOR EXTERNAL USE"


def _connect():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(url)


def _centroid(polygon) -> Optional[Tuple[float, float]]:
    pts = [p for p in (polygon or []) if isinstance(p, dict) and "lat" in p and "lon" in p]
    if not pts:
        return None
    return (sum(p["lat"] for p in pts) / len(pts), sum(p["lon"] for p in pts) / len(pts))


def _iso_z(dt):
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_daily_ndvi(stats) -> List[Tuple[str, float]]:
    """Extract (date_str, ndvi) pairs from Sentinel Hub stats response."""
    from tools import get_crop_health as gch
    result = []
    for interval in stats.get("data", []):
        outputs = interval.get("outputs", {})
        ndvi_raw = outputs.get("ndvi", {}).get("bands", {}).get("B0", {}).get("stats", {}).get("mean")
        ndvi = gch._to_float(ndvi_raw)
        if ndvi is None:
            continue
        day = (interval.get("interval", {}).get("from") or "")[:10]
        if day:
            result.append((day, round(ndvi, 4)))
    return result


def _fetch_historical_ndvi(
    token: str, lat: float, lon: float, start: date, end: date
) -> List[Tuple[str, float]]:
    """Fetch NDVI series for a point over [start, end]."""
    from tools import get_crop_health as gch
    start_z = _iso_z(datetime(start.year, start.month, start.day, tzinfo=timezone.utc))
    end_z = _iso_z(datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=timezone.utc))
    req = gch._build_stats_request(gch._build_bbox(lat, lon), start_z, end_z)
    stats = gch._fetch_ndvi_stats(token, req)
    return _parse_daily_ndvi(stats)


def _run_yield_model_as_of(
    field: dict, ndvi_history: List[float], as_of_date: date
) -> Optional[dict]:
    """Run the yield model pretending 'today' is as_of_date."""
    from yield_model import generate_yield_projection

    planting = field["planting_date"]
    if isinstance(planting, str):
        planting = date.fromisoformat(planting)

    class FakeDate(date):
        @classmethod
        def today(cls):
            return as_of_date

    with patch("proactive_intelligence.date", FakeDate):
        try:
            proj = generate_yield_projection(
                field_id=str(field["id"]),
                crop=field.get("crop_type") or "Maize",
                variety=field.get("variety"),
                planting_date=planting,
                area_ha=float(field.get("size_hectares") or 1),
                coordinates=field.get("polygon_coordinates"),
                fertilizer_history=field.get("fertilizer_history"),
                ndvi_history=ndvi_history or None,
                transplant_date=field.get("transplant_date"),
                is_transplanted=bool(field.get("is_transplanted")),
            )
            return {
                "projected_yield": getattr(proj, "projected_yield", None),
                "confidence_score": getattr(proj, "confidence_score", None),
                "adjustment_factors": getattr(proj, "adjustment_factors", None),
            }
        except Exception as exc:
            print(f"    Yield model error: {exc}")
            return None


def main():
    ap = argparse.ArgumentParser(description="Backtest yield model against historical actuals")
    ap.add_argument("--tenant-id", required=True)
    ap.add_argument("--checkpoints", default="40,60,80",
                    help="Comma-separated season progress percentages (default: 40,60,80)")
    ap.add_argument("--sleep", type=float, default=2.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    checkpoints = [int(c.strip()) for c in args.checkpoints.split(",")]

    cid = os.getenv("SATELLITE_API_CLIENT_ID")
    secret = os.getenv("SATELLITE_API_CLIENT_SECRET")
    if not cid or not secret:
        print("❌ Sentinel Hub credentials missing (SATELLITE_API_CLIENT_ID/SECRET).")
        sys.exit(1)

    conn = _connect()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT f.id::text AS id, f.tenant_id::text AS tenant_id,
               f.crop_type, f.variety, f.planting_date, f.size_hectares,
               f.polygon_coordinates, f.fertilizer_history,
               f.transplant_date, f.is_transplanted, f.natural_region,
               hr.actual_yield_tonnes, hr.season_year
        FROM fields f
        JOIN harvest_records hr ON hr.field_id = f.id
        WHERE f.tenant_id = %s::uuid
          AND hr.actual_yield_tonnes IS NOT NULL
          AND hr.actual_yield_tonnes > 0
          AND f.planting_date IS NOT NULL
          AND f.polygon_coordinates IS NOT NULL
        ORDER BY f.id, hr.season_year
        """,
        (args.tenant_id,),
    )
    records = cur.fetchall()

    if not records:
        print(f"No fields with harvest actuals found for tenant {args.tenant_id}.")
        cur.close()
        conn.close()
        return

    is_sample = all(
        r.get("source") == "historical_backfill"
        or (r.get("crop_type") or "").startswith("DEMO")
        for r in records
    )

    print(f"\n{'=' * 60}")
    if is_sample:
        print(SAMPLE_BANNER)
    print(f"Backtesting {len(records)} field-season(s), checkpoints: {checkpoints}%")
    print(f"{'=' * 60}\n")

    from tools import get_crop_health as gch
    token = gch._get_access_token(cid, secret)

    from services.calibration import MODEL_VERSION
    from services.calibration.compute import CalibrationPair, calibrate, segment
    from services.field_state.classifiers import confidence_from_fraction

    all_pairs: List[CalibrationPair] = []
    projections_written = 0

    for rec in records:
        planting = rec["planting_date"]
        if isinstance(planting, str):
            planting = date.fromisoformat(planting)

        variety_info = None
        try:
            from proactive_intelligence import get_variety_info
            variety_info = get_variety_info(rec.get("variety")) if rec.get("variety") else None
        except Exception:
            pass
        days_to_maturity = (variety_info or {}).get("days_to_maturity", 140) or 140

        centroid = _centroid(rec.get("polygon_coordinates"))
        if not centroid:
            print(f"  Field {rec['id'][:8]}… SKIP (no polygon)")
            continue

        lat, lon = centroid
        print(f"  Field {rec['id'][:8]}… crop={rec.get('crop_type')} actual={rec['actual_yield_tonnes']} t/ha")

        for cp in checkpoints:
            as_of_day = planting + timedelta(days=int(days_to_maturity * cp / 100))
            if as_of_day > date.today():
                print(f"    {cp}%: as-of date {as_of_day} is in the future, skipping")
                continue

            try:
                ndvi_series = _fetch_historical_ndvi(token, lat, lon, planting, as_of_day)
            except Exception as exc:
                print(f"    {cp}%: satellite fetch failed: {exc}")
                time.sleep(args.sleep)
                continue

            ndvi_values = [v for _, v in ndvi_series]
            print(f"    {cp}%: {len(ndvi_values)} NDVI obs up to {as_of_day}", end="")

            if args.dry_run:
                print(" (dry-run)")
                continue

            yield_raw = _run_yield_model_as_of(rec, ndvi_values, as_of_day)
            if not yield_raw or yield_raw.get("projected_yield") is None:
                print(" → no projection")
                continue

            projected = float(yield_raw["projected_yield"])
            band, pct = confidence_from_fraction(yield_raw.get("confidence_score"))

            inputs_snapshot = {
                "ndvi_count": len(ndvi_values),
                "ndvi_last_7": ndvi_values[-7:] if ndvi_values else [],
                "confidence_score": yield_raw.get("confidence_score"),
                "adjustment_factors": yield_raw.get("adjustment_factors"),
            }

            try:
                cur.execute(
                    """
                    INSERT INTO yield_projections
                        (field_id, tenant_id, projection_date, projected_tonnes_per_ha,
                         confidence_band, confidence_pct, model_version, is_backtest,
                         season_progress_pct, inputs_snapshot)
                    VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s, TRUE, %s, %s)
                    """,
                    (
                        rec["id"], rec["tenant_id"], as_of_day, projected,
                        band, pct, MODEL_VERSION, cp,
                        json.dumps(inputs_snapshot),
                    ),
                )
                conn.commit()
                projections_written += 1
            except Exception as exc:
                conn.rollback()
                print(f" → DB write failed: {exc}")
                continue

            pair = CalibrationPair(
                projected=projected,
                actual=float(rec["actual_yield_tonnes"]),
                crop_type=rec.get("crop_type"),
                natural_region=rec.get("natural_region"),
                variety=rec.get("variety"),
                season_progress_pct=cp,
            )
            all_pairs.append(pair)
            print(f" → proj={projected:.2f} actual={rec['actual_yield_tonnes']}")

            time.sleep(args.sleep)

    if not all_pairs:
        print("\nNo projection-actual pairs produced. Cannot compute calibration.")
        cur.close()
        conn.close()
        return

    print(f"\n{'=' * 60}")
    print(f"Projections written: {projections_written}")
    print(f"Pairs for calibration: {len(all_pairs)}")
    if is_sample:
        print(SAMPLE_BANNER)
    print(f"{'=' * 60}\n")

    overall = calibrate(all_pairs)
    print(f"Overall: n={overall.n}  MAE%={overall.mae_pct:.1f}  bias%={overall.bias_pct:+.1f}  RMSE={overall.rmse:.3f}")

    segments = segment(all_pairs)
    print(f"\n{'Crop':<15} {'Region':<8} {'Variety':<12} {'Bucket':<10} {'n':>3} {'MAE%':>7} {'Bias%':>7}")
    print("-" * 70)
    for (crop, region, variety, bucket), result in sorted(segments.items(), key=lambda x: x[0]):
        print(f"{crop or '-':<15} {region or '-':<8} {(variety or '-')[:12]:<12} {bucket:<10} "
              f"{result.n:>3} {result.mae_pct:>7.1f} {result.bias_pct:>+7.1f}")

    for (crop, region, variety, bucket), result in segments.items():
        try:
            cur.execute(
                """
                INSERT INTO model_calibration
                    (crop_type, natural_region, variety, season_progress_bucket,
                     model_version, n_observations, mae_pct, rmse, bias_pct)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (crop, region, variety, bucket,
                 MODEL_VERSION, result.n, result.mae_pct, result.rmse, result.bias_pct),
            )
        except Exception as exc:
            conn.rollback()
            print(f"  calibration write failed: {exc}")
            continue
    conn.commit()

    print(f"\n✅ Calibration rows written to model_calibration (model_version={MODEL_VERSION})")
    if is_sample:
        print(f"\n{SAMPLE_BANNER}")
        print("These results are from sample/demo data and must NOT be quoted externally.")
        print("Import a real contractor's historical book to produce validated figures.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
