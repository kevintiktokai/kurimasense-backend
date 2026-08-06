"""
The document stylesheet, generated from :mod:`services.documents.tokens`.

Pure — returns a CSS string and touches nothing. Unit-tested in
``tests/test_documents_stylesheet.py``.

Generated rather than written as a static ``.css`` file for one reason: a static
file would let a template author quietly introduce a colour or a size that is
almost the brand. Every value here traces to a token, so "the four documents look
like one product" is a property of the code rather than a matter of care.

The class vocabulary below **is** the layout system the plan called for. Rather
than Python primitives that emit markup, templates get a small, fixed set of
classes — ``.doc-table``, ``.callout``, ``.metric``, ``.section`` — because the
templates are HTML and an HTML author reaching for a class is the path of least
resistance. Primitives that must be called are primitives that get bypassed.
"""

from __future__ import annotations

from . import tokens as t

#: Where the bundled brand faces live, relative to the templates directory.
#: Passed in rather than hardcoded so tests can render without the font files and
#: still assert on structure.
FONTS_DIR_TOKEN = "{fonts}"


def font_face_rules(fonts_url: str) -> str:
    """
    ``@font-face`` rules for the bundled faces.

    ``fonts_url`` is a base URL (usually a ``file://`` path to
    ``services/documents/fonts``). The faces are bundled rather than linked
    because a document has to render identically on a host with no network — and
    because a document that silently falls back to a different face is a document
    that no longer matches the app it is corroborating.
    """
    faces = [
        (t.FONT_HEADING, "Fraunces-Regular.ttf", 400, "normal"),
        (t.FONT_HEADING, "Fraunces-SemiBold.ttf", 600, "normal"),
        (t.FONT_HEADING, "Fraunces-Bold.ttf", 700, "normal"),
        # Italic is not decoration here — the green italic second line of a
        # cover title is the playbook's signature, and without a real italic
        # face the renderer falls back to the roman and the cover quietly stops
        # looking like ours.
        (t.FONT_HEADING, "Fraunces-SemiBoldItalic.ttf", 600, "italic"),
        (t.FONT_HEADING, "Fraunces-BoldItalic.ttf", 700, "italic"),
        (t.FONT_BODY, "HankenGrotesk-Regular.ttf", 400, "normal"),
        (t.FONT_BODY, "HankenGrotesk-Medium.ttf", 500, "normal"),
        (t.FONT_BODY, "HankenGrotesk-SemiBold.ttf", 600, "normal"),
        (t.FONT_BODY, "HankenGrotesk-Bold.ttf", 700, "normal"),
    ]
    base = fonts_url.rstrip("/")
    return "\n".join(
        "@font-face {{ font-family: '{family}'; font-style: {style}; "
        "font-weight: {weight}; src: url('{base}/{filename}') format('truetype'); }}".format(
            family=family, weight=weight, base=base, filename=filename, style=style
        )
        for family, filename, weight, style in faces
    )


def css_string(value: str) -> str:
    """
    A Python string as a CSS string literal, safely quoted.

    Grower and field names reach the page furniture, and a grower called
    ``O'Brien`` must not be able to terminate the string and inject a
    declaration — the same reason the HTML side autoescapes.
    """
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
        .replace("\r", " ")
    )
    return f'"{escaped}"'


def page_furniture_css(
    *,
    subject: str,
    period: str,
    verification: str,
    issue_number: str,
) -> str:
    """
    The running header and footer content for one specific document.

    Kept separate from :func:`stylesheet` because these are *this document's*
    values, not design tokens — and emitted as CSS rather than pulled from the
    page with ``string-set`` because ``string-set`` silently resolves to nothing
    when its carrier element is hidden. The failure mode there is the worst one
    available to this package: a document that renders looking almost right,
    with an empty footer and no verification line, and is then forwarded to a
    buyer. Baking the strings in cannot half-work.

    When ``verification`` is empty — coverage could not be honestly stated — the
    footer says so in words rather than leaving a blank where a claim usually
    sits. A reader must be able to tell an unverified document from a verified
    one at a glance on any page.
    """
    footer_left = verification or "Issued without a verification line"
    return f"""
@page {{
  @top-left {{ content: {css_string(subject)}; }}
  @top-right {{ content: {css_string(period)}; }}
  @bottom-left {{ content: {css_string(footer_left)}; }}
  @bottom-right {{
    content: {css_string(issue_number)} " · " counter(page) " / " counter(pages);
  }}
}}
""".strip()


def _step(name: str, selector: str) -> str:
    """Emit one type-scale step as a CSS rule."""
    s = t.SCALE[name]
    tracking = (
        f" letter-spacing: {s.tracking_em}em;" if s.tracking_em else ""
    )
    return (
        f"{selector} {{ font-size: {s.size_pt:g}pt; line-height: {s.leading_pt:g}pt; "
        f"font-weight: {s.weight};{tracking} }}"
    )


def stylesheet(fonts_url: str | None = None) -> str:
    """
    The whole document stylesheet.

    Pass ``fonts_url`` to embed the bundled faces; omit it and documents render
    in the fallback stack, which is what tests do so the suite does not depend on
    binary assets being present.
    """
    heading_stack = f"'{t.FONT_HEADING}', {t.FONT_HEADING_FALLBACK}"
    body_stack = f"'{t.FONT_BODY}', {t.FONT_BODY_FALLBACK}"

    parts: list[str] = []

    if fonts_url:
        parts.append(font_face_rules(fonts_url))

    # ── Page furniture ────────────────────────────────────────────────────────
    #
    # The running footer is the load-bearing part of this whole file. It carries
    # the verification line and the issue number on *every* page, because pages
    # get separated: a compliance officer photocopies page 4 of an evidence pack
    # and files it, and page 4 has to still say what it is and what it covers.
    parts.append(f"""
@page {{
  size: {t.PAGE_SIZE};
  margin: {t.MARGIN_TOP} {t.MARGIN_SIDE} {t.MARGIN_BOTTOM} {t.MARGIN_SIDE};
  /* The paper tone belongs here, not on `html`. A background on the root
     element propagates to the canvas and paints over every page including the
     cover — which silently turned the dark cover light and made every line of
     cream type on it invisible. */
  background: {t.PAPER};

  @top-left {{
    font-family: {body_stack};
    font-size: {t.SCALE['footer'].size_pt:g}pt;
    color: {t.MUTED};
    vertical-align: bottom;
    padding-bottom: {t.space(2)};
  }}
  @top-right {{
    font-family: {body_stack};
    font-size: {t.SCALE['footer'].size_pt:g}pt;
    color: {t.MUTED};
    vertical-align: bottom;
    padding-bottom: {t.space(2)};
    text-align: right;
  }}
  @bottom-left {{
    font-family: {body_stack};
    font-size: {t.SCALE['footer'].size_pt:g}pt;
    color: {t.MUTED};
    vertical-align: top;
    padding-top: {t.space(2)};
  }}
  @bottom-right {{
    font-family: {body_stack};
    font-size: {t.SCALE['footer'].size_pt:g}pt;
    color: {t.MUTED};
    vertical-align: top;
    padding-top: {t.space(2)};
    text-align: right;
  }}
}}

/* The cover is a full dark page. Painting it with `background` on `@page` and
   dropping the margin to zero beats bleeding a div out past the page margin:
   a block taller than the content area breaks onto a second page, and the
   resulting stray dark sliver is the kind of defect that only shows up in the
   copy a buyer received.

   All four margin boxes are suppressed here — the cover states its own
   provenance, including the verification line, in the metadata block at its
   foot. A muted grey footer over a dark page would be invisible anyway. */
@page :first {{
  margin: 0;
  background: {t.LOAM};
  @top-left {{ content: none; }}
  @top-right {{ content: none; }}
  @bottom-left {{ content: none; }}
  @bottom-right {{ content: none; }}
}}
""")

    # ── Base ──────────────────────────────────────────────────────────────────
    parts.append(f"""
html {{
  font-family: {body_stack};
  color: {t.TEXT};
}}
body {{ margin: 0; }}
{_step('body', 'body, p, li, td, th')}
""")

    # ── Typography ────────────────────────────────────────────────────────────
    parts.append(f"""
h1, h2, h3, .display, .title, .section-title, .subsection-title {{
  font-family: {heading_stack};
  color: {t.TEXT};
  margin: 0;
}}
{_step('display', '.display, h1')}
{_step('title', '.title, h2')}
{_step('section', '.section-title, h3')}
{_step('subsection', '.subsection-title, h4')}
{_step('caption', '.caption')}
{_step('table', '.doc-table td, .doc-table th')}

/* Small-caps labels above a value or a section. The tracking is what stops them
   reading as shouted — at 7.5pt with no tracking they clot. */
{_step('label', '.label')}
.label {{
  font-family: {body_stack};
  text-transform: uppercase;
  color: {t.MUTED};
  display: block;
}}
.caption {{ color: {t.MUTED}; }}
""")

    # ── Cover ─────────────────────────────────────────────────────────────────
    #
    # The one place the dark institutional base from the app's Phase 3 palette is
    # used. On paper a full dark page is expensive to print and reads as a
    # brochure, so it is a band rather than a page.
    parts.append(f"""
/* The cover is a full dark page, as the playbook's is — not a band on white.
   A client who has seen the playbook should recognise this before reading a
   word of it. `@page :first` paints the bleed; this fills it. */
.cover {{
  color: {t.CREAM};
  box-sizing: border-box;
  position: relative;
  /* `@page :first` has no margin, so the padding here *is* the cover's margin
     and the block fills the sheet exactly. */
  padding: {t.MARGIN_TOP} {t.MARGIN_SIDE} {t.MARGIN_BOTTOM} {t.MARGIN_SIDE};
  height: 297mm;
  page-break-after: always;
}}
/* Pinned to the foot by absolute position rather than `margin-top: auto` in a
   flex column: WeasyPrint does not honour auto margins there, and the failure
   is silent — the whole cover bunches into the top third and still renders. */
.cover-foot {{
  position: absolute;
  left: {t.MARGIN_SIDE};
  right: {t.MARGIN_SIDE};
  bottom: {t.MARGIN_BOTTOM};
}}
.cover .display, .cover .title {{ color: {t.CREAM}; }}
.cover .label {{ color: {t.PRIMARY}; }}

.cover-mark-block {{ margin-bottom: {t.space(16)}; }}
.cover-mark-block img {{ width: 13mm; height: auto; display: block; }}
.wordmark {{
  font-family: {heading_stack};
  font-size: {t.SCALE['title'].size_pt:g}pt;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin-top: {t.space(2)};
}}
/* "Kurima" cream, "Sense" green — the playbook's lockup, reproduced rather
   than approximated. */
.wordmark .kurima {{ color: {t.CREAM}; }}
.wordmark .sense {{ color: {t.PRIMARY}; }}

/* The green italic second line is the playbook's signature move on a title.
   Worth keeping: it is the one thing that makes the cover unmistakably ours
   rather than a generic dark report cover. */
.cover .display .accent {{
  color: {t.PRIMARY};
  font-style: italic;
  display: block;
}}
.cover .subtitle {{
  color: {t.CREAM};
  opacity: 0.72;
  max-width: 110mm;
  margin: {t.space(4)} 0 {t.space(6)} 0;
  font-size: {t.SCALE['body'].size_pt:g}pt;
  line-height: {t.SCALE['body'].leading_pt:g}pt;
}}

/* Metadata sits at the foot of the cover under a hairline, as the playbook
   does — it is provenance, not a headline. `margin-top: auto` pins it there
   however long the title runs. */
.cover-meta {{
  padding-top: {t.space(4)};
  border-top: 0.5pt solid rgba(251, 248, 242, 0.22);
  display: flex;
  gap: {t.space(6)};
}}
.cover-meta > div {{ flex: 1; }}
.cover-meta > div.wide {{ flex: 1.6; }}
.cover-meta .label {{ color: {t.PRIMARY}; margin-bottom: {t.space(1)}; }}
.cover-meta .value {{ color: {t.CREAM}; font-size: {t.SCALE['body'].size_pt:g}pt; }}

/* The verification line, stated on the cover as well as in every subsequent
   footer. The cover suppresses the running furniture, and a cover that is the
   one page not carrying the claim is the page most likely to be photographed
   and sent on by itself. */
.cover-verification {{
  margin-top: {t.space(4)};
  color: {t.PRIMARY};
  font-size: {t.SCALE['caption'].size_pt:g}pt;
  line-height: {t.SCALE['caption'].leading_pt:g}pt;
}}

/* There is no closing mark block. The lockup is on the cover at full size and
   the footer carries "Verified by KurimaSense" on every page — a third
   repetition at the end bought nothing and, being unsplittable, pushed itself
   onto a nearly blank final page. The playbook asks for a discreet mark, and
   two placements is discreet. */
""")

    # ── Sections ──────────────────────────────────────────────────────────────
    parts.append(f"""
.section {{ margin-bottom: {t.space(8)}; }}
/* The first section on the page after the cover would otherwise sit directly
   under the running header, reading as though the header were its eyebrow. */
.cover + .section {{ margin-top: {t.space(3)}; }}
/* Opt-in for sections a template knows are short. `break-inside: avoid` is
   wrong as a default — a grower list has to be allowed to run over pages — but
   a four-row table whose heading and intro sit on the previous page reads as
   two unrelated fragments. Renderers fall back to breaking when the content
   genuinely exceeds a page, so this is safe to over-apply. */
.section.keep {{ break-inside: avoid; }}
/* No rule under the heading — the playbook doesn't use one, and the deep-green
   serif against warm paper carries the hierarchy on its own. A rule as well
   reads as belt and braces.

   Never orphan a heading at the foot of a page: in a document read as a scan, a
   heading on one page and its table on the next is read as two unrelated
   things. */
.section-title {{
  color: {t.INK};
  margin-bottom: {t.space(3)};
  break-after: avoid;
}}
/* The numbered clay eyebrow above a section heading — "01 · METHOD". Warm, not
   grey: on this paper a grey label looks like a rendering fault. */
.eyebrow {{
  font-family: {body_stack};
  font-size: {t.SCALE['label'].size_pt:g}pt;
  font-weight: 600;
  letter-spacing: {t.SCALE['label'].tracking_em}em;
  text-transform: uppercase;
  color: {t.CLAY};
  display: block;
  margin-bottom: {t.space(1)};
}}
.subsection-title {{
  color: {t.INK};
  margin: {t.space(4)} 0 {t.space(2)} 0;
  break-after: avoid;
}}
p {{ margin: 0 0 {t.space(3)} 0; }}
""")

    # ── Tables ────────────────────────────────────────────────────────────────
    #
    # Most of every one of these documents is a table, so this block is most of
    # the design work. Rules are horizontal only: vertical rules turn a data
    # table into a spreadsheet screenshot.
    parts.append(f"""
.doc-table {{
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 {t.space(4)} 0;
}}
.doc-table th {{
  color: {t.CLAY};
  font-family: {body_stack};
  font-size: {t.SCALE['label'].size_pt:g}pt;
  font-weight: 600;
  letter-spacing: {t.SCALE['label'].tracking_em}em;
  text-transform: uppercase;
  text-align: left;
  padding: {t.space(2)} {t.space(2)};
  border-bottom: 1pt solid {t.INK};
}}
.doc-table td {{
  padding: {t.space(2)};
  border-bottom: 0.5pt solid {t.HAIRLINE};
  vertical-align: top;
}}
.doc-table tbody tr:nth-child(even) {{ background: {t.PANEL}; }}
/* Header repeats on every page a long table spans. A grower list runs to
   several pages and an unheaded continuation is unreadable. */
.doc-table thead {{ display: table-header-group; }}
.doc-table tr {{ break-inside: avoid; }}

/* `.doc-table th` is more specific than `.num`, so a numeric column's heading
   would sit left over right-aligned figures unless it is called out explicitly.
   A heading that does not sit over its own column is how a reader ends up
   reading a hectare figure as a yield. */
.num, .doc-table th.num {{ text-align: right; }}
.num {{ font-variant-numeric: tabular-nums; }}
.unit {{ color: {t.MUTED}; }}

/* A value the document declines to state. Rendered as an em dash and a reason,
   never as a zero — the backend's whole posture is that an honest gap beats a
   confident wrong number, and the document layer must not undo that by
   printing 0.0 where the engine returned None. */
.absent {{ color: {t.MUTED}; }}
""")

    # ── Metrics and callouts ──────────────────────────────────────────────────
    parts.append(f"""
.metrics {{ display: flex; gap: {t.space(3)}; margin-bottom: {t.space(5)}; }}
.metric {{
  flex: 1;
  padding: {t.space(3)};
  background: {t.PANEL};
  border-left: 2pt solid {t.PRIMARY};
}}
.metric .value {{
  font-family: {heading_stack};
  color: {t.INK};
  font-size: {t.SCALE['title'].size_pt:g}pt;
  line-height: {t.SCALE['title'].leading_pt:g}pt;
  font-weight: 600;
}}

.callout {{
  padding: {t.space(3)} {t.space(4)};
  margin: 0 0 {t.space(4)} 0;
  background: {t.PANEL};
  border-left: 2pt solid {t.PRIMARY};
  break-inside: avoid;
}}
.callout .label {{ color: {t.CLAY}; }}
.callout.warn {{
  background: {t.tint(t.SUN, 0.12)};
  border-left-color: {t.SUN};
}}
.callout.alert {{
  background: {t.tint(t.ALERT, 0.08)};
  border-left-color: {t.ALERT};
}}
.callout .label {{ margin-bottom: {t.space(1)}; }}

figure {{ margin: 0 0 {t.space(4)} 0; break-inside: avoid; }}
figure img {{ width: 100%; height: auto; }}
figcaption {{
  font-size: {t.SCALE['caption'].size_pt:g}pt;
  line-height: {t.SCALE['caption'].leading_pt:g}pt;
  color: {t.MUTED};
  margin-top: {t.space(1)};
}}
""")

    return "\n".join(part.strip() for part in parts) + "\n"
