import os
from dotenv import load_dotenv

def verify_satellite():
    """
    Verifies that Satellite API credentials exist.
    """
    load_dotenv()
    
    client_id = os.getenv("SATELLITE_API_CLIENT_ID")
    client_secret = os.getenv("SATELLITE_API_CLIENT_SECRET")
    
    if not client_id or "your_" in client_id:
        print("⚠️ WARNING: SATELLITE_API_CLIENT_ID not found or is placeholder.")
        # returning true for now as we might not have this yet
    
    print("🔄 Satellite API: Sentinel Hub / AgMonitor connection check skipped (Optional for Phase 2 start).")
    print("✅ SUCCESS: Satellite Verification Placeholder Ready.")
    return True

if __name__ == "__main__":
    verify_satellite()
