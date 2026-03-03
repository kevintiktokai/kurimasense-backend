import sys
import os
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from ai_brain import get_brain, AgentInput, FieldContext

async def test_vision_flow():
    print("\n📷 Testing Vision Flow...")
    brain = get_brain()
    
    # Mock VisionAnalyzer
    mock_vision_result = {
        "detected_issues": [{
            "name": "Grey Leaf Spot",
            "type": "disease",
            "confidence": 0.95,
            "severity": "high",
            "affected_area": "lower leaves"
        }],
        "overall_health_score": 0.4,
        "diagnosis_summary": "Severe Grey Leaf Spot infection detected.",
        "treatment_recommendations": ["Apply Axystrobin", "Improve aeration"],
        "urgency": "high"
    }
    
    # We need to mock the VisionAnalyzer class instantiation inside process, 
    # but since it's instantiated inside, we might need to patch the class or the method if we could.
    # For now, let's try to patch the class in the module, but `ai_brain` imports it.
    # Easier: Mock the `brain.llm_router.generate` and trust correct routing, 
    # OR patch `ai_brain.VisionAnalyzer`.
    
    import ai_brain
    
    # Mock VisionAnalyzer class
    mock_analyzer_instance = AsyncMock()
    mock_analyzer_instance.analyze_image.return_value = mock_vision_result
    
    original_cls = ai_brain.VisionAnalyzer
    ai_brain.VisionAnalyzer = MagicMock(return_value=mock_analyzer_instance)
    
    try:
        input_data = AgentInput(
            user_id="test_user",
            message="What's wrong with this?",
            image_base64="data:image/jpeg;base64,fakeimagebytes"
        )
        
        response = await brain.process(input_data)
        
        print(f"Detected Intent: {response.detected_intent}")
        print(f"Response Body: {response.text_body[:100]}...")
        
        if response.detected_intent == "diagnosis_vision" and "Grey Leaf Spot" in response.text_body:
            print("✅ Vision Flow Success")
        else:
            print("❌ Vision Flow Failed")
            
    finally:
        ai_brain.VisionAnalyzer = original_cls

async def test_rag_flow():
    print("\n📚 Testing RAG Flow...")
    brain = get_brain()
    
    # Patch search_knowledge_base
    mock_kb_result = [{
        "metadata": {"source_title": "Maize Manual", "country": "Zimbabwe"},
        "content": "Plant SC 727 at 50,000 plants per hectare."
    }]
    
    # We need to patch ai_brain.search_knowledge_base
    import ai_brain
    ai_brain.search_knowledge_base = AsyncMock(return_value=mock_kb_result)
    
    # Mock LLM generation to avoid API call
    brain.llm_router.generate = AsyncMock(return_value=json.dumps({
        "text_body": "Based on the manual, plant at 50k/ha.",
        "confidence_score": 0.9
    }))
    
    input_data = AgentInput(
        user_id="test_user",
        message="What is the planting density for SC 727?",
        field_context=FieldContext(field_name="Home Field", crop_type="Maize")
    )
    
    response = await brain.process(input_data)
    
    # Check if search_knowledge_base was called
    if ai_brain.search_knowledge_base.called:
        print("✅ RAG Search Triggered")
    else:
        print("❌ RAG Search NOT Triggered")

if __name__ == "__main__":
    asyncio.run(test_vision_flow())
    asyncio.run(test_rag_flow())
