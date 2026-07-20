"""
LLM provider routing tests (OpenRouter migration, July 2026).

Cover: provider detection, model-tier resolution per provider, client base-URL
selection, the equivalent-tier fallback mapping, and text_chat_completion's
one-shot OpenRouter→OpenAI fallback. No network — clients are constructed
(cheap) or faked.
"""

import importlib

import llm_models


# --- Fallback tier mapping ---------------------------------------------------

def test_fallback_model_mapping():
    assert llm_models.openai_fallback_model(llm_models.DEEP_MODEL) == llm_models._OPENAI_FALLBACK_DEEP
    assert llm_models.openai_fallback_model(llm_models.VISION_MODEL) == llm_models._OPENAI_FALLBACK_VISION
    assert llm_models.openai_fallback_model("anything-else") == llm_models._OPENAI_FALLBACK_CHAT


# --- Provider detection ------------------------------------------------------

def test_have_text_provider_reflects_openai_key(monkeypatch):
    monkeypatch.setattr(llm_models, "OPENROUTER_API_KEY", None)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-real-key-value")
    assert llm_models.have_text_provider() is True
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert llm_models.have_text_provider() is False


def test_placeholder_keys_are_rejected(monkeypatch):
    monkeypatch.setattr(llm_models, "OPENROUTER_API_KEY", None)
    monkeypatch.setenv("OPENAI_API_KEY", "your_openai_key_here")
    assert llm_models.have_text_provider() is False


# --- Client construction -----------------------------------------------------

def test_make_text_client_direct_openai(monkeypatch):
    monkeypatch.setattr(llm_models, "OPENROUTER_API_KEY", None)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-real-key-value")
    client = llm_models.make_text_client()
    assert "api.openai.com" in str(client.base_url)


def test_make_text_client_none_without_any_key(monkeypatch):
    monkeypatch.setattr(llm_models, "OPENROUTER_API_KEY", None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert llm_models.make_text_client() is None


def test_make_openai_client_is_always_direct(monkeypatch):
    # Even with OpenRouter active, the embeddings/TTS/fallback client is OpenAI.
    monkeypatch.setattr(llm_models, "OPENROUTER_API_KEY", "sk-or-xxx")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-real-key-value")
    client = llm_models.make_openai_client()
    assert "api.openai.com" in str(client.base_url)


# --- text_chat_completion fallback ------------------------------------------

class _FakeCompletions:
    def __init__(self, recorder, raise_exc=None):
        self._recorder = recorder
        self._raise = raise_exc

    def create(self, **kwargs):
        if self._raise:
            raise self._raise
        self._recorder.append(kwargs)
        return "ok"


class _FakeClient:
    def __init__(self, recorder, raise_exc=None):
        self.chat = type("Chat", (), {"completions": _FakeCompletions(recorder, raise_exc)})()


def test_text_chat_completion_falls_back_to_openai(monkeypatch):
    calls = []
    monkeypatch.setattr(llm_models, "use_openrouter", lambda: True)
    monkeypatch.setattr(llm_models, "make_text_client",
                        lambda async_=False: _FakeClient(calls, raise_exc=RuntimeError("openrouter down")))
    monkeypatch.setattr(llm_models, "make_openai_client",
                        lambda async_=False: _FakeClient(calls))

    result = llm_models.text_chat_completion(
        model=llm_models.DEEP_MODEL,
        messages=[{"role": "user", "content": "hi"}],
    )
    assert result == "ok"
    assert len(calls) == 1  # the fallback call
    # Fallback rewrote the model to the equivalent direct-OpenAI tier.
    assert calls[0]["model"] == llm_models._OPENAI_FALLBACK_DEEP


def test_text_chat_completion_no_fallback_when_openai_only(monkeypatch):
    calls = []
    monkeypatch.setattr(llm_models, "use_openrouter", lambda: False)
    monkeypatch.setattr(llm_models, "make_text_client",
                        lambda async_=False: _FakeClient(calls, raise_exc=RuntimeError("boom")))
    # With OpenAI as the primary (not OpenRouter), the error must propagate.
    try:
        llm_models.text_chat_completion(model="gpt-4.1-mini", messages=[])
        assert False, "expected the primary error to propagate"
    except RuntimeError as e:
        assert "boom" in str(e)


# --- OpenRouter branch (import-time model resolution) ------------------------

def test_openrouter_branch_resolves_deepseek(monkeypatch):
    """With OPENROUTER_API_KEY set, the module resolves DeepSeek text tiers and a
    multimodal vision model, and the text client points at OpenRouter."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-testkey")
    monkeypatch.delenv("OPENROUTER_CHAT_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_VISION_MODEL", raising=False)
    try:
        importlib.reload(llm_models)
        assert llm_models.use_openrouter() is True
        assert llm_models.CHAT_MODEL == "deepseek/deepseek-chat"
        assert llm_models.DEEP_MODEL == "deepseek/deepseek-chat"
        assert "gpt-4o" in llm_models.VISION_MODEL  # multimodal, not DeepSeek
        assert "openrouter.ai" in str(llm_models.make_text_client().base_url)
    finally:
        # Restore baseline (no OpenRouter) so other tests see the default module.
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        importlib.reload(llm_models)
