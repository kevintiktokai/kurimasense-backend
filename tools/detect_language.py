import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI


def _error(message):
    return {"status": "error", "error_message": message}


def _load_payload():
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("No input received on stdin")
    return json.loads(raw)


def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or "your_" in api_key:
        sys.stdout.write(json.dumps(_error("OPENAI_API_KEY missing or placeholder")))
        return

    try:
        payload = _load_payload()
        text = payload.get("text") or payload.get("raw_message") or ""
        if not text.strip():
            sys.stdout.write(json.dumps({"status": "ok", "data": {"code": "en"}}))
            return

        client = OpenAI(api_key=api_key)
        prompt = (
            "Detect the language of the text and respond with JSON containing "
            "code (BCP-47 or ISO 639-1) and name. Example: {\"code\":\"sw\",\"name\":\"Swahili\"}. "
            "Text:\n" + text
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=60,
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned empty content")
        parsed = json.loads(content)
        sys.stdout.write(json.dumps({"status": "ok", "data": parsed}, indent=2))
    except Exception as exc:
        sys.stdout.write(json.dumps(_error(str(exc))))


if __name__ == "__main__":
    main()
