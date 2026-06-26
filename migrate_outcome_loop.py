"""
Migration: Institutional Outcome Loop tables (Sprint 1)
=======================================================
Creates yield_projections, harvest_records, model_calibration.
Idempotent: CREATE TABLE/INDEX IF NOT EXISTS; running twice is a no-op.

Run:  python migrate_outcome_loop.py
"""

import os
import pathlib

import psycopg2
from dotenv import load_dotenv

load_dotenv()

SQL_PATH = pathlib.Path(__file__).parent / "db" / "migrations" / "002_institutional_outcome_loop.sql"

VERIFY_SQL = """
SELECT table_name FROM information_schema.tables
WHERE table_schema='public'
  AND table_name IN ('yield_projections', 'harvest_records', 'model_calibration')
ORDER BY table_name;
"""


def migrate():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return
    migration_sql = SQL_PATH.read_text()
    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor()
        print("Creating yield_projections + harvest_records + model_calibration…")
        cur.execute(migration_sql)
        conn.commit()
        cur.execute(VERIFY_SQL)
        present = [r[0] for r in cur.fetchall()]
        expected = ["harvest_records", "model_calibration", "yield_projections"]
        if present == expected:
            print(f"✅ Tables present: {present}")
        else:
            print(f"⚠️ Expected {expected}, got {present}")
        cur.close()
    except Exception as exc:
        conn.rollback()
        print(f"❌ Migration failed (rolled back): {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
