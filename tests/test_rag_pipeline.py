import json
import subprocess
import sys
import os

TOOL_PATH = os.path.join(os.path.dirname(__file__), "..", "tools", "retrieve_context.py")

def test_retrieval(query, lat, lon, expected_keyword):
    print(f"\n--- Testing Query: '{query}' at ({lat}, {lon}) ---")
    
    payload = {
        "seed": {
            "raw_message": query,
            "location": {"lat": lat, "lon": lon}
        }
    }
    
    result = subprocess.run(
        [sys.executable, TOOL_PATH],
        input=json.dumps(payload),
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Tool Failed: {result.stderr}")
        return False
        
    try:
        output = json.loads(result.stdout)
        data = output.get("data", {})
        context = data.get("retrieved_context", "")
        region = data.get("region_used", "")
        
        print(f"Region Detected: {region}")
        print(f"Context Snippet: {context[:200]}...")
        
        if expected_keyword.lower() in context.lower():
            print(f"✅ Success: Found '{expected_keyword}' in context.")
            return True
        else:
            print(f"❌ Failure: Did not find '{expected_keyword}' in context.")
            return False
            
    except Exception as e:
        print(f"❌ JSON Parse Error: {e}")
        return False

if __name__ == "__main__":
    # Test 1: Zimbabwe (Seed Co / ART Farm)
    # Harare: -17.82, 31.05
    test_1 = test_retrieval("best maize planting depth", -17.82, 31.05, "Seed Co")
    
    # Test 2: Kenya (KALRO)
    # Nairobi: -1.29, 36.82
    test_2 = test_retrieval("maize spacing recommendations", -1.29, 36.82, "KALRO")
    
    # Test 3: West Africa (IITA Cassava)
    # Lagos: 6.52, 3.37
    test_3 = test_retrieval("cassava planting mounds", 6.52, 3.37, "IITA")
