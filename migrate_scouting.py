"""
Migration: scouting_observations (Sprint 3 grower-capture persistence).
======================================================================
Idempotent: CREATE TABLE/INDEX IF NOT EXISTS; RLS enable is a no-op if already on.

Run:  python migrate_scouting.py
"""

import os
import pathlib

import psycopg2
from dotenv import load_dotenv

load_dotenv()

SQL_PATH = pathlib.Path(__file__).parent / "db" / "migrations" / "007_scouting_observations.sql"

VERIFY_SQL = """
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND table_name = 'scouting_observations';
"""


def migrate():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return
    sql = SQL_PATH.read_text()
    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor()
        print("Creating scouting_observations…")
        cur.execute(sql)
        conn.commit()
        cur.execute(VERIFY_SQL)
        present = [r[0] for r in cur.fetchall()]
        print(f"✅ Present: {present}" if present else "⚠️ table missing")
        cur.close()
    except Exception as exc:
        conn.rollback()
        print(f"❌ Migration failed (rolled back): {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
