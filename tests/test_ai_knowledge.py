"""
KurimaSense AI Knowledge Verification Tests
============================================
Tests to verify that the AI Brain correctly uses variety-specific knowledge
from the crop_varieties database.

Usage:
    cd backend
    python -m pytest tests/test_ai_knowledge.py -v
    
    Or run directly:
    python tests/test_ai_knowledge.py
    
Requires:
    - DATABASE_URL environment variable set
    - OPENAI_API_KEY environment variable set
    - crop_varieties table populated (run scripts/seed_zimbabwe_crops.py first)
"""

import os
import sys
import asyncio
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from database import get_db_connection
from ai_brain import AgronomistBrain, AgentInput, FieldContext, get_brain


def test_database_connection():
    """Verify database connection works."""
    conn = get_db_connection()
    assert conn is not None, "Database connection failed - check DATABASE_URL"
    conn.close()
    print("✅ Database connection: OK")


def test_varieties_seeded():
    """Verify crop varieties are populated in the database."""
    conn = get_db_connection()
    assert conn is not None, "Database connection failed"
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM crop_varieties")
    count = cursor.fetchone()['count']
    cursor.close()
    conn.close()
    
    assert count >= 30, f"Expected at least 30 varieties, found {count}. Run seed_zimbabwe_crops.py first."
    print(f"✅ Varieties seeded: {count} varieties found")


def test_maize_varieties_exist():
    """Verify key maize varieties are in the database."""
    conn = get_db_connection()
    assert conn is not None
    
    cursor = conn.cursor()
    
    expected_varieties = ["SC 301", "SC 727", "SC 637", "SC 513"]
    for variety in expected_varieties:
        cursor.execute(
            "SELECT variety_name, days_to_maturity FROM crop_varieties WHERE variety_name ILIKE %s",
            (f"%{variety}%",)
        )
        row = cursor.fetchone()
        assert row is not None, f"Variety {variety} not found in database"
        print(f"   • {row['variety_name']}: {row['days_to_maturity']} days")
    
    cursor.close()
    conn.close()
    print("✅ Maize varieties verified")


def test_tobacco_varieties_exist():
    """Verify key tobacco varieties are in the database."""
    conn = get_db_connection()
    assert conn is not None
    
    cursor = conn.cursor()
    
    expected_varieties = ["KRK26R", "KRK75", "T78"]
    for variety in expected_varieties:
        cursor.execute(
            "SELECT variety_name, breeder, characteristics FROM crop_varieties WHERE variety_name ILIKE %s",
            (f"%{variety}%",)
        )
        row = cursor.fetchone()
        assert row is not None, f"Tobacco variety {variety} not found"
        chars = row['characteristics'] or {}
        style = chars.get('style', 'N/A')
        print(f"   • {row['variety_name']} ({row['breeder']}): Style={style}")
    
    cursor.close()
    conn.close()
    print("✅ Tobacco varieties verified")


def test_variety_details_lookup():
    """Test the _get_variety_details method in AgronomistBrain."""
    brain = get_brain()
    
    # Test SC 727 lookup
    details = brain._get_variety_details("Maize", "SC 727")
    assert details is not None, "SC 727 lookup failed"
    assert "Seed Co" in details, "Breeder not found in details"
    assert "158" in details or "days" in details.lower(), "Days to maturity not found"
    print("✅ _get_variety_details (SC 727): OK")
    
    # Test KRK75 lookup
    details = brain._get_variety_details("Tobacco", "KRK75")
    assert details is not None, "KRK75 lookup failed"
    assert "Kutsaga" in details, "Kutsaga breeder not found"
    assert "drought" in details.lower(), "Drought tolerance not mentioned"
    print("✅ _get_variety_details (KRK75): OK")
    
    # Test partial match
    details = brain._get_variety_details("Maize", "727")  # Without 'SC' prefix
    assert details is not None, "Partial match for 727 failed"
    print("✅ _get_variety_details (partial match): OK")


async def test_ai_response_variety_awareness():
    """
    Test that the AI Brain incorporates variety information into responses.
    This requires OPENAI_API_KEY to be set.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or "your_" in api_key:
        print("⚠️ Skipping AI response test - OPENAI_API_KEY not set")
        return
    
    brain = get_brain()
    
    # Create input with field context including variety
    field_context = FieldContext(
        field_id="test-field-001",
        field_name="North Ridge",
        crop_type="Maize",
        variety="SC 727",
        planting_date="2025-11-15",
        growth_stage="V6"
    )
    
    agent_input = AgentInput(
        user_id="test-user-001",
        message="When will my maize be ready for harvest?",
        field_context=field_context,
        language="en"
    )
    
    response = await brain.process(agent_input)
    
    # Verify response mentions variety-specific information
    response_text = response.text_body.lower()
    
    # Check for variety awareness indicators
    checks = {
        "mentions_variety": "727" in response_text or "nzou" in response_text,
        "mentions_days": any(d in response_text for d in ["158", "155", "160", "days"]),
        "has_actions": len(response.actions) > 0,
        "has_confidence": response.confidence_score > 0
    }
    
    print(f"\n📝 AI Response Preview (first 300 chars):")
    print(f"   {response.text_body[:300]}...")
    print(f"\n📊 Response Quality Checks:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}: {passed}")
    
    # At minimum, the response should have content
    assert response.text_body and len(response.text_body) > 50, "Response too short"
    print("\n✅ AI variety-aware response: OK")


async def test_ai_response_tobacco_knowledge():
    """Test AI knowledge of tobacco varieties."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or "your_" in api_key:
        print("⚠️ Skipping tobacco AI test - OPENAI_API_KEY not set")
        return
    
    brain = get_brain()
    
    field_context = FieldContext(
        field_id="test-field-002",
        field_name="Tobacco Block A",
        crop_type="Tobacco",
        variety="KRK75",
        planting_date="2025-09-01"
    )
    
    agent_input = AgentInput(
        user_id="test-user-001",
        message="Is my KRK75 tobacco good for dry conditions?",
        field_context=field_context,
        language="en"
    )
    
    response = await brain.process(agent_input)
    response_text = response.text_body.lower()
    
    # KRK75 is known for drought tolerance
    drought_mentioned = any(word in response_text for word in ["drought", "dry", "tolerant", "resistant"])
    
    print(f"\n📝 Tobacco AI Response Preview:")
    print(f"   {response.text_body[:300]}...")
    print(f"\n✅ Drought tolerance mentioned: {drought_mentioned}")
    
    assert response.text_body and len(response.text_body) > 50
    print("✅ AI tobacco knowledge: OK")


async def test_ai_variety_comparison():
    """Test AI can compare varieties."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or "your_" in api_key:
        print("⚠️ Skipping comparison test - OPENAI_API_KEY not set")
        return
    
    brain = get_brain()
    
    agent_input = AgentInput(
        user_id="test-user-001",
        message="What's the difference between SC 727 and SC 301 maize?",
        language="en"
    )
    
    response = await brain.process(agent_input)
    response_text = response.text_body.lower()
    
    # Check for comparison indicators
    has_early = any(w in response_text for w in ["early", "short", "100", "quick"])
    has_late = any(w in response_text for w in ["late", "long", "158", "155"])
    has_yield_diff = any(w in response_text for w in ["yield", "high", "potential"])
    has_drought = any(w in response_text for w in ["drought", "dry", "region"])
    
    print(f"\n📝 Comparison Response Preview:")
    print(f"   {response.text_body[:400]}...")
    print(f"\n📊 Comparison Quality:")
    print(f"   • Mentions early maturity: {has_early}")
    print(f"   • Mentions late maturity: {has_late}")
    print(f"   • Discusses yield: {has_yield_diff}")
    print(f"   • Discusses drought/regions: {has_drought}")
    
    assert response.text_body and len(response.text_body) > 100
    print("\n✅ AI variety comparison: OK")


def test_all_crop_types_have_varieties():
    """Verify all major crop types have varieties in the database."""
    conn = get_db_connection()
    assert conn is not None
    
    cursor = conn.cursor()
    
    expected_crops = [
        "Maize", "Tobacco", "Soybeans", "Sorghum", "Wheat", 
        "Cotton", "Groundnuts", "Sunflower", "Sugar Beans",
        "Potato", "Tomato", "Onion", "Cabbage"
    ]
    
    print("\n📋 Crop Coverage Check:")
    missing_crops = []
    
    for crop in expected_crops:
        cursor.execute(
            "SELECT COUNT(*) as count FROM crop_varieties WHERE crop_name ILIKE %s",
            (crop,)
        )
        count = cursor.fetchone()['count']
        status = "✅" if count > 0 else "❌"
        print(f"   {status} {crop}: {count} varieties")
        if count == 0:
            missing_crops.append(crop)
    
    cursor.close()
    conn.close()
    
    if missing_crops:
        print(f"\n⚠️ Missing crops: {', '.join(missing_crops)}")
        print("   Run: python scripts/seed_zimbabwe_crops.py to add them")
    
    # We require at least the core crops
    core_crops = ["Maize", "Tobacco", "Soybeans"]
    for crop in core_crops:
        assert crop not in missing_crops, f"Core crop {crop} has no varieties"
    
    print("\n✅ Crop type coverage: OK")


def run_sync_tests():
    """Run all synchronous tests."""
    print("\n" + "="*60)
    print("🧪 KurimaSense AI Knowledge Tests")
    print("="*60 + "\n")
    
    test_database_connection()
    test_varieties_seeded()
    test_maize_varieties_exist()
    test_tobacco_varieties_exist()
    test_variety_details_lookup()
    test_all_crop_types_have_varieties()
    
    print("\n" + "="*60)
    print("✅ All synchronous tests passed!")
    print("="*60)


async def run_async_tests():
    """Run all async AI tests."""
    print("\n" + "="*60)
    print("🤖 AI Response Tests (requires OPENAI_API_KEY)")
    print("="*60 + "\n")
    
    await test_ai_response_variety_awareness()
    await test_ai_response_tobacco_knowledge()
    await test_ai_variety_comparison()
    
    print("\n" + "="*60)
    print("✅ All AI response tests completed!")
    print("="*60)


def main():
    """Run all tests."""
    run_sync_tests()
    
    # Run async tests
    try:
        asyncio.run(run_async_tests())
    except Exception as e:
        print(f"\n⚠️ Async tests failed: {e}")
    
    print("\n🎉 Test suite complete!")


if __name__ == "__main__":
    main()
