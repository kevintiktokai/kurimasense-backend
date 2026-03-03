import json
import sys


def _error(message):
    return {"status": "error", "error_message": message}


def _load_payload():
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("No input received on stdin")
    return json.loads(raw)


def _format_actions(actions):
    if not actions:
        return ""
    lines = ["✅ Next Steps:"]
    for action in actions:
        lines.append(f"- {action}")
    return "\n".join(lines)


def _format_payload(payload):
    content = payload.get("content") or {}
    meta = payload.get("meta_data") or {}
    body = (content.get("text_body") or "").strip()
    actions = content.get("actions") or []
    confidence = meta.get("confidence_score")

    header = "🌾 KurimaSense Update"
    confidence_line = ""
    if confidence is not None:
        confidence_line = f"Confidence: {round(float(confidence) * 100, 1)}%"

    blocks = [header]
    if body:
        blocks.append(f"\n🧠 Insight:\n{body}")
    if actions:
        blocks.append(f"\n{_format_actions(actions)}")
    if confidence_line:
        blocks.append(f"\n{confidence_line}")
    blocks.append("\nReply with a photo or details if anything looks unusual.")

    formatted = "\n".join(blocks).strip()
    return {
        **payload,
        "content": {
            **content,
            "text_body": formatted,
        },
    }


def main():
    try:
        payload = _load_payload()
        formatted = _format_payload(payload)
        sys.stdout.write(json.dumps({"status": "ok", "data": formatted}, indent=2))
    except Exception as exc:
        sys.stdout.write(json.dumps(_error(str(exc))))


if __name__ == "__main__":
    main()
