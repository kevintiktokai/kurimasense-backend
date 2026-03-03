import os
import requests
import json
from typing import List, Dict

# Lightweight Imports
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
# We generally expect SUPABASE_URL to be like https://xyz.supabase.co
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") # Service Role Key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not OPENAI_API_KEY:
    print("❌ Error: Missing env vars: SUPABASE_URL, SUPABASE_KEY, or OPENAI_API_KEY.")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# --- Sources ---
DATA_SOURCES = [
    {
        "url": "https://artfarm.co.zw/wp-content/uploads/2025/07/ART-Maize-Production-Guide.pdf",
        "region": "southern_africa",
        "country": "zimbabwe",
        "crop": "maize",
        "title": "ART Commercial Maize Production Guide"
    },
    {
        "url": "https://seedcogroup.com/zm/fieldcrops/wp-content/uploads/2021/09/Maize-Growers-Guide_Seed-Co-Zambia-with-logo.pdf",
        "region": "southern_africa",
        "country": "zambia",
        "crop": "maize",
        "title": "Seed Co Maize Growers Guide"
    },
    {
        "url": "https://www.kcepcral.go.ke/wp-content/uploads/2017/04/KCEP-Maize-Extension-and-Training-Manual.pdf",
        "region": "east_africa",
        "country": "kenya",
        "crop": "maize",
        "title": "KALRO KCEP Maize Extension Manual"
    },
    {
        "url": "https://www.iita.org/wp-content/uploads/2016/06/Cassava_system_cropping_guide.pdf",
        "region": "west_africa",
        "country": "nigeria",
        "crop": "cassava",
        "title": "IITA Cassava System Cropping Guide"
    },
    {
        "url": "https://www.iita.org/wp-content/uploads/2020/05/Cowpea-manualENGLISH.pdf",
        "region": "west_africa",
        "country": "generic",
        "crop": "cowpea",
        "title": "IITA Cowpea Production Manual"
    }
]

def download_pdf(url: str) -> str:
    print(f"Downloading: {url}...")
    try:
        response = requests.get(url, timeout=30)
        temp_path = f"/tmp/{url.split('/')[-1]}"
        with open(temp_path, "wb") as f:
            f.write(response.content)
        return temp_path
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def simple_text_splitter(text, chunk_size=1000, chunk_overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - chunk_overlap)
    return chunks

def extract_text_from_pdf(path):
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            extract = page.extract_text()
            if extract:
                text += extract + "\n"
        return text
    except Exception as e:
        print(f"❌ PDF Read Error: {e}")
        return ""

def get_embeddings(texts):
    if not texts: return []
    try:
        response = client.embeddings.create(
            input=texts,
            model="text-embedding-3-small"
        )
        return [d.embedding for d in response.data]
    except Exception as e:
        print(f"❌ Embedding Error: {e}")
        return []

def process_documents():
    print("🚀 Starting Ingestion via Supabase REST API...")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    for source in DATA_SOURCES:
        pdf_path = download_pdf(source["url"])
        if not pdf_path: continue
        
        print(f"Processing {source['title']}...")
        full_text = extract_text_from_pdf(pdf_path)
        chunks = simple_text_splitter(full_text)
        print(f"  -> Generated {len(chunks)} chunks. Embedding...")
        
        # Batch process
        batch_size = 20 # Smaller batch for REST API payload safety
        for i in range(0, len(chunks), batch_size):
            batch_texts = chunks[i:i+batch_size]
            embeddings = get_embeddings(batch_texts)
            
            records = []
            for text, emb in zip(batch_texts, embeddings):
                meta = {
                    "region": source["region"],
                    "country": source["country"],
                    "crop": source["crop"],
                    "source_title": source["title"]
                }
                records.append({
                    "content": text,
                    "metadata": meta,
                    "embedding": emb
                })
            
            # RAW REST API CALL
            endpoint = f"{SUPABASE_URL}/rest/v1/knowledge_base"
            try:
                resp = requests.post(endpoint, json=records, headers=headers)
                if resp.status_code in [200, 201]:
                    print(f"    -> Stored batch {i//batch_size + 1}/{len(chunks)//batch_size + 1}")
                else:
                    print(f"❌ Insert Error {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"❌ Req Error: {e}")

        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    
    print("🎉 Ingestion Complete.")

if __name__ == "__main__":
    process_documents()
