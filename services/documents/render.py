"""
Template + data -> PDF bytes.

The only module here that touches I/O. Everything it depends on
(:mod:`~services.documents.tokens`, :mod:`~services.documents.stylesheet`,
:mod:`~services.documents.identity`) is pure and importable without WeasyPrint
installed, which is what keeps the design system testable in a bare CI container.

**WeasyPrint is imported lazily**, inside :func:`render_pdf`. It pulls in Pango
and Cairo through system libraries, and importing it at module scope would make
the whole ``services.documents`` package — including the pure parts — unimportable
on a host that lacks them. A route that never generates a PDF should not care.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup

from . import tokens as t
from .evidence_pack import EvidencePack
from .portfolio_report import PortfolioReport
from .identity import CoverageError, DocumentIdentity, MARK, format_hectares
from .stylesheet import page_furniture_css, stylesheet

_HERE = Path(__file__).resolve().parent
TEMPLATES_DIR = _HERE / "templates"
FONTS_DIR = _HERE / "fonts"
ASSETS_DIR = _HERE / "assets"

#: Read by templates for the cover band's eyebrow. Kept here rather than in
#: `identity` because it is presentation: the same `kind` renders differently in
#: an issue number (`EP`) and on a cover ("Season Evidence Pack").
KIND_LABELS: dict[str, str] = {
    "evidence_pack": "Season Evidence Pack",
    "portfolio_report": "Portfolio Report",
    "field_report": "Field Report",
    "season_plan": "Season Plan",
}


def _environment() -> Environment:
    """
    Jinja configured for documents rather than for web pages.

    ``StrictUndefined`` is the important setting. In a web template a missing
    variable renders as empty and someone notices; in a document it renders as a
    blank cell in a table a bank is reading, and nobody notices until it matters.
    A missing value has to be an explicit "not measured", never an accident.
    """
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def build_context(
    identity: DocumentIdentity,
    *,
    title: str,
    title_accent: str | None = None,
    subtitle: str | None = None,
    embed_fonts: bool = True,
    **extra: Any,
) -> dict[str, Any]:
    """
    The variables :file:`base.html` needs, resolved once.

    The verification line is resolved *here* rather than in the template so the
    refusal path is explicit. If coverage cannot be honestly stated the document
    still renders — carrying a plain sentence saying why it has no verification
    line, which is far better than a document that silently drops the line and
    looks like every other one.
    """
    try:
        verification = identity.verification_line
        refusal = ""
    except CoverageError as exc:
        verification = ""
        refusal = str(exc)

    fonts_url = FONTS_DIR.as_uri() if embed_fonts and FONTS_DIR.is_dir() else None
    period_label = _period_label(identity)

    # The mark is optional so the templates render in a checkout without the
    # binary asset — but its absence is a missing logo, not a missing document,
    # so it degrades to the wordmark set in type rather than raising.
    mark_file = ASSETS_DIR / tokens_mark_filename()
    mark_url = mark_file.as_uri() if mark_file.is_file() else None

    context: dict[str, Any] = {
        "identity": identity,
        "title": title,
        "title_accent": title_accent,
        "subtitle": subtitle,
        "mark_url": mark_url,
        "kind_label": KIND_LABELS.get(identity.kind, identity.kind),
        "mark": MARK,
        "verification": verification,
        "verification_refusal": refusal,
        "period_label": period_label,
        "issued_label": identity.issued_at.strftime("%-d %B %Y"),
        # Marked safe explicitly, and only here. Autoescaping is on — it has to
        # be, since grower and field names reach these templates — but escaping
        # the stylesheet turns every `font-family: 'Fraunces'` into
        # `font-family: &#39;Fraunces&#39;`, which WeasyPrint discards as an
        # invalid value. It then drops the `@page` rules that carry the
        # verification line, and the document renders looking almost right with
        # no footer at all. `css_string` does the quoting for the one part that
        # *is* caller input (names, periods), so nothing unescaped gets in.
        "stylesheet": Markup(
            stylesheet(fonts_url)
            + "\n"
            + page_furniture_css(
                subject=identity.subject,
                period=period_label,
                verification=verification,
                issue_number=identity.issue_number,
            )
        ),
        "space": t.space,
    }
    context.update(extra)
    return context


def tokens_mark_filename() -> str:
    """Indirection so the mark's filename lives with the other brand tokens."""
    return t.MARK_FILENAME


def _period_label(identity: DocumentIdentity) -> str:
    start, end = identity.coverage_start, identity.coverage_end
    if start is None or end is None:
        return "Period not stated"
    return f"{start.strftime('%-d %b %Y')} – {end.strftime('%-d %b %Y')}"


def render_html(template_name: str, context: dict[str, Any]) -> str:
    """Render a document template to HTML. Separated out so tests can assert on
    structure without paying for a PDF."""
    return _environment().get_template(template_name).render(**context)


def render_pdf(template_name: str, context: dict[str, Any]) -> bytes:
    """
    Render a document template to PDF bytes.

    Returns bytes rather than writing a file: the caller decides whether this
    becomes an HTTP response, an email attachment or an object-store upload, and
    a document that only exists as a temp file on a container is a document that
    stops existing when the container does.
    """
    from weasyprint import HTML  # lazy — see module docstring

    html = render_html(template_name, context)
    return HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()


THEME_STATUS_LABELS: dict[str, str] = {
    "covered": "Evidenced",
    "partial": "Partially evidenced",
    "absent": "No evidence recorded",
    "not_applicable": "No fields in scope",
}


def render_evidence_pack(pack: EvidencePack, *, issue_number: str) -> bytes:
    """
    A :class:`~services.documents.evidence_pack.EvidencePack` as PDF bytes.

    The identity is derived from the pack rather than passed in, so the
    verification line can only ever state the coverage the pack actually
    assembled. In particular ``hectares`` is the **observed** figure — passing
    the contracted one would produce a document claiming ground nobody looked
    at, which is the one failure this package exists to prevent.

    A pack with no observed hectares raises through
    :func:`~services.documents.identity.verification_line`'s refusal path and
    renders without a verification line, saying so. That is correct: there is
    nothing to verify.
    """
    identity = DocumentIdentity(
        kind="evidence_pack",
        issue_number=issue_number,
        issued_at=utcnow(),
        subject=pack.client_name,
        coverage_start=pack.coverage_start,
        coverage_end=pack.coverage_end,
        hectares=pack.covered_hectares or None,
    )
    context = build_context(
        identity,
        # The client's name is the title; the cover band's eyebrow already says
        # what kind of document this is. Repeating "Season Evidence Pack" twice
        # on the same band reads as a template nobody finished filling in.
        title=pack.client_name,
        title_accent=f"{pack.coverage_start:%Y}/{pack.coverage_end:%y} season",
        subtitle=(
            "Grower-level evidence for the period stated below, covering land "
            "use, soil, crop protection agent usage and good agricultural "
            "practice. Figures are qualified on the first page inside."
        ),
        pack=pack,
        hectares=format_hectares,
        hectares_label=(
            format_hectares(pack.covered_hectares) if pack.covered_hectares else "—"
        ),
        theme_status_labels=THEME_STATUS_LABELS,
    )
    return render_pdf("evidence_pack.html", context)


def render_portfolio_report(
    report: PortfolioReport, *, issue_number: str
) -> bytes:
    """
    A :class:`~services.documents.portfolio_report.PortfolioReport` as PDF bytes.

    ``hectares`` on the identity is the **observed** figure, never hectares
    under management. The verification line is generated from it, and a
    portfolio report claiming to have verified ground it has never seen is the
    same failure as an evidence pack doing so — with a lender on the other end.
    """
    identity = DocumentIdentity(
        kind="portfolio_report",
        issue_number=issue_number,
        issued_at=utcnow(),
        subject=report.client_name,
        coverage_start=report.coverage_start,
        coverage_end=report.coverage_end,
        hectares=report.hectares_observed or None,
    )

    managed = report.hectares_under_management

    def share(hectares: float) -> str:
        """A district's share of the book. Guarded because a portfolio with no
        recorded areas would otherwise divide by zero at render time — in front
        of whoever asked for the document."""
        if not managed:
            return "—"
        return f"{hectares / managed * 100:.0f}%"

    context = build_context(
        identity,
        title=report.client_name,
        title_accent=(
            f"{report.coverage_start:%Y}/{report.coverage_end:%y} portfolio"
        ),
        subtitle=(
            "Scale, concentration and condition across the book, with the "
            "fields not yet observed named rather than netted out."
        ),
        report=report,
        hectares=format_hectares,
        share=share,
        observed_label=(
            format_hectares(report.hectares_observed)
            if report.hectares_observed else "—"
        ),
        managed_label=format_hectares(managed) if managed else "—",
    )
    return render_pdf("portfolio_report.html", context)


def utcnow() -> datetime:
    """Timezone-aware now. Documents are issued from a server in one place and
    read in several, so a naive timestamp is a future argument about a date."""
    return datetime.now(timezone.utc)
