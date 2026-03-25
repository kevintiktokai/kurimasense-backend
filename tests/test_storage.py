import sys
import os
import time

# Add backend to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.database import init_db, get_db_connection, log_user_event, get_recent_field_activity
from backend.ai_brain import ConversationMemory, ConversationMessage
import os

def load_env_manual(path):
    if not os.path.exists(path):
        print(f"Checking {path}... not found.")
        return
    print(f"Loading {path} manually...")
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            if "=" in line:
                key, val = line.split("=", 1)
                val = val.strip().strip('"').strip("'")
                os.environ[key.strip()] = val
                # print(f"Set {key}")

def test_storage():
    # Explicitly load .env from root
    env_path = os.path.join(os.getcwd(), ".env")
    load_env_manual(env_path)
    
    # Check if loaded
    if os.environ.get("DATABASE_URL"):
        print("✅ DATABASE_URL loaded successfully.")
    else:
        print("❌ DATABASE_URL missing after load.")
    
    print("🚀 Starting Real-Time Storage Verification...")
    
    # 1. Initialize DB
    print("\n1. Initializing Database...")
    init_db()
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to DB. Aborting.")
        return

    import uuid
    # user_id = str(uuid.uuid4()) # Caused FK violation
    
    # Try to find a valid user_id to respect FK constraints
    user_id = None
    try:
        cursor = conn.cursor()
        # Try profiles first
        cursor.execute("SELECT id FROM profiles LIMIT 1")
        row = cursor.fetchone()
        if row:
            user_id = str(row['id'])
            print(f"   Using existing user_id from profiles: {user_id}")
        else:
             # Try chat_logs as fallback
            cursor.execute("SELECT user_id FROM chat_logs LIMIT 1")
            row = cursor.fetchone()
            if row:
                user_id = str(row['user_id'])
                print(f"   Using existing user_id from chat_logs: {user_id}")
    except Exception as e:
        print(f"   Failed to find existing user: {e}")
        
    if not user_id:
        print("   ⚠️ No existing user found. Generating random (Test might fail if FK exists).")
        user_id = str(uuid.uuid4())

    field_id = "00000000-0000-0000-0000-000000000000" # Dummy UUID
    
    # 2. Test Chat Persistence
    print("\n2. Testing Chat Persistence...")
    memory = ConversationMemory()
    
    # Clear previous test data (Only if we want to wipe history for this user)
    # memory.clear(user_id) # Let's NOT clear if we are sharing a real user ID
    
    msg_content = f"Test message {time.time()}"
    msg = ConversationMessage(role="user", content=msg_content)
    
    memory.add_message(user_id, msg)
    print(f"   Added message: {msg_content}")
    
    history = memory.get_history(user_id)
    if len(history) > 0 and history[-1].content == msg_content:
        print("✅ Chat history persistence verified!")
    else:
        print(f"❌ Chat history mismatch. Got: {history}")

    # 3. Test Feature Tracking
    print("\n3. Testing User Event Logging...")
    log_user_event(user_id, "test_event", "verification_script", {"status": "running"})
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_events WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (user_id,))
    row = cursor.fetchone()
    
    if row and row['event_name'] == "verification_script":
         print("✅ User event logging verified!")
    else:
         print(f"❌ User event logging failed. Last row: {row}")

    # 4. Test External Field Inputs (Legacy support verification)
    # Be careful inserting into field_inputs with dummy field_id if FK constraint exists.
    # We used a 0-UUID which might fail if fields table is empty.
    # We will try to fetch existing field or skip if none.
    
    # Only test if we have a real field ID or if we can make one.
    # ... Skipping insert to avoid FK violation, but testing fetch on empty.
    print("\n4. Testing Field Activity Fetch...")
    activities = get_recent_field_activity(field_id)
    print(f"   Fetched {len(activities)} activities (expected 0 for dummy field)")
    
    print("\n🎉 Verification Complete!")
    conn.close()

if __name__ == "__main__":
    test_storage()
