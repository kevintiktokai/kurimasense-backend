"""
The document registry: what was issued, to whom, and what it claimed.

An issue number printed on a page is decoration until something on our side can
say what it refers to. A buyer quotes ``EP-2026-000143`` back six months after a
contractor forwarded it, and the answer has to be a record, not a shrug.

Pure decisions live in the functions at the top of this module and are unit
tested without a database; the SQL is below them, following the split used by
``services/seasons/repository.py``.

.. note::

   **This records issuance, not delivery.** There is no open tracking, no
   callback, no per-recipient token, and there never should be. The playbook
   rates a data controversy as existential, and a producer mark that quietly
   reports on where a client's file travelled is precisely that. ``forwarded_at``
   is set only when a client tells us they sent it.

   :func:`verify_content` gives the useful half of tracking without the harmful
   half: someone holding a PDF can be told whether it is byte-for-byte the
   document issued under that number. Verification, not surveillance.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

from psycopg2.extras import RealDictCursor

from database import get_db_connection

from .identity import DocumentIdentity, issue_number

#: How many times to retry sequence allocation when two documents are issued at
#: the same instant. Each retry re-reads the high-water mark, so contention has
#: to be sustained to exhaust this — and exhausting it should raise rather than
#: silently reuse a number.
MAX_ALLOCATION_ATTEMPTS = 5


class RegistryError(RuntimeError):
    """Raised when a document cannot be issued a number it can keep."""


# ── Pure ──────────────────────────────────────────────────────────────────────


def content_digest(pdf_bytes: bytes) -> str:
    """
    The hash recorded against an issued document.

    SHA-256 of the exact bytes sent. Not of the source data: two renders of the
    same data are not byte-identical (the timestamp alone differs), and the
    question being answered is "is this the file we issued", not "does this
    describe the same season".
    """
    return hashlib.sha256(pdf_bytes).hexdigest()


def next_sequence(current_max: int | None) -> int:
    """
    The next sequence for a (kind, year).

    Starts at 1, not 0: ``EP-2026-000000`` reads as a placeholder and someone
    will assume it is one.
    """
    return (current_max or 0) + 1


def verify_content(recorded_digest: str, pdf_bytes: bytes) -> bool:
    """Whether a PDF is byte-for-byte the one issued under a number."""
    return content_digest(pdf_bytes) == recorded_digest


@dataclass(frozen=True)
class IssuedDocument:
    """A row of the registry."""

    id: str
    tenant_id: str
    kind: str
    issue_number: str
    subject: str
    coverage_start: date | None
    coverage_end: date | None
    hectares: float | None
    content_sha256: str
    issued_at: datetime
    forwarded_at: datetime | None
    forwarded_note: str | None


_COLS = """
    id::text AS id, tenant_id::text AS tenant_id, kind, issue_number,
    subject, coverage_start, coverage_end, hectares, content_sha256,
    issued_at, forwarded_at, forwarded_note
"""


def _row(record: dict[str, Any]) -> IssuedDocument:
    hectares = record.get("hectares")
    return IssuedDocument(
        id=record["id"],
        tenant_id=record["tenant_id"],
        kind=record["kind"],
        issue_number=record["issue_number"],
        subject=record["subject"],
        coverage_start=record.get("coverage_start"),
        coverage_end=record.get("coverage_end"),
        hectares=float(hectares) if hectares is not None else None,
        content_sha256=record["content_sha256"],
        issued_at=record["issued_at"],
        forwarded_at=record.get("forwarded_at"),
        forwarded_note=record.get("forwarded_note"),
    )


# ── Persistence ───────────────────────────────────────────────────────────────


def _conn(user_id: str | None, tenant_ids: list[str] | None):
    from tenancy import arm_rls_gucs

    conn = get_db_connection()
    if not conn:
        raise RegistryError("Database unavailable")
    arm_rls_gucs(conn, user_id, [str(t) for t in (tenant_ids or [])])
    return conn


def record_issue(
    *,
    identity: DocumentIdentity,
    tenant_id: str,
    pdf_bytes: bytes,
    issued_by_user_id: str | None = None,
    user_id: str | None = None,
    tenant_ids: list[str] | None = None,
) -> IssuedDocument:
    """
    Persist an issued document.

    Called *after* rendering, with the exact bytes that will be sent, so the
    recorded hash is the hash of what left the building rather than of a
    hypothetical re-render.
    """
    _, year, sequence = _parse(identity.issue_number)
    conn = _conn(user_id, tenant_ids)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"""
            INSERT INTO document_issues (
                tenant_id, kind, issue_number, issue_year, sequence,
                subject, coverage_start, coverage_end, hectares,
                content_sha256, issued_by_user_id, issued_at
            ) VALUES (
                %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::uuid, %s
            )
            RETURNING {_COLS}
            """,
            (
                tenant_id, identity.kind, identity.issue_number, year, sequence,
                identity.subject, identity.coverage_start, identity.coverage_end,
                identity.hectares, content_digest(pdf_bytes),
                issued_by_user_id, identity.issued_at,
            ),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    finally:
        _close(conn)
    return _row(dict(row))


def allocate_issue_number(
    kind: str,
    *,
    issued_at: datetime,
    user_id: str | None = None,
    tenant_ids: list[str] | None = None,
) -> str:
    """
    Reserve the next issue number for a kind, in the issue year.

    Read-then-insert races, so this is not run inside a transaction that holds a
    lock — the unique index on ``(kind, issue_year, sequence)`` is the arbiter,
    and a loser simply re-reads and tries again. Cheaper than a lock table, and
    the failure it prevents is the one that matters: two documents issued under
    the same number.

    The number is reserved by :func:`record_issue`, not here — this only reads
    the high-water mark, so callers must be prepared for the insert to conflict
    and retry the whole render. In practice ``issue_and_record`` does that.
    """
    conn = _conn(user_id, tenant_ids)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT MAX(sequence) AS m FROM document_issues "
            "WHERE kind = %s AND issue_year = %s",
            (kind, issued_at.year),
        )
        row = cur.fetchone()
        cur.close()
    finally:
        _close(conn)
    return issue_number(kind, next_sequence(row and row.get("m")), issued_at)


def get_by_issue_number(
    number: str,
    *,
    user_id: str | None = None,
    tenant_ids: list[str] | None = None,
) -> Optional[IssuedDocument]:
    """Look up what a quoted number refers to."""
    conn = _conn(user_id, tenant_ids)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"SELECT {_COLS} FROM document_issues WHERE issue_number = %s",
            (number.strip().upper(),),
        )
        row = cur.fetchone()
        cur.close()
    finally:
        _close(conn)
    return _row(dict(row)) if row else None


def list_for_tenant(
    tenant_id: str,
    *,
    kind: str | None = None,
    limit: int = 50,
    offset: int = 0,
    user_id: str | None = None,
    tenant_ids: list[str] | None = None,
) -> list[IssuedDocument]:
    """Everything issued for a client, newest first."""
    conn = _conn(user_id, tenant_ids)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if kind:
            cur.execute(
                f"SELECT {_COLS} FROM document_issues "
                f"WHERE tenant_id = %s::uuid AND kind = %s "
                f"ORDER BY issued_at DESC LIMIT %s OFFSET %s",
                (tenant_id, kind, limit, offset),
            )
        else:
            cur.execute(
                f"SELECT {_COLS} FROM document_issues "
                f"WHERE tenant_id = %s::uuid "
                f"ORDER BY issued_at DESC LIMIT %s OFFSET %s",
                (tenant_id, limit, offset),
            )
        rows = cur.fetchall()
        cur.close()
    finally:
        _close(conn)
    return [_row(dict(r)) for r in rows]


def mark_forwarded(
    number: str,
    *,
    note: str | None = None,
    when: datetime | None = None,
    user_id: str | None = None,
    tenant_ids: list[str] | None = None,
) -> Optional[IssuedDocument]:
    """
    Record that a client says they forwarded a document.

    **Self-reported.** Nothing in the document reports back, and nothing here
    infers delivery from anything. This exists so the playbook's "packs issued
    and forwarded" can be counted honestly — a client ticking a box — rather
    than by instrumenting a file that has left their building.
    """
    conn = _conn(user_id, tenant_ids)
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"UPDATE document_issues SET forwarded_at = COALESCE(%s, NOW()), "
            f"forwarded_note = %s WHERE issue_number = %s RETURNING {_COLS}",
            (when, note, number.strip().upper()),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    finally:
        _close(conn)
    return _row(dict(row)) if row else None


def _parse(number: str) -> tuple[str, int, int]:
    from .identity import parse_issue_number

    return parse_issue_number(number)


def _close(conn) -> None:
    try:
        conn.close()
    except Exception:  # pragma: no cover - close is best-effort
        pass
