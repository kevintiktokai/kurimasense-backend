"""
Migration: deny-by-default RLS on sensitive, backend-only tables (security).
=============================================================================
See db/migrations/004_enable_rls.sql for the full rationale.

Idempotent: ENABLE ROW LEVEL SECURITY is a no-op if already enabled.
The backend (postgres role, table owner) bypasses RLS (no FORCE), so the app is
unaffected; only the public anon/authenticated Supabase roles are denied.

Run:  python migrate_enable_rls.py
"""

import os
import pathlib

import psycopg2
from dotenv import load_dotenv

load_dotenv()

SQL_PATH = pathlib.Path(__file__).parent / "db" / "migrations" / "004_enable_rls.sql"

VERIFY_SQL = """
SELECT c.relname, c.relrowsecurity
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname IN ('yield_projections','harvest_records','model_calibration',
                    'grower_contracts','input_disbursements','deliveries',
                    'tenants','tenant_members','growers')
ORDER BY c.relname;
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
        print("Enabling RLS on sensitive, backend-only tables…")
        cur.execute(sql)
        conn.commit()
        cur.execute(VERIFY_SQL)
        rows = cur.fetchall()
        disabled = [name for name, on in rows if not on]
        if disabled:
            print(f"⚠️ RLS still disabled on: {disabled}")
        else:
            print(f"✅ RLS enabled on all {len(rows)} tables: {[r[0] for r in rows]}")
        cur.close()
    except Exception as exc:
        conn.rollback()
        print(f"❌ Migration failed (rolled back): {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
