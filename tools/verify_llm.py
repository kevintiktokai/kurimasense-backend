import sys
from dotenv import load_dotenv
from llm_models import CHAT_MODEL, have_text_provider, text_chat_completion, use_openrouter

def verify_llm():
    """
    Verifies that the active LLM provider (OpenRouter or OpenAI) is reachable.
    """
    load_dotenv()

    if not have_text_provider():
        print("❌ FAILED: no LLM provider configured (set OPENROUTER_API_KEY or OPENAI_API_KEY)")
        return False

    try:
        print(f"🔄 Attempting to contact LLM Brain via {'OpenRouter' if use_openrouter() else 'OpenAI'} ({CHAT_MODEL})...")
        response = text_chat_completion(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": "Say 'Connection Verified' if you can hear me."}],
            max_tokens=10
        )
        content = response.choices[0].message.content
        print(f"✅ SUCCESS: LLM Responded: '{content}'")
        return True
    except Exception as e:
        print(f"❌ FAILED: Error connecting to LLM: {e}")
        return False

if __name__ == "__main__":
    verify_llm()
