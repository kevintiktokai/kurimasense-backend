"""
Migration: pin search_path on the RAG match_documents function (security).
==========================================================================
See db/migrations/006_pin_match_documents_search_path.sql for rationale.
Idempotent. Safe to re-run.

Run:  python migrate_pin_search_path.py
"""

import os
import pathlib

import psycopg2
from dotenv import load_dotenv

load_dotenv()

SQL_PATH = pathlib.Path(__file__).parent / "db" / "migrations" / "006_pin_match_documents_search_path.sql"

VERIFY_SQL = """
SELECT p.oid::regprocedure::text AS signature, p.proconfig
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public' AND p.proname = 'match_documents';
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
        print("Pinning search_path on match_documents…")
        cur.execute(sql)
        conn.commit()
        cur.execute(VERIFY_SQL)
        rows = cur.fetchall()
        if not rows:
            print("ℹ️ No match_documents function found (nothing to pin).")
        for sig, cfg in rows:
            ok = cfg and any(c.startswith("search_path=") for c in cfg)
            print(f"{'✅' if ok else '⚠️'} {sig} -> {cfg}")
        cur.close()
    except Exception as exc:
        conn.rollback()
        print(f"❌ Migration failed (rolled back): {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
