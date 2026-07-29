"""An empty field_id must never reach a uuid column.

REGRESSION (July 2026): the notifications scheduler logged

    invalid input syntax for type uuid: ""

on every cycle — every 15 minutes, indefinitely. `notifications.field_id` is a
real uuid column and Postgres does NOT treat '' as NULL; it is a hard error.
Generators build events from row dicts where a missing field id arrives as ""
rather than None, so the insert failed and those notifications were silently
never delivered.
"""

import os
import pytest

psycopg2 = pytest.importorskip("psycopg2")

from services.notifications.models import NotificationEvent  # noqa: E402

DSN = os.environ.get("POSTGRES_TEST_DSN")


def test_empty_field_id_is_normalised_to_none():
    for empty in ("", "   ", "\n"):
        ev = NotificationEvent(
            user_id="u1", category="irrigation", title="t", body="b", field_id=empty,
        )
        assert ev.field_id is None, f"{empty!r} must normalise to None"


def test_a_real_field_id_is_preserved():
    fid = "a9d7b847-c738-4983-b2d4-830c99445d50"
    ev = NotificationEvent(user_id="u1", category="irrigation", title="t", body="b", field_id=fid)
    assert ev.field_id == fid

    ev_none = NotificationEvent(user_id="u1", category="irrigation", title="t", body="b")
    assert ev_none.field_id is None


@pytest.mark.skipif(not DSN, reason="needs POSTGRES_TEST_DSN")
def test_postgres_rejects_empty_string_but_accepts_nullif():
    """Pins the actual database behaviour the bug depended on, so the two
    guards above are demonstrably guarding something real."""
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    try:
        cur = conn.cursor()
        cur.execute("CREATE TEMP TABLE _probe (id serial primary key, field_id uuid)")

        with pytest.raises(psycopg2.errors.InvalidTextRepresentation):
            cur.execute("INSERT INTO _probe (field_id) VALUES (%s::uuid)", ("",))

        # The repository's NULLIF guard makes the same input safe.
        cur.execute("INSERT INTO _probe (field_id) VALUES (NULLIF(%s, '')::uuid)", ("",))
        cur.execute("SELECT field_id FROM _probe")
        assert cur.fetchone()[0] is None

        # ...and a genuine uuid still round-trips.
        fid = "a9d7b847-c738-4983-b2d4-830c99445d50"
        cur.execute("INSERT INTO _probe (field_id) VALUES (NULLIF(%s, '')::uuid)", (fid,))
        cur.execute("SELECT field_id FROM _probe WHERE field_id IS NOT NULL")
        assert str(cur.fetchone()[0]) == fid
        cur.close()
    finally:
        conn.close()


def test_repository_insert_uses_nullif_for_field_id():
    from pathlib import Path
    src = Path(__file__).resolve().parent.parent / "services" / "notifications" / "repository.py"
    text = src.read_text()
    assert "NULLIF(%s, '')::uuid" in text, (
        "the notifications INSERT must guard field_id with NULLIF so a producer "
        "bypassing NotificationEvent cannot reintroduce the empty-uuid failure"
    )
