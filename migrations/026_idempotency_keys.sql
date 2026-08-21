-- 026: make a replayed capture land once.
--
-- THE PROBLEM
-- -----------
-- The grower app has an offline outbox (lib/offline/) because rural
-- connectivity is the norm, not the exception. It queues captures in IndexedDB
-- and drains them when a connection appears, retrying on failure — which is the
-- entire point of an outbox.
--
-- Retrying a POST has one dangerous case, and it is not the obvious one. If the
-- request never arrived, retrying is free. If the request arrived, the row was
-- committed, and only the *response* was lost, the client sees exactly the same
-- thing — a network error — and retries. Now the harvest is recorded twice.
--
-- That case is not rare here. It is the normal failure mode of a phone at the
-- edge of coverage, which is precisely the situation the outbox exists to serve.
-- A farmer logging a harvest on a bad connection is the intended user of this
-- feature, and duplicating their yield is a lie about their own field that they
-- then have to notice and undo.
--
-- `lib/http` refuses to retry POSTs for this exact reason. The outbox cannot
-- take that way out — retrying is its job — so it needs the other one.
--
-- THE ANCHOR ALREADY EXISTED
-- --------------------------
-- OutboxItem.id is a client-generated UUID, and its comment has always read
-- "stable across retries (idempotency anchor)". The value was there and stable
-- from the start; it was simply never put on the wire. This table is the other
-- half of a design that was already half-built.
--
-- WHAT IS STORED
-- --------------
-- The response, so a replay returns what the first attempt returned rather than
-- a bare "already done". The client is replaying because it never learned the
-- outcome; telling it "yes, and here is the record" is the answer it was
-- waiting for.
--
-- Scoped by user, so one caller's key can never return another caller's
-- response — a key is client-generated and therefore guessable.

CREATE TABLE IF NOT EXISTS idempotency_keys (
    -- Client-generated. Not a uuid column: clients may send any opaque token,
    -- and a malformed one should be rejected by length, not by a cast error.
    key TEXT NOT NULL,

    -- The caller. Part of the primary key so a guessed key from another user
    -- misses rather than replaying someone else's response.
    user_id TEXT NOT NULL,

    -- Method + path the key was first used for. A key replayed against a
    -- *different* endpoint is a client bug, and answering it with the first
    -- endpoint's response would be worse than refusing.
    endpoint TEXT NOT NULL,

    -- NULL until the request completes. A row with a NULL status is a claim:
    -- some request holds this key right now.
    response_status INTEGER,
    response_body JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    PRIMARY KEY (key, user_id)
);

-- Sweeping old keys. A key only needs to outlive the client's willingness to
-- retry; the outbox gives up long before this.
CREATE INDEX IF NOT EXISTS idx_idempotency_created
    ON idempotency_keys (created_at);

-- RLS. The table is keyed by user rather than tenant, so it takes the personal
-- policy shape (migration 010) rather than the ts_* tenant shape.
ALTER TABLE public.idempotency_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.idempotency_keys FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS us_idempotency_keys ON public.idempotency_keys;
CREATE POLICY us_idempotency_keys ON public.idempotency_keys
    FOR ALL
    USING (user_id = current_setting('app.user_id', true))
    WITH CHECK (user_id = current_setting('app.user_id', true));

-- Rollback:
--   DROP POLICY IF EXISTS us_idempotency_keys ON public.idempotency_keys;
--   DROP TABLE idempotency_keys;
