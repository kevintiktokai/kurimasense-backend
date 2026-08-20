"""
Generating and looking up documents.

    POST /fields/{field_id}/documents/season-plan     — plan for the field
    POST /fields/{field_id}/documents/field-report    — one field, one season
    POST /portfolio/documents/evidence-pack           — the STP pack
    POST /portfolio/documents/portfolio-report        — the whole book
    GET  /documents                                   — what has been issued
    GET  /documents/{issue_number}                    — what a number refers to
    POST /documents/{issue_number}/forwarded          — client self-reports

Thin, per this repo's split: the agronomy is in ``services/planning`` and
``services/zones``, the assembly in ``services/documents``, the persistence in
``services/documents/registry``. This file resolves access, gathers what each
document needs, and hands over.

**Every document is issued, not merely rendered.** Generation goes through
``issuing.issue_document``, so a PDF cannot leave here without a registry row
recording what it claimed and a hash of the exact bytes. A preview path that
skipped the registry would be the obvious shortcut and exactly the wrong one:
the untracked copy is the one that ends up forwarded.

Existing endpoints are reused as callables rather than reimplemented — the same
reason ``section_routes.get_zone_diagnosis`` calls ``get_field_sections``. Two
views of one field must not disagree about which zone is which, and a document
disagreeing with the screen the farmer just read is worse than either alone.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field as PydanticField

from auth_roles import get_authenticated_user
from schemas import AuthenticatedUser
from services.documents import issuing, registry
from services.field_state.aggregator import (
    FieldAccessDenied, FieldNotFound, resolve_access,
)

logger = logging.getLogger("kurimasense")

router = APIRouter(tags=["documents"])

#: How far back a document's coverage window reaches when nothing else defines
#: it. A season, near enough — long enough to contain one, short enough that a
#: pack does not claim to cover ground observed two years ago.
DEFAULT_COVERAGE_DAYS = 240


def _resolve_field(field_id: str, user: AuthenticatedUser) -> dict:
    try:
        return resolve_access(
            field_id, user.user_id,
            tenant_ids=user.tenant_ids,
            is_admin=user.role == "admin",
        )
    except FieldNotFound:
        raise HTTPException(status_code=404, detail="Field not found")
    except FieldAccessDenied:
        raise HTTPException(status_code=403, detail="Access denied")


def _tenant_for(user: AuthenticatedUser, tenant_id: Optional[str]) -> str:
    """Resolve which tenant a portfolio-level document is for.

    Mirrors ``portfolio_routes``: institutional callers get their own tenant and
    are refused another's, admins may target one explicitly.
    """
    if user.role == "admin":
        target = tenant_id or user.tenant_id
    elif user.role == "institutional":
        if tenant_id is not None and tenant_id != user.tenant_id:
            raise HTTPException(
                status_code=403, detail="Cannot generate another tenant's document"
            )
        target = user.tenant_id
    else:
        raise HTTPException(status_code=403, detail="Institutional access only")
    if not target:
        raise HTTPException(status_code=400, detail="No tenant specified")
    return target


def _coverage(start: Optional[date], end: Optional[date]) -> tuple[date, date]:
    """A coverage window, defaulted but never invented backwards."""
    resolved_end = end or date.today()
    resolved_start = start or (resolved_end - timedelta(days=DEFAULT_COVERAGE_DAYS))
    if resolved_start > resolved_end:
        raise HTTPException(
            status_code=400, detail="Coverage period runs backwards"
        )
    return resolved_start, resolved_end


def _pdf(pdf_bytes: bytes, issued: registry.IssuedDocument) -> Response:
    """
    The PDF, named by its issue number.

    ``inline`` rather than ``attachment``: the caller is usually about to look
    at it before deciding whether to send it, and a document nobody reviewed is
    how a wrong figure reaches a buyer. The issue number is in the filename so
    that a copy saved to a desktop is still identifiable.
    """
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{issued.issue_number}.pdf"',
            "X-Document-Issue-Number": issued.issue_number,
        },
    )


def _issue(
    *,
    kind: str,
    tenant_id: str,
    user: AuthenticatedUser,
    render,
    identity_for,
) -> Response:
    """Shared issue-and-respond path, so no endpoint can skip the registry."""
    try:
        pdf_bytes, issued = issuing.issue_document(
            kind=kind,
            tenant_id=tenant_id,
            render=render,
            identity_for=identity_for,
            issued_by_user_id=user.user_id,
            user_id=user.user_id,
            tenant_ids=[str(t) for t in (user.tenant_ids or [])],
        )
    except issuing.IssueCollision:
        # Every attempt lost a race. Retrying immediately would probably lose
        # again; 503 tells the caller to come back rather than handing them a
        # document with a number that may not be theirs.
        logger.warning("issue-number contention generating %s", kind)
        raise HTTPException(
            status_code=503,
            detail="Could not allocate a document number just now. Try again.",
        )
    except registry.RegistryError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return _pdf(pdf_bytes, issued)


# ── Season plan ───────────────────────────────────────────────────────────────


@router.post("/fields/{field_id}/documents/season-plan")
def generate_season_plan(
    field_id: str,
    persona: Optional[str] = Query(
        None,
        description="Overrides the profile's persona. Unknown values fall back "
                    "to smallholder, never to the commercial profile.",
    ),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """The season's programme as a PDF the farmer can take into the field."""
    from season_lifecycle_routes import (
        get_action_windows, get_establishment_plan, get_fertiliser_plan,
    )
    from services.documents.render import render_season_plan
    from services.documents.season_plan import build_season_plan
    from services.documents.identity import DocumentIdentity
    from services.documents.render import utcnow

    field = _resolve_field(field_id, user)

    establishment = _optional(get_establishment_plan, field_id, user=user)
    fertiliser = _optional(get_fertiliser_plan, field_id, user=user)
    windows = _optional(get_action_windows, field_id, user=user) or {}

    planting = _as_date(field.get("planting_date"))
    start, end = _coverage(planting, None)

    plan = build_season_plan(
        field_name=field.get("name") or "Field",
        crop=field.get("crop_type") or "crop",
        variety=field.get("variety"),
        persona=persona or field.get("persona"),
        hectares=_as_float(field.get("size_hectares")),
        planned_planting_date=planting,
        coverage_start=start,
        coverage_end=end,
        establishment=establishment,
        fertiliser=fertiliser,
        windows=(windows.get("windows") if isinstance(windows, dict) else windows) or (),
    )

    return _issue(
        kind="season_plan",
        tenant_id=str(field.get("tenant_id") or user.tenant_id),
        user=user,
        render=lambda number: render_season_plan(plan, issue_number=number),
        identity_for=lambda number: DocumentIdentity(
            kind="season_plan", issue_number=number, issued_at=utcnow(),
            subject=plan.field_name, coverage_start=plan.coverage_start,
            coverage_end=plan.coverage_end, hectares=None,
        ),
    )


# ── Field report ──────────────────────────────────────────────────────────────


@router.post("/fields/{field_id}/documents/field-report")
def generate_field_report(
    field_id: str,
    season_id: Optional[str] = Query(
        None, description="Defaults to the field's active season."
    ),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """
    One field, one season.

    Refuses to issue an empty report. A document carrying an issue number and no
    findings reads as a clean bill of health for a field nobody looked at, which
    is worse than no document — so ``has_content`` is a 422, not a blank page.
    """
    from season_routes import get_principal
    from section_routes import get_zone_diagnosis
    from services.documents.field_report import build_field_report
    from services.documents.identity import DocumentIdentity
    from services.documents.render import render_field_report, utcnow

    field = _resolve_field(field_id, user)
    principal = {
        "requester_id": user.user_id,
        "tenant_ids": user.tenant_ids,
        "is_admin": user.role == "admin",
    }

    diagnosis = _optional(get_zone_diagnosis, field_id, principal=principal) or {}
    zones = diagnosis.get("zones", []) if isinstance(diagnosis, dict) else []

    season = _season_for(field_id, season_id, user)
    retrospective = None
    stand_check = None
    if season:
        retrospective = _optional(
            _retrospective_for, season["id"], user=user
        )
        stand_check = _stand_check_from(season)

    start, end = _coverage(
        _as_date((season or {}).get("planting_date")) or _as_date(field.get("planting_date")),
        None,
    )

    report = build_field_report(
        field_name=field.get("name") or "Field",
        grower_name=field.get("grower_name"),
        district=field.get("district"),
        hectares=_as_float(field.get("size_hectares")),
        crop_type=(season or {}).get("crop_type") or field.get("crop_type"),
        variety=(season or {}).get("variety") or field.get("variety"),
        season_label=(season or {}).get("season_label"),
        coverage_start=start,
        coverage_end=end,
        stand_check=stand_check,
        zones=zones,
        retrospective=retrospective,
    )

    if not report.has_content:
        raise HTTPException(
            status_code=422,
            detail=(
                "There is nothing to report on this field yet — no zone "
                "findings, no stand check and no closed season. Issuing a "
                "document now would read as a clean bill of health for a field "
                "nothing has been observed on."
            ),
        )

    return _issue(
        kind="field_report",
        tenant_id=str(field.get("tenant_id") or user.tenant_id),
        user=user,
        render=lambda number: render_field_report(report, issue_number=number),
        identity_for=lambda number: DocumentIdentity(
            kind="field_report", issue_number=number, issued_at=utcnow(),
            subject=report.field_name, coverage_start=report.coverage_start,
            coverage_end=report.coverage_end, hectares=None,
        ),
    )


# ── Portfolio report ──────────────────────────────────────────────────────────


@router.post("/portfolio/documents/portfolio-report")
async def generate_portfolio_report(
    tenant_id: Optional[str] = Query(None, description="Admin override."),
    anonymise: bool = Query(
        False,
        description=(
            "Replace grower and field names with labels. A guard against "
            "showing a real client's names in a prospect meeting — NOT consent "
            "to show the figures, which remain theirs."
        ),
    ),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """The whole book: scale, concentration, condition, attention list."""
    from services.documents.identity import DocumentIdentity
    from services.documents.portfolio_report import FieldRow, build_portfolio_report
    from services.documents.render import render_portfolio_report, utcnow
    from services.portfolio.aggregate import (
        TenantNotFound, compute_portfolio_aggregate,
    )

    target = _tenant_for(user, tenant_id)
    try:
        aggregate = await compute_portfolio_aggregate(target, requester_id=user.user_id)
    except TenantNotFound:
        raise HTTPException(status_code=404, detail="Tenant not found or not institutional")

    rows = [
        FieldRow(
            field_id=p.field_id,
            field_name=p.field_name,
            grower_id=p.grower_id,
            grower_name=p.grower_name,
            district=p.district,
            crop_type=p.crop_type,
            hectares=p.size_hectares,
            kurima_score=p.kurima_score,
            band=(p.kurima_label or "").lower() or None,
            urgency=p.urgency,
            primary_concern=p.primary_concern,
            days_since_observation=p.days_since_observation,
        )
        for p in aggregate.priorities
    ]

    start, end = _coverage(None, None)
    report = build_portfolio_report(
        client_name=aggregate.tenant.name,
        coverage_start=start,
        coverage_end=end,
        fields=rows,
        anonymise=anonymise,
    )

    return _issue(
        kind="portfolio_report",
        tenant_id=target,
        user=user,
        render=lambda number: render_portfolio_report(report, issue_number=number),
        identity_for=lambda number: DocumentIdentity(
            kind="portfolio_report", issue_number=number, issued_at=utcnow(),
            subject=report.client_name, coverage_start=report.coverage_start,
            coverage_end=report.coverage_end,
            hectares=report.hectares_observed or None,
        ),
    )


# ── Evidence pack ─────────────────────────────────────────────────────────────


@router.post("/portfolio/documents/evidence-pack")
def generate_evidence_pack(
    tenant_id: Optional[str] = Query(None, description="Admin override."),
    coverage_start: Optional[date] = Query(None),
    coverage_end: Optional[date] = Query(None),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """
    The pack a contractor forwards to a leaf buyer.

    The coverage window is a query parameter here and defaulted elsewhere,
    because this is the one document whose window is a claim: it appears in the
    verification line, and a contractor reporting on last season needs to say so
    rather than accept the last 240 days.
    """
    from services.documents.evidence_pack import build_evidence_pack
    from services.documents.evidence_repository import (
        EvidenceUnavailable, gather_growers,
    )
    from services.documents.identity import DocumentIdentity
    from services.documents.render import render_evidence_pack, utcnow

    target = _tenant_for(user, tenant_id)
    start, end = _coverage(coverage_start, coverage_end)

    try:
        growers = gather_growers(
            target, coverage_start=start, coverage_end=end,
            user_id=user.user_id,
            tenant_ids=[str(t) for t in (user.tenant_ids or [])],
        )
    except EvidenceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if not growers:
        raise HTTPException(
            status_code=422,
            detail=(
                "No fields in this portfolio for the period requested. An "
                "evidence pack covering nothing would still carry a mark."
            ),
        )

    pack = build_evidence_pack(
        client_name=_tenant_name(target, user),
        coverage_start=start,
        coverage_end=end,
        growers=growers,
    )

    return _issue(
        kind="evidence_pack",
        tenant_id=target,
        user=user,
        render=lambda number: render_evidence_pack(pack, issue_number=number),
        identity_for=lambda number: DocumentIdentity(
            kind="evidence_pack", issue_number=number, issued_at=utcnow(),
            subject=pack.client_name, coverage_start=pack.coverage_start,
            coverage_end=pack.coverage_end,
            hectares=pack.covered_hectares or None,
        ),
    )


# ── The registry ──────────────────────────────────────────────────────────────


class ForwardedRequest(BaseModel):
    note: Optional[str] = PydanticField(
        None, max_length=500,
        description="Who it went to, in the client's own words.",
    )


@router.get("/documents")
def list_documents(
    tenant_id: Optional[str] = Query(None, description="Admin override."),
    kind: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Everything issued for a client, newest first."""
    target = _tenant_for(user, tenant_id)
    rows = registry.list_for_tenant(
        target, kind=kind, limit=limit, offset=offset,
        user_id=user.user_id, tenant_ids=[str(t) for t in (user.tenant_ids or [])],
    )
    return {"documents": [_serialise(r) for r in rows]}


@router.get("/documents/{issue_number}")
def get_document(
    issue_number: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """
    What a quoted number refers to.

    Returns what the document claimed at issue time, not what the underlying
    data says now — that is the point of storing it. A buyer ringing up about
    EP-2026-000143 is asking about the paper in their hand.
    """
    row = registry.get_by_issue_number(
        issue_number,
        user_id=user.user_id,
        tenant_ids=[str(t) for t in (user.tenant_ids or [])],
    )
    if not row:
        raise HTTPException(status_code=404, detail="No document with that number")
    _assert_visible(row, user)
    return _serialise(row)


@router.post("/documents/{issue_number}/forwarded")
def mark_document_forwarded(
    issue_number: str,
    body: ForwardedRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """
    Record that the client says they forwarded this document.

    **Self-reported.** Nothing in the document reports back and nothing here
    infers delivery. This exists so "packs issued and forwarded" can be counted
    honestly — a client saying so — rather than by instrumenting a file that has
    left their building.
    """
    existing = registry.get_by_issue_number(
        issue_number,
        user_id=user.user_id,
        tenant_ids=[str(t) for t in (user.tenant_ids or [])],
    )
    if not existing:
        raise HTTPException(status_code=404, detail="No document with that number")
    _assert_visible(existing, user)

    row = registry.mark_forwarded(
        issue_number, note=body.note,
        user_id=user.user_id,
        tenant_ids=[str(t) for t in (user.tenant_ids or [])],
    )
    return _serialise(row) if row else {}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _assert_visible(row: registry.IssuedDocument, user: AuthenticatedUser) -> None:
    """404, not 403, for another tenant's document.

    An issue number is quotable and sequential. Answering 403 would confirm that
    a number exists and belongs to someone — enough to enumerate how many
    documents a competitor has issued.
    """
    if user.role == "admin":
        return
    owned = {str(t) for t in (user.tenant_ids or [])}
    if str(row.tenant_id) not in owned:
        raise HTTPException(status_code=404, detail="No document with that number")


def _serialise(row: registry.IssuedDocument) -> dict[str, Any]:
    return {
        "issue_number": row.issue_number,
        "kind": row.kind,
        "subject": row.subject,
        "coverage_start": row.coverage_start.isoformat() if row.coverage_start else None,
        "coverage_end": row.coverage_end.isoformat() if row.coverage_end else None,
        "hectares": row.hectares,
        "content_sha256": row.content_sha256,
        "issued_at": row.issued_at.isoformat() if row.issued_at else None,
        "forwarded_at": row.forwarded_at.isoformat() if row.forwarded_at else None,
        "forwarded_note": row.forwarded_note,
    }


def _optional(fn, *args, **kwargs):
    """
    Call a reused endpoint, treating "nothing to say" as absent.

    A section of a document that cannot be built is a missing section, not a
    failed request — the engines already decline rather than guess, and a 404
    from one of them must not take the whole document down. Anything else
    propagates: a database error should not quietly become a shorter document.
    """
    try:
        return fn(*args, **kwargs)
    except HTTPException as exc:
        if exc.status_code in (404, 422):
            return None
        raise


def _season_for(
    field_id: str, season_id: Optional[str], user: AuthenticatedUser
) -> Optional[dict]:
    from services.seasons import service as seasons

    try:
        if season_id:
            return seasons.get(season_id, user.user_id, user.tenant_ids)
        rows = seasons.list_for_field(field_id, user.user_id, user.tenant_ids)
    except Exception:  # pragma: no cover - absent season is not an error here
        return None
    if not rows:
        return None
    active = [r for r in rows if r.get("status") == "active"]
    return (active or rows)[0]


def _retrospective_for(season_id: str, *, user: AuthenticatedUser):
    from season_lifecycle_routes import get_season_retrospective

    return get_season_retrospective(season_id, user=user)


def _stand_check_from(season: dict):
    from services.documents.field_report import StandCheck

    established = _as_float(season.get("established_population_per_ha"))
    emergence = _as_date(season.get("emergence_date"))
    if established is None and emergence is None:
        return None
    return StandCheck(
        checked_on=emergence or date.today(),
        target_population_per_ha=_as_float(season.get("target_population_per_ha")),
        established_population_per_ha=established,
    )


def _tenant_name(tenant_id: str, user: AuthenticatedUser) -> str:
    """The client's name for the cover.

    Falls back to the id rather than to a blank cover: a pack headed by nothing
    is worse than one headed by a UUID, because the second is obviously wrong.
    """
    from database import get_db_connection

    conn = get_db_connection()
    if not conn:
        return tenant_id
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM tenants WHERE id = %s::uuid", (tenant_id,))
        row = cur.fetchone()
        cur.close()
    except Exception:  # pragma: no cover - a missing name must not block a pack
        return tenant_id
    finally:
        try:
            conn.close()
        except Exception:  # pragma: no cover
            pass
    return (row[0] if row and row[0] else tenant_id)


def _as_date(value: Any) -> Optional[date]:
    if value is None or isinstance(value, date):
        return value if isinstance(value, date) else None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
