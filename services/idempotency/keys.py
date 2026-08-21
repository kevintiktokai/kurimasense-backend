"""
Deciding what to do with a replayed request. Pure — no database, no FastAPI.

WHY THIS EXISTS
---------------
The grower app keeps an offline outbox because rural connectivity is the norm.
It queues captures and drains them when a connection appears, retrying on
failure — which is the whole point of an outbox.

Retrying a POST has one dangerous case, and it is not the obvious one. If the
request never arrived, retrying is free. If the request arrived, the row was
committed, and only the *response* was lost, the client sees exactly the same
thing — a network error — and retries. The harvest is now recorded twice.

That is the normal failure mode of a phone at the edge of coverage, which is
precisely the situation the outbox exists to serve. `lib/http` avoids it by
refusing to retry POSTs at all; the outbox cannot, because retrying is its job.
So the server has to be able to recognise the second copy.

THE RULE THAT MATTERS MOST HERE
-------------------------------
A 5xx is **not** remembered. If the first attempt failed on our side, the
client must be able to genuinely retry, and replaying a stored 500 forever
would turn one bad moment into a permanently stuck capture. Everything below
500 is remembered: a 2xx because that is the outcome the client never heard,
and a 4xx because it is deterministic — the same request will be rejected the
same way, and re-running it just to say so again is waste.
"""

from dataclasses import dataclass
from typing import Any, Optional

#: Generous but bounded. The outbox sends a UUID (36 chars); the ceiling is to
#: stop an unbounded header becoming an unbounded row.
MAX_KEY_LENGTH = 200
MIN_KEY_LENGTH = 8

#: Only these carry a risk worth guarding. A GET replayed twice is a GET.
GUARDED_METHODS = frozenset({"POST", "PATCH", "PUT"})


class IdempotencyConflict(Exception):
    """A key was reused for a different endpoint."""


@dataclass(frozen=True)
class StoredResponse:
    """What the first attempt returned, as recorded."""

    status: int
    body: Any


def is_guarded(method: str, key: Optional[str]) -> bool:
    """Whether this request should go through the idempotency path at all."""
    if not key:
        return False
    return method.upper() in GUARDED_METHODS


def normalise_key(key: str) -> str:
    """
    Trim, and nothing else.

    Deliberately not lowercased: the key is an opaque client token, and two
    clients sending tokens that differ only in case mean two different
    requests. Folding them together would merge captures from different
    devices.
    """
    return key.strip()


def is_valid_key(key: Optional[str]) -> bool:
    if not key:
        return False
    trimmed = normalise_key(key)
    if not (MIN_KEY_LENGTH <= len(trimmed) <= MAX_KEY_LENGTH):
        return False
    # Printable ASCII without whitespace. A header carrying control characters
    # is not a client we want to store rows on behalf of.
    return all(33 <= ord(c) <= 126 for c in trimmed)


def endpoint_fingerprint(method: str, path: str) -> str:
    """
    What the key was first used for.

    Stored so that a key replayed against a *different* endpoint can be
    refused. Answering `POST /fields/x/harvest` with the response from
    `POST /fields/y/harvest` because a client reused a token would be a far
    worse bug than the one this module exists to prevent.
    """
    return f"{method.upper()} {path}"


#: Statuses the client is expected to retry, and must therefore be free to.
#:
#: The exact complement of the outbox's own retriable set
#: (lib/offline/outbox.ts: ``status >= 500 || status === 408 || status === 429``).
#: The two have to agree. If the server remembers an outcome the client treats
#: as retriable, the client retries, is handed the remembered answer every
#: time, exhausts its attempts and parks the capture as failed — turning a
#: moment of rate limiting into a permanently lost harvest.
TRANSIENT_STATUSES = frozenset({408, 429})


def should_remember(status: int) -> bool:
    """
    Whether this outcome is worth storing against the key.

    False for anything the client will retry: 5xx, plus 408 and 429. A stored
    5xx makes a transient server failure permanent for that capture; a stored
    429 does the same for a moment of rate limiting. Both are worse than the
    duplicate this module exists to prevent, because a duplicate is at least
    visible and recoverable — a capture that can never complete is neither.

    True for the rest: 2xx because it is the outcome the client never heard,
    and other 4xx because they are deterministic — the same request will be
    rejected the same way, so re-running it to say so again is waste.
    """
    if status >= 500:
        return False
    return status not in TRANSIENT_STATUSES


def decide(
    *,
    method: str,
    path: str,
    key: Optional[str],
    existing_endpoint: Optional[str] = None,
    existing: Optional[StoredResponse] = None,
    claim_in_progress: bool = False,
) -> str:
    """
    What to do with this request. Returns one of:

      ``"proceed"``   — not guarded, or first time seeing this key
      ``"replay"``    — we know what the first attempt returned; return that
      ``"in_flight"`` — a claim exists with no outcome yet
      ``"conflict"``  — this key was used for a different endpoint

    Split out from the middleware so the decision can be tested without a
    database, a request object or a running app.
    """
    if not is_guarded(method, key) or not is_valid_key(key):
        return "proceed"

    if existing_endpoint is not None:
        if existing_endpoint != endpoint_fingerprint(method, path):
            return "conflict"

    if existing is not None:
        return "replay"
    if claim_in_progress:
        return "in_flight"
    return "proceed"
