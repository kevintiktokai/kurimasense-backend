"""
Document routes.

Generation needs a database, so what is covered here is everything that decides
*whether and how* a document goes out: tenant resolution, the coverage window,
the refusal to issue an empty report, the 404-not-403 rule on the registry, and
the guarantee that no endpoint can render without issuing.
"""

from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

import document_routes as routes
from services.documents import registry
from services.documents.field_report import build_field_report


class _User:
    def __init__(self, role="institutional", tenant_id="t-1", tenant_ids=("t-1",)):
        self.role = role
        self.user_id = "u-1"
        self.tenant_id = tenant_id
        self.tenant_ids = list(tenant_ids)


def _issued(tenant_id="t-1", number="EP-2026-000143"):
    return registry.IssuedDocument(
        id="row-1", tenant_id=tenant_id, kind="evidence_pack",
        issue_number=number, subject="Servemox",
        coverage_start=date(2025, 11, 1), coverage_end=date(2026, 5, 31),
        hectares=214.0, content_sha256="abc",
        issued_at=datetime(2026, 8, 6, tzinfo=timezone.utc),
        forwarded_at=None, forwarded_note=None,
    )


# ── Tenant resolution ─────────────────────────────────────────────────────────


def test_an_institutional_caller_gets_their_own_tenant():
    assert routes._tenant_for(_User(), None) == "t-1"


def test_an_institutional_caller_cannot_target_another_tenant():
    with pytest.raises(HTTPException) as exc:
        routes._tenant_for(_User(), "t-2")
    assert exc.value.status_code == 403


def test_passing_your_own_tenant_id_explicitly_is_fine():
    assert routes._tenant_for(_User(), "t-1") == "t-1"


def test_an_admin_may_target_any_tenant():
    assert routes._tenant_for(_User(role="admin"), "t-2") == "t-2"


@pytest.mark.parametrize("role", ["consumer", "viewer", ""])
def test_other_roles_are_refused(role):
    with pytest.raises(HTTPException) as exc:
        routes._tenant_for(_User(role=role), None)
    assert exc.value.status_code == 403


def test_a_caller_with_no_tenant_gets_400_not_a_document_for_nobody():
    with pytest.raises(HTTPException) as exc:
        routes._tenant_for(_User(tenant_id=None, tenant_ids=()), None)
    assert exc.value.status_code == 400


# ── Coverage window ───────────────────────────────────────────────────────────


def test_coverage_defaults_to_a_season_back_from_today():
    start, end = routes._coverage(None, None)
    assert end == date.today()
    assert (end - start).days == routes.DEFAULT_COVERAGE_DAYS


def test_an_explicit_start_is_kept():
    start, _ = routes._coverage(date(2025, 11, 1), date(2026, 5, 31))
    assert start == date(2025, 11, 1)


def test_a_backwards_period_is_refused_rather_than_swapped():
    # Swapping would produce a plausible document from a caller whose dates are
    # the wrong way round, and hide the bug that caused it.
    with pytest.raises(HTTPException) as exc:
        routes._coverage(date(2026, 5, 31), date(2025, 11, 1))
    assert exc.value.status_code == 400


def test_a_single_day_window_is_allowed():
    day = date(2026, 1, 5)
    assert routes._coverage(day, day) == (day, day)


# ── Registry visibility ───────────────────────────────────────────────────────


def test_your_own_document_is_visible():
    routes._assert_visible(_issued("t-1"), _User())


def test_another_tenants_document_is_404_not_403():
    # An issue number is quotable and sequential. 403 would confirm the number
    # exists and belongs to someone — enough to enumerate a competitor's volume.
    with pytest.raises(HTTPException) as exc:
        routes._assert_visible(_issued("t-2"), _User())
    assert exc.value.status_code == 404


def test_an_admin_sees_any_document():
    routes._assert_visible(_issued("t-2"), _User(role="admin"))


def test_serialisation_reports_what_the_document_claimed_at_issue_time():
    payload = routes._serialise(_issued())
    assert payload["hectares"] == 214.0
    assert payload["coverage_start"] == "2025-11-01"
    assert payload["content_sha256"] == "abc"


def test_a_fresh_document_is_not_serialised_as_forwarded():
    payload = routes._serialise(_issued())
    assert payload["forwarded_at"] is None and payload["forwarded_note"] is None


# ── Optional sections ─────────────────────────────────────────────────────────


def test_a_missing_section_is_absent_rather_than_fatal():
    # The engines decline rather than guess; a 404 from one must not take the
    # whole document down.
    def absent():
        raise HTTPException(status_code=404, detail="No establishment agronomy")

    assert routes._optional(absent) is None


def test_an_unprocessable_section_is_also_treated_as_absent():
    def unbuildable():
        raise HTTPException(status_code=422, detail="Nothing to plan")

    assert routes._optional(unbuildable) is None


def test_a_real_failure_propagates_rather_than_shortening_the_document():
    # A database error quietly becoming a shorter document is the failure this
    # guards: the reader cannot tell an absent section from a broken one.
    def broken():
        raise HTTPException(status_code=503, detail="Database unavailable")

    with pytest.raises(HTTPException) as exc:
        routes._optional(broken)
    assert exc.value.status_code == 503


def test_a_working_section_is_returned_unchanged():
    assert routes._optional(lambda: {"ok": True}) == {"ok": True}


# ── Stand check adaptation ────────────────────────────────────────────────────


def test_a_season_with_no_stand_data_yields_no_stand_check():
    # Rather than a StandCheck with everything None, which would suppress the
    # missing-stand-check note the field report exists to show.
    assert routes._stand_check_from({}) is None


def test_a_season_with_an_established_population_yields_one():
    check = routes._stand_check_from({
        "established_population_per_ha": 33000,
        "target_population_per_ha": 44000,
        "emergence_date": "2025-12-08",
    })
    assert check is not None
    assert check.achieved_share == pytest.approx(0.75)
    assert check.checked_on == date(2025, 12, 8)


def test_partial_stand_data_still_produces_a_check_so_it_can_be_qualified():
    # Present but unusable is a different conversation from never done.
    check = routes._stand_check_from({"established_population_per_ha": 33000})
    assert check is not None and check.achieved_share is None


# ── Refusing to issue nothing ─────────────────────────────────────────────────


def test_an_empty_field_report_has_no_content_to_issue():
    # The route turns this into a 422. A document with an issue number and no
    # findings reads as a clean bill of health for a field nobody looked at.
    report = build_field_report(
        field_name="Home Field",
        coverage_start=date(2025, 11, 1),
        coverage_end=date(2026, 5, 31),
    )
    assert not report.has_content


# ── The issue path ────────────────────────────────────────────────────────────


def test_the_response_is_named_by_its_issue_number(monkeypatch):
    # A copy saved to a desktop has to stay identifiable.
    response = routes._pdf(b"%PDF-1.7", _issued())
    assert "EP-2026-000143.pdf" in response.headers["content-disposition"]
    assert response.headers["x-document-issue-number"] == "EP-2026-000143"
    assert response.media_type == "application/pdf"


def test_the_pdf_is_returned_inline_for_review_before_sending():
    # A document nobody reviewed is how a wrong figure reaches a buyer.
    assert routes._pdf(b"%PDF", _issued()).headers["content-disposition"].startswith("inline")


def test_sustained_issue_contention_becomes_503_not_a_reused_number(monkeypatch):
    def collide(**kwargs):
        raise routes.issuing.IssueCollision("no number available")

    monkeypatch.setattr(routes.issuing, "issue_document", collide)
    with pytest.raises(HTTPException) as exc:
        routes._issue(
            kind="field_report", tenant_id="t-1", user=_User(),
            render=lambda n: b"%PDF", identity_for=lambda n: None,
        )
    assert exc.value.status_code == 503


def test_a_registry_outage_becomes_503_rather_than_an_unrecorded_document(monkeypatch):
    # The tempting failure mode is to hand over the PDF anyway. That is the
    # untracked copy that ends up forwarded.
    def unavailable(**kwargs):
        raise registry.RegistryError("Database unavailable")

    monkeypatch.setattr(routes.issuing, "issue_document", unavailable)
    with pytest.raises(HTTPException) as exc:
        routes._issue(
            kind="field_report", tenant_id="t-1", user=_User(),
            render=lambda n: b"%PDF", identity_for=lambda n: None,
        )
    assert exc.value.status_code == 503


def test_a_successful_issue_returns_the_rendered_bytes(monkeypatch):
    monkeypatch.setattr(
        routes.issuing, "issue_document",
        lambda **kwargs: (kwargs["render"]("FR-2026-000012"), _issued(number="FR-2026-000012")),
    )
    response = routes._issue(
        kind="field_report", tenant_id="t-1", user=_User(),
        render=lambda n: f"%PDF {n}".encode(), identity_for=lambda n: None,
    )
    assert response.body == b"%PDF FR-2026-000012"


# ── No back door ──────────────────────────────────────────────────────────────


def test_every_generating_endpoint_goes_through_the_issue_path():
    # A preview that skipped the registry is the obvious shortcut and exactly
    # the wrong one — the untracked copy is the one that gets forwarded. This
    # asserts no generator calls a renderer without _issue in the same function.
    import inspect

    source = inspect.getsource(routes)
    for name in ("generate_season_plan", "generate_field_report", "generate_portfolio_report"):
        body = source.split(f"def {name}(", 1)[1].split("\n@router", 1)[0]
        assert "_issue(" in body, name
        assert "render_pdf(" not in body, name
