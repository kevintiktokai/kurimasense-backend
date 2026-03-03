import json
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import OpenAI


def _error(message):
    return {"status": "error", "error_message": message}


def _load_payload():
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("No input received on stdin")
    return json.loads(raw)


def _ensure_tmp_dir():
    tmp_dir = os.path.join(os.getcwd(), ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    return tmp_dir


def _build_output_path(tmp_dir):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return os.path.join(tmp_dir, f"tts_{stamp}.mp3")


def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or "your_" in api_key:
        sys.stdout.write(json.dumps(_error("OPENAI_API_KEY missing or placeholder")))
        return

    try:
        payload = _load_payload()
        content = payload.get("content") or {}
        text = (content.get("text_body") or "").strip()
        if not text:
            raise ValueError("Payload content.text_body is empty")

        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
        voice = os.getenv("OPENAI_TTS_VOICE", "alloy")

        tmp_dir = _ensure_tmp_dir()
        output_path = _build_output_path(tmp_dir)
        audio = client.audio.speech.create(model=model, voice=voice, input=text)
        audio.write_to_file(output_path)

        formatted = {
            **payload,
            "message_type": "audio",
            "content": {
                **content,
                "media_url": output_path,
            },
        }

        sys.stdout.write(json.dumps({"status": "ok", "data": formatted}, indent=2))
    except Exception as exc:
        sys.stdout.write(json.dumps(_error(str(exc))))


if __name__ == "__main__":
    main()
