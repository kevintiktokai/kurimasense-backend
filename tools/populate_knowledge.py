import os
import sys
import json
import asyncio
from typing import List, Dict
from openai import AsyncOpenAI
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
    print("❌ Missing API keys. Ensure SUPABASE_URL, SUPABASE_KEY, and OPENAI_API_KEY are set.")
    sys.exit(1)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Simple text chunking with overlap."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if len(chunk) > 50:  # Skip tiny chunks
            chunks.append(chunk)
    return chunks

async def get_embedding(text: str) -> List[float]:
    """Generate embedding for text."""
    try:
        response = await client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"⚠️ Embedding failed: {e}")
        return []

async def process_document(doc: Dict[str, str]):
    """Process a single document: chunk, embed, and upload."""
    url = doc.get("url", "unknown")
    title = doc.get("title", "Untitled")
    content = doc.get("content", "")
    metadata = doc.get("metadata", {})
    
    # Merge metadata
    full_metadata = {
        "source_title": title,
        "source_url": url,
        "country": "Zimbabwe",
        "processed_at": asyncio.get_event_loop().time(),
        **metadata
    }
    
    print(f"📄 Processing: {title} ({url})")
    chunks = chunk_text(content)
    print(f"   -> {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        embedding = await get_embedding(chunk)
        if not embedding:
            continue
            
        # Insert into Supabase
        # Assuming table 'documents' with: id, content, metadata, embedding
        payload = {
            "content": chunk,
            "metadata": full_metadata,
            "embedding": embedding
        }
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        try:
            resp = requests.post(
                f"{SUPABASE_URL}/rest/v1/documents",
                json=payload,
                headers=headers,
                timeout=10
            )
            if resp.status_code not in [200, 201]:
                print(f"❌ Upload failed chunk {i}: {resp.text}")
        except Exception as e:
            print(f"❌ Request failed chunk {i}: {e}")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 populate_knowledge.py <path_to_data.json>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            
        documents = data if isinstance(data, list) else [data]
        
        print(f"🚀 Starting population of {len(documents)} documents...")
        for doc in documents:
            await process_document(doc)
            
        print("\n✅ Knowledge Base Population Complete!")
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in file: {file_path}")

if __name__ == "__main__":
    asyncio.run(main())
