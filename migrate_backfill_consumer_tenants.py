"""
Migration: backfill one owner-tenant per profile (Workstream 3, Block 1)
=======================================================================
For every non-admin profile, create a tenant and an `owner` tenant_members row,
so every existing user has a tenant before field data is re-scoped.

* role = consumer      -> tenant_type='consumer', name = full_name|email|'User xxxx'
* role = institutional -> tenant_type='institutional', name = profiles.tenant_name,
                          institutional_type = profiles.institutional_type
* role = admin         -> skipped (admins operate via X-Admin-Token; no tenant)

Idempotent: a user who already has a tenant_members row is skipped, so running
twice produces the same result as once. Done in a single SQL statement using a
NOT EXISTS guard + a CTE so tenant and membership are created atomically.

Run:  python migrate_backfill_consumer_tenants.py

----------------------------------------------------------------------------
Verification (also run automatically below) — expected output:

  -- one consumer tenant per consumer profile (counts must MATCH):
  SELECT COUNT(*) FROM profiles WHERE role = 'consumer';      --> N
  SELECT COUNT(*) FROM tenants  WHERE tenant_type = 'consumer';--> N (== above)

  -- every non-admin profile has a membership (must be 0):
  SELECT COUNT(*) FROM profiles p
  LEFT JOIN tenant_members tm ON tm.user_id = p.id
  WHERE tm.user_id IS NULL AND p.role != 'admin';             --> 0
----------------------------------------------------------------------------
"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Backfill is done per-row in Python: for each non-admin profile without a
# membership, create one tenant + one owner membership inside a transaction.
# Clear and unambiguous for the data sizes involved (hundreds of users), and
# idempotent via the NOT EXISTS guard below.
SELECT_TODO_SQL = """
SELECT p.id,
       p.role,
       CASE
           WHEN p.role = 'institutional'
               THEN COALESCE(NULLIF(p.tenant_name, ''), p.full_name, 'Institution')
           ELSE COALESCE(NULLIF(p.full_name, ''), 'User ' || left(p.id::text, 8))
       END AS tenant_name,
       CASE WHEN p.role = 'institutional' THEN 'institutional' ELSE 'consumer' END AS tenant_type,
       CASE WHEN p.role = 'institutional' THEN p.institutional_type ELSE NULL END AS institutional_type
FROM profiles p
WHERE p.role IN ('consumer', 'institutional')
  AND NOT EXISTS (SELECT 1 FROM tenant_members tm WHERE tm.user_id = p.id);
"""

INSERT_TENANT_SQL = """
INSERT INTO tenants (name, tenant_type, institutional_type)
VALUES (%s, %s, %s) RETURNING id;
"""

INSERT_MEMBER_SQL = """
INSERT INTO tenant_members (tenant_id, user_id, member_role)
VALUES (%s, %s, 'owner')
ON CONFLICT (tenant_id, user_id) DO NOTHING;
"""

VERIFY_SQL = """
SELECT
  (SELECT COUNT(*) FROM profiles WHERE role = 'consumer') AS consumer_profiles,
  (SELECT COUNT(*) FROM tenants WHERE tenant_type = 'consumer') AS consumer_tenants,
  (SELECT COUNT(*) FROM profiles p
     LEFT JOIN tenant_members tm ON tm.user_id = p.id
     WHERE tm.user_id IS NULL AND p.role != 'admin') AS unassigned_non_admin;
"""


def migrate():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return
    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor()
        cur.execute(SELECT_TODO_SQL)
        todo = cur.fetchall()
        print(f"Backfilling {len(todo)} tenant(s)…")
        for user_id, role, tenant_name, tenant_type, institutional_type in todo:
            cur.execute(INSERT_TENANT_SQL, (tenant_name, tenant_type, institutional_type))
            tenant_id = cur.fetchone()[0]
            cur.execute(INSERT_MEMBER_SQL, (tenant_id, user_id))
        conn.commit()

        cur.execute(VERIFY_SQL)
        cp, ct, unassigned = cur.fetchone()
        print(f"  consumer_profiles={cp}  consumer_tenants={ct}  (match: {cp == ct})")
        print(f"  unassigned_non_admin={unassigned}  (expected 0)")
        if cp != ct:
            print("⚠️  consumer profile/tenant counts differ — investigate before proceeding.")
        if unassigned != 0:
            print("⚠️  some non-admin profiles still have no tenant — investigate.")
        cur.close()
    except Exception as exc:  # pragma: no cover - operational
        conn.rollback()
        print(f"❌ Backfill failed (rolled back): {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
