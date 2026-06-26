"""
CSV importer for a contractor's historical yield book.
Loads rows into harvest_records with source='historical_backfill'.

Expected CSV columns:
  field_id (or polygon_lat,polygon_lon for centroid match),
  season_year, crop_type, variety, actual_yield_tonnes,
  quality_grade (optional), area_harvested_ha (optional),
  planting_date (optional), harvest_date (optional)

Usage:
  python scripts/import_historical_book.py --csv path/to/book.csv --tenant-id UUID

Idempotent: skips rows where (field_id, season_year, source='historical_backfill') already exists.
"""

import argparse
import csv
import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def import_book(csv_path: str, tenant_id: str, dry_run: bool = False):
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)

    conn = psycopg2.connect(db_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        imported = 0
        skipped = 0
        errors = 0

        for i, row in enumerate(reader, start=2):
            field_id = row.get("field_id", "").strip()
            if not field_id:
                print(f"  Row {i}: no field_id, skipping")
                skipped += 1
                continue

            try:
                season_year = int(row["season_year"])
                actual = float(row["actual_yield_tonnes"])
            except (KeyError, ValueError) as e:
                print(f"  Row {i}: invalid data ({e}), skipping")
                errors += 1
                continue

            if actual <= 0:
                print(f"  Row {i}: actual_yield_tonnes <= 0, skipping")
                skipped += 1
                continue

            cur.execute(
                """
                SELECT 1 FROM harvest_records
                WHERE field_id = %s::uuid AND season_year = %s AND source = 'historical_backfill'
                """,
                (field_id, season_year),
            )
            if cur.fetchone():
                skipped += 1
                continue

            area = float(row.get("area_harvested_ha") or 0) or None

            if dry_run:
                print(f"  Row {i}: would insert field={field_id} season={season_year} actual={actual}")
                imported += 1
                continue

            cur.execute(
                """
                INSERT INTO harvest_records
                    (field_id, tenant_id, season_year, crop_type, variety,
                     planting_date, harvest_date, area_harvested_ha,
                     actual_yield_tonnes, quality_grade, source)
                VALUES (%s::uuid, %s::uuid, %s, %s, %s,
                        %s, %s, %s, %s, %s, 'historical_backfill')
                """,
                (
                    field_id, tenant_id, season_year,
                    row.get("crop_type", "").strip() or None,
                    row.get("variety", "").strip() or None,
                    row.get("planting_date", "").strip() or None,
                    row.get("harvest_date", "").strip() or None,
                    area,
                    actual,
                    row.get("quality_grade", "").strip() or None,
                ),
            )
            imported += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n✅ Done: {imported} imported, {skipped} skipped, {errors} errors")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import historical yield book")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--tenant-id", required=True, help="Tenant UUID")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be imported")
    args = parser.parse_args()
    import_book(args.csv, args.tenant_id, args.dry_run)
