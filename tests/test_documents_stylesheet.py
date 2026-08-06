"""
Tokens and the generated stylesheet.

What's worth testing here is not "does it emit CSS" but the two properties the
design system exists to guarantee: every value traces to a token, and the page
furniture that carries the verification line is actually wired up.
"""

import re

import pytest

from services.documents import tokens as t
from services.documents.stylesheet import (
    css_string,
    font_face_rules,
    page_furniture_css,
    stylesheet,
)


# ── Tokens ────────────────────────────────────────────────────────────────────


def test_palette_matches_the_velocity_playbook():
    # Sampled from the playbook's rendered pages — the KurimaSense document that
    # already leaves the building. A pack arriving in the same inbox has to look
    # like it came from the same company, so these are the tripwire: changing one
    # should mean the playbook changed too.
    assert t.PRIMARY == "#6DBE45"   # the logo's leaves, the playbook accent
    assert t.INK == "#0B3A22"       # headings
    assert t.PAPER == "#FBF8F2"     # the page
    assert t.LOAM == "#062515"      # the cover
    assert t.CLAY == "#785536"      # labels and eyebrows


def test_the_documents_do_not_use_the_apps_primary():
    # Deliberate divergence, flagged rather than quietly reconciled: the app's
    # --ee-primary is #0fb885, a teal-mint, while the playbook and the logo are
    # a leaf green. If someone unifies them, this test should be deleted with
    # that decision — not edited to make a surprise go away.
    assert t.PRIMARY != "#0fb885"


def test_nothing_in_the_palette_sits_on_pure_white():
    # The playbook's page is warm. A white panel on a warm page reads as a
    # pasted screenshot.
    assert t.SURFACE == t.PAPER
    assert t.PAPER != "#FFFFFF"


def test_tint_at_full_strength_is_the_hue_itself():
    assert t.tint(t.PRIMARY, 1.0) == t.PRIMARY.upper()


def test_tint_at_zero_strength_is_the_ground():
    assert t.tint(t.PRIMARY, 0.0, on=t.SURFACE) == t.PAPER.upper()


def test_tint_mixes_towards_the_ground_it_sits_on():
    # The same hue at the same strength lands somewhere different on warm paper
    # than on white. That is the point of the `on` argument: a green panel mixed
    # with pure white and dropped on the warm background reads as a cold patch.
    on_white = t.tint(t.PRIMARY, 0.2, on="#FFFFFF")
    on_paper = t.tint(t.PRIMARY, 0.2, on=t.BG)
    assert on_white != on_paper


def test_tint_is_monotonic():
    # Stronger means more hue, at every step — a stripe scale that folds back on
    # itself produces two rows the same colour.
    reds = [int(t.tint(t.ALERT, s / 10)[1:3], 16) for s in range(11)]
    assert reds == sorted(reds, reverse=True) or reds == sorted(reds)


@pytest.mark.parametrize("bad", [-0.1, 1.1])
def test_tint_rejects_out_of_range_strength(bad):
    with pytest.raises(ValueError, match="strength"):
        t.tint(t.PRIMARY, bad)


def test_tint_accepts_shorthand_hex():
    assert t.tint("#fff", 1.0) == "#FFFFFF"


@pytest.mark.parametrize("bad", ["", "#12345", "rgb(1,2,3)", "#GGGGGG"])
def test_tint_rejects_non_hex(bad):
    with pytest.raises(ValueError, match="hex colour"):
        t.tint(bad, 1.0)


def test_type_scale_is_ordered():
    # A scale where `section` is smaller than `body` produces a document that
    # reads as an unstyled draft.
    order = ["display", "title", "section", "subsection", "body"]
    sizes = [t.SCALE[name].size_pt for name in order]
    assert sizes == sorted(sizes, reverse=True)


def test_every_step_has_leading_at_least_its_size():
    # Leading below the type size sets lines overlapping.
    for name, step in t.SCALE.items():
        assert step.leading_pt >= step.size_pt, name


def test_spacing_is_a_multiple_of_the_baseline():
    assert t.space(1) == "4pt"
    assert t.space(4) == "16pt"


def test_half_steps_are_expressible():
    # Table cell padding wants 2pt; the grid should not force everything to 4.
    assert t.space(0.5) == "2pt"


# ── Stylesheet ────────────────────────────────────────────────────────────────


def test_stylesheet_sets_a4():
    css = stylesheet()
    assert "size: A4" in css


def test_stylesheet_styles_the_margin_boxes_the_furniture_fills():
    # The design system owns how the running header and footer *look*; the
    # per-document values that go in them come from page_furniture_css.
    css = stylesheet()
    for box in ("@top-left", "@top-right", "@bottom-left", "@bottom-right"):
        assert box in css


def test_running_footer_carries_the_verification_line_on_every_page():
    # This is the load-bearing assertion of the whole design system. Pages get
    # separated — a compliance officer photocopies page 4 and files it — and
    # page 4 has to still say what it is and what it covers.
    css = page_furniture_css(
        subject="Servemox",
        period="1 Nov 2025 – 31 May 2026",
        verification="Verified by KurimaSense · 214 ha",
        issue_number="EP-2026-000143",
    )
    assert "@bottom-left" in css
    assert "Verified by KurimaSense" in css


def test_running_footer_carries_the_issue_number_and_page_count():
    css = page_furniture_css(
        subject="Servemox", period="p", verification="v",
        issue_number="EP-2026-000143",
    )
    assert "EP-2026-000143" in css
    assert "counter(page)" in css and "counter(pages)" in css


def test_footer_says_so_when_there_is_no_verification_line():
    # A blank where a claim usually sits reads as a rendering glitch. A reader
    # has to be able to tell a verified document from an unverified one on any
    # page, without the cover.
    css = page_furniture_css(
        subject="Servemox", period="p", verification="", issue_number="FR-2026-000001",
    )
    assert "Issued without a verification line" in css


def test_furniture_quotes_names_that_would_otherwise_break_out_of_the_string():
    # A grower called O'Brien, or one whose name contains a double quote, must
    # not be able to terminate the CSS string and inject a declaration.
    css = page_furniture_css(
        subject='O\'Brien" } @page { @bottom-left { content: "pwned',
        period="p",
        verification="v",
        issue_number="EP-2026-000001",
    )
    # Asserted by parsing rather than by substring: the injected text *does*
    # appear in the output — escaped, inside the string literal — so counting
    # occurrences of "@page" proves nothing. What matters is that a CSS parser
    # sees one at-rule, not two.
    tinycss2 = pytest.importorskip("tinycss2")
    rules = [
        r for r in tinycss2.parse_stylesheet(
            css, skip_whitespace=True, skip_comments=True
        )
        if r.type == "at-rule"
    ]
    assert len(rules) == 1
    assert rules[0].lower_at_keyword == "page"


def test_css_string_escapes_backslashes_before_quotes():
    # Order matters: escaping quotes first and backslashes second would turn
    # `\"` back into an unescaped quote and reopen the hole.
    assert css_string('a\\"b') == '"a\\\\\\"b"'


def test_furniture_strips_newlines_that_would_break_the_declaration():
    css = page_furniture_css(
        subject="Line one\nline two", period="p", verification="v",
        issue_number="EP-2026-000001",
    )
    assert "Line one line two" in css


def test_cover_page_suppresses_the_running_header():
    css = stylesheet()
    assert "@page :first" in css


def test_the_page_colour_is_set_on_page_not_on_html():
    # This one shipped as a bug and is worth pinning. A background on the root
    # element propagates to the canvas and paints over *every* page, including
    # the dark cover — which silently turned the cover light and made every line
    # of cream type on it invisible. The document still rendered.
    css = stylesheet()
    html_block = css.split("html {", 1)[1].split("}", 1)[0]
    assert "background" not in html_block
    assert f"background: {t.PAPER}" in css


def test_the_cover_page_is_dark():
    css = stylesheet()
    first = css.split("@page :first {", 1)[1]
    assert f"background: {t.LOAM}" in first


def test_the_cover_foot_is_pinned_rather_than_auto_margined():
    # `margin-top: auto` in a flex column is not honoured by WeasyPrint, and the
    # failure is silent: the whole cover bunches into the top third and still
    # renders. Absolute positioning cannot half-work.
    css = stylesheet()
    foot = css.split(".cover-foot {", 1)[1].split("}", 1)[0]
    assert "position: absolute" in foot
    assert "bottom:" in foot


def test_an_intro_paragraph_stays_with_its_heading():
    # Heading and sentence at the foot of one page, the table they introduce
    # starting the next. Unlike `.section.keep` this works for tables that
    # genuinely have to run over pages.
    assert ".section-title + p" in stylesheet()


def test_short_sections_can_opt_out_of_breaking():
    # Not a default: a grower list has to be allowed to run over pages. But a
    # heading and intro stranded a page away from their four-row table read as
    # two unrelated fragments.
    css = stylesheet()
    assert ".section.keep" in css


def test_there_is_no_closing_mark_block():
    # Removed after a render showed it pushing itself onto a nearly blank final
    # page. The mark is on the cover and in every footer; that is enough, and it
    # is what "discreet" in the brief means.
    assert ".closing-mark" not in stylesheet()


def test_the_wordmark_is_two_colours():
    # "Kurima" in cream, "Sense" in green — the playbook's lockup. A single
    # colour is a different mark.
    css = stylesheet()
    assert ".wordmark .kurima" in css and ".wordmark .sense" in css


def test_an_italic_heading_face_is_bundled():
    # The green italic second line of a cover title is the playbook's signature.
    # Without a real italic face the renderer falls back to the roman and the
    # cover quietly stops looking like ours.
    rules = font_face_rules("file:///fonts")
    assert "font-style: italic" in rules
    assert "Fraunces-SemiBoldItalic.ttf" in rules


def test_long_tables_repeat_their_header():
    # A grower list runs to several pages; an unheaded continuation is unreadable.
    css = stylesheet()
    assert "display: table-header-group" in css


def test_numeric_column_headings_align_with_their_figures():
    # `.doc-table th` is more specific than `.num`, so without an explicit
    # `th.num` rule the heading sits left over right-aligned figures — and a
    # heading that does not sit over its own column is how a reader ends up
    # reading a hectare figure as a yield.
    assert ".doc-table th.num" in stylesheet()


def test_section_headings_do_not_orphan():
    css = stylesheet()
    assert "break-after: avoid" in css


def test_no_neumorphic_shadows_survive_into_print():
    # The app's `--shadow-neu` renders as grey mud on paper and as nothing at all
    # through a scan. Documents get flat rules instead.
    assert "box-shadow" not in stylesheet()


def test_stylesheet_contains_no_hardcoded_hex_outside_the_palette():
    # Every colour in the sheet must trace to a token or be derived from one.
    known = {
        c.upper()
        for c in [
            t.PRIMARY, t.INK, t.TEXT, t.MUTED, t.CLAY, t.PAPER, t.PANEL,
            t.LOAM, t.CREAM, t.SUN, t.WATER, t.RULE, t.HAIRLINE, t.ALERT,
            t.tint(t.SUN, 0.12), t.tint(t.ALERT, 0.08),
        ]
    }
    found = {m.upper() for m in re.findall(r"#[0-9A-Fa-f]{6}\b", stylesheet())}
    assert found <= known, f"untokenised colours: {sorted(found - known)}"


def test_fonts_are_not_embedded_unless_asked():
    # Tests render without the binary assets; the fallback stack has to work.
    assert "@font-face" not in stylesheet()
    assert "DejaVu Serif" in stylesheet()


def test_font_faces_cover_every_weight_the_scale_uses():
    rules = font_face_rules("file:///fonts")
    used_weights = {step.weight for step in t.SCALE.values()}
    for weight in used_weights:
        assert f"font-weight: {weight};" in rules, weight


def test_font_face_urls_are_rooted_at_the_given_base():
    rules = font_face_rules("file:///srv/fonts/")
    assert "url('file:///srv/fonts/Fraunces-Regular.ttf')" in rules
    # Trailing slash on the base must not produce a doubled separator, which
    # silently fails to load and drops the document to the fallback face.
    assert "//Fraunces" not in rules.replace("file:///", "")
