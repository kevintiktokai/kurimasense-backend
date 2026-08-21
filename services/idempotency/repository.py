"""
Storage for idempotency keys. The SQL half; the decisions live in ``keys.py``.

Degrades open. If the database is unavailable, every function here behaves as
though the key had never been seen, so the request proceeds normally. That is
the right trade: the failure this guards against is a duplicate capture, and
refusing to accept a farmer's harvest because the bookkeeping table is down
would be a worse outcome than the duplicate.
"""

import json
import logging
from typing import Any, Optional, Tuple

from psycopg2.extras import RealDictCursor

from database import get_db_connection
from services.idempotency.keys import StoredResponse

logger = logging.getLogger("kurimasense")


def _conn(user_id: str):
    """A connection with the personal-scope GUC armed for the RLS policy."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        from tenancy import arm_rls_gucs

        arm_rls_gucs(conn, user_id, [])
    except Exception:
        logger.exception("could not arm GUCs for idempotency lookup")
        try:
            conn.close()
        except Exception:
            pass
        return None
    return conn


def lookup(key: str, user_id: str) -> Tuple[Optional[str], Optional[StoredResponse], bool]:
    """
    ``(endpoint, stored_response, claim_in_progress)`` for this key.

    ``(None, None, False)`` means never seen — or that we could not find out,
    which is treated the same way on purpose.
    """
    conn = _conn(user_id)
    if conn is None:
        return None, None, False
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT endpoint, response_status, response_body "
            "FROM idempotency_keys WHERE key = %s AND user_id = %s",
            (key, user_id),
        )
        row = cur.fetchone()
        cur.close()
    except Exception:
        logger.exception("idempotency lookup failed; treating as unseen")
        return None, None, False
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if not row:
        return None, None, False
    if row["response_status"] is None:
        return row["endpoint"], None, True
    return (
        row["endpoint"],
        StoredResponse(status=row["response_status"], body=row["response_body"]),
        False,
    )


def claim(key: str, user_id: str, endpoint: str) -> bool:
    """
    Stake this key before running the request.

    Returns False if somebody else got there first — the unique constraint is
    what makes two simultaneous drains of the same item safe, rather than a
    check-then-act that both sides pass.
    """
    conn = _conn(user_id)
    if conn is None:
        return True  # degrade open: proceed without the guard
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO idempotency_keys (key, user_id, endpoint) "
            "VALUES (%s, %s, %s) ON CONFLICT (key, user_id) DO NOTHING",
            (key, user_id, endpoint),
        )
        claimed = cur.rowcount == 1
        conn.commit()
        cur.close()
        return claimed
    except Exception:
        logger.exception("idempotency claim failed; proceeding unguarded")
        return True
    finally:
        try:
            conn.close()
        except Exception:
            pass


def complete(key: str, user_id: str, status: int, body: Any) -> None:
    """Record what the request returned, so a replay can be answered with it."""
    conn = _conn(user_id)
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE idempotency_keys SET response_status = %s, response_body = %s, "
            "completed_at = NOW() WHERE key = %s AND user_id = %s",
            (status, json.dumps(body) if body is not None else None, key, user_id),
        )
        conn.commit()
        cur.close()
    except Exception:
        logger.exception("could not record idempotent response")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def release(key: str, user_id: str) -> None:
    """
    Drop the claim so the client can genuinely retry.

    Called when the request failed on our side (5xx) or blew up. Holding the
    claim would leave the capture permanently stuck behind a key that never
    completes — the outbox would keep replaying and keep being told the request
    is already in flight, forever.
    """
    conn = _conn(user_id)
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM idempotency_keys WHERE key = %s AND user_id = %s "
            "AND response_status IS NULL",
            (key, user_id),
        )
        conn.commit()
        cur.close()
    except Exception:
        logger.exception("could not release idempotency claim")
    finally:
        try:
            conn.close()
        except Exception:
            pass
