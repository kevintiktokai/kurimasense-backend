"""
Central LLM model selection + provider routing — single source of truth for
every chat/vision LLM call.

Providers
---------
The chat/vision surface speaks the OpenAI Chat Completions API. OpenRouter is
OpenAI-API-compatible, so when ``OPENROUTER_API_KEY`` is set we point the SAME
OpenAI SDK at OpenRouter's base URL and route text + vision there (default text
tier: DeepSeek, materially cheaper). When it's absent we call OpenAI directly —
behaviour is identical to before this module gained routing.

Two endpoints DELIBERATELY never go through OpenRouter because it doesn't
implement them:
  * Embeddings (RAG, ``text-embedding-3-small``) — ``tools/retrieve_context``.
  * Text-to-speech (``audio.speech``) — ``tools/format_voice``.
Both keep using a DIRECT OpenAI client, so ``OPENAI_API_KEY`` is still required
for RAG + voice even when the chat tier runs on OpenRouter.

Reliability: ``text_chat_completion`` (and the async brain path) try the active
provider and, if it errors, fall back once to a direct-OpenAI call with the
equivalent tier model — so an OpenRouter outage degrades to OpenAI instead of
failing the request, provided ``OPENAI_API_KEY`` is also set.

Tiers (env-overridable, so a model bump is a Railway env-var change, not code):
- CHAT_MODEL   — conversational/agronomy chat, insights, structured extraction.
- DEEP_MODEL   — quality-critical outputs (full crop-plan generation).
- VISION_MODEL — image diagnosis (must be a multimodal model).
"""

import os

# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")


def _valid(key) -> bool:
    return bool(key) and "your_" not in key and "placeholder" not in key


def use_openrouter() -> bool:
    """True when the chat/vision tier should route through OpenRouter."""
    return _valid(OPENROUTER_API_KEY)


def have_text_provider() -> bool:
    """True when SOME chat provider is configured (OpenRouter or direct OpenAI).
    Call-site guards use this instead of checking OPENAI_API_KEY directly, so an
    OpenRouter-only deployment still runs the LLM instead of silently falling
    back to static/deterministic responses."""
    return use_openrouter() or _valid(os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------------------------------------
# Model tiers — resolved per active provider
# ---------------------------------------------------------------------------
if use_openrouter():
    # OpenRouter model IDs are "vendor/model". DeepSeek for the text tiers (cheap);
    # a multimodal model for vision (DeepSeek chat is text-only).
    CHAT_MODEL = os.getenv("OPENROUTER_CHAT_MODEL", "deepseek/deepseek-chat")
    DEEP_MODEL = os.getenv("OPENROUTER_DEEP_MODEL", "deepseek/deepseek-chat")
    VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "openai/gpt-4o")
else:
    CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
    DEEP_MODEL = os.getenv("OPENAI_DEEP_MODEL", "gpt-4.1")
    VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", DEEP_MODEL)

# Direct-OpenAI models used as the fallback when an OpenRouter call fails.
# (Always OpenAI IDs, independent of the active provider.)
_OPENAI_FALLBACK_CHAT = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
_OPENAI_FALLBACK_DEEP = os.getenv("OPENAI_DEEP_MODEL", "gpt-4.1")
_OPENAI_FALLBACK_VISION = os.getenv("OPENAI_VISION_MODEL", _OPENAI_FALLBACK_DEEP)


def openai_fallback_model(model: str) -> str:
    """Map an active-provider model to the direct-OpenAI model to retry with."""
    if model == DEEP_MODEL:
        return _OPENAI_FALLBACK_DEEP
    if model == VISION_MODEL:
        return _OPENAI_FALLBACK_VISION
    return _OPENAI_FALLBACK_CHAT


# Model families that reject custom temperature and expect
# max_completion_tokens instead of max_tokens.
_REASONING_PREFIXES = ("gpt-5", "o1", "o3", "o4")


def is_reasoning_model(model: str) -> bool:
    return any(model.startswith(p) for p in _REASONING_PREFIXES)


def prepare_chat_params(kwargs: dict) -> dict:
    """Adapt chat.completions params to the target model family (returns a new
    dict). Call sites build params for the classic (gpt-4.x / DeepSeek) family;
    this converts them when a reasoning model is configured."""
    out = dict(kwargs)
    model = out.get("model", "")
    if is_reasoning_model(model):
        out.pop("temperature", None)
        if "max_tokens" in out:
            out["max_completion_tokens"] = out.pop("max_tokens")
    return out


# ---------------------------------------------------------------------------
# Client factories (lazy openai import: some light import paths avoid the dep)
# ---------------------------------------------------------------------------
def _openrouter_headers():
    # Optional attribution headers OpenRouter uses for rankings/dashboards.
    headers = {}
    ref = os.getenv("OPENROUTER_SITE_URL")
    title = os.getenv("OPENROUTER_APP_NAME", "KurimaSense")
    if ref:
        headers["HTTP-Referer"] = ref
    if title:
        headers["X-Title"] = title
    return headers or None


def make_text_client(async_: bool = False):
    """OpenAI-SDK client for chat/vision completions. Points at OpenRouter when
    OPENROUTER_API_KEY is set, else direct OpenAI. Returns None if neither key
    is configured."""
    from openai import OpenAI, AsyncOpenAI
    cls = AsyncOpenAI if async_ else OpenAI
    if use_openrouter():
        return cls(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            default_headers=_openrouter_headers(),
        )
    key = os.getenv("OPENAI_API_KEY")
    if not _valid(key):
        return None
    return cls(api_key=key)


def make_openai_client(async_: bool = False):
    """DIRECT OpenAI client — required for embeddings + TTS (not on OpenRouter),
    and used as the chat fallback. Returns None if OPENAI_API_KEY is unset."""
    from openai import OpenAI, AsyncOpenAI
    key = os.getenv("OPENAI_API_KEY")
    if not _valid(key):
        return None
    cls = AsyncOpenAI if async_ else OpenAI
    return cls(api_key=key)


def text_chat_completion(**kwargs):
    """Synchronous chat completion routed to the active text provider, with a
    one-shot fallback to direct OpenAI (equivalent tier model) if the primary
    provider errors. Accepts standard chat.completions.create kwargs and returns
    the raw response object."""
    primary = make_text_client(async_=False)
    if primary is None:
        raise RuntimeError(
            "No LLM text client configured — set OPENROUTER_API_KEY or OPENAI_API_KEY."
        )
    try:
        return primary.chat.completions.create(**prepare_chat_params(kwargs))
    except Exception:
        # Only fall back when the primary was OpenRouter and a distinct OpenAI
        # key exists; otherwise re-raise the original error.
        if not use_openrouter():
            raise
        fb = make_openai_client(async_=False)
        if fb is None:
            raise
        fb_kwargs = dict(kwargs)
        fb_kwargs["model"] = openai_fallback_model(kwargs.get("model", CHAT_MODEL))
        return fb.chat.completions.create(**prepare_chat_params(fb_kwargs))
