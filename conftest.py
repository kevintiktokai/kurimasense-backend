"""
Pytest configuration for the KurimaSense backend suite.

Most tests are deterministic and hermetic (pure engines + faked DB), so they run
anywhere. A few need external resources that aren't available in CI:

  * test_ai_knowledge.py  — asserts a live Postgres connection (DATABASE_URL).
  * test_storage.py       — same, and imports via a `backend.` path that only
                            resolves in a differently-rooted checkout.
  * test_rag_pipeline.py  — calls the embeddings/LLM stack (needs OPENAI_API_KEY
                            + network).

Rather than hardcode an ignore list in the CI workflow (which silently rots as
tests move), we skip those modules here *only when their prerequisite env is
absent*. So a developer with DATABASE_URL/OPENAI_API_KEY set still runs the full
suite locally, while CI (no secrets) runs the deterministic majority green.
"""

import os

collect_ignore = []

if not os.environ.get("DATABASE_URL"):
    collect_ignore += ["tests/test_ai_knowledge.py", "tests/test_storage.py"]

if not os.environ.get("OPENAI_API_KEY"):
    collect_ignore += ["tests/test_rag_pipeline.py"]
