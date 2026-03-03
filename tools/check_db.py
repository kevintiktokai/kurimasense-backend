import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load env from backend/.env (script is in backend/tools/)
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)  # Go up from tools/ to backend/
env_path = os.path.join(backend_dir, ".env")
print(f"Loading env from: {env_path}")
load_dotenv(env_path)

db_url = os.environ.get("DATABASE_URL")

if not db_url:
    print("❌ DATABASE_URL not found in environment")
    sys.exit(1)

# Hide credentials in output
safe_url = db_url.split('@')[-1] if '@' in db_url else db_url
print(f"Connecting to: {safe_url}")

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    ver = cur.fetchone()
    print(f"✅ Connection successful! DB Version: {ver[0]}")
    
    # Check key tables exist
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]
    print(f"📋 Tables found: {', '.join(tables) if tables else 'None'}")
    
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)
