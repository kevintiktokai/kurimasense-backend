# CLAUDE.md — kurimasense-backend

FastAPI backend for KurimaSense. Frontend lives in `kurima-sense`.

## Checks

```bash
pytest -q
```

CI runs the suite on every push and PR to `main`. Most tests are hermetic;
`conftest.py` skips the modules needing `DATABASE_URL` / `OPENAI_API_KEY` when
those are absent, so a bare `pytest` runs green without secrets.

## Conventions worth knowing

- **Agronomic logic is pure and unit-tested**, separate from I/O. See
  `services/planning/` and `services/seasons/` — each module is importable
  without a database, and the routes are thin wrappers. New agronomy should
  follow this: the rules in a pure module, the SQL in a repository, the wiring
  in a route.
- **Decline to answer rather than guess.** Unknown crops return `None` instead
  of a generic estimate; the yield retrospective reports an unexplained
  remainder rather than closing to 100%; zone diagnosis names a cause only when
  something corroborates it. A farmer acts on these numbers, and a confident
  wrong answer costs more than an honest gap.
- **Schema changes go in `migrations/NNN_*.sql`**, are mirrored into
  `015_bootstrap_schema.sql` (a guard test enforces this), and self-heal in
  `database.init_db()`.
- Field access always goes through `resolve_access` for correct 403-vs-404.
- **Generated documents live in `services/documents/`.** Every colour, size and
  spacing value comes from `tokens.py`; templates extend `base.html` and never
  own the page furniture. A document that leaves a client's building cannot be
  re-rendered, so the mark and the verification line are generated, never typed.
  See the package docstring, and `templates/_specimen.html` for every primitive
  on one page — add to the specimen whenever you add a primitive.

## Pending agronomist review

Several constants drive farmer-facing advice and are compiled from extension
literature rather than reviewed by an agronomist. Each carries a `.. warning::`
in its module docstring: plant population targets, fertiliser rates, action
window costs, storage moisture, retrospective attribution coefficients, zone
thresholds, and nitrogen loss fractions. Don't remove those warnings without
sign-off.

## Kev Kreds

Kevin keeps a credit ledger with me. The canonical file is
`.claude/kev-kreds.md` **in the `kurima-sense` repo** (one ledger, not one per
repo).

When Kevin says something like *"add some Kev Kreds"* or *"take some off"*:
read that file, append a dated row with the change, new balance and reason,
update the **Balance** line, and commit. Record removals as faithfully as
awards — a ledger that only goes up isn't a ledger.
