import asyncio
import json
import os
from datetime import date, timedelta
from dotenv import load_dotenv

# Load env vars
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, '.env')
print(f"DEBUG: Loading env from {env_path}")
loaded = load_dotenv(env_path)
print(f"DEBUG: load_dotenv result: {loaded}")
print(f"DEBUG: OPENAI_API_KEY present: {'OPENAI_API_KEY' in os.environ}")
if 'OPENAI_API_KEY' in os.environ:
    print(f"DEBUG: OPENAI_API_KEY length: {len(os.environ['OPENAI_API_KEY'])}")

from proactive_intelligence import generate_proactive_alerts

async def test_maize_sc727():
    print("🧪 Testing PhD Intelligence: Maize SC 727 (Nzou)")
    
    # Mock data for SC 727 in Mid-Vegetative stage
    field_id = "test-field-123"
    field_name = "Main Block"
    crop_type = "Maize"
    variety_name = "SC 727"
    planting_date = date.today() - timedelta(days=40) # ~V4-V6 stage
    weather_data = {
        "temperature": 28,
        "humidity": 85,
        "precipitation": 5,
        "wind_speed": 2
    }
    
    # Run proactive alerts generation
    result = await generate_proactive_alerts(
        field_id=field_id,
        field_name=field_name,
        crop_type=crop_type,
        variety_name=variety_name,
        planting_date=planting_date,
        weather_data=weather_data
    )
    
    print("\n✅ Proactive Alerts Generated")
    print(f"Growth Stage: {result['growth_stage']['name']}")
    print(f"Description: {result['growth_stage']['description']}")
    
    print("\n🧠 AI Priorities (Variety-Specific):")
    for action in result.get('ai_priorities', []):
        print(f"- [{action.get('priority').upper()}] {action.get('title')}: {action.get('description')}")
        
    print("\n⚠️ Scientific Alerts:")
    for alert in result.get('alerts', []):
        print(f"- {alert.get('title')}: {alert.get('message')}")

    # Validation
    has_gls_mention = any("GLS" in str(a) or "Grey Leaf Spot" in str(a) for a in result.get('ai_priorities', []) + result.get('alerts', []))
    has_phd_logic = any("pH" in str(a) or "NUE" in str(a) or "physiological" in str(a).lower() for a in result.get('ai_priorities', []) + result.get('alerts', []))
    
    if has_gls_mention:
        print("\n✨ Variety-specific GLS warning detected!")
    else:
        print("\n❌ FAILED: No variety-specific GLS mention found.")
        
    if has_phd_logic:
        print("✨ PhD-level agronomic logic detected!")
    else:
        print("💡 NOTE: PhD logic (pH/NUE) not explicitly detected in this run. LLM output varies.")

if __name__ == "__main__":
    asyncio.run(test_maize_sc727())
