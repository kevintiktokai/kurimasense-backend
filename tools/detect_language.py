import json
import os
import sys

from dotenv import load_dotenv
from llm_models import CHAT_MODEL, have_text_provider, text_chat_completion


def _error(message):
    return {"status": "error", "error_message": message}


def _load_payload():
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("No input received on stdin")
    return json.loads(raw)


def main():
    load_dotenv()
    if not have_text_provider():
        sys.stdout.write(json.dumps(_error("No LLM provider configured (OPENROUTER_API_KEY or OPENAI_API_KEY)")))
        return

    try:
        payload = _load_payload()
        text = payload.get("text") or payload.get("raw_message") or ""
        if not text.strip():
            sys.stdout.write(json.dumps({"status": "ok", "data": {"code": "en"}}))
            return

        prompt = (
            "Detect the language of the text and respond with JSON containing "
            "code (BCP-47 or ISO 639-1) and name. Example: {\"code\":\"sw\",\"name\":\"Swahili\"}. "
            "Text:\n" + text
        )
        response = text_chat_completion(
            model=CHAT_MODEL,
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
