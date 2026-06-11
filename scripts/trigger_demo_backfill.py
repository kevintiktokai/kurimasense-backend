#!/usr/bin/env python3
"""
Trigger demo satellite backfill via the API (follow-up to MVP PR 1)
==================================================================
Reads ``scripts/.demo_backfill_queue.txt`` (the field-id queue written by
``seed_demo_fields.py``), and for each field id calls
``POST /fields/{id}/analyze`` on the deployed backend with a short delay between
calls (respecting Sentinel Hub rate limits).

Unlike ``backfill_demo_fields.py`` (which runs server-side on Render using the
Sentinel creds directly), this trigger runs from anywhere with your session
token and just kicks off the existing per-field analysis.

Usage:
    python scripts/trigger_demo_backfill.py \
        --base-url https://kurimasense-backend.onrender.com \
        --token "$JWT"

Exits gracefully (code 0) if the queue file does not exist.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.error
import urllib.request

QUEUE_FILE = os.path.join(os.path.dirname(__file__), ".demo_backfill_queue.txt")


def read_queue(path: str) -> list[str]:
    """Return the field ids in the queue file (one per line), or [] if missing."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def trigger(base_url: str, token: str, field_id: str) -> int:
    """POST /fields/{id}/analyze. Returns the HTTP status code (0 on transport error)."""
    url = f"{base_url.rstrip('/')}/fields/{field_id}/analyze"
    req = urllib.request.Request(url, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Trigger demo field backfill via POST /fields/{id}/analyze.")
    ap.add_argument("--base-url", required=True, help="Backend base URL, e.g. https://kurimasense-backend.onrender.com")
    ap.add_argument("--token", required=True, help="Supabase session access token (Bearer JWT)")
    ap.add_argument("--queue", default=QUEUE_FILE, help="Path to the field-id queue file")
    ap.add_argument("--delay", type=float, default=3.0, help="Seconds between calls (default 3)")
    args = ap.parse_args(argv)

    field_ids = read_queue(args.queue)
    if not field_ids:
        print(f"No queue file at {args.queue} (or it is empty). Nothing to trigger.")
        return 0

    n = len(field_ids)
    print(f"Triggering backfill for {n} field(s) via {args.base_url} …")
    for i, fid in enumerate(field_ids, 1):
        status = trigger(args.base_url, args.token, fid)
        suffix = "" if status in (200, 201, 202) else f" (HTTP {status})"
        print(f"[{i}/{n}] Triggered backfill for field {fid}{suffix}")
        if i < n:
            time.sleep(args.delay)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
