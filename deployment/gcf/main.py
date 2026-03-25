import json
import os

from router import route


def _load_seed(request):
    try:
        return request.get_json(silent=True) or {}
    except Exception:
        return {}


def router_http(request):
    seed = _load_seed(request)
    try:
        response = route(seed)
        return (json.dumps(response), 200, {"Content-Type": "application/json"})
    except Exception as exc:
        return (json.dumps({"error": str(exc)}), 500, {"Content-Type": "application/json"})


def proactive_http(request):
    payload = _load_seed(request)
    seeds = payload.get("seeds") or []
    results = []
    for seed in seeds:
        try:
            results.append(route(seed))
        except Exception as exc:
            results.append({"error": str(exc), "seed": seed})
    return (json.dumps({"results": results}), 200, {"Content-Type": "application/json"})


def proactive_cron(event, context):
    targets = os.getenv("PROACTIVE_TARGETS_JSON", "[]")
    try:
        seeds = json.loads(targets)
    except json.JSONDecodeError:
        return

    for seed in seeds:
        try:
            route(seed)
        except Exception:
            continue
