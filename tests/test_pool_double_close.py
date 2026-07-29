"""Connection-pool safety.

REGRESSION (July 2026): production logs showed two errors on repeat —

    Variety lookup error: tuple indices must be integers or slices, not str
    Variety lookup error: connection already closed

They were the SAME bug. A very common shape in this codebase is::

    row = cursor.fetchone()
    cursor.close(); conn.close()      # -> returned to the pool
    return {"x": row["x"]}            # raises -> except: conn.close()

so the error path returned the connection a SECOND time. psycopg2's putconn
raises PoolError("trying to put unkeyed connection") on that second call, and
_PooledConn.close() reacted by calling conn.close() for real — physically
closing a socket that was by then sitting in the pool marked AVAILABLE. The
next request to draw it got "connection already closed".

Self-amplifying: every double-close permanently burned one of the 20 pooled
connections, so unrelated endpoints degraded as the pool rotted.

These tests run against a REAL PostgreSQL (POSTGRES_TEST_DSN), because the bug
lives in psycopg2's pool bookkeeping — a mock would prove nothing.
"""

import os
import pytest

psycopg2 = pytest.importorskip("psycopg2")
from psycopg2.pool import ThreadedConnectionPool  # noqa: E402

import database  # noqa: E402

DSN = os.environ.get("POSTGRES_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="needs POSTGRES_TEST_DSN")


@pytest.fixture
def pool():
    p = ThreadedConnectionPool(minconn=2, maxconn=4, dsn=DSN)
    yield p
    p.closeall()


def test_double_close_does_not_poison_the_pool(pool):
    """The exact production sequence: close on the happy path, close again in
    the error handler. The connection must stay usable for the NEXT caller."""
    conn = database._PooledConn(pool, pool.getconn())
    raw = conn._conn

    conn.close()   # happy path — returned to the pool
    conn.close()   # error handler — must be a no-op, NOT a physical close

    assert raw.closed == 0, "double close physically closed a pooled connection"

    # And the pool still hands out a working connection.
    c2 = database._PooledConn(pool, pool.getconn())
    cur = c2.cursor()
    cur.execute("SELECT 1")
    assert cur.fetchone()[0] == 1
    cur.close()
    c2.close()


def test_repeated_double_closes_do_not_exhaust_the_pool(pool):
    """Burn far more connections than the pool holds. Before the fix each
    iteration killed one; the pool was unusable within a handful of calls."""
    for _ in range(25):
        c = database._PooledConn(pool, pool.getconn())
        c.close()
        c.close()  # the bug

    c = database._PooledConn(pool, pool.getconn())
    cur = c.cursor()
    cur.execute("SELECT 42")
    assert cur.fetchone()[0] == 42
    cur.close()
    c.close()


def test_context_manager_exit_then_explicit_close_is_safe(pool):
    """`with get_db_connection() as conn:` followed by a close in an except
    block is the same double-close via a different route."""
    c = database._PooledConn(pool, pool.getconn())
    raw = c._conn
    with c:
        pass          # __exit__ -> close()
    c.close()         # explicit second close
    assert raw.closed == 0


def test_get_db_connection_never_returns_a_closed_connection(monkeypatch, pool):
    """A connection can die while idle (server restart, pooler timeout). The
    request that happens to draw it must not be the one that fails."""
    # Simulate a connection that died WHILE SITTING IDLE — the real scenario
    # (server restart, Supabase pooler idle timeout, or the double-close bug
    # above). It has to be injected into the idle list directly: putconn()
    # discards an already-closed connection, so it can't reproduce this.
    dead = pool.getconn()
    pool.putconn(dead)
    assert dead in pool._pool
    dead.close()                       # dies in place, still listed as available
    # getconn() pops from the END of the idle list, so put it there.
    pool._pool.remove(dead)
    pool._pool.append(dead)

    monkeypatch.setattr(database, "_get_pool", lambda: pool)
    conn = database.get_db_connection()

    assert conn is not None, "should have discarded the dead connection and retried"
    assert conn._conn.closed == 0
    cur = conn.cursor()
    cur.execute("SELECT 7")
    assert cur.fetchone()[0] == 7
    cur.close()
    conn.close()
