"""
/tools/retrieve_context.py

Fixes:
- Do not call `requests` inside async code (blocks event loop)
- Reuse HTTP + OpenAI clients (keep-alive)
- Add simple TTL cache for embeddings + retrieval results
"""

import os
import sys
import json
import time
import hashlib
from typing import Any, Dict, List, Optional, Tuple

import httpx
from openai import AsyncOpenAI, OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# ---- simple TTL caches (in-memory) ----
_EMBED_TTL_SEC = 60 * 60 * 12  # 12h
_RAG_TTL_SEC = 60 * 10         # 10m

_embed_cache: Dict[str, Tuple[float, List[float]]] = {}
_rag_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}


def _now() -> float:
    return time.time()


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _cache_get(cache: Dict[str, Tuple[float, Any]], key: str, ttl: int) -> Optional[Any]:
    item = cache.get(key)
    if not item:
        return None
    ts, val = item
    if _now() - ts > ttl:
        cache.pop(key, None)
        return None
    return val


def _cache_set(cache: Dict[str, Tuple[float, Any]], key: str, val: Any) -> None:
    cache[key] = (_now(), val)


def _error(message: str) -> Dict[str, Any]:
    return {"status": "error", "error_message": message}


def _get_region_from_coords(lat, lon) -> str:
    try:
        lat = float(lat)
        lon = float(lon)
        if lat < -10:
            return "southern_africa"
        if -10 <= lat <= 5 and lon >= 28:
            return "east_africa"
        if lat >= 4 and lon <= 15:
            return "west_africa"
        return "generic"
    except Exception:
        return "generic"


# ---- global clients (reuse connections) ----
_async_openai: Optional[AsyncOpenAI] = None
_http: Optional[httpx.AsyncClient] = None


def _get_openai() -> AsyncOpenAI:
    global _async_openai
    if _async_openai is None:
        _async_openai = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _async_openai


def _get_http() -> httpx.AsyncClient:
    global _http
    if _http is None:
        # keep-alive for speed; short timeouts so slow deps don't stall UI forever
        _http = httpx.AsyncClient(timeout=httpx.Timeout(connect=3.0, read=5.0, write=5.0, pool=5.0))
    return _http


async def _embed_query(query: str) -> List[float]:
    key = _sha("emb:" + query)
    cached = _cache_get(_embed_cache, key, _EMBED_TTL_SEC)
    if cached is not None:
        return cached

    client = _get_openai()
    resp = await client.embeddings.create(input=query, model="text-embedding-3-small")
    vec = resp.data[0].embedding
    _cache_set(_embed_cache, key, vec)
    return vec


async def search_knowledge_base(query: str, region: str, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Async RAG retrieval from Supabase RPC.
    Non-blocking + cached.
    """
    if not SUPABASE_URL or not SUPABASE_KEY or not OPENAI_API_KEY:
        return []

    # Cache the retrieval itself (query+region+limit)
    rag_key = _sha(f"rag:{region}:{limit}:{query}")
    cached = _cache_get(_rag_cache, rag_key, _RAG_TTL_SEC)
    if cached is not None:
        return cached

    query_vector = await _embed_query(query)

    endpoint = f"{SUPABASE_URL}/rest/v1/rpc/match_documents"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    params = {
        "query_embedding": query_vector,
        "match_threshold": 0.25,
        "match_count": limit * 2,
        "filter_region": region,
    }

    http = _get_http()
    try:
        resp = await http.post(endpoint, json=params, headers=headers)
        if resp.status_code != 200:
            return []

        results = resp.json() or []

        # Re-rank: prioritize stronger sources
        def rank(res: Dict[str, Any]) -> int:
            meta = res.get("metadata") or {}
            source = str(meta.get("source_title", "")).lower()
            if "research digest" in source:
                return 0
            if "manual" in source or "seed co" in source:
                return 1
            return 2

        results.sort(key=rank)
        results = results[:limit]

        _cache_set(_rag_cache, rag_key, results)
        return results
    except Exception:
        return []


def search_knowledge_base_sync(query: str, region: str, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Sync version for CLI/tool usage.
    Kept for backwards compatibility.
    """
    if not SUPABASE_URL or not SUPABASE_KEY or not OPENAI_API_KEY:
        return []

    client = OpenAI(api_key=OPENAI_API_KEY)
    emb = client.embeddings.create(input=query, model="text-embedding-3-small")
    query_vector = emb.data[0].embedding

    endpoint = f"{SUPABASE_URL}/rest/v1/rpc/match_documents"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
    params = {"query_embedding": query_vector, "match_threshold": 0.5, "match_count": limit, "filter_region": region}

    try:
        import requests
        r = requests.post(endpoint, json=params, headers=headers, timeout=5)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def main():
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            raise ValueError("No input")

        payload = json.loads(raw)
        seed = payload.get("seed") or payload

        query = seed.get("raw_message", "")
        location = seed.get("location", {})
        lat = location.get("lat")
        lon = location.get("lon")

        region = _get_region_from_coords(lat, lon)
        context = seed.get("context", {})
        if context.get("region"):
            region = context.get("region")

        # NOTE: CLI path is sync for simplicity; your FastAPI path uses async above.
        results = search_knowledge_base_sync(query, region)

        context_text = ""
        for r in results:
            meta = r.get("metadata", {})
            context_text += f"Source: {meta.get('source_title')} ({meta.get('country')})\n"
            context_text += f"{r.get('content')}\n---\n"

        output = {"retrieved_context": context_text, "region_used": region, "chunk_count": len(results)}
        print(json.dumps({"status": "ok", "data": output}))
    except Exception as e:
        print(json.dumps(_error(str(e))))


if __name__ == "__main__":
    main()
