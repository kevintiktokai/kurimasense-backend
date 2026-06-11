"""
Migration: add `persona` to profiles (Workstream 5 — self-service signup fix)
=============================================================================
``profiles.role`` was repurposed by ``migrate_user_roles.py`` into the access
*tier* (``consumer`` | ``institutional`` | ``admin``) with a CHECK constraint.
But the frontend onboarding still wrote the user's *agricultural identity*
(``farmer`` / ``smallholder`` / ``agronomist`` / ``hobbyist``) into ``role`` —
violating ``profiles_role_check`` so EVERY signup failed with "Failed to save
profile" (Postgres 23514).

This migration adds a dedicated ``persona`` column so the consumer identity is
stored separately from the access tier. Onboarding now writes
``role = 'consumer'`` + ``persona = '<choice>'`` for consumers, and institutions
go through ``POST /me/institutional``.

Idempotent: ADD COLUMN IF NOT EXISTS + named CHECK added only if absent.

Run:  python migrate_add_persona.py
"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

MIGRATION_SQL = """
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS persona TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'profiles_persona_check'
    ) THEN
        ALTER TABLE profiles
            ADD CONSTRAINT profiles_persona_check
            CHECK (
                persona IS NULL
                OR persona IN ('farmer', 'smallholder', 'agronomist', 'hobbyist')
            );
    END IF;
END $$;
"""

VERIFY_SQL = """
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'profiles' AND column_name = 'persona';
"""


def migrate():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return

    conn = psycopg2.connect(db_url)
    try:
        cursor = conn.cursor()
        print("Adding profiles.persona…")
        cursor.execute(MIGRATION_SQL)
        conn.commit()
        print("✅ Migration applied (idempotent).")

        cursor.execute(VERIFY_SQL)
        for row in cursor.fetchall():
            print(f"  {row[0]:<12} {row[1]:<8} nullable={row[2]}")
        cursor.close()
    except Exception as exc:  # pragma: no cover - operational
        conn.rollback()
        print(f"❌ Migration failed (rolled back): {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
