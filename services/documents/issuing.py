"""
Issuing a document: allocate a number, render, record what was sent.

The three steps have to happen in that order and cannot be collapsed. The issue
number is printed *inside* the PDF, so it must exist before rendering; the hash
is of the rendered bytes, so it must be taken after. Between the two, another
process may have taken the number.

This module is the retry loop that makes that safe. It is separated from
``registry`` because registry is persistence and this is policy, and separated
from ``render`` because render must stay usable without a database — a preview,
a test, and a specimen all render without issuing anything.
"""

from __future__ import annotations

import logging
from typing import Callable

import psycopg2

from . import registry
from .identity import DocumentIdentity
from .render import utcnow

logger = logging.getLogger("kurimasense")


class IssueCollision(registry.RegistryError):
    """Raised when a number could not be secured after repeated attempts."""


def issue_document(
    *,
    kind: str,
    tenant_id: str,
    render: Callable[[str], bytes],
    identity_for: Callable[[str], DocumentIdentity],
    issued_by_user_id: str | None = None,
    user_id: str | None = None,
    tenant_ids: list[str] | None = None,
) -> tuple[bytes, registry.IssuedDocument]:
    """
    Issue a document and return ``(pdf_bytes, registry_row)``.

    ``render`` and ``identity_for`` both take the allocated issue number, since
    the number appears on every page and in the identity the verification line
    is built from.

    On a unique-constraint collision the whole thing is retried — including the
    render. Re-rendering is the cheap option here: the alternative is patching a
    new number into a PDF that already has the old one in its page furniture,
    which is exactly the kind of near-miss that produces a document whose footer
    and cover disagree.

    Exhausting the attempts raises. It must never fall back to reusing a number:
    two documents sharing one is the failure the registry exists to prevent, and
    it would surface months later as a buyer quoting a number that resolves to
    the wrong client's ground.
    """
    last_error: Exception | None = None

    for attempt in range(1, registry.MAX_ALLOCATION_ATTEMPTS + 1):
        number = registry.allocate_issue_number(
            kind, issued_at=utcnow(), user_id=user_id, tenant_ids=tenant_ids
        )
        pdf_bytes = render(number)
        identity = identity_for(number)

        try:
            row = registry.record_issue(
                identity=identity,
                tenant_id=tenant_id,
                pdf_bytes=pdf_bytes,
                issued_by_user_id=issued_by_user_id,
                user_id=user_id,
                tenant_ids=tenant_ids,
            )
        except psycopg2.errors.UniqueViolation as exc:
            # Someone else took the number between our read and our insert.
            last_error = exc
            logger.info(
                "document issue collision on %s (attempt %d/%d), retrying",
                number, attempt, registry.MAX_ALLOCATION_ATTEMPTS,
            )
            continue

        return pdf_bytes, row

    raise IssueCollision(
        f"could not allocate an issue number for {kind} after "
        f"{registry.MAX_ALLOCATION_ATTEMPTS} attempts"
    ) from last_error
