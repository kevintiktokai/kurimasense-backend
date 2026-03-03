import json
import os
import subprocess
import sys
from datetime import datetime, timezone


REQUIRED_SEED_FIELDS = {
    "user_id",
    "session_id",
    "timestamp",
    "location",
    "context",
    "intent_classification",
    "raw_message",
}


def _read_seed_payload():
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("No input received on stdin")
    return json.loads(raw)


def _validate_seed(seed):
    missing = REQUIRED_SEED_FIELDS.difference(seed.keys())
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")
    location = seed.get("location") or {}
    if "lat" not in location or "lon" not in location:
        raise ValueError("Seed.location must include lat and lon")


def _run_tool(script_path, payload):
    result = subprocess.run(
        [sys.executable, script_path],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return {
            "status": "error",
            "error_message": result.stderr.strip() or "Tool execution failed",
        }
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "status": "error",
            "error_message": "Tool output was not valid JSON",
        }


def _build_error_payload(seed, message):
    return {
        "recipient_id": seed.get("user_id", "unknown"),
        "channel": "whatsapp",
        "message_type": "text",
        "content": {
            "text_body": message,
            "actions": ["Share more details"],
        },
        "meta_data": {
            "confidence_score": 0.0,
            "reasoning_trace": "Router validation failed",
        },
    }


def route(seed):
    if not isinstance(seed, dict):
        raise ValueError("Seed must be a JSON object")
    _validate_seed(seed)

    intent = seed.get("intent_classification")
    tool_status = {}
    weather = None
    satellite = None

    tools_dir = os.path.join(os.path.dirname(__file__), "tools")
    weather_tool = os.path.join(tools_dir, "get_weather_forecast.py")
    crop_tool = os.path.join(tools_dir, "get_crop_health.py")
    advice_tool = os.path.join(tools_dir, "generate_advice.py")
    format_tool = os.path.join(tools_dir, "format_whatsapp.py")
    language_tool = os.path.join(tools_dir, "detect_language.py")
    voice_tool = os.path.join(tools_dir, "format_voice.py")

    if intent in {"weather_check", "general_advice", "disease_id"}:
        weather_result = _run_tool(weather_tool, seed)
        tool_status["weather"] = weather_result.get("status")
        if weather_result.get("status") == "ok":
            weather = weather_result.get("data")
        else:
            tool_status["weather_error"] = weather_result.get("error_message")

    if intent in {"general_advice", "disease_id"}:
        sat_result = _run_tool(crop_tool, seed)
        tool_status["satellite"] = sat_result.get("status")
        if sat_result.get("status") == "ok":
            satellite = sat_result.get("data")
        else:
            tool_status["satellite_error"] = sat_result.get("error_message")

    soil = {
        "weather": weather,
        "satellite": satellite,
    }

    # RAG Retrieval
    retrieved_context = None
    region_used = None
    retrieval_tool = os.path.join(tools_dir, "retrieve_context.py")
    
    if intent in {"general_advice", "disease_id", "best_practices"}:
        rag_result = _run_tool(retrieval_tool, {"seed": seed})
        if rag_result.get("status") == "ok":
             data = rag_result.get("data", {})
             retrieved_context = data.get("retrieved_context")
             region_used = data.get("region_used")


    language = seed.get("language")
    if not language:
        language_result = _run_tool(language_tool, {"raw_message": seed.get("raw_message")})
        if language_result.get("status") == "ok":
            data = language_result.get("data")
            if isinstance(data, dict):
                language = data.get("code")
            if language:
                seed["language"] = language

    advice_payload = {
        "seed": seed,
        "soil": soil,
        "tool_status": tool_status,
        "language": language,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "retrieved_context": retrieved_context,
        "region_used": region_used
    }

    advice_result = _run_tool(advice_tool, advice_payload)
    if advice_result.get("status") != "ok":
        error_message = advice_result.get("error_message", "Advice generation failed")
        return _build_error_payload(seed, error_message)

    payload = advice_result.get("data") or {}
    formatted_result = _run_tool(format_tool, payload)
    if formatted_result.get("status") == "ok":
        payload = formatted_result.get("data")

    context = {}
    raw_context = seed.get("context")
    if isinstance(raw_context, dict):
        context = raw_context
    voice_enabled = context.get("voice_enabled") is True
    if voice_enabled:
        voice_result = _run_tool(voice_tool, payload)
        if voice_result.get("status") == "ok":
            return voice_result.get("data")

    return payload


def main():
    try:
        seed = _read_seed_payload()
        response = route(seed)
    except Exception as exc:
        response = _build_error_payload({"user_id": "unknown"}, str(exc))
    sys.stdout.write(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
