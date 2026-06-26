"""
Migration: Financial / Exposure Layer tables (Sprint 2)
=======================================================
Creates grower_contracts, input_disbursements, deliveries.
Idempotent: CREATE TABLE/INDEX IF NOT EXISTS; running twice is a no-op.

Run:  python migrate_financial_exposure.py
"""

import os
import pathlib

import psycopg2
from dotenv import load_dotenv

load_dotenv()

SQL_PATH = pathlib.Path(__file__).parent / "db" / "migrations" / "003_financial_exposure.sql"

VERIFY_SQL = """
SELECT table_name FROM information_schema.tables
WHERE table_schema='public'
  AND table_name IN ('grower_contracts', 'input_disbursements', 'deliveries')
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
        print("Creating grower_contracts + input_disbursements + deliveries…")
        cur.execute(migration_sql)
        conn.commit()
        cur.execute(VERIFY_SQL)
        present = [r[0] for r in cur.fetchall()]
        expected = ["deliveries", "grower_contracts", "input_disbursements"]
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
