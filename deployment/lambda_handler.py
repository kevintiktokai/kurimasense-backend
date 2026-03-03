import json
import os

from router import route


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _load_seed_from_event(event):
    if isinstance(event, dict) and "body" in event:
        raw = event.get("body") or "{}"
        if isinstance(raw, str):
            return json.loads(raw)
        return raw
    return event


def handle_request(event, context):
    try:
        seed = _load_seed_from_event(event)
        response = route(seed)
        return _response(200, response)
    except Exception as exc:
        return _response(500, {"error": str(exc)})


def handle_scheduled(event, context):
    targets = os.getenv("PROACTIVE_TARGETS_JSON", "[]")
    try:
        seeds = json.loads(targets)
    except json.JSONDecodeError:
        return _response(500, {"error": "PROACTIVE_TARGETS_JSON is invalid JSON"})

    results = []
    for seed in seeds:
        try:
            results.append(route(seed))
        except Exception as exc:
            results.append({"error": str(exc), "seed": seed})

    return _response(200, {"results": results})
