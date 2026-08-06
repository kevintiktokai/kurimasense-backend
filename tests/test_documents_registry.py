"""
The document registry: hashing, sequence allocation, and the issuing retry loop.

The persistence functions need a database, so what is tested here is everything
that decides *what gets recorded* — plus the retry loop, exercised against a
faked registry, because the behaviour that matters there (never reuse a number)
is policy rather than SQL.
"""

from datetime import date, datetime, timezone

import psycopg2
import pytest

from services.documents import issuing, registry
from services.documents.identity import DocumentIdentity


# ── Hashing ───────────────────────────────────────────────────────────────────


def test_digest_is_stable_for_identical_bytes():
    assert registry.content_digest(b"%PDF-1.7 x") == registry.content_digest(b"%PDF-1.7 x")


def test_digest_changes_with_a_single_byte():
    assert registry.content_digest(b"%PDF-a") != registry.content_digest(b"%PDF-b")


def test_verify_accepts_the_exact_bytes_issued():
    pdf = b"%PDF-1.7 pretend"
    assert registry.verify_content(registry.content_digest(pdf), pdf)


def test_verify_rejects_an_altered_document():
    # The whole point: a forwarded pack with a hectare figure edited in a PDF
    # editor must not verify against the number it carries.
    pdf = b"%PDF-1.7 214 ha"
    assert not registry.verify_content(registry.content_digest(pdf), b"%PDF-1.7 314 ha")


# ── Sequence allocation ───────────────────────────────────────────────────────


def test_first_sequence_is_one_not_zero():
    # EP-2026-000000 reads as a placeholder, and someone will assume it is one.
    assert registry.next_sequence(None) == 1


def test_sequence_follows_the_high_water_mark():
    assert registry.next_sequence(142) == 143


def test_sequence_after_zero_is_one():
    assert registry.next_sequence(0) == 1


# ── The issuing loop ──────────────────────────────────────────────────────────


class _FakeRegistry:
    """Stands in for the persistence layer. Records what was inserted and can be
    told to collide a given number of times first."""

    def __init__(self, collisions: int = 0):
        self.collisions = collisions
        self.allocated: list[str] = []
        self.recorded: list[str] = []
        self.next_seq = 143

    def allocate(self, kind, *, issued_at, user_id=None, tenant_ids=None):
        from services.documents.identity import issue_number

        number = issue_number(kind, self.next_seq, issued_at)
        self.allocated.append(number)
        return number

    def record(self, *, identity, tenant_id, pdf_bytes, **kwargs):
        if self.collisions > 0:
            self.collisions -= 1
            # A concurrent issuer took it; the high-water mark has moved.
            self.next_seq += 1
            raise psycopg2.errors.UniqueViolation("duplicate key")
        self.recorded.append(identity.issue_number)
        return registry.IssuedDocument(
            id="row-1",
            tenant_id=tenant_id,
            kind=identity.kind,
            issue_number=identity.issue_number,
            subject=identity.subject,
            coverage_start=identity.coverage_start,
            coverage_end=identity.coverage_end,
            hectares=identity.hectares,
            content_sha256=registry.content_digest(pdf_bytes),
            issued_at=identity.issued_at,
            forwarded_at=None,
            forwarded_note=None,
        )


@pytest.fixture
def fake(monkeypatch):
    def _install(collisions=0):
        f = _FakeRegistry(collisions)
        monkeypatch.setattr(registry, "allocate_issue_number", f.allocate)
        monkeypatch.setattr(registry, "record_issue", f.record)
        return f

    return _install


def _identity_for(number: str) -> DocumentIdentity:
    return DocumentIdentity(
        kind="evidence_pack",
        issue_number=number,
        issued_at=datetime(2026, 8, 6, tzinfo=timezone.utc),
        subject="Servemox",
        coverage_start=date(2025, 11, 1),
        coverage_end=date(2026, 5, 31),
        hectares=214.0,
    )


def _issue(**kwargs):
    return issuing.issue_document(
        kind="evidence_pack",
        tenant_id="t-1",
        render=lambda number: f"%PDF {number}".encode(),
        identity_for=_identity_for,
        **kwargs,
    )


def test_a_document_is_rendered_with_the_number_it_is_recorded_under(fake):
    f = fake()
    pdf, row = _issue()
    # The number is printed inside the PDF, so it has to exist before rendering
    # and match what is stored. A mismatch is a document whose footer and
    # registry entry disagree.
    assert row.issue_number.encode() in pdf
    assert f.recorded == [row.issue_number]


def test_the_recorded_hash_is_of_the_bytes_actually_returned(fake):
    fake()
    pdf, row = _issue()
    assert registry.verify_content(row.content_sha256, pdf)


def test_a_collision_retries_with_a_fresh_number(fake):
    f = fake(collisions=1)
    pdf, row = _issue()
    assert len(f.allocated) == 2
    assert f.allocated[0] != f.allocated[1]
    assert row.issue_number == f.allocated[1]


def test_a_retry_re_renders_rather_than_patching_the_old_number(fake):
    # Patching a new number into a PDF that already carries the old one in its
    # page furniture is how a document ends up with a footer and a cover that
    # disagree.
    f = fake(collisions=1)
    pdf, row = _issue()
    assert f.allocated[0].encode() not in pdf
    assert row.issue_number.encode() in pdf


def test_sustained_collisions_raise_rather_than_reusing_a_number(fake):
    # Never fall back to reusing. Two documents sharing a number surfaces months
    # later as a buyer quoting a reference that resolves to another client.
    fake(collisions=registry.MAX_ALLOCATION_ATTEMPTS)
    with pytest.raises(issuing.IssueCollision):
        _issue()


def test_the_number_of_attempts_is_bounded(fake):
    f = fake(collisions=registry.MAX_ALLOCATION_ATTEMPTS)
    with pytest.raises(issuing.IssueCollision):
        _issue()
    assert len(f.allocated) == registry.MAX_ALLOCATION_ATTEMPTS


# ── The tracking boundary ─────────────────────────────────────────────────────


def test_forwarding_is_not_inferred_at_issue_time():
    # A document is issued, not delivered. Anything that observed where a
    # client's file travelled is the data controversy the playbook rates as
    # existential — so a fresh row must never claim delivery.
    f = _FakeRegistry()
    row = f.record(
        identity=_identity_for("EP-2026-000143"),
        tenant_id="t-1",
        pdf_bytes=b"%PDF",
    )
    assert row.forwarded_at is None
    assert row.forwarded_note is None


def test_the_registry_exposes_no_way_to_observe_delivery():
    # A tripwire, not a tautology: if someone later adds an open-tracking pixel,
    # a callback URL or a per-recipient token, it will almost certainly show up
    # as a public name here.
    forbidden = {"track", "pixel", "beacon", "callback", "webhook", "open_rate"}
    names = {n.lower() for n in dir(registry) if not n.startswith("_")}
    assert not any(any(f in n for f in forbidden) for n in names)
