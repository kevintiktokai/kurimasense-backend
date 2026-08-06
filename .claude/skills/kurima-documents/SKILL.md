---
name: kurima-documents
description: Author or change a generated KurimaSense PDF document (evidence pack, portfolio report, field report, season plan). Use when adding a template to services/documents/, changing document styling, or touching the mark, issue number or verification line.
---

# Writing a KurimaSense document

These documents leave the client's building. A contractor forwards an evidence
pack to a leaf buyer; a lender files a report. **Once sent it cannot be
re-rendered or corrected.** Everything below follows from that.

Read `services/documents/__init__.py` first — it maps the package.

## Rules

1. **Never write a colour, size or spacing value into a template or the
   stylesheet.** They come from `tokens.py`. If you need a value that isn't
   there, add a token — a near-miss hex is how four documents stop looking like
   one product.

   The palette is sampled from the **Velocity Playbook**, not from the app.
   These differ on purpose (`#6DBE45` leaf green vs the app's `#0fb885`
   teal-mint) and a test pins the divergence. If you unify them, delete that
   test along with the decision — don't edit it to make a surprise go away.

2. **Never hand-write the mark or the verification line.** `identity.py` builds
   them from the same values the document body reported on. If coverage can't be
   honestly stated, `verification_line` raises `CoverageError` and the document
   renders saying so. **Do not catch that and substitute a default.** A pack
   claiming coverage over ground nobody observed is the artefact most likely to
   end the company.

3. **Extend `base.html`. Supply `content` and nothing else.** The page furniture
   is shared on purpose — it's the part a buyer reads.

4. **An absent value is a dash and a reason, never a zero.** The engines return
   `None` rather than guessing; a template that renders `0%` for an unmeasured
   stand undoes that at the last step. Use `class="absent"`.

5. **A portfolio document must never be built for a demo without checking
   consent.** `portfolio_report.anonymise_rows` removes names, and its docstring
   is explicit that this is a guard against an accident, not permission — the
   districts and hectares are still a real client's. Read it before using it.

6. **Autoescaping stays on.** Grower and field names reach these templates. The
   only `Markup` in the package is the stylesheet, and the caller-supplied parts
   of that go through `css_string`.

## Which documents carry a verification line

Not all of them, and this is a judgement about what the document *is*:

- **Evidence pack, portfolio report** — yes. They assert coverage across ground,
  and the line states **observed** hectares, never contracted or under
  management.
- **Field report** — no. It explains one field's season rather than verifying
  hectares, so its identity carries no hectares, `verification_line` refuses,
  and the footer reads "Issued without a verification line". That is correct,
  not a gap: a mark reading as certification would overstate what it is.
- **Season plan** — no, and more emphatically. A plan describes what has not
  happened yet; verifying a forecast is a category error, and this is the one
  document a farmer takes into the field.

All four are in `templates/`. The plan in `kurima-sense/docs/` is complete.

## Adding a document

1. Add the kind to `KIND_PREFIXES` (`identity.py`) and `KIND_LABELS`
   (`render.py`).
2. Write `templates/<kind>.html` extending `base.html`, using only the existing
   classes: `.section`, `.doc-table`, `.metric`, `.callout`, `.label`, `.num`,
   `.absent`, `.caption`.
3. If you need a new primitive, add it to `stylesheet.py` **and** to
   `templates/_specimen.html`. A primitive not on the specimen is one nobody has
   looked at.
4. Test the pure parts without WeasyPrint; test the PDF behind
   `pytest.importorskip("weasyprint")`.

## Page-level traps, all found by rendering

Four of these shipped green and were only visible in an image:

- **`background` on `html` propagates to the canvas** and paints over *every*
  page, including the dark cover — turning it light and making every line of
  cream type invisible. Page colour goes on `@page`.
- **`margin-top: auto` in a flex column is not honoured.** The cover bunched
  into the top third and still rendered. The cover foot is absolutely
  positioned.
- **`string-set` resolves to nothing from a hidden element.** The running
  footer came out empty. Furniture is baked into `@page` content.
- **Jinja autoescaping mangles an injected stylesheet.** Mark it `Markup`, and
  put caller input through `css_string`.

## Looking at what you made

Tests do not tell you whether a document is well designed. Render it and look:

```python
from services.documents.render import build_context, render_pdf
open("out.pdf", "wb").write(render_pdf("_specimen.html", build_context(...)))
```

Then rasterise (`pypdfium2`) and **actually look at every page**, including the
last one. Defects found this way so far: headings misaligned over numeric
columns, a subtitle with no air, a lost space in the footer, a mark split across
a page boundary, a section heading stranded a page from its table, and all four
traps above. Every one passed a green suite.
