import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI
from llm_models import CHAT_MODEL


REQUEST_TIMEOUT_SECONDS = 30
RETRY_ATTEMPTS = 2


def _error(message):
    return {"status": "error", "error_message": message}


def _load_payload():
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("No input received on stdin")
    return json.loads(raw)


def _load_knowledge(path):
    if not path:
        return None
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().strip()


def _build_prompt(seed, soil, tool_status, knowledge, language, region=None):
    context_intro = "You are the KurimaSense AI Agronomist."
    if region:
        region_name = region.replace("_", " ").title()
        context_intro += f" You are specializing in agronomy for {region_name}. Use the specific regional standards provided in the context."

    knowledge_block = ""
    if knowledge:
        knowledge_block = f"\n\nVERIFIED AGRONOMIC CONTEXT:\n{knowledge}\n(Source this information in your answer where possible)\n"
    
    language_line = ""
    if language:
        language_line = f"Respond in {language}. Translate all your output to {language}."

    return (
        f"{context_intro} "
        "Follow these rules: be deterministic, never guess chemical rates, "
        "ask a clarifying question if confidence is low, and keep advice short. "
        "Use local context and explicitly mention missing data. "
        f"{language_line}\n\n"
        f"Seed:\n{json.dumps(seed, indent=2)}\n\n"
        f"Soil:\n{json.dumps(soil, indent=2)}\n\n"
        f"Tool Status:\n{json.dumps(tool_status, indent=2)}\n\n"
        f"Return a JSON object with keys: text_body, actions, confidence_score, reasoning_trace."
        f"{knowledge_block}"
    )


def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or "your_" in api_key:
        sys.stdout.write(json.dumps(_error("OPENAI_API_KEY missing or placeholder")))
        return

    try:
        payload = _load_payload()
        seed = payload.get("seed") or {}
        soil = payload.get("soil") or {}
        tool_status = payload.get("tool_status") or {}
        
        # New: Retrieve RAG context passed from Router
        retrieved_context = payload.get("retrieved_context")
        region_used = payload.get("region_used")

        client = OpenAI(api_key=api_key)
        language = payload.get("language") or seed.get("language")
        
        # Fallback to local file if no RAG context
        knowledge = retrieved_context
        if not knowledge:
            knowledge_path = os.getenv("AGRONOMY_KB_PATH", ".tmp/agronomy_knowledge.txt")
            knowledge = _load_knowledge(knowledge_path)

        prompt = _build_prompt(seed, soil, tool_status, knowledge, language, region_used)
        image_data = seed.get("image_data")
        
        # Prepare messages
        image_data = seed.get("image_data")
        history = seed.get("chat_history", [])
        
        # Prepare messages
        messages = []
        
        # 1. Add System/Context Prompt as System Message (or first User message if model prefers)
        # Using 'system' role is better for instructions
        messages.append({"role": "system", "content": prompt }) 
        
        # 2. Add History
        for msg in history:
            role = "assistant" if msg["role"] == "ai" else "user"
            messages.append({"role": role, "content": msg["content"]})
            
        # 3. Add Current Turn
        if image_data:
            # Multimodal Request
             messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": "Answer this based on the above context: " + seed.get("raw_message", "")}, # Redundant but safe
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data, 
                            "detail": "auto"
                        }
                    }
                ]
            })
        else:
            # Text-only Request
            # Note: The 'prompt' variable currently contains the USER query too. 
            # We need to separate instructions from the query if we use a system message.
            # However, to minimize refactoring risk, we'll keep the 'prompt' as the system instruction + current query
            # BUT since we are inserting history, we should change the architecture slightly:
            # System: "You are an Agronomist... [Rules]... [RAG Context]"
            # History User: "My corn is yellow"
            # History AI: "That's nitrogen deficiency."
            # Current User: "How do I fix it?"
            
            # Since 'prompt' currently concatenates everything, let's treat it as the FINAL user message for now to be safe, 
            # BUT we must inject history BEFORE it.
            # Wait, 'prompt' contains the Seed/Soil/Tools JSON dump. 
            # This is "Instruction Tuning". 
            
            # Revised Strategy for 'prompt' construction in previous tool:
            # It dumps 'Seed' which contains 'chat_history'.
            # If we dump history in the text prompt, the model sees it as JSON data, not conversation turns.
            # To make it truly conversational, we should parse it out.
            
            # Let's keep it simple:
            # The 'prompt' variable has ALL the RAG context and Instructions.
            # Let's verify what _build_prompt does. It adds "Seed: ..." JSON.
            
            # If we want true conversational flow, we should rely on the JSON dump of history inside 'prompt' 
            # OR explicitly separate them.
            # Given the existing setup, simply dumping the history in the JSON seed (which happens automatically in _build_prompt)
            # gives the model the data, but maybe not the "feeling" of a conversation.
            # However, GPT-4 is smart enough to read "Seed: { chat_history: [...] }" and understand context.
            # The user says "How do I fix *this*?". 'this' refers to the previous turn.
            # If 'chat_history' is in the Seed JSON, the model CAN see it.
            
            # SO: The fact that I added 'chat_history' to Seed in app.py MIGHT be enough 
            # if _build_prompt dumps the whole seed.
            # Let's check _build_prompt in generate_advice.py...
            # Yes: f"Seed:\n{json.dumps(seed, indent=2)}\n\n"
            
            # So, technically, simply adding it to seed in `app.py` makes it available.
            # BUT, explicitly formatting it as message turns is much more powerful for "chatty" behavior.
            
            # Let's try the Message injection approach for better performance.
            # But we must be careful not to duplicate.
            # If we inject history as messages, we don't need it in the Seed JSON dump.
            
            pass 
            
        # Implementation:
        # We will use the 'messages' list.
        # System: Core Instructions (Identity, Rules) + RAG Context.
        # History...
        # User: Current Query + MetaData (Soil, Tools)
        
        # Refactoring `prompt` variable is risky. 
        # Let's stick to the current "Instruction-Heavy" wrapper for the final turn,
        # but prepend actual history messages before it.
        
        messages = []
        
        # History first? No, System first.
        # We don't have a clean "System Prompt" string variable, it's mixed in `prompt`.
        # Let's keep `prompt` as the FINAL User message (it contains the question + all context).
        # We will insert history BEFORE it.
        
        for msg in history:
            role = "assistant" if msg["role"] == "ai" else "user"
            content = msg["content"]
            # Basic sanitization
            if content: 
                messages.append({"role": role, "content": str(content)})
                
        if image_data:
             messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data, 
                            "detail": "auto"
                        }
                    }
                ]
            })
        else:
             messages.append({"role": "user", "content": prompt})

        response = None
        last_error = None
        for _ in range(RETRY_ATTEMPTS):
            try:
                response = client.chat.completions.create(
                    model=CHAT_MODEL,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=500, # Increased for potentially complex image analysis
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                break
            except Exception as exc:
                last_error = exc
        if response is None:
            raise RuntimeError(f"OpenAI request failed: {last_error}")
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned empty content")
        parsed = json.loads(content)

        output = {
            "recipient_id": seed.get("user_id", "unknown"),
            "channel": "whatsapp",
            "message_type": "text",
            "content": {
                "text_body": parsed.get("text_body"),
                "actions": parsed.get("actions", []),
            },
            "meta_data": {
                "confidence_score": parsed.get("confidence_score", 0.0),
                "reasoning_trace": parsed.get("reasoning_trace", ""),
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

        sys.stdout.write(json.dumps({"status": "ok", "data": output}, indent=2))
    except Exception as exc:
        sys.stdout.write(json.dumps(_error(str(exc))))


if __name__ == "__main__":
    main()
