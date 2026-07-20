"""ASGI entrypoint shim.

Railway's Railpack auto-detection starts the service with ``uvicorn main:app``,
but the FastAPI instance lives in ``app.py`` (i.e. ``app:app``). This module
re-exports it so ``main:app`` resolves too — the service now boots whether the
platform uses the Dockerfile (``app:app``) or Railpack's guessed ``main:app``.
No behaviour change: it is the same singleton app instance either way.
"""

from app import app  # noqa: F401  (re-exported for `uvicorn main:app`)
