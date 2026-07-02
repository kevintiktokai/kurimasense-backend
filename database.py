import os
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

_POOL: ThreadedConnectionPool | None = None

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

def init_db():
    """
    Initialize the database with required tables.
    """
    conn = get_db_connection()
    if conn:
        print("✅ Database connection established successfully.")
        
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
            """)

            conn.commit()
            cursor.close()
            print("✅ All database tables verified/created successfully.")
        except Exception as e:
            print(f"⚠️ Failed to initialize database tables: {e}")
            print("App will continue in degraded mode with mock data.")

        conn.close()

    else:
        print("❌ Database connection failed. App will run in degraded/mock mode.")

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

def get_recent_field_activity(field_id: str, limit: int = 5) -> list:
    """
    Fetch recent inputs and logs for a field to provide context to the AI.
    """
    conn = get_db_connection()
    if not conn: return []
    
    activities = []
    try:
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

