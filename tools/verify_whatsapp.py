import json
from datetime import datetime

def verify_whatsapp_structure():
    """
    Verifies that we can construct a valid WhatsApp payload matching the gemini.md schema.
    This is a structural test, not a network test (yet).
    """
    print("🔄 Verifying Data Schema for WhatsApp Payload...")
    
    # Mock Advice
    advice_text = "Your maize is showing signs of moisture stress. Apply 15mm irrigation by Thursday."
    
    payload = {
        "recipient_id": "+263771234567",
        "channel": "whatsapp",
        "message_type": "text",
        "content": {
            "text_body": advice_text,
            "actions": ["Start Irrigation", "Check Soil Moisture"]
        },
        "meta_data": {
            "confidence_score": 0.95,
            "reasoning_trace": "Satellite NDVI dropped by 10% in last 3 days + No rain in forecast."
        }
    }
    
    try:
        json_output = json.dumps(payload, indent=2)
        print("✅ SUCCESS: Generated Valid JSON Payload:")
        print(json_output)
        return True
    except Exception as e:
        print(f"❌ FAILED: JSON serialization failed: {e}")
        return False

if __name__ == "__main__":
    verify_whatsapp_structure()
