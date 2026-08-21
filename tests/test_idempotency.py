"""
A replayed capture lands once.

The offline outbox retries POSTs — that is what an outbox is for. The dangerous
case is the ambiguous one: the request arrived, the row was committed, and only
the response was lost. The client cannot tell that apart from "never arrived",
so it retries, and the harvest is recorded twice.

That is not an edge case here. It is the normal failure mode of a phone at the
edge of coverage, which is exactly the situation the outbox exists to serve. A
farmer logging a harvest on a bad connection is the *intended* user of the
feature, and duplicating their yield is a lie about their own field that they
then have to notice and undo.

`lib/http` avoids the problem by refusing to retry POSTs at all. The outbox
cannot take that way out, so the server has to recognise the second copy.
"""

import pathlib

import pytest

from services.idempotency.keys import (
    GUARDED_METHODS,
    MAX_KEY_LENGTH,
    StoredResponse,
    decide,
    endpoint_fingerprint,
    is_guarded,
    is_valid_key,
    normalise_key,
    should_remember,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent


# ── What gets guarded ────────────────────────────────────────────────────────

def test_only_mutating_methods_are_guarded():
    for method in ("POST", "PATCH", "PUT"):
        assert is_guarded(method, "a-real-key-value") is True, method
    # A GET replayed twice is a GET. Guarding it would spend a row per read.
    for method in ("GET", "HEAD", "OPTIONS", "DELETE"):
        assert is_guarded(method, "a-real-key-value") is False, method


def test_no_key_means_no_guard():
    # The guard is opt-in per request. Callers that do not send a key — every
    # surface except the outbox — behave exactly as before.
    assert is_guarded("POST", None) is False
    assert is_guarded("POST", "") is False


def test_the_method_set_is_the_one_the_middleware_uses():
    assert GUARDED_METHODS == frozenset({"POST", "PATCH", "PUT"})


# ── Key validation ───────────────────────────────────────────────────────────

def test_a_uuid_is_a_valid_key():
    # What the outbox actually sends: OutboxItem.id, whose comment has always
    # read "stable across retries (idempotency anchor)".
    assert is_valid_key("f47ac10b-58cc-4372-a567-0e02b2c3d479")


def test_absurd_and_empty_keys_are_refused():
    assert not is_valid_key("x" * (MAX_KEY_LENGTH + 1))
    assert not is_valid_key("short")
    assert not is_valid_key(None)
    assert not is_valid_key("   ")


def test_control_characters_are_refused():
    assert not is_valid_key("valid-prefix\n\rinjected")
    assert not is_valid_key("has a space in it")


def test_keys_are_not_case_folded():
    # An opaque client token. Two tokens differing only in case are two
    # different requests, and folding them would merge captures from different
    # devices into one.
    assert normalise_key("AbC-123-XyZ-999") != normalise_key("abc-123-xyz-999").upper().lower()
    assert normalise_key("  spaced-key-value  ") == "spaced-key-value"


# ── The 5xx rule ─────────────────────────────────────────────────────────────

def test_a_server_failure_is_not_remembered():
    # The rule that matters most. If the first attempt failed on our side, the
    # client must be able to genuinely retry. Replaying a stored 500 forever
    # would turn one bad moment into a permanently stuck capture — worse than
    # the duplicate this whole module exists to prevent.
    for status in (500, 502, 503, 504):
        assert should_remember(status) is False, status


def test_a_rate_limit_is_not_remembered_either():
    # Caught before this shipped. 429 and 408 are below 500, so a naive
    # `status < 500` remembers them — and the outbox treats both as *retriable*
    # (outbox.ts: status >= 500 || 408 || 429). So the client would retry, be
    # handed the stored 429 every single time, exhaust its attempts, and park
    # the capture as failed.
    #
    # A moment of rate limiting would become a permanently lost harvest, which
    # is strictly worse than the duplicate this module exists to prevent: a
    # duplicate is visible and recoverable, a capture that can never complete
    # is neither.
    for status in (408, 429):
        assert should_remember(status) is False, status


def test_the_remembered_set_is_the_complement_of_what_the_client_retries():
    # These two live in different repos and must agree. If they ever diverge,
    # the disagreement is silent and costs a farmer their record.
    from services.idempotency.keys import TRANSIENT_STATUSES

    assert TRANSIENT_STATUSES == frozenset({408, 429})
    for status in sorted(TRANSIENT_STATUSES) + [500, 502, 503]:
        assert should_remember(status) is False, status


def test_success_and_deterministic_client_errors_are_remembered():
    # 2xx because that is the outcome the client never heard.
    for status in (200, 201, 204):
        assert should_remember(status) is True, status
    # 4xx because it is deterministic: the same request will be rejected the
    # same way, and re-running it just to say so again is waste. 408 and 429
    # are deliberately absent — see above.
    for status in (400, 403, 404, 409, 422):
        assert should_remember(status) is True, status


# ── Endpoint binding ─────────────────────────────────────────────────────────

def test_a_key_is_bound_to_the_endpoint_it_was_first_used_for():
    # Answering POST /fields/y/harvest with the response from
    # POST /fields/x/harvest because a client reused a token would be a far
    # worse bug than the one being prevented.
    assert decide(
        method="POST",
        path="/fields/y/harvest",
        key="a-reused-key-value",
        existing_endpoint=endpoint_fingerprint("POST", "/fields/x/harvest"),
    ) == "conflict"


def test_the_same_endpoint_is_not_a_conflict():
    assert decide(
        method="POST",
        path="/fields/x/harvest",
        key="a-reused-key-value",
        existing_endpoint=endpoint_fingerprint("POST", "/fields/x/harvest"),
        existing=StoredResponse(status=201, body={"id": "abc"}),
    ) == "replay"


def test_method_is_part_of_the_fingerprint():
    assert endpoint_fingerprint("POST", "/x") != endpoint_fingerprint("PATCH", "/x")


# ── The decision table ───────────────────────────────────────────────────────

def test_an_unseen_key_proceeds():
    assert decide(method="POST", path="/x", key="never-seen-before-key") == "proceed"


def test_a_completed_key_replays():
    assert decide(
        method="POST",
        path="/x",
        key="already-done-key-here",
        existing_endpoint=endpoint_fingerprint("POST", "/x"),
        existing=StoredResponse(status=201, body={"ok": True}),
    ) == "replay"


def test_a_claimed_but_unfinished_key_is_in_flight():
    # Two drains racing the same item. The second is told to wait rather than
    # being allowed to create a second row.
    assert decide(
        method="POST",
        path="/x",
        key="in-progress-key-here",
        existing_endpoint=endpoint_fingerprint("POST", "/x"),
        claim_in_progress=True,
    ) == "in_flight"


def test_an_invalid_key_just_proceeds_rather_than_failing_the_request():
    # A malformed header must not cost the farmer their capture. The guard is a
    # safety net, and a safety net that drops requests is not one.
    assert decide(method="POST", path="/x", key="bad") == "proceed"
    assert decide(method="POST", path="/x", key="has spaces here") == "proceed"


# ── Wiring ───────────────────────────────────────────────────────────────────

def test_the_cors_preflight_allows_the_header():
    # Without this the browser blocks the preflight and the outbox silently
    # loses its duplicate protection — the requests still go through, just
    # unguarded, which is the worst of both worlds.
    app_source = (ROOT / "app.py").read_text()
    allow_headers = [
        line for line in app_source.splitlines()
        if "Access-Control-Allow-Headers" in line and not line.strip().startswith("#")
    ]
    assert allow_headers, "no Access-Control-Allow-Headers line found"
    assert all("Idempotency-Key" in line for line in allow_headers), allow_headers


def test_the_middleware_releases_the_claim_on_a_server_error():
    # Holding the claim after a 5xx would leave the capture permanently stuck:
    # the outbox replays, is told "still being processed", and never gets past
    # it. The release is what makes a retry actually a retry.
    app_source = (ROOT / "app.py").read_text()
    middleware = app_source.split("class IdempotencyMiddleware", 1)[1].split("\nclass ", 1)[0]
    assert "should_remember" in middleware
    assert middleware.count("release(") >= 2, (
        "expected a release on both the 5xx path and the exception path"
    )


def test_the_middleware_scopes_keys_to_a_subject():
    # A client-generated key is guessable. Without a per-user scope, one
    # caller's key could return another caller's stored response.
    app_source = (ROOT / "app.py").read_text()
    middleware = app_source.split("class IdempotencyMiddleware", 1)[1].split("\nclass ", 1)[0]
    assert "_idempotency_subject" in middleware
    assert "user_id" in middleware


def test_the_migration_scopes_the_key_by_user():
    migration = (ROOT / "migrations" / "026_idempotency_keys.sql").read_text()
    assert "PRIMARY KEY (key, user_id)" in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration


@pytest.mark.parametrize(
    "status,remembered",
    [(201, True), (422, True), (503, False), (429, False), (408, False)],
)
def test_the_rule_in_one_line(status, remembered):
    assert should_remember(status) is remembered
