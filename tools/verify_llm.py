import os
import sys
from dotenv import load_dotenv
import openai
from llm_models import CHAT_MODEL

def verify_llm():
    """
    Verifies that the LLM API key is valid and can generate a simple response.
    """
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or "your_" in api_key:
        print("❌ FAILED: OPENAI_API_KEY not found or is still a placeholder in .env")
        return False

    client = openai.OpenAI(api_key=api_key)
    
    try:
        print("🔄 Attempting to contact LLM Brain...")
        response = client.chat.completions.create(
            model=CHAT_MODEL, # or whatever is available
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
