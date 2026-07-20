"""ASGI entrypoint shim + portable launcher.

Two jobs:

1. Re-export the FastAPI instance so ``uvicorn main:app`` resolves (Railway's
   Railpack auto-detection guesses that module path; the instance lives in
   ``app.py``). Same singleton either way.

2. ``python main.py`` — the recommended start command everywhere. It picks the
   bind host at runtime:

   * IPv6 available  → ``::``  (dual-stack: accepts IPv6 AND IPv4-mapped).
     Railway's health prober and private network connect over IPv6, so an
     ``0.0.0.0`` bind is unreachable to them — the app runs while every probe
     gets connection refused (July 2026 incident).
   * IPv6 unavailable → ``0.0.0.0``. A hard-coded ``::`` crashes at boot in
     IPv4-only environments ("could not bind on any address"), verified in the
     dev sandbox — so neither family can be hard-coded portably.

   ``UVICORN_HOST`` overrides the detection; ``PORT`` sets the port (platform
   injected, default 8000).
"""

import os
import socket

from app import app  # noqa: F401  (re-exported for `uvicorn main:app`)


def pick_bind_host() -> str:
    """Dual-stack ``::`` when the environment supports IPv6, else ``0.0.0.0``."""
    override = os.environ.get("UVICORN_HOST")
    if override:
        return override
    if not socket.has_ipv6:
        return "0.0.0.0"
    try:
        probe = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        try:
            probe.bind(("::", 0))
        finally:
            probe.close()
        return "::"
    except OSError:
        return "0.0.0.0"


if __name__ == "__main__":
    import uvicorn

    host = pick_bind_host()
    port = int(os.environ.get("PORT", "8000"))
    print(f"🚀 Binding {host}:{port} (dual-stack={'yes' if host == '::' else 'no — IPv4 only'})")
    uvicorn.run("app:app", host=host, port=port)
