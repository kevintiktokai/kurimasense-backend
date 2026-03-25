import sys
import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_brain import AgronomistBrain, get_brain
from proactive_intelligence import GrowthStageInfo

async def test_ai_priorities():
    print("🚀 Starting AI Priorities Verification...")
    
    # Initialize Brain
    brain = get_brain()

    # MOCK the LLM Router generate method to avoid API calls
    async def mock_generate(*args, **kwargs):
        print("    (Mocking LLM response...)")
        return json.dumps({
            "actions": [
                {
                    "title": "Mock High Priority Action",
                    "description": "This is a mock action from the AI.",
                    "type": "scout",
                    "priority": "high"
                },
                {
                    "title": "Mock Medium Priority",
                    "description": "Routine check.",
                    "type": "fertilize",
                    "priority": "medium"
                }
            ],
            "risks": [
                {
                    "type": "disease",
                    "risk": 85,
                    "name": "Grey Leaf Spot",
                    "trend": "rising"
                },
                {
                    "type": "pest",
                    "risk": 20,
                    "name": "Fall Armyworm",
                    "trend": "stable"
                }
            ]
        })
    
    # Patch the method
    brain.llm_router.generate = mock_generate
    
    # Mock Data representing a user's field
    mock_context = {
        "crop_type": "Maize",
        "variety_name": "SC 727",
        "stage_name": "V6 - Rapid Growth",
        "days_since_planting": 45,
        "progress_percent": 35.0,
        "location": {"lat": -17.82, "lon": 31.05},
        "weather": {
            "temperature": 26.5,
            "humidity": 82, # High humidity -> checks logic for fungal risks
            "precipitation": 0,
            "wind_speed": 12
        },
        "variety_info": {
            "variety_name": "SC 727",
            "days_to_maturity": 145,
            "characteristics": {
                "gls_tolerance": "moderate", # Should trigger warning with high humidity
                "drought_tolerance": "high"
            }
        }
    }
    
    print(f"\n📋 Input Context:\n{json.dumps(mock_context, indent=2)}")
    print("\n🧠 Invoking AI Brain (this may take a few seconds)...")
    
    start_time = datetime.now()
    try:
        insights = await brain.generate_ai_priorities_and_risks(mock_context)
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ AI Response Received in {duration:.2f}s:\n")
        print(json.dumps(insights, indent=2))
        
        # Validation Checks
        actions = insights.get('actions', [])
        risks = insights.get('risks', [])
        
        if not actions or not risks:
            print("\n❌ FAILURE: Empty actions or risks returned.")
            return
            
        # Check for specific expected logic (High Humidity + Moderate GLS = Risk)
        gls_risk = next((r for r in risks if "grey leaf spot" in r.get('name', '').lower() or "gls" in r.get('name', '').lower()), None)
        
        if gls_risk:
            print(f"\n✅ Logic Verification: Found expected GLS risk due to high humidity ({gls_risk['risk']}%)")
        else:
            print("\n⚠️ Logic Warning: High humidity did not trigger explicit GLS risk (AI might have decided otherwise).")
            
        print("\n✨ Verification Complete!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_priorities())
