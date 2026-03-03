import sys
import os
import asyncio
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# We assume keys are in ENV for this run
from tools.retrieve_context import search_knowledge_base

async def verify():
    print("🔍 Testing Real RAG Retrieval for ALL Categories...")
    
    test_cases = [
        {"query": "SC 727 yield potential", "expected": "Seed Co", "category": "Maize"},
        {"query": "Albar SZ 9314 characteristics", "expected": "Quton", "category": "Cotton"},
        {"query": "Kutsaga RK1 disease resistance", "expected": "Kutsaga", "category": "Tobacco"},
        {"query": "Broccoli irrigation requirements", "expected": "Starke Ayres", "category": "Horticulture"},
        # New "Bible" Content
        {"query": "Wheat planting dates highveld", "expected": "Seed Co", "category": "Wheat"},
        {"query": "Soyabean planting population", "expected": "Seed Co", "category": "Soybean"},
        {"query": "Sorghum variety for dry areas", "expected": "Seed Co", "category": "Sorghum"},
        {"query": "Groundnut gypsum application", "expected": "Seed Co", "category": "Groundnut"},
        # PhD Level Research
        {"query": "Why apply lime to soybean acidic soil", "expected": "Research Digest", "category": "PhD Research"}
    ]
    
    success_count = 0
    
    for test in test_cases:
        print(f"\n--- Testing {test['category']} ---")
        print(f"Query: '{test['query']}'")
        results = await search_knowledge_base(test['query'], "generic")
        
        if not results:
            print(f"❌ {test['category']} FAILED: No results found.")
            continue
            
        # Check first result for expected source or content
        found = False
        for res in results:
            content = res.get("content", "")
            meta = res.get("metadata", {})
            source = meta.get("source", "") + str(meta.get("source_title", ""))
            
            if test['expected'].lower() in source.lower() or test['expected'].lower() in content.lower():
                found = True
                print(f"✅ {test['category']} SUCCESS: Found {test['expected']} content.")
                print(f"   Source: {source}")
                print(f"   Snippet: {content[:100]}...")
                break
        
        if found:
            success_count += 1
        else:
            print(f"⚠️ {test['category']} WARNING: Results found but expected keyword '{test['expected']}' missing.")
            
    print(f"\n📊 Summary: {success_count}/{len(test_cases)} Passed")
    if success_count == len(test_cases):
        print("🎉 ALL SYSTEMS GO: Knowledge Base is fully grounded!")

if __name__ == "__main__":
    asyncio.run(verify())
