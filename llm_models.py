"""
Central LLM model selection — single source of truth for every OpenAI call.

Previously each call site hardcoded its model (six sites across ai_brain,
climate_service and tools/), all pinned to mid-2024 models (gpt-4o-mini /
gpt-4o). This module upgrades the defaults and makes every tier overridable via
env, so future model bumps are a Render env-var change, not a code change.

Tiers (audit, July 2026):
- CHAT_MODEL   — conversational/agronomy chat, insights, structured extraction.
                 Default gpt-4.1-mini: drop-in upgrade over gpt-4o-mini (same
                 param semantics, materially smarter + cheaper).
- DEEP_MODEL   — full crop-plan generation and other quality-critical outputs.
                 Default gpt-4.1 (drop-in upgrade over gpt-4o).
- VISION_MODEL — image diagnosis. Default gpt-4.1 (strong vision).

`prepare_chat_params` keeps the door open to reasoning-family models
(gpt-5*/o-series) via env override: those models reject non-default temperature
and use max_completion_tokens, so params are adapted per-model instead of
erroring at request time.
"""

import os

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
DEEP_MODEL = os.getenv("OPENAI_DEEP_MODEL", "gpt-4.1")
VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", DEEP_MODEL)

# Model families that reject custom temperature and expect
# max_completion_tokens instead of max_tokens.
_REASONING_PREFIXES = ("gpt-5", "o1", "o3", "o4")


def is_reasoning_model(model: str) -> bool:
    return any(model.startswith(p) for p in _REASONING_PREFIXES)


def prepare_chat_params(kwargs: dict) -> dict:
    """Adapt chat.completions params to the target model family in place-safe
    fashion (returns a new dict). Call sites build params for the classic
    (gpt-4.x) family; this converts them when a reasoning model is configured."""
    out = dict(kwargs)
    model = out.get("model", "")
    if is_reasoning_model(model):
        out.pop("temperature", None)
        if "max_tokens" in out:
            out["max_completion_tokens"] = out.pop("max_tokens")
    return out
