import os
import psycopg2
from dotenv import load_dotenv

# 1. Test Environment Loading
print("--- Debugging Environment ---")
load_dotenv()
db_url = os.environ.get("DATABASE_URL")

if not db_url:
    print("❌ ERROR: DATABASE_URL not found in environment.")
    print("   Please check backend/.env exists and is readable.")
else:
    print("✅ DATABASE_URL found.")
    # Mask password for safe printing
    safe_url = db_url.split("@")[1] if "@" in db_url else "INVALID_FORMAT"
    print(f"   Target: ...@{safe_url}")

# 2. Test Connection
print("\n--- Testing Connection ---")
if db_url:
    try:
        conn = psycopg2.connect(db_url)
        print("✅ Connection Established!")
        
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"   Server Version: {version[0]}")
        
        cur.execute("SELECT count(*) FROM fields;")
        count = cur.fetchone()
        print(f"   Active Fields Table Row Count: {count[0]}")
        
        conn.close()
        print("✅ Connection Closed cleanly.")
        
    except psycopg2.OperationalError as e:
        print("❌ CONNECTION FAILED (OperationalError)")
        print(f"   Details: {e}")
        # Hint at common issues
        if "Translate" in str(e):
            print("   -> Tip: DNS Issue. Check hostname.")
        elif "password" in str(e):
            print("   -> Tip: Auth Failed. Check password.")
        elif "timeout" in str(e):
            print("   -> Tip: Network Blocked. Check Firewall/Port 6543.")
            
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}")
        print(f"   {e}")
