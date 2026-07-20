import os
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

import threading as _threading

_POOL: ThreadedConnectionPool | None = None
_POOL_INIT_LOCK = _threading.Lock()

class _PooledConn:
    """
    Wraps a psycopg2 connection so existing code calling conn.close()
    returns it to the pool instead of closing the socket.

    Supports context manager usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            ...
    """
    def __init__(self, pool: ThreadedConnectionPool, conn):
        self._pool = pool
        self._conn = conn

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # Do not suppress exceptions

    def close(self):
        try:
            # Return to pool instead of closing
            self._pool.putconn(self._conn)
        except Exception:
            try:
                self._conn.close()
            except Exception:
                pass

def _get_pool() -> ThreadedConnectionPool | None:
    global _POOL
    if _POOL is not None:
        return _POOL

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("WARNING: DATABASE_URL not set.")
        return None

    # Startup init now runs in a background thread while requests arrive, so
    # pool creation can genuinely race. The lock makes it single-flight; the
    # re-check inside handles the loser of the race.
    with _POOL_INIT_LOCK:
        if _POOL is not None:
            return _POOL
        try:
            # Increased from 10 → 20 to handle concurrent AI insight requests
            # (each /ai/insights call uses up to 5 connections with current patterns)
            _POOL = ThreadedConnectionPool(minconn=2, maxconn=20, dsn=db_url)
            return _POOL
        except Exception as e:
            print(f"CRITICAL: DB Pool init failed: {e}")
            return None

def get_db_connection():
    try:
        pool = _get_pool()
        if not pool:
            return None
        conn = pool.getconn()
        # Keep RealDictCursor usage at cursor() call sites as you already do.
        return _PooledConn(pool, conn)
    except Exception as e:
        # Check for IPv6 specific error to provide better advice
        if "Network is unreachable" in str(e):
            print(f"CRITICAL: DB Connectivity Error (IPv6/IPv4 Mismatch): {e}")
            print("TIP: Use the Supabase Pooled Connection URL (IPv4) instead of the Direct URL on Render.")
        else:
            print(f"CRITICAL: DB Connection Error: {e}")
        return None

def schema_self_heal_enabled() -> bool:
    """Whether boot-time DDL ("self-healing schema") is allowed.

    Default on — unchanged behavior. Set ``DB_SELF_HEAL_SCHEMA=false`` once the
    schema is managed by ``migrations/015_bootstrap_schema.sql``: a locked-down
    NOBYPASSRLS app role (migration 016) cannot run DDL, so with the flag off
    the backend never issues CREATE/ALTER at runtime and boots cleanly under
    that role. Seeding (plain DML) is unaffected by this flag.
    """
    return os.environ.get("DB_SELF_HEAL_SCHEMA", "true").strip().lower() not in (
        "false", "0", "no",
    )


def init_db():
    """
    Initialize the database with required tables.
    """
    conn = get_db_connection()
    if conn:
        print("✅ Database connection established successfully.")

        if not schema_self_heal_enabled():
            # Schema is migration-managed (015+); skip all runtime DDL but keep
            # the idempotent catalogue seed (DML, allowed for the app role).
            print("⏭️ Schema self-heal disabled (DB_SELF_HEAL_SCHEMA=false) — schema managed by migrations/.")
            conn.close()
            try:
                seed_crop_varieties()
            except Exception as e:
                print(f"⚠️ Crop-variety seed skipped: {e}")
            return

        # Ensure All Required Tables Exist
        try:
            cursor = conn.cursor()
            
            # Chat Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT, -- Can be UUID or 'web-user-xx'
                    role TEXT,
                    content TEXT,
                    field_context_id TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Chat sessions (LLM-style chat: history sidebar, new/resume chats).
            # chat_logs.session_id joins messages to a session; legacy rows keep
            # NULL (the old single-thread history). Self-heals like the SAR cols.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id TEXT NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            cursor.execute("""
                ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS session_id UUID;
                CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_chat_logs_session ON chat_logs(session_id, created_at);
            """)

            # Fields Table (matches Supabase schema)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fields (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    crop_type TEXT,
                    polygon_coordinates JSONB,
                    size_hectares DECIMAL(10,2),
                    health_score INTEGER,
                    planting_date DATE,
                    variety TEXT,
                    fertilizer_history TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Add missing columns if they don't exist (for existing tables)
            cursor.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='fields' AND column_name='user_id') THEN
                        ALTER TABLE fields ADD COLUMN user_id TEXT;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='fields' AND column_name='planting_date') THEN
                        ALTER TABLE fields ADD COLUMN planting_date DATE;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='fields' AND column_name='variety') THEN
                        ALTER TABLE fields ADD COLUMN variety TEXT;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='fields' AND column_name='fertilizer_history') THEN
                        ALTER TABLE fields ADD COLUMN fertilizer_history TEXT;
                    END IF;
                END $$;
            """)
            
            # Daily Logs Table (matches Supabase schema - PLURAL)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
                    user_id UUID, -- Added for isolation
                    log_date DATE DEFAULT CURRENT_DATE,
                    ndvi DOUBLE PRECISION,
                    evi DOUBLE PRECISION,
                    soil_moisture DOUBLE PRECISION,
                    cloud_cover DOUBLE PRECISION,
                    source TEXT DEFAULT 'Sentinel-2',
                    insight_text TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            # Sentinel-1 SAR backscatter columns (migration 009) — self-heal on
            # deploy so the SAR persistence path never inserts a missing column.
            cursor.execute("""
                ALTER TABLE daily_logs ADD COLUMN IF NOT EXISTS sar_vv_db DOUBLE PRECISION;
                ALTER TABLE daily_logs ADD COLUMN IF NOT EXISTS sar_vh_db DOUBLE PRECISION;
            """)

            # Field Inputs Table (matches Supabase schema)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS field_inputs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
                    user_id UUID, -- Added for isolation
                    input_type TEXT,
                    quantity DECIMAL(10,2),
                    unit TEXT,
                    input_date DATE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            # User Events Table (NEW for Feature Tracking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_events (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id TEXT, -- Can be UUID or 'web-user-xx'
                    event_type TEXT,     -- e.g. 'feature_usage', 'user_action'
                    event_name TEXT,     -- e.g. 'weather_check', 'yield_projection'
                    event_data JSONB,    -- e.g. { "location": "Harare" }
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            # Crop Varieties Table (NEW for Zimbabwe Knowledge Base)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crop_varieties (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    crop_name TEXT NOT NULL,         -- e.g. 'Maize', 'Tobacco'
                    variety_name TEXT NOT NULL,      -- e.g. 'SC 727', 'K RK26R'
                    breeder TEXT,                    -- e.g. 'Seed Co', 'Kutsaga'
                    days_to_maturity INTEGER,        -- e.g. 155
                    yield_potential_low DECIMAL(10,2), -- t/ha
                    yield_potential_high DECIMAL(10,2), -- t/ha
                    description TEXT,
                    characteristics JSONB,           -- e.g. { "disease_resistance": [...], "drought_tolerance": "High" }
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(crop_name, variety_name)
                )
            """)
            # Farm Tasks Table (NEW for persistent AI priorities)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS farm_tasks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id TEXT NOT NULL,
                    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    description TEXT,
                    activity_type TEXT NOT NULL, -- irrigation, spraying, scouting, harvest, fertilize, custom
                    priority TEXT NOT NULL,      -- urgent, high, normal, low
                    task_date DATE DEFAULT CURRENT_DATE,
                    completed BOOLEAN DEFAULT FALSE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    is_ai_generated BOOLEAN DEFAULT FALSE,
                    recurring_rule JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Soil Intelligence profiles (migration 012) — one persistent, merged
            # multi-provider soil/terrain profile per field, stored as JSONB with
            # per-attribute source/confidence/refresh metadata. Self-heals on boot
            # so the soil subsystem works on every environment without a manual
            # migration step (same pattern as the SAR columns above).
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS soil_profiles (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
                    lat DOUBLE PRECISION,
                    lon DOUBLE PRECISION,
                    profile JSONB NOT NULL DEFAULT '{}'::jsonb,
                    provider_status JSONB NOT NULL DEFAULT '{}'::jsonb,
                    schema_version INTEGER NOT NULL DEFAULT 1,
                    built_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    refresh_after TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE (field_id)
                )
            """)

            # Institutional operations tables (migration 013) — team invites,
            # agronomist field activities, and field assignments. Self-heal on
            # boot like the tables above; the member-role/status ALTERs are also
            # idempotent so environments migrate on deploy without a manual step.
            cursor.execute("""
                ALTER TABLE tenant_members DROP CONSTRAINT IF EXISTS tenant_members_member_role_check;
                ALTER TABLE tenant_members ADD CONSTRAINT tenant_members_member_role_check
                    CHECK (member_role IN ('owner', 'admin', 'manager', 'agronomist',
                                           'field_officer', 'analyst', 'officer', 'viewer'));
                ALTER TABLE tenant_members ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
                ALTER TABLE tenant_members ADD COLUMN IF NOT EXISTS display_name TEXT;
                ALTER TABLE tenant_members ADD COLUMN IF NOT EXISTS email TEXT;
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS team_invites (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    email TEXT,
                    member_role TEXT NOT NULL DEFAULT 'field_officer',
                    code TEXT NOT NULL UNIQUE,
                    invited_by_user_id UUID,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    accepted_at TIMESTAMP WITH TIME ZONE,
                    accepted_by_user_id UUID,
                    revoked_at TIMESTAMP WITH TIME ZONE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS field_activities (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
                    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL,
                    activity_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    notes TEXT,
                    recommendation TEXT,
                    visit_date DATE DEFAULT CURRENT_DATE,
                    lat DOUBLE PRECISION,
                    lon DOUBLE PRECISION,
                    photo_url TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS field_assignments (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
                    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
                    assignee_user_id UUID NOT NULL,
                    assigned_by_user_id UUID,
                    note TEXT,
                    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    unassigned_at TIMESTAMP WITH TIME ZONE
                );
                CREATE UNIQUE INDEX IF NOT EXISTS uq_field_assignments_active
                    ON field_assignments(field_id) WHERE unassigned_at IS NULL;
            """)

            # Performance indexes — created once, idempotent via IF NOT EXISTS
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fields_user_id        ON fields(user_id);
                CREATE INDEX IF NOT EXISTS idx_daily_logs_field_id   ON daily_logs(field_id);
                CREATE INDEX IF NOT EXISTS idx_daily_logs_field_date ON daily_logs(field_id, log_date DESC);
                CREATE INDEX IF NOT EXISTS idx_farm_tasks_user_date  ON farm_tasks(user_id, task_date);

                -- NEW: Critical indexes for slow queries identified in performance audit
                CREATE INDEX IF NOT EXISTS idx_chat_logs_user_date   ON chat_logs(user_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_chat_logs_user_field  ON chat_logs(user_id, field_context_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_field_inputs_field    ON field_inputs(field_id, input_date DESC);
                CREATE INDEX IF NOT EXISTS idx_farm_tasks_user_status ON farm_tasks(user_id, completed, priority);
                CREATE INDEX IF NOT EXISTS idx_user_events_user      ON user_events(user_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_daily_logs_user       ON daily_logs(user_id, log_date DESC);

                CREATE INDEX IF NOT EXISTS idx_soil_profiles_field   ON soil_profiles(field_id);
                CREATE INDEX IF NOT EXISTS idx_soil_profiles_refresh ON soil_profiles(refresh_after);

                CREATE INDEX IF NOT EXISTS idx_team_invites_tenant      ON team_invites(tenant_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_field_activities_field   ON field_activities(field_id, visit_date DESC);
                CREATE INDEX IF NOT EXISTS idx_field_activities_tenant  ON field_activities(tenant_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_field_activities_user    ON field_activities(user_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_field_assignments_assignee ON field_assignments(assignee_user_id) WHERE unassigned_at IS NULL;
                CREATE INDEX IF NOT EXISTS idx_field_assignments_field    ON field_assignments(field_id, assigned_at DESC);
            """)

            conn.commit()
            cursor.close()
            print("✅ All database tables verified/created successfully.")
        except Exception as e:
            print(f"⚠️ Failed to initialize database tables: {e}")
            print("App will continue in degraded mode with mock data.")

        conn.close()

        # Self-heal the crop_varieties catalogue on boot (idempotent). This is
        # what the crop-variety picker in field creation reads; on prod the
        # table was empty because the manual seed script had never been run, so
        # the picker silently degraded to a free-text box (a regression). Seeding
        # here — like the table/column self-healing above — guarantees the picker
        # works on every environment without a manual step.
        try:
            seed_crop_varieties()
        except Exception as e:
            print(f"⚠️ Crop-variety seed skipped: {e}")

    else:
        print("❌ Database connection failed. App will run in degraded/mock mode.")

def seed_crop_varieties():
    """Idempotently ensure the crop_varieties catalogue is populated.

    Reads the canonical Zimbabwe variety list from
    ``scripts/seed_zimbabwe_crops.py`` (single source of truth, also usable as a
    standalone CLI) and upserts it. Runs at startup from ``init_db``. Cheap and
    self-limiting: it first counts existing rows and only does the upsert when the
    table is under-populated, so warm reboots pay just one COUNT query.
    """
    import os
    import importlib.util

    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS n FROM crop_varieties")
        row = cursor.fetchone()
        existing = (row['n'] if isinstance(row, dict) else row[0]) or 0

        # Load the canonical data list without executing the script's CLI entrypoint.
        seed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "scripts", "seed_zimbabwe_crops.py")
        spec = importlib.util.spec_from_file_location("_variety_seed", seed_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        varieties = getattr(mod, "ZIMBABWE_VARIETIES", [])

        # Already fully seeded — nothing to do (warm-reboot fast path).
        if existing >= len(varieties) and existing > 0:
            cursor.close()
            conn.close()
            return

        seeded = 0
        for v in varieties:
            cursor.execute("""
                INSERT INTO crop_varieties
                    (crop_name, variety_name, breeder, days_to_maturity,
                     yield_potential_low, yield_potential_high, description, characteristics)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (crop_name, variety_name) DO NOTHING
            """, (
                v.get('crop_name'), v.get('variety_name'), v.get('breeder'),
                v.get('days_to_maturity'), v.get('yield_potential_low'),
                v.get('yield_potential_high'), v.get('description'),
                _json.dumps(v.get('characteristics') or {}),
            ))
            seeded += 1
        conn.commit()
        cursor.close()
        conn.close()
        print(f"🌱 Crop-variety catalogue ensured ({seeded} varieties upserted; had {existing}).")
    except Exception as e:
        print(f"⚠️ seed_crop_varieties failed: {e}")
        try:
            conn.close()
        except Exception:
            pass


import threading
import json as _json

def _log_user_event_sync(user_id: str, event_type: str, event_name: str, event_data: dict = None):
    """Internal sync implementation of event logging."""
    conn = get_db_connection()
    if not conn: return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_events (user_id, event_type, event_name, event_data)
            VALUES (%s, %s, %s, %s)
        """, (user_id, event_type, event_name, _json.dumps(event_data) if event_data else '{}'))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Failed to log user event: {e}")
        if conn: conn.close()


def log_user_event(user_id: str, event_type: str, event_name: str, event_data: dict = None):
    """
    Log a user event (feature usage) to the database.
    Runs in a background thread so it never blocks the HTTP response.
    """
    t = threading.Thread(
        target=_log_user_event_sync,
        args=(user_id, event_type, event_name, event_data),
        daemon=True,
    )
    t.start()

def get_recent_field_activity(field_id: str, limit: int = 5, user_id: str = None) -> list:
    """
    Fetch recent inputs and logs for a field to provide context to the AI.
    Pass ``user_id`` so the RLS GUCs are armed (FORCE-ready) — without it the
    field_inputs read returns [] under FORCE ROW LEVEL SECURITY.
    """
    conn = get_db_connection()
    if not conn: return []

    activities = []
    try:
        if user_id:
            # Lazy import: tenancy imports database, so a top-level import here
            # would be circular.
            from tenancy import caller_tenant_ids, arm_rls_gucs
            arm_rls_gucs(conn, user_id, caller_tenant_ids(user_id))
        cursor = conn.cursor()

        # Get Field Inputs
        cursor.execute("""
            SELECT 'input' as type, input_type as name, quantity, unit, input_date as date
            FROM field_inputs 
            WHERE field_id = %s::uuid 
            ORDER BY input_date DESC LIMIT %s
        """, (field_id, limit))
        
        for row in cursor.fetchall():
            activities.append(f"Applied {row['quantity']}{row['unit']} of {row['name']} on {row['date']}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Failed to fetch activities: {e}")
        if conn: conn.close()
        
    return activities

