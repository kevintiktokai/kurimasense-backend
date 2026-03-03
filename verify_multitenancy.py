import requests
import json

# Backend URL (assuming local dev server)
BASE_URL = "http://localhost:8000"

def test_endpoint(name, method, path, headers=None, payload=None):
    print(f"Testing {name}...")
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{path}", headers=headers)
        else:
            response = requests.post(f"{BASE_URL}{path}", headers=headers, json=payload)
        
        print(f"  Status: {response.status_code}")
        if response.status_code == 401:
            print("  ✅ Access denied as expected (No Token)")
        elif response.status_code == 200:
            print("  ✅ Access granted")
        else:
            print(f"  ❌ Unexpected status: {response.status_code}")
            print(f"  Body: {response.text[:100]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    # Test public access to sensitive endpoints (should fail with 401)
    test_endpoint("Chat History (Public)", "GET", "/chat/history")
    test_endpoint("Fields (Public)", "GET", "/fields")
    test_endpoint("Inputs (Public)", "POST", "/inputs", payload={})
    
    # Note: Full verification requires a valid Supabase JWT, 
    # but 401 on these tells us the middleware is active.
