import os
import re
import json
import random
import traceback
import urllib.request
import urllib.error
import asyncio
import logging
from datetime import datetime, date, timedelta
import time
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Depends, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.concurrency import run_in_threadpool
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from router import route
from ai_brain import (
    AgronomistBrain, AgentInput, AgentResponse,
    FieldContext, WeatherContext, ConversationMessage,
    VisionAnalyzer, get_brain, get_vision_analyzer
)
from database import get_db_connection, init_db, log_user_event, get_recent_field_activity
from proactive_intelligence import (
    calculate_growth_stage,
    generate_proactive_alerts,
    get_variety_info,
    assess_disease_risk,
    generate_harvest_alert
)
from tools.get_crop_health import run as run_crop_health
from tools.generate_yield import run as run_generate_yield
from tools.get_weather_forecast import fetch_weather as fetch_weather_data
import climate_service

# Shared dependencies (auth, caching, helpers)
from deps import (
    verify_token,
    cache_get as _cache_get,
    cache_set as _cache_set,
    cache_invalidate_prefix as _cache_invalidate_prefix,
    get_user_language,
    get_health_status as _get_health_status,
    get_field_context as _get_field_context,
    resolve_coordinates,
    validate_environment,
    MOCK_FIELDS, MOCK_CHATS, MOCK_INPUTS,
    SUPABASE_JWT_SECRET, SUPABASE_JWT_PUBLIC_KEY,
    SUPABASE_URL, SUPABASE_ANON_KEY,
)

logger = logging.getLogger("kurimasense")

# Cache functions and verify_token are imported from deps.py
# ---------------------------------------------------------------------------

app = FastAPI(title="KurimaSense AI")

# CORS Configuration
# Allow specific origins from environment or default to known frontends
allowed_origins_env = os.environ.get("CORS_ORIGINS", "").strip()
if allowed_origins_env:
    origins_list = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
else:
    origins_list = [
        "https://kurima-sense.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

# Always allow Vercel preview URLs
allow_origin_regex = r"https://.*\.vercel\.app"

print(f"🌐 CORS_ORIGINS env: '{allowed_origins_env}'")
print(f"🌐 Parsed origins_list: {origins_list}")
print(f"🌐 allow_origin_regex: {allow_origin_regex}")


def is_origin_allowed(origin: str) -> bool:
    """Check if the origin is allowed based on our CORS policy."""
    if not origin:
        return False
    if origin in origins_list:
        return True
    if re.match(allow_origin_regex, origin):
        return True
    return False


class RobustCORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware that ensures CORS headers are ALWAYS added,
    even for error responses. FastAPI's built-in CORSMiddleware can miss
    errors thrown from dependencies.
    """
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")
        
        # Handle preflight OPTIONS request
        if request.method == "OPTIONS":
            if is_origin_allowed(origin):
                return JSONResponse(
                    content={"status": "ok"},
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                        "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Requested-With, Accept, Origin",
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Max-Age": "86400",
                    }
                )
            else:
                return JSONResponse(content={"error": "CORS not allowed"}, status_code=403)
        
        # Process the request
        try:
            response = await call_next(request)
        except Exception as e:
            # Catch any unhandled exception and return proper CORS response
            print(f"Unhandled exception in middleware: {e}")
            response = JSONResponse(
                content={"detail": "Internal server error"},
                status_code=500
            )
        
        # Add CORS headers to ALL responses if origin is allowed
        if is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "Content-Length, Content-Type"
        
        return response


# Add our robust CORS middleware FIRST (it wraps everything)
app.add_middleware(RobustCORSMiddleware)

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        process_time_ms = round(process_time * 1000, 2)
        response.headers["X-Process-Time"] = str(process_time_ms)
        print(json.dumps({
            "event": "request_completed",
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": process_time_ms
        }))
        return response

app.add_middleware(TimingMiddleware)

# NOTE: Standard CORSMiddleware removed — RobustCORSMiddleware above handles
# all CORS logic including preflight, error responses, and header injection.
# Having two CORS middlewares caused duplicate headers and unpredictable behavior.


# Global exception handler to ensure CORS headers on HTTPExceptions
@app.exception_handler(HTTPException)
async def cors_http_exception_handler(request: Request, exc: HTTPException):
    origin = request.headers.get("origin", "")
    headers = {}
    if is_origin_allowed(origin):
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers
    )


# Catch-all exception handler
@app.exception_handler(Exception)
async def cors_general_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin", "")
    headers = {}
    if is_origin_allowed(origin):
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=headers
    )

# JWT configuration imported from deps.py (SUPABASE_JWT_SECRET, etc.)

# JWKS, verify_token, and mock data are imported from deps.py


# Auth (verify_token), caching, mock data, and helpers are all imported from deps.py above.

@app.get("/health")
def health_check():
    """
    Health check endpoint that also returns CORS debug info.
    Use this to verify the backend is running the latest code.
    """
    # Test database connection
    db_status = "unknown"
    db_error = None
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            db_status = "connected"
        else:
            db_status = "no_connection"
    except Exception as e:
        db_status = "error"
        db_error = str(e)
    
    return {
        "status": "ok",
        "cors": {
            "env_value": allowed_origins_env,
            "parsed_origins": origins_list,
            "origin_regex": allow_origin_regex
        },
        "database": {
            "status": db_status,
            "error": db_error
        },
        "version": "2026-02-03-v8-planting-dates"
    }


@app.get("/jwt-config")
def jwt_config_check(user_id: str = Depends(verify_token)):
    """
    Debug endpoint to check JWT configuration (doesn't expose secrets).
    """
    jwks_status = "not_configured"
    jwks_keys_count = 0
    
    if SUPABASE_URL:
        jwks_url = f"{SUPABASE_URL}/auth/v1/jwks"
        try:
            headers = {'User-Agent': 'KurimaSense/1.0'}
            if SUPABASE_ANON_KEY:
                headers['apikey'] = SUPABASE_ANON_KEY
            
            req = urllib.request.Request(jwks_url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                jwks_data = json.loads(response.read().decode())
                jwks_keys_count = len(jwks_data.get('keys', []))
                jwks_status = f"reachable ({jwks_keys_count} keys)"
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode()
                error_json = json.loads(error_body)
                jwks_status = f"error (HTTP {e.code}): {error_json.get('message', 'Unknown')}"
            except:
                jwks_status = f"error (HTTP {e.code})"
        except Exception as e:
            jwks_status = f"error ({type(e).__name__})"
    
    return {
        "jwt_secret_configured": bool(SUPABASE_JWT_SECRET),
        "jwt_secret_length": len(SUPABASE_JWT_SECRET) if SUPABASE_JWT_SECRET else 0,
        "jwt_public_key_configured": bool(SUPABASE_JWT_PUBLIC_KEY),
        "supabase_url_configured": bool(SUPABASE_URL),
        "supabase_anon_key_configured": bool(SUPABASE_ANON_KEY),
        "supabase_url_preview": SUPABASE_URL[:30] + "..." if SUPABASE_URL and len(SUPABASE_URL) > 30 else SUPABASE_URL,
        "jwks_endpoint_status": jwks_status,
        "jwks_keys_found": jwks_keys_count,
        "expected_algorithm": "ES256 (asymmetric)" if not SUPABASE_JWT_SECRET else "HS256 (symmetric) or ES256",
    }


@app.get("/db-schema")
def db_schema_check(user_id: str = Depends(verify_token)):
    """
    Debug endpoint to check database schema.
    """
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "message": "No database connection"}
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if fields table exists and its columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'fields'
            ORDER BY ordinal_position
        """)
        fields_columns = [dict(row) for row in cursor.fetchall()]
        
        # Check if daily_logs table exists and its columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'daily_logs'
            ORDER BY ordinal_position
        """)
        daily_logs_columns = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return {
            "status": "ok",
            "tables": {
                "fields": fields_columns,
                "daily_logs": daily_logs_columns
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.on_event("startup")
def startup_checks():
    """Run startup validations and initialize database."""
    # Validate environment variables
    validate_environment()
    # Initialize database tables
    init_db()

@app.get("/fields")
def get_fields(user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        print("Using Mock Data (Offline Mode)")
        return MOCK_FIELDS
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT
                f.id,
                f.name,
                f.crop_type,
                f.size_hectares,
                f.polygon_coordinates,
                f.health_score,
                f.planting_date,
                f.transplant_date,
                f.is_transplanted,
                f.variety,
                f.fertilizer_history,
                latest.log_date::text   AS last_pass,
                latest.ndvi             AS latest_ndvi,
                latest.soil_moisture    AS latest_moisture,
                latest.insight_text     AS latest_insight
            FROM fields f
            LEFT JOIN LATERAL (
                SELECT log_date, ndvi, soil_moisture, insight_text
                FROM daily_logs
                WHERE field_id = f.id
                ORDER BY log_date DESC
                LIMIT 1
            ) latest ON true
            WHERE f.user_id = %s::uuid
            ORDER BY f.created_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        results = []
        
        for row in rows:
            score = float(row.get('health_score', 0))
            status = 'Critical'
            if score > 0.7: status = 'Excellent'
            elif score > 0.4: status = 'Good'
            
            coords = row.get('polygon_coordinates')
            location = None
            if coords and isinstance(coords, list) and len(coords) > 0:
                lats = [p['lat'] for p in coords]
                lons = [p['lon'] for p in coords]
                location = {"lat": sum(lats) / len(lats), "lon": sum(lons) / len(lons)}

            # Format planting_date as string if it's a date object
            planting_date_str = None
            if row.get('planting_date'):
                pd = row['planting_date']
                planting_date_str = pd.isoformat() if hasattr(pd, 'isoformat') else str(pd)
            
            # Format transplant_date as string if it's a date object
            transplant_date_str = None
            if row.get('transplant_date'):
                td = row['transplant_date']
                transplant_date_str = td.isoformat() if hasattr(td, 'isoformat') else str(td)
            
            results.append({
                "id": str(row['id']),
                "name": row['name'],
                "crop": row['crop_type'],
                "area": float(row['size_hectares'] or 0),
                "ndvi": float(row['latest_ndvi'] or 0),
                "soilMoisture": float(row['latest_moisture'] or 45),
                "healthStatus": status,
                "lastSatellitePass": row['last_pass'] or "Pending...",
                "location": location,
                "coordinates": coords,
                "plantingDate": planting_date_str,
                "transplantDate": transplant_date_str,
                "isTransplanted": row.get('is_transplanted', False),
                "variety": row.get('variety'),
                "fertilizerHistory": row.get('fertilizer_history'),
                "latestInsight": row.get('latest_insight')
            })
            
        cursor.close()
        conn.close()
        return results
        
    except Exception as e:
        print(f"Fields Query Error: {e}")
        return MOCK_FIELDS

# BackgroundTasks imported at top level

async def trigger_sentinel_analysis(field_id: str, lat: float, lon: float):
    """
    Background task to fetch satellite data and update daily_logs.
    Now async to avoid asyncio.run() conflicts with FastAPI's event loop.
    """
    conn = get_db_connection()
    if not conn:
        # Offline/Mock Mode Logic
        print(f"Offline Mode: Simulating Analysis for {field_id}...")
        import random
        await asyncio.sleep(2)  # Non-blocking delay

        # Find field in MOCK_FIELDS and update it
        for field in MOCK_FIELDS:
            if field["id"] == field_id:
                # Simulate varying data
                field["ndvi"] = round(random.uniform(0.6, 0.9), 2)
                field["soilMoisture"] = random.randint(30, 60)
                field["lastSatellitePass"] = "Just now"
                field["healthStatus"] = "Excellent" if field["ndvi"] > 0.7 else "Good"
                print(f"Updated Mock Field {field_id} with new insights.")
                break
        return

    try:
        print(f"Starting Sentinel Analysis for Field {field_id}...")

        # Call the satellite tool directly (no subprocess overhead)
        print(f"Calling satellite tool...")
        tool_output = run_crop_health(lat, lon)

        if tool_output.get("status") == "error":
            print(f"Satellite API Error: {tool_output.get('error_message')}")
            raise Exception(tool_output.get("error_message"))

        data = tool_output.get("data", {})

        # Extract Real Values
        real_ndvi = data.get("ndvi_mean", 0.0)
        real_evi = data.get("evi_mean", 0.0)
        real_moisture = int(real_ndvi * 65)  # Crude approximation for prototype

        print(f"Satellite Analysis Result: NDVI={real_ndvi}, EVI={real_evi}")

        # Update Field Health based on NDVI
        new_health = 0.9 if real_ndvi > 0.6 else 0.5

        # GENERATE AI INSIGHT (now properly awaited instead of asyncio.run())
        brain = get_brain()
        metrics = {
            "ndvi": real_ndvi,
            "soil_moisture": real_moisture,
            "health_score": new_health,
            "evi": real_evi
        }

        try:
            insight_text = await brain.generate_field_insight(metrics)
            print(f"Generated Insight: {insight_text}")
        except Exception as e:
            print(f"Insight gen error: {e}")
            insight_text = "Analysis complete. Review new metrics."

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            INSERT INTO daily_logs (field_id, ndvi, evi, soil_moisture, cloud_cover, source, insight_text)
            VALUES (%s, %s, %s, %s, %s, 'Sentinel-2', %s)
        """, (field_id, real_ndvi, real_evi, real_moisture, data.get("cloud_cover_pct", 0), insight_text))
        
        cursor.execute("UPDATE fields SET health_score = %s WHERE id = %s", (new_health, field_id))
        
        conn.commit()
        print(f"Sentinel Analysis Complete for {field_id}")
        
    except Exception as e:
        print(f"Sentinel Analysis Failed: {e}. Using fallback simulation.")
        # Fallback simulation so user still gets "some" data even if API fails (e.g. invalid key)
        # This keeps the app "functional" as requested
        # In production we might want to show an error instead.
        try:
             # Just set some plausible defaults if real fetch fails
             cursor = conn.cursor(cursor_factory=RealDictCursor)
             # Logic to insert fallback data... omitted to keep code clean, 
             # assuming main flow works or we just fail gracefully.
             conn.rollback()
        except:
            pass
    finally:
        conn.close()

@app.post("/fields/{field_id}/analyze")
def analyze_field(field_id: str, background_tasks: BackgroundTasks, user_id: str = Depends(verify_token)):
    # Find coords to pass to analysis
    lat, lon = -17.82, 31.05 # Default
    
    conn = get_db_connection()
    if not conn:
        # Find in mock
        for f in MOCK_FIELDS:
            if f["id"] == field_id:
                loc = f.get("location")
                if loc:
                    lat, lon = loc["lat"], loc["lon"]
                break
    else:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            # Verify ownership and get coords
            cursor.execute("""
                SELECT polygon_coordinates FROM fields 
                WHERE id = %s::uuid AND user_id = %s::uuid
            """, (field_id, user_id))
            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                raise HTTPException(status_code=404, detail="Field not found or access denied")
            
            coords = row['polygon_coordinates']
            if coords and isinstance(coords, list) and len(coords) > 0:
                lat, lon = coords[0]['lat'], coords[0]['lon']
            
            cursor.close()
            conn.close()
        except HTTPException:
            raise
        except Exception as e:
            print(f"Analyze Field DB Error: {e}")
            if conn: conn.close()
        
    background_tasks.add_task(trigger_sentinel_analysis, field_id, lat, lon)
    return {"status": "success", "message": "Analysis started"}

@app.get("/fields/{field_id}/history")
def get_field_history(field_id: str, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        # Mock History
        import random
        from datetime import datetime, timedelta
        
        history = []
        today = datetime.now()
        for i in range(14):
            date = today - timedelta(days=i)
            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "ndvi": round(0.6 + (i * 0.01) + random.uniform(-0.05, 0.05), 2),
                "soilMoisture": int(50 + (i * 0.5) + random.randint(-5, 5))
            })
        return list(reversed(history))

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        # Ensure field belongs to user implicitly via a join or by checking field ownership first
        # For simplicity and security, we join with fields table
        cursor.execute("""
            SELECT dl.log_date::text as date, dl.ndvi, dl.soil_moisture 
            FROM daily_logs dl
            JOIN fields f ON dl.field_id = f.id
            WHERE dl.field_id = %s::uuid AND f.user_id = %s::uuid
            ORDER BY dl.log_date ASC 
            LIMIT 30
        """, (field_id, user_id))
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            history.append({
                "date": row['date'],
                "ndvi": float(row['ndvi'] or 0),
                "soilMoisture": float(row['soil_moisture'] or 0)
            })
            
        return history
    except Exception as e:
        print(f"History Query Error: {e}")
        return []
    finally:
        if conn: conn.close()

@app.post("/fields")
def create_field(payload: dict, background_tasks: BackgroundTasks, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    
    name = payload.get("name")
    crop = payload.get("crop", "Maize")
    coords = payload.get("coordinates", [])
    area_ha = payload.get("area", 0.0) or 15.0
    planting_date = payload.get("plantingDate")
    transplant_date = payload.get("transplantDate")
    variety = payload.get("variety")
    fertilizer_history = payload.get("fertilizerHistory")
    
    # Determine if this is a transplanted crop
    TRANSPLANTED_CROPS = ['Tomato', 'Cabbage', 'Onion', 'Potato', 'Pepper', 'Eggplant', 'Lettuce']
    is_transplanted = crop in TRANSPLANTED_CROPS or payload.get("isTransplanted", False)


    if not conn:
        print("Saving to Mock DB (Offline Mode)")
        import uuid
        new_id = str(uuid.uuid4())
        
        # Calculate Mock Center
        location = None
        if coords:
             lats = [p['lat'] for p in coords]
             lons = [p['lon'] for p in coords]
             location = {"lat": sum(lats) / len(lats), "lon": sum(lons) / len(lons)}
        
        new_field = {
            "id": new_id,
            "name": name,
            "crop": crop,
            "area": area_ha,
            "planting_date": planting_date,
            "transplant_date": transplant_date,
            "is_transplanted": is_transplanted,
            "variety": variety,
            "fertilizer_history": fertilizer_history,
            "ndvi": 0.5, 
            "soilMoisture": 50,
            "healthStatus": "Good",
            "lastSatellitePass": "Just now",
            "location": location,
            "coordinates": coords
        }
        MOCK_FIELDS.insert(0, new_field)
        return {"status": "success", "id": new_id}
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Insert with all field data including planting info and transplant info
        cursor.execute("""
            INSERT INTO fields (
                name, crop_type, polygon_coordinates, size_hectares, 
                health_score, user_id, planting_date, transplant_date, 
                is_transplanted, variety, fertilizer_history
            ) 
            VALUES (%s, %s, %s, %s, 50, %s::uuid, %s, %s, %s, %s, %s) 
            RETURNING id
        """, (name, crop, json.dumps(coords), area_ha, user_id, planting_date, 
              transplant_date, is_transplanted, variety, fertilizer_history))
        
        new_id = cursor.fetchone()['id']
        conn.commit()
        
        print(f"✅ Field created: {name}, planting_date={planting_date}, variety={variety}")
        
        # Insert initial placeholder insight so field doesn't show "Pending..."
        try:
            cursor.execute("""
                INSERT INTO daily_logs (field_id, ndvi, soil_moisture, source, insight_text)
                VALUES (%s, 0.65, 45, 'initial', %s)
            """, (new_id, f"Welcome! Your {crop} field has been created. Satellite analysis will update within 24 hours."))
            conn.commit()
        except Exception as insight_err:
            print(f"Initial insight creation warning: {insight_err}")
        
        return {"status": "success", "id": str(new_id)}
        
    except Exception as e:
        print(f"Create Field Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.delete("/fields/{field_id}")
def delete_field(field_id: str, user_id: str = Depends(verify_token)):
    """
    Delete a field and all associated data (daily_logs, field_inputs).
    Only the owner can delete their field.
    """
    conn = get_db_connection()
    
    if not conn:
        # Handle mock mode
        global MOCK_FIELDS
        MOCK_FIELDS = [f for f in MOCK_FIELDS if f.get("id") != field_id]
        return {"status": "success", "message": "Field deleted (mock mode)"}
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # First verify the field belongs to this user
        cursor.execute("""
            SELECT id, name FROM fields 
            WHERE id = %s::uuid AND user_id = %s::uuid
        """, (field_id, user_id))
        
        field = cursor.fetchone()
        if not field:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Field not found or you don't have permission to delete it")
        
        field_name = field.get('name', 'Unknown')
        
        # Delete associated daily_logs first (foreign key constraint)
        cursor.execute("DELETE FROM daily_logs WHERE field_id = %s::uuid", (field_id,))
        logs_deleted = cursor.rowcount
        
        # Delete associated field_inputs if table exists
        try:
            cursor.execute("DELETE FROM field_inputs WHERE field_id = %s::uuid", (field_id,))
            inputs_deleted = cursor.rowcount
        except Exception:
            inputs_deleted = 0
        
        # Delete the field itself
        cursor.execute("DELETE FROM fields WHERE id = %s::uuid AND user_id = %s::uuid", (field_id, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"🗑️ Field deleted: {field_name} (id={field_id}), logs={logs_deleted}, inputs={inputs_deleted}")
        
        # Log the event
        log_user_event(user_id, "field_management", "field_deleted", {"field_id": field_id, "field_name": field_name})

        # Invalidate cached responses that include this field's data
        _cache_invalidate_prefix(f"insights:{user_id}")
        _cache_invalidate_prefix(f"yield:{user_id}:")

        return {
            "status": "success", 
            "message": f"Field '{field_name}' deleted successfully",
            "deleted": {
                "field_id": field_id,
                "daily_logs": logs_deleted,
                "field_inputs": inputs_deleted
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete Field Error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to delete field: {str(e)}")


@app.get("/user")
def get_user_profile(user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        return {
            "name": "Alex Jackson",
            "email": "alex@simba.ag",
            "region": "Zimbabwe",
            "role": "Farmer",
            "crops": ["Maize", "Tobacco"]
        }
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT full_name, role, preferred_language 
            FROM profiles WHERE id = %s
        """, (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return {
                "name": row['full_name'] or "User",
                "email": f"User {user_id[:8]}", # Mock email since we don't store it in profiles
                "region": "Zimbabwe",
                "role": row['role'] or "Farmer",
                "crops": ["Maize"] # Default
            }
    except Exception as e:
        print(f"User Query Error: {e}")
        
    return {
        "name": "User",
        "email": "",
        "region": "Zimbabwe",
        "role": "Farmer",
        "crops": []
    }

@app.post("/inputs")
def log_input(payload: dict, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    
    field_id = payload.get("field_id")
    input_type = payload.get("input_type")
    quantity = payload.get("quantity")
    unit = payload.get("unit", "units")
    date = payload.get("date", "now")
    
    if not conn:
        import uuid
        new_id = str(uuid.uuid4())
        MOCK_INPUTS.append({
            "id": new_id,
            "field_id": field_id,
            "user_id": user_id,
            "type": input_type,
            "quantity": quantity,
            "date": date
        })
        return {"status": "success", "id": new_id}
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            INSERT INTO field_inputs (field_id, user_id, input_type, quantity, unit, input_date)
            VALUES (%s, %s::uuid, %s, %s, %s, %s)
            RETURNING id
        """, (field_id, user_id, input_type, quantity, unit, date))
        
        new_id = cursor.fetchone()['id']
        conn.commit()
        return {"status": "success", "id": str(new_id)}
        
    except Exception as e:
        print(f"Log Input Error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/dashboard")
def get_dashboard_stats(user_id: str = Depends(verify_token)):
    """
    Get dashboard statistics with variety-aware yield projections.
    Uses crop_varieties database for accurate yield potentials.
    """
    conn = get_db_connection()
    
    # --- Aggregate Yield Logic ---
    total_projected = 0
    active_fields_count = 0
    total_area = 0
    fields_to_scan = []
    
    # Default yield potentials by crop (conservative midpoints in t/ha)
    DEFAULT_YIELDS = {
        "maize": 6.0, "tobacco": 2.0, "soybean": 2.5, "wheat": 4.5,
        "tomato": 40.0, "cabbage": 50.0, "potato": 25.0, "cotton": 2.5,
        "groundnuts": 2.0, "sunflower": 2.0, "sorghum": 3.0, "sugar_beans": 2.0
    }
    
    if not conn:
        fields_to_scan = MOCK_FIELDS
    else:
        # Fetch user's fields WITH variety information
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check if user_id column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'fields' AND column_name = 'user_id'
            """)
            has_user_id = cursor.fetchone() is not None
            
            if has_user_id:
                # Enhanced query with variety join for accurate yield potential
                cursor.execute("""
                    SELECT 
                        f.id, f.name, f.crop_type, f.size_hectares, f.health_score, 
                        f.polygon_coordinates, f.variety,
                        cv.yield_potential_low, cv.yield_potential_high
                    FROM fields f
                    LEFT JOIN crop_varieties cv ON 
                        cv.variety_name ILIKE f.variety AND 
                        cv.crop_name ILIKE f.crop_type
                    WHERE f.user_id = %s::uuid
                """, (user_id,))
            else:
                # Fallback for legacy schema
                cursor.execute("""
                    SELECT 
                        f.id, f.name, f.crop_type, f.size_hectares, f.health_score, 
                        f.polygon_coordinates, f.variety,
                        cv.yield_potential_low, cv.yield_potential_high
                    FROM fields f
                    LEFT JOIN crop_varieties cv ON 
                        cv.variety_name ILIKE f.variety AND 
                        cv.crop_name ILIKE f.crop_type
                """)
            
            rows = cursor.fetchall()
            
            for row in rows:
                area = float(row['size_hectares'] or 0)
                crop = (row['crop_type'] or 'maize').lower()
                
                # Use variety-specific yield if available, otherwise crop default
                yield_low = row.get('yield_potential_low')
                yield_high = row.get('yield_potential_high')
                
                if yield_low and yield_high:
                    # Use midpoint of variety potential, adjusted by health
                    base_yield = (float(yield_low) + float(yield_high)) / 2
                else:
                    # Fall back to crop default
                    base_yield = DEFAULT_YIELDS.get(crop.replace(' ', '_'), 5.0)
                
                # Adjust by health score (NDVI proxy)
                health_score = float(row['health_score'] or 50) / 100.0
                health_factor = 0.7 + (health_score * 0.3)  # Maps 0-100% to 0.7-1.0
                
                projected = area * base_yield * health_factor
                
                fields_to_scan.append({
                    "id": str(row['id']),
                    "name": row['name'],
                    "crop": row['crop_type'],
                    "area": area,
                    "ndvi": health_score,
                    "projected_yield": projected,
                    "variety": row.get('variety')
                })
            
            cursor.close()
        except Exception as e:
            print(f"Dashboard DB Error: {e}")
            import traceback
            traceback.print_exc()
            fields_to_scan = []

    avg_health = 0
    for f in fields_to_scan:
        p_yield = f.get("projected_yield", f.get("area", 0) * 5.0)
        total_projected += p_yield
        total_area += f.get("area", 0)
        active_fields_count += 1
        avg_health += f.get("ndvi", 0.5)

    avg_health_score = int((avg_health / active_fields_count) * 100) if active_fields_count else 50

    return {
        "stats": {
            "active_fields": active_fields_count,
            "crop_health": avg_health_score, 
            "rain_forecast": "12mm",
            "farmers_reached": total_area 
        },
        "chartData": [
            {"name": "Week 1", "yield": total_projected * 0.4},
            {"name": "Week 2", "yield": total_projected * 0.6},
            {"name": "Week 3", "yield": total_projected * 0.85},
            {"name": "Current", "yield": total_projected}
        ],
        "alerts": [],
        "projected_yield": round(total_projected, 1),
        "yield_disclaimer": "⚠️ Estimates based on variety potential and current field health. Actual results vary with weather and management."
    }

@app.post("/fields/{field_id}/yield")
def post_generate_yield(field_id: str, user_id: str = Depends(verify_token)):
    """
    Generates yield projection using AI based on field parameters.
    """
    # Log usage
    log_user_event(user_id, "feature_usage", "yield_projection", {"field_id": field_id})

    cache_key = f"yield:{user_id}:{field_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    # 1. Fetch Field Data from Database first
    field = None
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT id, name, crop_type, planting_date, variety, fertilizer_history, size_hectares
                FROM fields 
                WHERE id = %s::uuid AND user_id = %s::uuid
            """, (field_id, user_id))
            row = cursor.fetchone()
            cursor.close()
            
            # Fetch Preferred Language (Best Effort)
            user_lang = "en"
            try:
                # Re-use connection for efficiency
                l_cursor = conn.cursor(cursor_factory=RealDictCursor)
                l_cursor.execute("SELECT preferred_language FROM profiles WHERE id = %s", (user_id,))
                l_row = l_cursor.fetchone()
                if l_row and l_row.get('preferred_language'):
                    user_lang = l_row['preferred_language']
                l_cursor.close()
            except Exception as lang_e:
                print(f"Yield language fetch warning: {lang_e}")
            

            conn.close()
            
            if row:
                # Format planting_date as string
                planting_date_str = None
                if row.get('planting_date'):
                    pd = row['planting_date']
                    planting_date_str = pd.isoformat() if hasattr(pd, 'isoformat') else str(pd)
                
                field = {
                    "id": str(row['id']),
                    "name": row['name'],
                    "crop": row['crop_type'],
                    "planting_date": planting_date_str,
                    "variety": row.get('variety'),
                    "fertilizer_history": row.get('fertilizer_history'),
                    "area": float(row.get('size_hectares') or 0)
                }
                print(f"📊 Yield projection for field: {field['name']}, planting_date={field['planting_date']}")
        except Exception as e:
            print(f"DB fetch for yield projection failed: {e}")
            if conn:
                conn.close()
    
    # Fallback to MOCK_FIELDS
    if not field and MOCK_FIELDS:
        for f in MOCK_FIELDS:
            if f["id"] == field_id:
                field = f
                break
            
    if not field:
         raise HTTPException(status_code=404, detail="Field not found")

    # 2. Call AI Tool
    try:
        response = run_generate_yield(
            {
                "crop": field.get("crop"),
                "variety": field.get("variety"),
                "planting_date": field.get("planting_date"),
                "fertilizer_history": field.get("fertilizer_history"),
                "area": field.get("area"),
                "region": "Zimbabwe"
            },
            user_lang
        )
        if response.get("status") == "error":
             raise Exception(response.get("error_message"))
             
        data = response.get("data")
        
        # 3. Save Result to Field (Persistence)
        # This updates the "state" so the dashboard aggregate changes!
        field["projected_yield"] = data.get("projected_yield", 0)
        field["yield_potential"] = data.get("yield_potential", 0)
        field["last_analysis"] = datetime.now().isoformat()

        _cache_set(cache_key, data)
        return data
        
    except Exception as e:
        print(f"Yield Gen Error: {e}")
        # Fallback
        return {
            "current_stage": "Unknown",
            "projected_yield": field.get("area", 10) * 5, 
            "yield_potential": field.get("area", 10) * 8, 
            "next_actions": ["Scout for pests", "Check moisture"]
        }

@app.get("/market/prices")
def get_market_prices(region: str = "Zimbabwe"):
    """
    Returns current market prices for major crops by region.
    In production, this would call a real commodity API.
    """
    # Regional price data (USD per tonne, except where noted)
    # Zimbabwe prices as of Jan 2026 (simulated)
    price_data = {
        "Zimbabwe": {
            "Maize": {"price": 285, "unit": "$/t", "trend": "+1.8%", "last_updated": "2h ago"},
            "Wheat": {"price": 340, "unit": "$/t", "trend": "-0.3%", "last_updated": "2h ago"},
            "Soybean": {"price": 520, "unit": "$/t", "trend": "+2.4%", "last_updated": "2h ago"},
            "Tobacco": {"price": 3.45, "unit": "$/kg", "trend": "+1.2%", "last_updated": "2h ago"},
            "Cotton": {"price": 1.28, "unit": "$/lb", "trend": "-0.8%", "last_updated": "2h ago"},
            "Rice": {"price": 450, "unit": "$/t", "trend": "+0.5%", "last_updated": "2h ago"},
            "Groundnuts": {"price": 680, "unit": "$/t", "trend": "+1.5%", "last_updated": "2h ago"},
            "Sunflower": {"price": 420, "unit": "$/t", "trend": "+0.9%", "last_updated": "2h ago"},
        },
        "South Africa": {
            "Maize": {"price": 295, "unit": "$/t", "trend": "+2.1%", "last_updated": "1h ago"},
            "Wheat": {"price": 350, "unit": "$/t", "trend": "+0.5%", "last_updated": "1h ago"},
            "Soybean": {"price": 535, "unit": "$/t", "trend": "+1.9%", "last_updated": "1h ago"},
        }
    }
    
    regional_prices = price_data.get(region, price_data["Zimbabwe"])
    
    return {
        "region": region,
        "prices": regional_prices,
        "currency": "USD",
        "timestamp": datetime.now().isoformat()
    }

# ========== FIELD ENDPOINTS ==========

@app.post("/router")
def router_endpoint(payload: dict, user_id: str = Depends(verify_token)):
    try:
        return route(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/chat/send")
async def chat_adapter(payload: dict, user_id: str = Depends(verify_token)):
    """
    Handles chat interaction using the AgronomistBrain.
    
    Enhanced with variety-aware context:
    - Fetches full field data including variety and growth stage
    - Uses the same context builder as /chat/v2/send
    - Supports proactive insights from variety characteristics
    """
    try:
        import uuid
        from datetime import datetime
        
        user_msg = payload.get("message", "")
        context = payload.get("context", {})
        # user_id comes from verified JWT token (Depends(verify_token)), not payload
        field_id = context.get("field_id")
        
        # 1. Fetch Context Concurrently
        location = context.get("location", {"lat": -17.82, "lon": 31.05})
        lat = location.get("lat", -17.82)
        lon = location.get("lon", 31.05)

        async def _get_f_ctx():
            if not field_id: return FieldContext()
            try: return await _get_field_context(field_id, user_id)
            except Exception as e:
                print(f"Field context fetch error: {e}")
                recents = get_recent_field_activity(field_id)
                return FieldContext(field_id=field_id, field_name="Selected Field", recent_activities=recents)

        async def _get_w_ctx():
            try: return await get_current_weather(lat, lon)
            except Exception as e:
                print(f"Weather fetch failed: {e}")
                return None

        f_ctx, weather_data = await asyncio.gather(_get_f_ctx(), _get_w_ctx())

        w_ctx = None
        if weather_data:
            w_ctx = WeatherContext(
                current_temp=weather_data.get("temperature"),
                humidity=weather_data.get("humidity"),
                precipitation_prob=0.0,
                wind_speed=weather_data.get("wind_speed"),
                forecast_summary=weather_data.get("weather_description")
            )
        
        # 3. Construct Input
        agent_input = AgentInput(
            user_id=user_id,
            message=user_msg,
            session_id=field_id,
            field_context=f_ctx,
            weather_context=w_ctx,
            language=context.get("language", "en"),
            image_base64=payload.get("image")
        )
        
        # 4. Process with Brain
        brain = get_brain()
        response = await brain.process(agent_input)
        
        # 5. Log User Event
        log_user_event(user_id, "chat_message", "message_sent", {"field_id": field_id})
        
        return {"response": response.text_body}
        
    except Exception as exc:
        print(f"Chat Adapter Error: {exc}")
        import traceback
        traceback.print_exc()
        return {"response": "Sorry, I encountered an error connecting to the AI Agronomist."}

@app.get("/chat/history")
def get_chat_history(limit: int = 50, user_id: str = Depends(verify_token)):
    conn = get_db_connection()
    if not conn:
        return MOCK_CHATS[-limit:]
        
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT role, content, to_char(created_at, 'HH:MI AM') as timestamp 
            FROM chat_logs 
            WHERE user_id = %s
            ORDER BY created_at ASC 
            LIMIT %s
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        history = []
        for row in rows:
            history.append({
                "role": row['role'],
                "content": row['content'],
                "timestamp": row['timestamp']
            })
            
        return history
    except Exception as e:
        print(f"Chat History Error: {e}")
        return []


@app.post("/proactive")
def proactive_endpoint(payload: dict, user_id: str = Depends(verify_token)):
    seeds = payload.get("seeds") or []
    results = []
    for seed in seeds:
        try:
            results.append(route(seed))
        except Exception as exc:
            results.append({"error": str(exc), "seed": seed})
    return {"results": results}


# ========== AI BRAIN ENHANCED ENDPOINTS ==========

@app.post("/chat/v2/send")
async def chat_v2_send(payload: dict, user_id: str = Depends(verify_token)):
    """
    Enhanced AI Chat using the AI Brain layer.
    Features:
    - Intelligent context management
    - Multi-LLM routing
    - Conversation memory
    - Vision AI support (send image in payload)
    - Proactive insights
    
    Payload:
    {
        "message": "User's question",
        "image": "base64 image data (optional)",
        "field_id": "field UUID (optional)",
        "session_id": "session UUID (optional)",
        "language": "en" (optional)
    }
    """
    try:
        brain = get_brain()
        
        user_msg = payload.get("message", "")
        image_data = payload.get("image")
        field_id = payload.get("field_id")
        session_id = payload.get("session_id")
        language = payload.get("language") or get_user_language(user_id) or "en"
        
        print(f"🧠 AI Brain Processing: user={user_id[:8]}..., field={field_id}, has_image={bool(image_data)}")
        
        # Parallelize data loading
        def _fetch_history_sync():
            try:
                conn = get_db_connection()
                if not conn: return []
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT role, content, created_at 
                    FROM chat_logs 
                    WHERE user_id = %s AND (field_context_id = %s OR field_context_id IS NULL)
                    ORDER BY created_at DESC 
                    LIMIT 10
                """, (user_id, field_id))
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                return [
                    ConversationMessage(
                        role=r["role"], 
                        content=r["content"],
                        timestamp=r["created_at"].isoformat() if r.get("created_at") else None
                    ) 
                    for r in reversed(rows)
                ]
            except Exception as e:
                print(f"History fetch failed: {e}")
                return []

        async def _get_f_ctx():
            if not field_id: return None
            try: return await _get_field_context(field_id, user_id)
            except Exception: return None

        async def _get_coords_weather():
            try:
                lat, lon = await resolve_coordinates(field_id, None, None, user_id)
                # Ensure get_current_weather works properly
                return await get_current_weather(lat, lon)
            except Exception as e:
                print(f"Weather context fetch failed: {e}")
                return None
                
        field_context, weather_data, chat_history = await asyncio.gather(
            _get_f_ctx(),
            _get_coords_weather(),
            run_in_threadpool(_fetch_history_sync)
        )
        
        weather_context = None
        if weather_data:
            weather_context = WeatherContext(
                current_temp=weather_data.get("temperature"),
                humidity=weather_data.get("humidity"),
                precipitation_prob=weather_data.get("precipitation", 0.0),
                wind_speed=weather_data.get("wind_speed"),
                forecast_summary=weather_data.get("weather_description"),
                alerts=[]
            )

        # Create agent input
        agent_input = AgentInput(
            user_id=user_id,
            message=user_msg,
            session_id=session_id,
            image_base64=image_data,
            field_context=field_context,
            weather_context=weather_context,
            language=language,
            chat_history=chat_history
        )
        
        # Process with AI Brain
        response = await brain.process(agent_input)
        
        # Persist to database
        def _persist_sync():
            conn = get_db_connection()
            if not conn:
                return
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                # One round-trip: insert both rows
                cursor.execute("""
                    INSERT INTO chat_logs (user_id, role, content, field_context_id)
                    VALUES
                        (%s, 'user', %s, %s),
                        (%s, 'ai', %s, %s)
                """, (user_id, user_msg, field_id, user_id, response.text_body, field_id))
                conn.commit()
                cursor.close()
                conn.close()
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass

        await run_in_threadpool(_persist_sync)
        
        return {
            "response": response.text_body,
            "actions": response.actions,
            "confidence_score": response.confidence_score,
            "detected_intent": response.detected_intent,
            "proactive_insights": response.proactive_insights,
            "follow_up_questions": response.follow_up_questions
        }
        
    except Exception as exc:
        print(f"🧠 AI Brain Error: {type(exc).__name__}: {exc}")
        return {
            "response": "I'm having trouble processing your request right now. Please try again.",
            "actions": ["Try again"],
            "confidence_score": 0.0,
            "detected_intent": "error",
            "error": str(exc)
        }


@app.post("/chat/v2/stream")
async def chat_v2_stream(payload: dict, user_id: str = Depends(verify_token)):
    """
    SSE streaming version of the AI chat endpoint.
    Sends partial tokens as they arrive from the LLM so the frontend
    can render them incrementally ("typing" effect).

    SSE event types:
      - data: {"token": "..."} – a chunk of the AI response text
      - data: {"done": true, "detected_intent": "..."}  – final metadata
      - data: {"error": "..."}  – on failure
    """
    brain = get_brain()

    user_msg = payload.get("message", "")
    field_id = payload.get("field_id")
    session_id = payload.get("session_id")
    language = payload.get("language", "en")

    # ── Reuse the same parallel context fetching as /chat/v2/send ──
    def _fetch_history_sync():
        try:
            conn = get_db_connection()
            if not conn:
                return []
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT role, content, created_at
                FROM chat_logs
                WHERE user_id = %s AND (field_context_id = %s OR field_context_id IS NULL)
                ORDER BY created_at DESC LIMIT 10
            """, (user_id, field_id))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return [
                ConversationMessage(
                    role=r["role"],
                    content=r["content"],
                    timestamp=r["created_at"].isoformat() if r.get("created_at") else None
                )
                for r in reversed(rows)
            ]
        except Exception as e:
            print(f"Stream history fetch failed: {e}")
            return []

    async def _get_f_ctx():
        if not field_id:
            return None
        try:
            return await _get_field_context(field_id, user_id)
        except Exception:
            return None

    async def _get_coords_weather():
        try:
            lat, lon = await resolve_coordinates(field_id, None, None, user_id)
            return await get_current_weather(lat, lon)
        except Exception:
            return None

    field_context, weather_data, chat_history = await asyncio.gather(
        _get_f_ctx(),
        _get_coords_weather(),
        run_in_threadpool(_fetch_history_sync),
    )

    weather_context = None
    if weather_data:
        weather_context = WeatherContext(
            current_temp=weather_data.get("temperature"),
            humidity=weather_data.get("humidity"),
            precipitation_prob=weather_data.get("precipitation", 0.0),
            wind_speed=weather_data.get("wind_speed"),
            forecast_summary=weather_data.get("weather_description"),
            alerts=[],
        )

    # ── Build the same context prompt and messages the brain uses ──
    context_prompt = await brain._build_context_prompt(
        field_context, weather_context, language, user_query=user_msg
    )
    agent_input = AgentInput(
        user_id=user_id,
        message=user_msg,
        session_id=session_id,
        field_context=field_context,
        weather_context=weather_context,
        language=language,
        chat_history=chat_history,
    )
    messages = brain._build_messages(agent_input, context_prompt)
    _, model = brain.llm_router.select_model()
    intent = brain.intent_classifier.classify(user_msg)

    # ── SSE generator ──
    async def _event_stream():
        full_text = ""
        try:
            async for token in brain.llm_router.generate_stream(
                messages=messages, model=model, max_tokens=1000, temperature=0.3
            ):
                full_text += token
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Final event with metadata
            yield f"data: {json.dumps({'done': True, 'detected_intent': intent.value})}\n\n"

            # Persist both messages in one round-trip (fire-and-forget in thread)
            def _persist():
                conn = get_db_connection()
                if not conn:
                    return
                try:
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute(
                        """INSERT INTO chat_logs (user_id, role, content, field_context_id)
                           VALUES (%s,'user',%s,%s),(%s,'ai',%s,%s)""",
                        (user_id, user_msg, field_id, user_id, full_text, field_id),
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception:
                    try:
                        conn.close()
                    except Exception:
                        pass

            await run_in_threadpool(_persist)

        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


# _get_field_context and _get_health_status imported from deps.py


@app.post("/vision/analyze")
async def vision_analyze_endpoint(payload: dict, user_id: str = Depends(verify_token)):
    """
    Analyze a crop image for diseases, pests, and nutrient deficiencies.
    Uses GPT-4 Vision for state-of-the-art analysis.
    
    Payload:
    {
        "image": "base64 image data (required)",
        "crop_type": "maize" (optional, helps with accuracy),
        "additional_context": "Any farmer observations" (optional)
    }
    """
    try:
        image_data = payload.get("image")
        if not image_data:
            raise HTTPException(status_code=400, detail="Image data is required")
        
        crop_type = payload.get("crop_type")
        additional_context = payload.get("additional_context")
        
        print(f"📸 Vision Analysis: crop={crop_type}, user={user_id[:8]}...")
        # Analyze image
        analyzer = get_vision_analyzer()
        result = await analyzer.analyze_image(
            image_base64=image_data,
            crop_type=crop_type,
            additional_context=additional_context
        )
        
        return {
            "analysis": result,
            "timestamp": datetime.now().isoformat(),
            "model": "gpt-4o-vision"
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        print(f"📸 Vision Analysis Error: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(exc)}")


@app.get("/ai/capabilities")
async def get_ai_capabilities():
    """
    Returns the current AI capabilities and feature flags.
    Useful for frontend to know what features are available.
    """
    brain = get_brain()
    
    return {
        "version": "2.0",
        "features": {
            "conversation_memory": True,
            "vision_analysis": bool(brain.llm_router.openai_client),
            "multi_llm_routing": True,
            "intent_classification": True,
            "field_context_aware": True,
            "weather_context_aware": True,
            "proactive_insights": True
        },
        "available_intents": [
            "weather_check", "disease_id", "pest_alert", "market_price",
            "yield_projection", "spray_window", "field_analysis", 
            "planning", "general_advice"
        ],
        "supported_languages": ["en", "sn", "nd"],  # English, Shona, Ndebele
        "max_history_turns": 20
    }


@app.get("/ai/insights")
async def get_ai_insights(user_id: str = Depends(verify_token)):
    """
    Get AI-generated insights, risks, and recommended actions for the user's farm.

    Enhanced with proactive_intelligence integration:
    - Uses variety-specific disease risk assessment
    - Calculates growth stage alerts
    - Generates variety-aware recommendations
    """
    cache_key = f"insights:{user_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    import random
    from datetime import datetime, date
    from proactive_intelligence import (
        calculate_growth_stage,
        assess_disease_risk,
        get_variety_info,
        generate_harvest_alert
    )

    current_time = datetime.now()
    current_date = current_time.date()
    time_str = current_time.strftime("%I:%M %p")

    # ------------------------------------------------------------------ #
    # Parallel I/O: fetch fields, today's tasks, and weather concurrently #
    # ------------------------------------------------------------------ #

    def _fetch_fields():
        conn = get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT id, name, crop_type, variety, planting_date,
                       polygon_coordinates, health_score,
                       transplant_date, is_transplanted
                FROM fields WHERE user_id = %s
            """, (user_id,))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"⚠️ Error fetching fields for insights: {e}")
            return []
        finally:
            conn.close()

    def _fetch_tasks():
        conn = get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT t.*, f.name as field_name
                FROM farm_tasks t
                LEFT JOIN fields f ON t.field_id = f.id
                WHERE t.user_id = %s AND t.task_date = %s
            """, (user_id, current_date))
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"⚠️ Error fetching existing tasks: {e}")
            return []
        finally:
            conn.close()

    def _fetch_weather():
        try:
            _weather_api_key = os.getenv("WEATHER_API_KEY")
            if _weather_api_key and "your_" not in _weather_api_key:
                # Default to Harare, Zimbabwe; field-specific coords not available yet
                return fetch_weather_data(-17.82, 31.05, _weather_api_key)
        except Exception as e:
            print(f"Weather fetch failed: {e}")
        return None

    fields, existing_tasks, weather_data = await asyncio.gather(
        run_in_threadpool(_fetch_fields),
        run_in_threadpool(_fetch_tasks),
        run_in_threadpool(_fetch_weather),
    )

    # Generate context-aware insights
    insights = []
    risks = []
    actions = []

    
    if len(fields) == 0:
        # No fields - suggest getting started
        insights.append({
            "id": "no-fields-1",
            "type": "action",
            "title": "Get Started with KurimaSense",
            "message": "Add your first field to start receiving AI-powered insights and recommendations.",
            "severity": "low",
            "timestamp": time_str,
            "actionLabel": "Add Field"
        })
    else:
        # WEATHER-BASED LOGIC (Real Data)
        if weather_data:
            precip_chance = weather_data.get('precip_chance_24h', 0)
            humidity = weather_data.get('humidity', 50)
            temp = weather_data.get('current_temp', 25)
            summary = weather_data.get('forecast_summary', '').lower()
            
            # Simple Agronomic Rules
            if precip_chance < 0.2 and 'rain' not in summary:
                 insights.append({
                    "id": f"weather-spray-{current_time.timestamp()}",
                    "type": "weather",
                    "title": "Optimal Spray Window",
                    "message": f"Low rain chance ({int(precip_chance*100)}%) and {temp}°C. Good conditions for foliar application.",
                    "severity": "medium",
                    "timestamp": time_str,
                    "actionLabel": "Plan Spray"
                })
            elif precip_chance > 0.6 or 'rain' in summary:
                insights.append({
                    "id": f"weather-rain-{current_time.timestamp()}",
                    "type": "weather", 
                    "title": "Rain Expected",
                    "message": f"High chance of rain ({int(precip_chance*100)}%). Delay fertilizer application to prevent runoff.",
                    "severity": "high",
                    "timestamp": time_str
                })
                
            # Pest/Disease Rules (simplified)
            if humidity > 80 and temp > 20: # Warm & Humid = Fungal Risk
                risks.append({
                    "id": "risk-fungal-real",
                    "type": "disease",
                    "name": "Gray Leaf Spot Risk",
                    "risk": 85,
                    "trend": "rising",
                    "fieldName": "All Fields"
                })
                insights.append({
                     "id": "alert-fungal",
                     "type": "disease",
                     "title": "High Fungal Disease Risk",
                     "message": "High humidity (>80%) creates favorable conditions for Gray Leaf Spot and Rust.",
                     "severity": "high",
                     "actionLabel": "Scout Now"
                })
            
            if temp > 30 and precip_chance < 0.1: # Hot & Dry = Pest Risk (Timeline)
                 risks.append({
                    "id": "risk-pest-real",
                    "type": "pest",
                    "name": "Fall Armyworm Alert",
                    "risk": 75,
                    "trend": "rising",
                    "fieldName": "Maize Fields"
                })
        else:
            # Fallback to simulated weather insight if API fails
            insights.append({
                "id": f"weather-sim-{current_time.timestamp()}",
                "type": "weather",
                "title": "Weather Data Unavailable",
                "message": "Could not fetch real-time weather. Check internet connection.",
                "severity": "low",
                "timestamp": time_str
            })

        
        # Field-specific insights using proactive_intelligence
        for field in fields[:3]:  # Limit to first 3 fields
            health_score = field.get('health_score') or random.randint(60, 95)
            crop = field.get('crop_type') or 'Maize'
            field_name = field.get('name') or 'Unknown Field'
            variety_name = field.get('variety')
            planting_date = field.get('planting_date')
            transplant_date = field.get('transplant_date')
            is_transplanted = field.get('is_transplanted', False)
            
            # ===== VARIETY-AWARE PROACTIVE INTELLIGENCE =====
            if variety_name and planting_date:
                try:
                    # Get variety info for disease risk assessment
                    variety_info = get_variety_info(variety_name)
                    
                    # Calculate growth stage
                    growth_stage = calculate_growth_stage(
                        planting_date=planting_date if isinstance(planting_date, date) else date.fromisoformat(str(planting_date)[:10]),
                        variety_name=variety_name,
                        crop_type=crop,
                        transplant_date=transplant_date,
                        is_transplanted=is_transplanted
                    )
                    
                    # Generate growth stage insight
                    insights.append({
                        "id": f"stage-{field['id']}",
                        "type": "growth",
                        "title": f"{field_name}: {growth_stage.stage_name}",
                        "message": f"{variety_name} is {growth_stage.days_since_planting} days old ({growth_stage.progress_percent:.0f}% complete). {growth_stage.description}",
                        "severity": "low" if growth_stage.days_to_harvest > 14 else "medium",
                        "fieldName": field_name,
                        "timestamp": time_str,
                        "actionLabel": "View Field"
                    })
                    
                    # Add top activity as action
                    if growth_stage.key_activities:
                        actions.append({
                            "id": f"action-stage-{field['id']}",
                            "title": growth_stage.key_activities[0],
                            "description": f"{variety_name} at {growth_stage.stage_name} requires attention.",
                            "priority": "high" if growth_stage.days_to_harvest < 14 else "normal",
                            "type": "scout",
                            "fieldName": field_name,
                            "dueDate": "This Week",
                            "estimatedTime": "30 min"
                        })
                    
                    # Generate harvest alerts
                    harvest_alert = generate_harvest_alert(growth_stage, variety_info, field_name)
                    if harvest_alert:
                        severity_map = {"critical": "high", "warning": "medium", "info": "low"}
                        insights.append({
                            "id": harvest_alert.id,
                            "type": "harvest",
                            "title": harvest_alert.title,
                            "message": harvest_alert.message,
                            "severity": severity_map.get(harvest_alert.severity, "low"),
                            "fieldName": field_name,
                            "timestamp": time_str,
                            "actionLabel": "Plan Harvest" if harvest_alert.action_required else None
                        })
                    
                    # Disease risk assessment using variety characteristics + weather
                    if weather_data and variety_info:
                        disease_alerts = assess_disease_risk(
                            variety_info=variety_info,
                            weather_data={
                                "humidity": weather_data.get('humidity', 50),
                                "temperature": weather_data.get('current_temp', 25),
                                "precipitation": weather_data.get('precipitation', 0)
                            },
                            growth_stage=growth_stage
                        )
                        
                        for alert in disease_alerts:
                            if alert.severity in ['critical', 'warning']:
                                risks.append({
                                    "id": alert.id,
                                    "type": "disease",
                                    "name": alert.title.replace("⚠️ ", "").replace("🟠 ", ""),
                                    "risk": 85 if alert.severity == "critical" else 65,
                                    "trend": "rising",
                                    "fieldName": field_name
                                })
                                
                            insights.append({
                                "id": alert.id,
                                "type": alert.alert_type,
                                "title": alert.title,
                                "message": alert.message,
                                "severity": "high" if alert.severity == "critical" else "medium" if alert.severity == "warning" else "low",
                                "fieldName": field_name,
                                "timestamp": time_str,
                                "actionLabel": "Scout Now" if alert.action_required else None
                            })
                            
                except Exception as pi_error:
                    print(f"⚠️ Proactive intelligence error for {field_name}: {pi_error}")
            
            # ===== FALLBACK: Health-based insights =====
            if health_score < 70:
                insights.append({
                    "id": f"health-{field['id']}",
                    "type": "health",
                    "title": f"Health Alert: {field_name}",
                    "message": f"NDVI readings indicate potential stress in {field_name}. Consider scouting for pest or disease pressure.",
                    "severity": "high",
                    "fieldName": field_name,
                    "timestamp": time_str,
                    "actionLabel": "Scout Now"
                })
                
            # Market opportunity (Mock for now)
            if crop.lower() == 'maize':
                insights.append({
                    "id": f"market-{field['id']}",
                    "type": "market",
                    "title": "Maize Prices Stable",
                    "message": f"Regional maize prices holding at $240/ton. Monitor for post-harvest dip.",
                    "severity": "low",
                    "fieldName": field_name,
                    "timestamp": time_str
                })
        
        # Default Risks if no weather data generated them
        if not risks:
             risks = [
                {
                    "id": "risk-pest-sim",
                    "type": "pest",
                    "name": "Fall Armyworm",
                    "risk": random.randint(20, 45),
                    "trend": "stable",
                },
                {
                    "id": "risk-weather-sim",
                    "type": "weather",
                    "name": "Drought Stress",
                    "risk": random.randint(10, 40),
                    "trend": "falling"
                }
            ]
        
        # PREPARE ACTIONS
        if existing_tasks:
            # Format existing tasks to match the actions structure
            for task in existing_tasks:
                actions.append({
                    "id": str(task['id']),
                    "title": task['title'],
                    "description": task['description'],
                    "priority": task['priority'],
                    "type": task['activity_type'],
                    "fieldName": task.get('field_name'), # Using the joined field_name
                    "completed": task['completed'],
                    "dueDate": "Today",
                    "estimatedTime": task.get('estimated_time', '30 min')
                })
        else:
            # Generate dynamic actions using AgronomistBrain if none exist
            brain = AgronomistBrain()
            
            # Prepare context for the brain
            # Typically we'd pass real weather and field data here
            # For now, we'll generate variety-aware suggestions based on the user's primary field
            primary_field = fields[0] if fields else None
            
            generated_actions = []
            
            if primary_field:
                # Mock variety-aware suggestions until we fully wire up the brain's internal logic
                # in this specific path
                variety_name = primary_field.get('variety', 'SC 727')
                generated_actions = [
                    {
                        "title": f"Scout {variety_name} for GLS",
                        "description": f"Check for Grey Leaf Spot symptoms, common in {variety_name} at this stage.",
                        "priority": "high",
                        "type": "scout",
                        "field_id": primary_field['id'],
                    },
                    {
                        "title": "Monitor Soil Moisture",
                        "description": "Variety sensitive to moisture stress during vegetative growth.",
                        "priority": "normal",
                        "type": "irrigate",
                        "field_id": primary_field['id'],
                    }
                ]
            else:
                # Fallback generic actions
                generated_actions = [
                    {
                        "title": "Check Weather Forecast",
                        "description": "Plan your week's activities based on upcoming rainfall.",
                        "priority": "normal",
                        "type": "general",
                    }
                ]
            
            # Persist generated actions to DB
            _persist_conn = get_db_connection()
            if _persist_conn:
                try:
                    cursor = _persist_conn.cursor(cursor_factory=RealDictCursor)
                    for ga in generated_actions:
                        cursor.execute("""
                            INSERT INTO farm_tasks (user_id, field_id, title, description, activity_type, priority, is_ai_generated)
                            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                            RETURNING *
                        """, (user_id, ga.get('field_id'), ga['title'], ga['description'], ga['type'], ga['priority']))
                        new_task = cursor.fetchone()
                        
                        # Fetch the field name for the newly created task
                        field_name = primary_field['name'] if primary_field and ga.get('field_id') == primary_field['id'] else None
                        
                        actions.append({
                            "id": str(new_task['id']),
                            "title": new_task['title'],
                            "description": new_task['description'],
                            "priority": new_task['priority'],
                            "type": new_task['activity_type'],
                            "fieldName": field_name,
                            "completed": False,
                            "dueDate": "Today"
                        })
                    _persist_conn.commit()
                    cursor.close()
                except Exception as e:
                    print(f"⚠️ Error persisting generated tasks: {e}")
                finally:
                    _persist_conn.close()
    
    result = {
        "insights": insights[:5],
        "risks": risks,
        "actions": actions,
        "generated_at": current_time.isoformat(),
        "field_count": len(fields)
    }
    _cache_set(cache_key, result)
    return result

@app.get("/ai/tasks")
async def get_farm_tasks(
    field_id: Optional[str] = None, 
    date: Optional[str] = None,
    user_id: str = Depends(verify_token)
):
    """Fetch tasks for the user, optionally filtered by field or date."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = "SELECT * FROM farm_tasks WHERE user_id = %s"
        params = [user_id]
        
        if field_id:
            query += " AND field_id = %s"
            params.append(field_id)
        
        if date:
            query += " AND task_date = %s"
            params.append(date)
        else:
            # Default to today if no date provided
            query += " AND task_date = CURRENT_DATE"
            
        query += " ORDER BY completed ASC, priority DESC, created_at DESC"
        
        cursor.execute(query, tuple(params))
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert UUID to string for JSON serialization
        for t in tasks:
            t['id'] = str(t['id'])
            if t.get('field_id'): t['field_id'] = str(t['field_id'])
            
        return tasks
    except Exception as e:
        if conn: conn.close()
        print(f"Error fetching tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/ai/tasks/{task_id}")
async def update_farm_task(
    task_id: str,
    updates: dict,
    user_id: str = Depends(verify_token)
):
    """Update a task's status or details."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        allowed_fields = ['completed', 'title', 'description', 'priority', 'activity_type']
        update_parts = []
        params = []
        
        for key, value in updates.items():
            if key in allowed_fields:
                update_parts.append(f"{key} = %s")
                params.append(value)
        
        if 'completed' in updates:
            if updates['completed']:
                update_parts.append("completed_at = NOW()")
            else:
                update_parts.append("completed_at = NULL")
            
        if not update_parts:
            raise HTTPException(status_code=400, detail="No valid update fields provided")
        
        # Adding explicit cast to UUID to avoid potential comparison issues with string
        query = f"UPDATE farm_tasks SET {', '.join(update_parts)} WHERE id = %s::uuid AND user_id = %s RETURNING *"
        params.extend([task_id, user_id])
        
        cursor.execute(query, tuple(params))
        updated_task = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if not updated_task:
            raise HTTPException(status_code=404, detail="Task not found or access denied")
        
        updated_task['id'] = str(updated_task['id'])
        if updated_task.get('field_id'): updated_task['field_id'] = str(updated_task['field_id'])
            
        return updated_task
    except Exception as e:
        if conn: conn.close()
        print(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/tasks")
async def create_farm_task(
    task: dict,
    user_id: str = Depends(verify_token)
):
    """Create a new task manually."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            INSERT INTO farm_tasks (user_id, field_id, title, description, activity_type, priority, task_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            user_id, 
            task.get('field_id'), 
            task['title'], 
            task.get('description'), 
            task['activity_type'], 
            task['priority'],
            task.get('task_date', datetime.now().date())
        ))
        new_task = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        new_task['id'] = str(new_task['id'])
        if new_task.get('field_id'): new_task['field_id'] = str(new_task['field_id'])
            
        return new_task
    except Exception as e:
        if conn: conn.close()
        print(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== CLIMATE INTELLIGENCE ENDPOINTS ==========

@app.get("/climate/current")
async def get_current_weather(lat: float = None, lon: float = None, field_id: str = None, user_id: str = Depends(verify_token)):
    """
    Get current weather conditions.
    Priority: field_id coordinates > explicit lat/lon > user default location
    """
    # Resolve coordinates
    resolved_lat, resolved_lon = await resolve_coordinates(field_id, lat, lon, user_id)
    
    try:
        data = await climate_service.get_current_weather(resolved_lat, resolved_lon)
        # Log usage (only if user triggered explicitly or we interpret it as such)
        if field_id or user_id: 
             log_user_event(user_id, "feature_usage", "weather_check", {"location": {"lat": resolved_lat, "lon": resolved_lon}})
        return data
    except Exception as e:
        print(f"Climate Current Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather data: {str(e)}")


@app.get("/climate/forecast")
async def get_forecast(lat: float = None, lon: float = None, field_id: str = None, days: int = 7, user_id: str = Depends(verify_token)):
    """
    Get 7-day forecast with hourly breakdown for the next 48 hours.
    """
    resolved_lat, resolved_lon = await resolve_coordinates(field_id, lat, lon, user_id)
    
    try:
        daily = await climate_service.get_daily_forecast(resolved_lat, resolved_lon, days=days)
        hourly = await climate_service.get_hourly_forecast(resolved_lat, resolved_lon, hours=48)
        
        return {
            "location": {"lat": resolved_lat, "lon": resolved_lon},
            "daily": daily.get("daily", []),
            "hourly": hourly.get("hourly", []),
            "timezone": daily.get("timezone")
        }
    except Exception as e:
        print(f"Climate Forecast Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch forecast: {str(e)}")


@app.get("/climate/agricultural")
async def get_agricultural_metrics(
    lat: float = None, 
    lon: float = None, 
    field_id: str = None,
    base_temp: float = 10.0,
    start_date: str = None,
    user_id: str = Depends(verify_token)
):
    """
    Get agricultural-specific metrics: GDD, evapotranspiration, soil moisture.
    """
    resolved_lat, resolved_lon = await resolve_coordinates(field_id, lat, lon, user_id)
    
    # [NEW] Resolve variety for specific GDD calculation
    variety = None
    if field_id:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT variety FROM fields WHERE id = %s", (field_id,))
                row = cursor.fetchone()
                if row:
                    variety = row['variety']
                cursor.close()
                conn.close()
            except Exception:
                pass
    
    try:
        # Fetch all agricultural metrics concurrently
        import asyncio
        
        
        metrics, gdd = await asyncio.gather(
            climate_service.get_agricultural_metrics(resolved_lat, resolved_lon),
            climate_service.calculate_gdd(
                resolved_lat, 
                resolved_lon, 
                base_temp, 
                start_date,
                variety=variety
            ),
            return_exceptions=True
        )
        
        # Handle any exceptions
        if isinstance(metrics, Exception):
            metrics = {}
        if isinstance(gdd, Exception):
            gdd = {}
        
        return {
            "location": {"lat": resolved_lat, "lon": resolved_lon},
            "soil": metrics.get("soil_temperature", {}),
            "moisture": metrics.get("soil_moisture", {}),
            "evapotranspiration": metrics.get("evapotranspiration", {}),
            "water_balance": metrics.get("water_balance", {}),
            "growing_degree_days": gdd
        }
    except Exception as e:
        print(f"Agricultural Metrics Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch agricultural metrics: {str(e)}")


@app.get("/climate/alerts")
async def get_weather_alerts(lat: float = None, lon: float = None, field_id: str = None, user_id: str = Depends(verify_token)):
    """
    Get weather alerts and warnings for the next 7 days.
    """
    resolved_lat, resolved_lon = await resolve_coordinates(field_id, lat, lon, user_id)
    
    try:
        data = await climate_service.get_weather_alerts(resolved_lat, resolved_lon)
        return data
    except Exception as e:
        print(f"Weather Alerts Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")


@app.get("/climate/spray-window")
async def get_spray_window(lat: float = None, lon: float = None, field_id: str = None, hours: int = 72, user_id: str = Depends(verify_token)):
    """
    Calculate optimal spray windows based on weather conditions.
    """
    resolved_lat, resolved_lon = await resolve_coordinates(field_id, lat, lon, user_id)
    
    try:
        data = await climate_service.get_spray_window(resolved_lat, resolved_lon, hours=hours)
        return data
    except Exception as e:
        print(f"Spray Window Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate spray windows: {str(e)}")


@app.get("/climate/historical")
async def get_historical_comparison(lat: float = None, lon: float = None, field_id: str = None, user_id: str = Depends(verify_token)):
    """
    Compare current weather with historical averages for the same period.
    """
    resolved_lat, resolved_lon = await resolve_coordinates(field_id, lat, lon, user_id)
    
    try:
        data = await climate_service.get_historical_comparison(resolved_lat, resolved_lon)
        return data
    except Exception as e:
        print(f"Historical Comparison Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch historical data: {str(e)}")


@app.get("/climate/full")
async def get_full_climate_data(lat: float = None, lon: float = None, field_id: str = None, user_id: str = Depends(verify_token)):
    """
    Get comprehensive climate data in a single call for the dashboard.
    """
    resolved_lat, resolved_lon = await resolve_coordinates(field_id, lat, lon, user_id)
    
    try:
        data = await climate_service.get_full_climate_data(resolved_lat, resolved_lon)
        return data
    except Exception as e:
        print(f"Full Climate Data Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch climate data: {str(e)}")


@app.get("/crops/{crop_name}/varieties")
async def get_crop_varieties(crop_name: str, user_id: str = Depends(verify_token)):
    """
    Get available varieties for a specific crop.
    Returns variety details including maturity, yield potential, and characteristics.
    """
    print(f"📋 Fetching varieties for crop: {crop_name}")
    
    conn = get_db_connection()
    if not conn:
        print(f"⚠️ No database connection for varieties lookup")
        # Return empty list with proper structure instead of error
        return []
        
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                variety_name, 
                breeder, 
                days_to_maturity, 
                yield_potential_low,
                yield_potential_high,
                description,
                characteristics
            FROM crop_varieties 
            WHERE crop_name ILIKE %s
            ORDER BY variety_name ASC
        """, (crop_name,))
        
        varieties = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"✅ Found {len(varieties)} varieties for {crop_name}")
        return varieties
        
    except Exception as e:
        print(f"❌ Varieties Fetch Error for {crop_name}: {e}")
        import traceback
        traceback.print_exc()
        if conn: 
            try:
                conn.close()
            except:
                pass
        # Return empty list on error instead of raising exception
        return []


@app.get("/crops")
async def list_crops(user_id: str = Depends(verify_token)):
    """
    Get list of all available crops with variety counts.
    """
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                crop_name,
                COUNT(*) as variety_count,
                MIN(days_to_maturity) as min_maturity,
                MAX(days_to_maturity) as max_maturity
            FROM crop_varieties 
            GROUP BY crop_name
            ORDER BY crop_name ASC
        """)
        
        crops = cursor.fetchall()
        cursor.close()
        conn.close()
        return crops
        
    except Exception as e:
        print(f"❌ Crops List Error: {e}")
        if conn: conn.close()
        return []


# ========== PROACTIVE INTELLIGENCE ENDPOINTS ==========

@app.get("/ai/proactive-alerts/{field_id}")
async def get_field_proactive_alerts(field_id: str, user_id: str = Depends(verify_token)):
    """
    Get variety-aware proactive alerts for a specific field.
    
    Returns:
    - Growth stage information with key activities
    - Disease risk alerts based on variety resistance + weather
    - Harvest countdown notifications
    - Variety-specific recommendations
    """
    print(f"🧠 Generating proactive alerts for field: {field_id}")
    
    # 1. Fetch field data
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection unavailable")
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                f.id, f.name, f.crop_type, f.planting_date, f.variety,
                f.polygon_coordinates, f.health_score,
                f.transplant_date, f.is_transplanted
            FROM fields f
            WHERE f.id = %s::uuid AND f.user_id = %s::uuid
        """, (field_id, user_id))
        
        field = cursor.fetchone()
        cursor.close()
        
        if not field:
            conn.close()
            raise HTTPException(status_code=404, detail="Field not found")
        
        # Check required fields
        if not field.get('planting_date'):
            conn.close()
            return {
                "field_id": field_id,
                "field_name": field.get('name'),
                "error": "missing_planting_date",
                "message": "Planting date required for growth stage tracking. Please update field details.",
                "alerts": [{
                    "id": "setup-required",
                    "type": "setup",
                    "severity": "warning",
                    "title": "⚙️ Complete Field Setup",
                    "message": "Add planting date to enable growth stage tracking and proactive alerts.",
                    "action_required": True,
                    "recommended_actions": ["Update field with planting date", "Add variety for tailored advice"]
                }]
            }
        
        # 2. Fetch weather data for the field location
        weather_data = None
        try:
            coords = field.get('polygon_coordinates', [])
            if coords and len(coords) > 0:
                lat = sum(p.get('lat', -17.82) for p in coords) / len(coords)
                lon = sum(p.get('lon', 31.05) for p in coords) / len(coords)
            else:
                lat, lon = -17.82, 31.05  # Default to Harare
            
            current_weather = await climate_service.get_current_weather(lat, lon)
            if current_weather:
                weather_data = {
                    "temperature": current_weather.get("temperature"),
                    "humidity": current_weather.get("humidity"),
                    "precipitation": current_weather.get("precipitation", 0),
                    "wind_speed": current_weather.get("wind_speed")
                }
        except Exception as e:
            print(f"Weather fetch for proactive alerts failed: {e}")
        
        conn.close()
        
        # 3. Generate proactive alerts using the intelligence service
        from datetime import date as date_type
        
        # Parse planting_date
        planting_date = field['planting_date']
        if hasattr(planting_date, 'date'):
            planting_date = planting_date.date()
        elif isinstance(planting_date, str):
            planting_date = datetime.strptime(planting_date, '%Y-%m-%d').date()
        
        # Parse transplant_date (for transplanted crops)
        transplant_date = field.get('transplant_date')
        if transplant_date:
            if hasattr(transplant_date, 'date'):
                transplant_date = transplant_date.date()
            elif isinstance(transplant_date, str):
                transplant_date = datetime.strptime(transplant_date, '%Y-%m-%d').date()
        
        is_transplanted = field.get('is_transplanted', False)
        
        alerts_data = await generate_proactive_alerts(
            field_id=str(field['id']),
            field_name=field.get('name', 'Field'),
            crop_type=field.get('crop_type', 'Maize'),
            variety_name=field.get('variety', 'Unknown'),
            planting_date=planting_date,
            weather_data=weather_data,
            transplant_date=transplant_date,
            is_transplanted=is_transplanted
        )
        
        # 4. Augment with "Real AI" Priorities & Risks
        # The generate_proactive_alerts provides the deterministic stage calculation.
        # Now we ask the AgronomistBrain to provide specific advice for this context.
        try:
            brain = get_brain()
            
            # We need variety info for context. generate_proactive_alerts fetched it but didn't return full details.
            # We fetch it again here for the AI context.
            from proactive_intelligence import get_variety_info
            variety_full_info = get_variety_info(field.get('variety', 'Unknown'))
            
            ai_context = {
                "crop_type": field.get('crop_type', 'Maize'),
                "variety_name": field.get('variety', 'Unknown'),
                "stage_name": alerts_data['growth_stage']['name'],
                "days_since_planting": alerts_data['growth_stage']['days_since_planting'],
                "progress_percent": alerts_data['growth_stage']['progress_percent'],
                "location": {"lat": lat, "lon": lon},
                "weather": weather_data,
                "variety_info": variety_full_info
            }
            
            print(f"🧠 Generating AI Daily Priorities for {field.get('variety')}...")
            ai_insights = await brain.generate_ai_priorities_and_risks(ai_context)
            
            # Merge AI Actions into growth stage activities
            ai_actions = ai_insights.get('actions', [])
            if ai_actions:
                # Replace empty placeholder with high-quality AI advice
                alerts_data['growth_stage']['key_activities'] = [
                    f"➤ {a.get('title')}: {a.get('description')}" for a in ai_actions
                ]
            
            # Merge AI Risks into Alerts list
            ai_risks = ai_insights.get('risks', [])
            for risk in ai_risks:
                risk_score = risk.get('risk', 0)
                if risk_score > 25: # Filter out low noise
                    trend_icon = "↗️" if risk.get('trend') == 'rising' else "↘️" if risk.get('trend') == 'falling' else "➡️"
                    severity = "critical" if risk_score > 75 else "warning" if risk_score > 50 else "info"
                    
                    alerts_data['alerts'].append({
                        "id": f"ai-risk-{datetime.now().timestamp()}-{hash(risk.get('name'))}",
                        "type": "ai_risk", # Custom type for frontend to render nicely if needed
                        "severity": severity,
                        "title": f"{risk.get('name')} Risk ({risk_score}%)",
                        "message": f"AI Risk Assessment: {risk.get('name')} is at {risk_score}% and {risk.get('trend')}. {trend_icon}",
                        "action_required": risk_score > 50,
                        "recommended_actions": ["Monitor closely via AI Chat"], # Generic action for now
                        "created_at": datetime.now().isoformat()
                    })
            
            # Inject High Priority Actions as specific alerts
            for action in ai_actions:
                if action.get('priority') == 'high':
                     alerts_data['alerts'].append({
                        "id": f"ai-action-{datetime.now().timestamp()}",
                        "type": "advisory",
                        "severity": "warning",
                        "title": f"🚨 Priority: {action.get('title')}",
                        "message": action.get('description'),
                        "action_required": True,
                        "recommended_actions": [action.get('description')],
                        "created_at": datetime.now().isoformat()
                     })
                     
        except Exception as ai_e:
            print(f"⚠️ AI Augmentation Failed (Graceful Fallback): {ai_e}")
            import traceback
            traceback.print_exc()
            # On failure, alerts_data remains valid but with empty/minimal lists from step 3.
            # We could add a generic fallback alert here if desired.
            if not alerts_data['growth_stage']['key_activities']:
                alerts_data['growth_stage']['key_activities'] = ["Monitor field conditions", "Check for pests"]

        
        # Log the event
        log_user_event(user_id, "feature_usage", "proactive_alerts", {"field_id": field_id})
        
        return alerts_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Proactive Alerts Error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            try:
                conn.close()
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to generate alerts: {str(e)}")


@app.get("/ai/growth-stage/{field_id}")
async def get_growth_stage(field_id: str, user_id: str = Depends(verify_token)):
    """
    Get detailed growth stage information for a field.
    Uses variety-specific maturity data for accurate staging.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT crop_type, planting_date, variety, name
            FROM fields
            WHERE id = %s::uuid AND user_id = %s::uuid
        """, (field_id, user_id))
        
        field = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")
        
        if not field.get('planting_date'):
            return {
                "error": "missing_planting_date",
                "message": "Please set planting date to track growth stage"
            }
        
        from datetime import date as date_type
        planting_date = field['planting_date']
        if hasattr(planting_date, 'date'):
            planting_date = planting_date.date()
        elif isinstance(planting_date, str):
            from datetime import datetime
            planting_date = datetime.strptime(planting_date, '%Y-%m-%d').date()
        
        # Calculate growth stage
        stage_info = calculate_growth_stage(
            planting_date=planting_date,
            variety_name=field.get('variety', 'Unknown'),
            crop_type=field.get('crop_type', 'Maize')
        )
        
        # Get variety details
        variety_info = get_variety_info(field.get('variety', ''))
        
        return {
            "field_id": field_id,
            "field_name": field.get('name'),
            "crop_type": field.get('crop_type'),
            "variety": {
                "name": field.get('variety'),
                "breeder": variety_info.get('breeder') if variety_info else None,
                "days_to_maturity": variety_info.get('days_to_maturity') if variety_info else None
            },
            "growth_stage": {
                "name": stage_info.stage_name,
                "code": stage_info.stage_code,
                "days_since_planting": stage_info.days_since_planting,
                "days_to_harvest": stage_info.days_to_harvest,
                "progress_percent": stage_info.progress_percent,
                "description": stage_info.description
            },
            "key_activities": stage_info.key_activities,
            "risks": stage_info.risks,
            "planting_date": field['planting_date'].isoformat() if hasattr(field['planting_date'], 'isoformat') else str(field['planting_date'])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Growth Stage Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to calculate growth stage: {str(e)}")


@app.get("/ai/disease-risk/{field_id}")
async def get_disease_risk(field_id: str, user_id: str = Depends(verify_token)):
    """
    Get disease risk assessment based on variety resistance + current weather.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT crop_type, planting_date, variety, name, polygon_coordinates
            FROM fields
            WHERE id = %s::uuid AND user_id = %s::uuid
        """, (field_id, user_id))
        
        field = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")
        
        # Get variety info
        variety_info = get_variety_info(field.get('variety', ''))
        
        # Get current weather
        weather_data = {}
        try:
            coords = field.get('polygon_coordinates', [])
            if coords and len(coords) > 0:
                lat = sum(p.get('lat', -17.82) for p in coords) / len(coords)
                lon = sum(p.get('lon', 31.05) for p in coords) / len(coords)
            else:
                lat, lon = -17.82, 31.05
            
            current_weather = await climate_service.get_current_weather(lat, lon)
            if current_weather:
                weather_data = {
                    "temperature": current_weather.get("temperature", 25),
                    "humidity": current_weather.get("humidity", 50),
                    "precipitation": current_weather.get("precipitation", 0)
                }
        except Exception as e:
            print(f"Weather fetch failed: {e}")
            weather_data = {"temperature": 25, "humidity": 50, "precipitation": 0}
        
        # Calculate growth stage for context
        growth_stage = None
        if field.get('planting_date'):
            from datetime import date as date_type
            planting_date = field['planting_date']
            if hasattr(planting_date, 'date'):
                planting_date = planting_date.date()
            elif isinstance(planting_date, str):
                from datetime import datetime
                planting_date = datetime.strptime(planting_date, '%Y-%m-%d').date()
            
            growth_stage = calculate_growth_stage(
                planting_date=planting_date,
                variety_name=field.get('variety', 'Unknown'),
                crop_type=field.get('crop_type', 'Maize')
            )
        
        # Assess disease risk
        alerts = assess_disease_risk(variety_info, weather_data, growth_stage) if variety_info else []
        
        return {
            "field_id": field_id,
            "field_name": field.get('name'),
            "variety": field.get('variety'),
            "variety_characteristics": variety_info.get('characteristics', {}) if variety_info else {},
            "current_weather": weather_data,
            "growth_stage": growth_stage.stage_name if growth_stage else None,
            "disease_alerts": [
                {
                    "type": a.alert_type,
                    "severity": a.severity,
                    "title": a.title,
                    "message": a.message,
                    "action_required": a.action_required,
                    "recommended_actions": a.recommended_actions
                }
                for a in alerts
            ],
            "overall_risk_level": "high" if any(a.severity == "critical" for a in alerts) else (
                "medium" if any(a.severity == "warning" for a in alerts) else "low"
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Disease Risk Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to assess disease risk: {str(e)}")


# resolve_coordinates imported from deps.py


# ========== YIELD HISTORY ENDPOINTS ==========

@app.get("/fields/{field_id}/yield-history")
async def get_yield_history(field_id: str, user_id: str = Depends(verify_token)):
    """
    Get historical yield records for a field.
    
    Returns list of past season yields with projected vs actual comparison.
    Useful for trend analysis and model calibration.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verify field ownership
        cursor.execute("""
            SELECT id, name, crop_type FROM fields 
            WHERE id = %s::uuid AND user_id = %s::uuid
        """, (field_id, user_id))
        
        field = cursor.fetchone()
        if not field:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Field not found")
        
        # Fetch yield history
        cursor.execute("""
            SELECT 
                id, season_year, season_type,
                crop_type, variety, planting_date, harvest_date,
                area_harvested_ha, actual_yield_tonnes, yield_per_ha,
                quality_grade, moisture_at_harvest,
                projected_yield_tonnes, variance_percent,
                sale_price_per_tonne, total_revenue,
                notes, created_at
            FROM yield_history
            WHERE field_id = %s::uuid AND user_id = %s::uuid
            ORDER BY season_year DESC, harvest_date DESC
        """, (field_id, user_id))
        
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Calculate summary statistics
        if records:
            yields = [float(r['yield_per_ha']) for r in records if r['yield_per_ha']]
            avg_yield = sum(yields) / len(yields) if yields else 0
            best_yield = max(yields) if yields else 0
            
            variances = [float(r['variance_percent']) for r in records if r['variance_percent'] is not None]
            avg_variance = sum(variances) / len(variances) if variances else None
        else:
            avg_yield = 0
            best_yield = 0
            avg_variance = None
        
        return {
            "field_id": field_id,
            "field_name": field['name'],
            "history": [
                {
                    "id": str(r['id']),
                    "season": f"{r['season_year']} {r['season_type'].title()}",
                    "season_year": r['season_year'],
                    "season_type": r['season_type'],
                    "crop_type": r['crop_type'],
                    "variety": r['variety'],
                    "planting_date": r['planting_date'].isoformat() if r['planting_date'] else None,
                    "harvest_date": r['harvest_date'].isoformat() if r['harvest_date'] else None,
                    "area_harvested_ha": float(r['area_harvested_ha']),
                    "actual_yield_tonnes": float(r['actual_yield_tonnes']),
                    "yield_per_ha": float(r['yield_per_ha']) if r['yield_per_ha'] else None,
                    "quality_grade": r['quality_grade'],
                    "moisture_at_harvest": float(r['moisture_at_harvest']) if r['moisture_at_harvest'] else None,
                    "projected_yield_tonnes": float(r['projected_yield_tonnes']) if r['projected_yield_tonnes'] else None,
                    "variance_percent": float(r['variance_percent']) if r['variance_percent'] else None,
                    "sale_price_per_tonne": float(r['sale_price_per_tonne']) if r['sale_price_per_tonne'] else None,
                    "total_revenue": float(r['total_revenue']) if r['total_revenue'] else None,
                    "notes": r['notes']
                }
                for r in records
            ],
            "summary": {
                "total_seasons": len(records),
                "average_yield_per_ha": round(avg_yield, 2),
                "best_yield_per_ha": round(best_yield, 2),
                "average_projection_variance": round(avg_variance, 1) if avg_variance else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Yield History Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch yield history: {str(e)}")


@app.post("/fields/{field_id}/yield-history")
async def record_yield(field_id: str, payload: dict, user_id: str = Depends(verify_token)):
    """
    Record a new yield entry for a field (harvest data).
    
    Payload:
    {
        "season_year": 2025,
        "season_type": "summer",  # or "winter"
        "crop_type": "Maize",
        "variety": "SC 727",
        "planting_date": "2024-11-15",
        "harvest_date": "2025-04-20",
        "area_harvested_ha": 10.5,
        "actual_yield_tonnes": 68.25,
        "quality_grade": "A",  # optional
        "moisture_at_harvest": 12.5,  # optional, percentage
        "projected_yield_tonnes": 75.0,  # optional, for comparison
        "sale_price_per_tonne": 240.00,  # optional, USD
        "notes": "Drought in February affected yield"  # optional
    }
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verify field ownership
        cursor.execute("""
            SELECT id, crop_type FROM fields 
            WHERE id = %s::uuid AND user_id = %s::uuid
        """, (field_id, user_id))
        
        field = cursor.fetchone()
        if not field:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Field not found")
        
        # Extract and validate payload
        season_year = payload.get('season_year')
        season_type = payload.get('season_type', 'summer')
        crop_type = payload.get('crop_type') or field['crop_type']
        variety = payload.get('variety')
        planting_date = payload.get('planting_date')
        harvest_date = payload.get('harvest_date')
        area_harvested_ha = payload.get('area_harvested_ha')
        actual_yield_tonnes = payload.get('actual_yield_tonnes')
        
        if not season_year or not area_harvested_ha or actual_yield_tonnes is None:
            raise HTTPException(
                status_code=400, 
                detail="Required: season_year, area_harvested_ha, actual_yield_tonnes"
            )
        
        # Optional fields
        quality_grade = payload.get('quality_grade')
        moisture_at_harvest = payload.get('moisture_at_harvest')
        projected_yield_tonnes = payload.get('projected_yield_tonnes')
        sale_price_per_tonne = payload.get('sale_price_per_tonne')
        notes = payload.get('notes')
        
        # Insert yield record
        cursor.execute("""
            INSERT INTO yield_history (
                field_id, user_id, season_year, season_type,
                crop_type, variety, planting_date, harvest_date,
                area_harvested_ha, actual_yield_tonnes,
                quality_grade, moisture_at_harvest,
                projected_yield_tonnes, sale_price_per_tonne, notes
            ) VALUES (
                %s::uuid, %s::uuid, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s
            ) RETURNING id
        """, (
            field_id, user_id, season_year, season_type,
            crop_type, variety, planting_date, harvest_date,
            area_harvested_ha, actual_yield_tonnes,
            quality_grade, moisture_at_harvest,
            projected_yield_tonnes, sale_price_per_tonne, notes
        ))
        
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log the event
        log_user_event(user_id, "feature_usage", "record_yield", {
            "field_id": field_id,
            "season_year": season_year,
            "actual_yield": actual_yield_tonnes
        })
        
        return {
            "status": "success",
            "id": str(result['id']),
            "message": f"Yield record saved for {season_year} {season_type} season",
            "yield_per_ha": round(actual_yield_tonnes / area_harvested_ha, 2) if area_harvested_ha > 0 else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Record Yield Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to record yield: {str(e)}")


@app.get("/yield-analytics")
async def get_yield_analytics(user_id: str = Depends(verify_token)):
    """
    Get aggregate yield analytics across all user fields.
    
    Returns:
    - Average yield trends over seasons
    - Best performing varieties
    - Projection accuracy metrics
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Overall statistics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT field_id) as fields_with_data,
                COUNT(*) as total_records,
                AVG(yield_per_ha) as avg_yield_per_ha,
                MAX(yield_per_ha) as max_yield_per_ha,
                AVG(variance_percent) as avg_variance
            FROM yield_history
            WHERE user_id = %s::uuid
        """, (user_id,))
        
        overall = cursor.fetchone()
        
        # Yield by variety
        cursor.execute("""
            SELECT 
                crop_type,
                variety,
                COUNT(*) as seasons,
                AVG(yield_per_ha) as avg_yield_per_ha,
                MAX(yield_per_ha) as best_yield_per_ha,
                AVG(variance_percent) as avg_variance
            FROM yield_history
            WHERE user_id = %s::uuid AND variety IS NOT NULL
            GROUP BY crop_type, variety
            ORDER BY avg_yield_per_ha DESC
            LIMIT 10
        """, (user_id,))
        
        by_variety = cursor.fetchall()
        
        # Yield trend by year
        cursor.execute("""
            SELECT 
                season_year,
                season_type,
                SUM(actual_yield_tonnes) as total_yield,
                SUM(area_harvested_ha) as total_area,
                AVG(yield_per_ha) as avg_yield_per_ha
            FROM yield_history
            WHERE user_id = %s::uuid
            GROUP BY season_year, season_type
            ORDER BY season_year DESC, season_type
        """, (user_id,))
        
        by_season = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "summary": {
                "fields_with_history": overall['fields_with_data'] or 0,
                "total_harvest_records": overall['total_records'] or 0,
                "average_yield_per_ha": round(float(overall['avg_yield_per_ha']), 2) if overall['avg_yield_per_ha'] else None,
                "best_yield_per_ha": round(float(overall['max_yield_per_ha']), 2) if overall['max_yield_per_ha'] else None,
                "projection_accuracy": f"{100 - abs(float(overall['avg_variance'])):.1f}%" if overall['avg_variance'] else None
            },
            "top_varieties": [
                {
                    "crop": v['crop_type'],
                    "variety": v['variety'],
                    "seasons_recorded": v['seasons'],
                    "avg_yield_per_ha": round(float(v['avg_yield_per_ha']), 2),
                    "best_yield_per_ha": round(float(v['best_yield_per_ha']), 2)
                }
                for v in by_variety
            ],
            "seasonal_trends": [
                {
                    "season": f"{s['season_year']} {s['season_type'].title()}",
                    "total_yield_tonnes": round(float(s['total_yield']), 1),
                    "total_area_ha": round(float(s['total_area']), 1),
                    "avg_yield_per_ha": round(float(s['avg_yield_per_ha']), 2)
                }
                for s in by_season
            ]
        }
        
    except Exception as e:
        print(f"Yield Analytics Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


# ===========================================================================
# AGRONOMIC DECISION ENGINE ENDPOINTS
# ===========================================================================
# Fast-path, science-based recommendations that don't require LLM calls.
# These provide instant, deterministic advice from the crop knowledge engine.

from agronomic_engine import (
    check_planting_window,
    get_fertilizer_recommendation,
    get_ipm_recommendations,
    get_irrigation_advice,
    check_harvest_readiness,
)
from crop_knowledge import (
    get_crop_profile, get_all_crop_names, build_crop_context_for_ai,
    get_diseases_for_conditions, get_pests_for_stage,
)


@app.get("/agro/planting-window")
async def planting_window_check(
    crop: str,
    region: str = "",
    user_id: str = Depends(verify_token),
):
    """
    Check if now is the right time to plant a specific crop.
    Returns planting window status and recommendations.
    """
    return check_planting_window(crop, region)


@app.get("/agro/fertilizer/{field_id}")
async def fertilizer_recommendation(
    field_id: str,
    soil_ph: Optional[float] = None,
    user_id: str = Depends(verify_token),
):
    """
    Get stage-specific fertilizer recommendations for a field.
    Uses crop type, planting date, and soil pH to generate precise advice.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT crop_type, planting_date FROM fields WHERE id = %s AND user_id = %s",
            (field_id, user_id),
        )
        field = cursor.fetchone()
        cursor.close()
        conn.close()

        if not field:
            raise HTTPException(status_code=404, detail="Field not found")

        crop_type = field["crop_type"]
        planting_date = field.get("planting_date")

        if not planting_date:
            return {"recommendation": "Set a planting date to get fertilizer advice."}

        days = (date.today() - planting_date).days if isinstance(planting_date, date) else 0

        return get_fertilizer_recommendation(crop_type, days, soil_ph)

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agro/ipm/{field_id}")
async def ipm_recommendations(
    field_id: str,
    user_id: str = Depends(verify_token),
):
    """
    Integrated Pest Management recommendations for a field.
    Combines current weather, growth stage, and crop-specific disease/pest profiles.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT crop_type, planting_date, polygon_coordinates FROM fields WHERE id = %s AND user_id = %s",
            (field_id, user_id),
        )
        field = cursor.fetchone()
        cursor.close()
        conn.close()

        if not field:
            raise HTTPException(status_code=404, detail="Field not found")

        crop_type = field["crop_type"]
        planting_date = field.get("planting_date")
        days = (date.today() - planting_date).days if planting_date and isinstance(planting_date, date) else 30

        # Get weather for disease risk assessment
        temp, humidity = None, None
        try:
            coords = field.get("polygon_coordinates")
            if coords:
                if isinstance(coords, str):
                    coords = json.loads(coords)
                if isinstance(coords, list) and len(coords) > 0:
                    lat = coords[0].get("lat") or coords[0].get("latitude")
                    lon = coords[0].get("lng") or coords[0].get("lon") or coords[0].get("longitude")
                    if lat and lon:
                        from climate_service import get_current_weather
                        weather = await get_current_weather(float(lat), float(lon))
                        if weather:
                            temp = weather.get("temperature")
                            humidity = weather.get("humidity")
        except Exception as e:
            print(f"Weather fetch for IPM failed: {e}")

        return get_ipm_recommendations(crop_type, days, temp, humidity)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agro/irrigation/{field_id}")
async def irrigation_advice(
    field_id: str,
    recent_rainfall_mm: float = 0.0,
    user_id: str = Depends(verify_token),
):
    """
    Crop-coefficient-based irrigation scheduling for a field.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT crop_type, planting_date FROM fields WHERE id = %s AND user_id = %s",
            (field_id, user_id),
        )
        field = cursor.fetchone()
        cursor.close()
        conn.close()

        if not field:
            raise HTTPException(status_code=404, detail="Field not found")

        days = 0
        planting_date = field.get("planting_date")
        if planting_date and isinstance(planting_date, date):
            days = (date.today() - planting_date).days

        return get_irrigation_advice(field["crop_type"], days, recent_rainfall_mm)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agro/harvest/{field_id}")
async def harvest_readiness(
    field_id: str,
    user_id: str = Depends(verify_token),
):
    """
    Check harvest readiness for a field, including post-harvest guidance.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT crop_type, planting_date, variety FROM fields WHERE id = %s AND user_id = %s",
            (field_id, user_id),
        )
        field = cursor.fetchone()
        cursor.close()
        conn.close()

        if not field:
            raise HTTPException(status_code=404, detail="Field not found")

        days = 0
        planting_date = field.get("planting_date")
        if planting_date and isinstance(planting_date, date):
            days = (date.today() - planting_date).days

        # Try to get variety maturity from DB
        variety_maturity = None
        variety = field.get("variety")
        if variety:
            conn2 = get_db_connection()
            if conn2:
                try:
                    cur2 = conn2.cursor()
                    cur2.execute(
                        "SELECT days_to_maturity FROM crop_varieties WHERE LOWER(variety_name) LIKE LOWER(%s) LIMIT 1",
                        (f"%{variety}%",),
                    )
                    row = cur2.fetchone()
                    if row and row.get("days_to_maturity"):
                        variety_maturity = int(row["days_to_maturity"])
                    cur2.close()
                    conn2.close()
                except Exception:
                    if conn2:
                        conn2.close()

        return check_harvest_readiness(field["crop_type"], days, variety_maturity)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agro/crop-intelligence/{field_id}")
async def crop_intelligence(
    field_id: str,
    user_id: str = Depends(verify_token),
):
    """
    Full crop intelligence report combining all agronomic engines.
    Returns growth stage, disease risks, pest alerts, fertilizer advice,
    irrigation needs, and harvest readiness in a single call.
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT crop_type, planting_date, variety, polygon_coordinates, name FROM fields WHERE id = %s AND user_id = %s",
            (field_id, user_id),
        )
        field = cursor.fetchone()
        cursor.close()
        conn.close()

        if not field:
            raise HTTPException(status_code=404, detail="Field not found")

        crop_type = field["crop_type"]
        planting_date = field.get("planting_date")
        days = 0
        if planting_date and isinstance(planting_date, date):
            days = (date.today() - planting_date).days

        # Get weather
        temp, humidity, rainfall = None, None, 0.0
        try:
            coords = field.get("polygon_coordinates")
            if coords:
                if isinstance(coords, str):
                    coords = json.loads(coords)
                if isinstance(coords, list) and len(coords) > 0:
                    lat = coords[0].get("lat") or coords[0].get("latitude")
                    lon = coords[0].get("lng") or coords[0].get("lon") or coords[0].get("longitude")
                    if lat and lon:
                        from climate_service import get_current_weather
                        weather = await get_current_weather(float(lat), float(lon))
                        if weather:
                            temp = weather.get("temperature")
                            humidity = weather.get("humidity")
                            rainfall = weather.get("precipitation", 0.0)
        except Exception:
            pass

        # Get variety maturity
        variety_maturity = None
        variety = field.get("variety")
        if variety:
            conn2 = get_db_connection()
            if conn2:
                try:
                    cur2 = conn2.cursor()
                    cur2.execute(
                        "SELECT days_to_maturity FROM crop_varieties WHERE LOWER(variety_name) LIKE LOWER(%s) LIMIT 1",
                        (f"%{variety}%",),
                    )
                    row = cur2.fetchone()
                    if row and row.get("days_to_maturity"):
                        variety_maturity = int(row["days_to_maturity"])
                    cur2.close()
                    conn2.close()
                except Exception:
                    if conn2:
                        conn2.close()

        # Assemble full intelligence report
        return {
            "field": {
                "id": field_id,
                "name": field.get("name"),
                "crop": crop_type,
                "variety": variety,
                "days_since_planting": days,
            },
            "ipm": get_ipm_recommendations(crop_type, days, temp, humidity),
            "fertilizer": get_fertilizer_recommendation(crop_type, days),
            "irrigation": get_irrigation_advice(crop_type, days, rainfall * 7),
            "harvest": check_harvest_readiness(crop_type, days, variety_maturity),
            "planting_window": check_planting_window(crop_type),
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Crop Intelligence Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agro/supported-crops")
async def supported_crops():
    """List all crops with detailed knowledge profiles."""
    crops = get_all_crop_names()
    result = []
    for name in crops:
        profile = get_crop_profile(name)
        if profile:
            result.append({
                "name": profile.crop_name,
                "scientific_name": profile.scientific_name,
                "family": profile.family,
                "optimal_ph": list(profile.optimal_ph),
                "optimal_temp": list(profile.optimal_temp),
                "total_water_mm": profile.total_water_mm,
                "growth_stages": len(profile.growth_stages),
                "diseases_tracked": len(profile.diseases),
                "pests_tracked": len(profile.pests),
                "regions": profile.natural_region_suitability,
            })
    return {"crops": result, "total": len(result)}

