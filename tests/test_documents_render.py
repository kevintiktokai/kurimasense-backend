"""
Rendering: the base template, the specimen, and the refusal path.

Split so the HTML assertions run everywhere and the PDF assertions skip cleanly
on a host without WeasyPrint's system libraries — the pure design system stays
covered in a bare container, which is the whole reason `render.py` is the only
module here that does I/O.
"""

from datetime import date, datetime, timezone

import pytest

from services.documents.identity import DocumentIdentity
from services.documents.render import build_context, render_html, render_pdf

weasyprint = pytest.importorskip(
    "weasyprint", reason="PDF rendering needs Pango/Cairo"
)


SPECIMEN_ROWS = [
    {"field": "Home Field", "crop": "Maize", "area": "12.4", "established": 94,
     "note": "Stand check 8 Dec"},
    {"field": "River Block", "crop": "Tobacco", "area": "31", "established": None,
     "note": "No stand check recorded"},
]


def _identity(**overrides):
    base = dict(
        kind="evidence_pack",
        issue_number="EP-2026-000143",
        issued_at=datetime(2026, 8, 6, tzinfo=timezone.utc),
        subject="Servemox",
        coverage_start=date(2025, 11, 1),
        coverage_end=date(2026, 5, 31),
        hectares=214.0,
    )
    base.update(overrides)
    return DocumentIdentity(**base)


def _context(identity=None, **extra):
    return build_context(
        identity or _identity(),
        title="Design specimen",
        subtitle="Every primitive the document system offers",
        embed_fonts=False,
        specimen_rows=SPECIMEN_ROWS,
        **extra,
    )


# ── Context ───────────────────────────────────────────────────────────────────


def test_context_resolves_the_verification_line():
    ctx = _context()
    assert ctx["verification"].startswith("Verified by KurimaSense")
    assert ctx["verification_refusal"] == ""


def test_context_degrades_to_an_explicit_refusal_when_coverage_is_unknown():
    # The failure this guards: a document that silently drops the verification
    # line and then looks identical to one that carries it.
    ctx = _context(_identity(hectares=None))
    assert ctx["verification"] == ""
    assert "no hectare figure" in ctx["verification_refusal"]


def test_cover_label_is_the_readable_name_not_the_kind_key():
    assert _context()["kind_label"] == "Season Evidence Pack"


def test_unknown_kind_falls_back_to_the_key_rather_than_blank():
    ctx = _context(_identity(kind="something_new"))
    assert ctx["kind_label"] == "something_new"


# ── HTML ──────────────────────────────────────────────────────────────────────


def test_meta_carriers_are_present_for_the_running_furniture():
    html = render_html("_specimen.html", _context())
    for value in ("Servemox", "EP-2026-000143", "Verified by KurimaSense"):
        assert value in html


def test_missing_template_variables_raise_rather_than_rendering_blank():
    # StrictUndefined. In a web page a missing variable renders as empty and
    # someone notices; in a document it is a blank cell in a table a bank reads.
    ctx = _context()
    del ctx["specimen_rows"]
    with pytest.raises(Exception):
        render_html("_specimen.html", ctx)


def test_absent_values_render_as_a_dash_not_a_zero():
    html = render_html("_specimen.html", _context())
    # River Block has no stand check. The engine returned None and the document
    # must not turn that into 0%. Matched against the cell markup rather than a
    # bare "0%", which also occurs in the stylesheet as `width: 100%`.
    assert '<td class="num absent">—</td>' in html
    assert '0<span class="unit">%</span>' not in html


def test_refusal_sentence_appears_in_the_document_when_coverage_is_unknown():
    html = render_html("_specimen.html", _context(_identity(coverage_start=None)))
    assert "does not carry a verification line" in html


# ── PDF ───────────────────────────────────────────────────────────────────────


def test_specimen_renders_to_a_pdf():
    pdf = render_pdf("_specimen.html", _context())
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 2000


def test_rendered_pdf_carries_the_verification_line_in_its_text():
    # Extracted from the PDF rather than the HTML, because the footer is produced
    # by CSS Paged Media `string()` — the one part of the design system that HTML
    # assertions cannot reach.
    pypdf = pytest.importorskip("pypdf")
    import io

    pdf = render_pdf("_specimen.html", _context())
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert "Verified by KurimaSense" in text
    assert "EP-2026-000143" in text


def test_verification_line_repeats_on_every_page():
    # Pages get separated. Each one has to still say what it covers.
    pypdf = pytest.importorskip("pypdf")
    import io

    pdf = render_pdf("_specimen.html", _context())
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    for index, page in enumerate(reader.pages):
        assert "Verified by KurimaSense" in (page.extract_text() or ""), index


def test_pdf_is_a4():
    import io

    pypdf = pytest.importorskip("pypdf")
    pdf = render_pdf("_specimen.html", _context())
    box = pypdf.PdfReader(io.BytesIO(pdf)).pages[0].mediabox
    # A4 is 595.28 x 841.89 pt.
    assert round(float(box.width)) == 595
    assert round(float(box.height)) == 842


# ── Evidence pack ─────────────────────────────────────────────────────────────


def _pack(**overrides):
    from services.documents.evidence_pack import (
        FieldEvidence, GrowerEvidence, build_evidence_pack,
    )

    themes = frozenset(
        {"land_use", "soil", "crop_protection", "good_agricultural_practice"}
    )

    def fld(name, ha, observed=True, th=themes):
        return FieldEvidence(name.lower(), name, ha, "Tobacco", observed, th)

    kwargs = dict(
        client_name="Servemox",
        coverage_start=date(2025, 11, 1),
        coverage_end=date(2026, 5, 31),
        growers=[
            GrowerEvidence("g1", "Tariro", "M12345", (fld("Home Field", 12.4),)),
            GrowerEvidence("g2", "Rudo", None, (fld("River Block", 31.0, observed=False, th=frozenset()),)),
        ],
    )
    kwargs.update(overrides)
    return build_evidence_pack(**kwargs)


def test_evidence_pack_renders_to_a_pdf():
    from services.documents.render import render_evidence_pack

    pdf = render_evidence_pack(_pack(), issue_number="EP-2026-000143")
    assert pdf.startswith(b"%PDF-")


def test_the_verification_line_states_observed_hectares_not_contracted():
    # The one that matters. 12.4 ha observed, 43.4 ha under contract — a line
    # claiming 43 would assert coverage over ground nobody looked at.
    # Printed as "12 ha": format_hectares drops the decimal above 10 ha, since
    # satellite-derived boundaries do not justify one.
    import io

    pypdf = pytest.importorskip("pypdf")
    from services.documents.render import render_evidence_pack

    pack = _pack()
    assert pack.total_hectares > pack.covered_hectares  # the trap exists

    pdf = render_evidence_pack(pack, issue_number="EP-2026-000143")
    text = "\n".join(
        p.extract_text() or "" for p in pypdf.PdfReader(io.BytesIO(pdf)).pages
    )
    assert "· 12 ha" in text
    assert "43 ha" not in text


def test_a_pack_with_nothing_observed_renders_without_a_verification_line():
    # Correct rather than defensive: there is genuinely nothing to verify, and
    # the document says so instead of carrying an unqualified mark.
    import io

    pypdf = pytest.importorskip("pypdf")
    from services.documents.evidence_pack import FieldEvidence, GrowerEvidence
    from services.documents.render import render_evidence_pack

    pack = _pack(
        growers=[
            GrowerEvidence(
                "g1", "Tariro", "M1",
                (FieldEvidence("f", "F", 10.0, "Tobacco", False, frozenset()),),
            )
        ]
    )
    pdf = render_evidence_pack(pack, issue_number="EP-2026-000001")
    text = "\n".join(
        p.extract_text() or "" for p in pypdf.PdfReader(io.BytesIO(pdf)).pages
    )
    assert "does not carry a verification line" in text
    assert "Verified by KurimaSense ·" not in text


def test_untraceable_growers_appear_in_the_rendered_table():
    from services.documents.render import render_html

    # Rendered, not just computed: the gap has to survive into the document.
    html = render_html(
        "evidence_pack.html",
        _pack_context(),
    )
    assert "Rudo" in html
    assert "not recorded" in html


def _pack_context():
    from services.documents.identity import DocumentIdentity, format_hectares
    from services.documents.render import THEME_STATUS_LABELS, build_context, utcnow

    pack = _pack()
    identity = DocumentIdentity(
        kind="evidence_pack",
        issue_number="EP-2026-000143",
        issued_at=utcnow(),
        subject=pack.client_name,
        coverage_start=pack.coverage_start,
        coverage_end=pack.coverage_end,
        hectares=pack.covered_hectares or None,
    )
    return build_context(
        identity,
        title=pack.client_name,
        subtitle="Season evidence",
        embed_fonts=False,
        pack=pack,
        hectares=format_hectares,
        hectares_label=format_hectares(pack.covered_hectares),
        theme_status_labels=THEME_STATUS_LABELS,
    )
