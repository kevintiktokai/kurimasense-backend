"""
Every tenant-scoped table is isolated, and stays isolated when the next one
is added.

Lint-shaped, like the secret-comparison and index guards, and for the sharpest
version of the same reason: a table with no RLS policy does not fail anything.
It reads exactly like a table that has one. The only difference shows up when
someone runs a query without a tenant predicate — and the whole point of RLS is
that you cannot rely on nobody ever doing that.

WHAT THIS EXISTS TO STOP
------------------------
Migration 017 forces RLS on a **hardcoded array of table names** written when
017 was written. It is correct and it does not stay correct: three tables were
added afterwards and all three missed it.

  018  field_section_analysis   ENABLE + policy, never FORCEd
  019  seasons                  ENABLE + policy, never FORCEd
  022  document_issues          no RLS at all

`document_issues` is the one that mattered. It records what was issued to which
client — the subject, the hectares, the coverage window — and `registry.py`
looks rows up by issue number with no tenant predicate at all. That was safe
only because `document_routes._assert_visible` remembered to check.

Migration 024 fixed those three. This file is the part that generalises: it
fails on the *fourth* one, before it ships.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MIGRATIONS = ROOT / "migrations"


def _sql() -> str:
    """Every migration, concatenated. Order does not matter to these checks."""
    return "\n".join(p.read_text() for p in sorted(MIGRATIONS.glob("*.sql")))


def _strip_comments(sql: str) -> str:
    """`--` lines. Without this, a rollback note reads as a live statement."""
    return "\n".join(
        line for line in sql.splitlines() if not line.strip().startswith("--")
    )


def tenant_scoped_tables() -> set[str]:
    """
    Tables carrying a `tenant_id` column — the set that must be isolated.

    Two ways to acquire one, and the second is the one that hides: declared in
    the CREATE TABLE, or bolted on later with ALTER TABLE ... ADD COLUMN. Every
    table in the contract-farming set got its tenant_id the second way.
    """
    body = _strip_comments(_sql())
    tables = set()
    for match in re.finditer(
        r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(?:public\.)?(\w+)\s*\((.*?)\n\s*\);",
        body,
        re.IGNORECASE | re.DOTALL,
    ):
        if re.search(r"^\s*tenant_id\b", match.group(2), re.IGNORECASE | re.MULTILINE):
            tables.add(match.group(1).lower())
    for match in re.finditer(
        r"ALTER TABLE\s+(?:public\.)?(\w+)\s+ADD COLUMN(?:\s+IF NOT EXISTS)?\s+tenant_id\b",
        body,
        re.IGNORECASE,
    ):
        tables.add(match.group(1).lower())
    return tables


def _do_block_sweeps(statement: str) -> set[str]:
    """
    Table names swept by a DO block that runs `statement` over an array.

    Three migrations apply RLS this way rather than table by table:

        DECLARE t text; xs text[] := ARRAY['a','b'];
        BEGIN FOREACH t IN ARRAY xs LOOP
            EXECUTE format('... %I ...', t);

    A scan that only understands literal `ALTER TABLE <name>` sees none of it
    and reports every one of those tables as unprotected — which is how a guard
    earns enough false positives to get deleted.
    """
    body = _strip_comments(_sql())
    swept = set()
    for block in re.finditer(r"DO\s*\$\$(.*?)END\s*\$\$;", body, re.DOTALL | re.IGNORECASE):
        source = block.group(1)
        if not re.search(statement, source, re.IGNORECASE):
            continue
        # Two spellings in this repo: a declared `xs text[] := ARRAY[...]`
        # (017, 024) and an inline `FOREACH t IN ARRAY ARRAY[...]` (013).
        for array in re.finditer(
            r"(?:text\[\]\s*:=\s*|IN\s+ARRAY\s+)ARRAY\s*\[(.*?)\]", source, re.DOTALL
        ):
            swept.update(name.lower() for name in re.findall(r"'(\w+)'", array.group(1)))
    return swept


def tables_with_a_policy() -> set[str]:
    body = _strip_comments(_sql())
    named = {
        m.lower()
        for m in re.findall(
            r"CREATE POLICY\s+\w+\s+ON\s+(?:public\.)?(\w+)", body, re.IGNORECASE
        )
    }
    return named | _do_block_sweeps(r"CREATE POLICY")


def forced_tables() -> set[str]:
    body = _strip_comments(_sql())
    named = {
        m.lower()
        for m in re.findall(
            r"ALTER TABLE\s+(?:public\.)?(\w+)\s+FORCE ROW LEVEL SECURITY",
            body,
            re.IGNORECASE,
        )
    }
    return named | _do_block_sweeps(r"FORCE ROW LEVEL SECURITY")


# Tables that carry a tenant_id but are deliberately not FORCEd. Each needs a
# reason, and "we forgot" is not one.
FORCE_EXEMPT = {
    # Bootstrap exemption: forcing these locks out the GUC derivation that every
    # other policy depends on, and locks ops out of the database entirely.
    # See migration 017's header and docs/rls_force_runbook.md.
    "tenants",
    "tenant_members",
}


def test_every_tenant_scoped_table_has_a_policy():
    missing = sorted(tenant_scoped_tables() - tables_with_a_policy() - FORCE_EXEMPT)
    assert missing == [], (
        "these tables carry a tenant_id and no RLS policy, so they are isolated "
        f"against nothing: {missing}"
    )


def test_every_tenant_scoped_table_is_forced():
    missing = sorted(tenant_scoped_tables() - forced_tables() - FORCE_EXEMPT)
    assert missing == [], (
        "these tables have a policy but were never FORCEd, so the table owner "
        f"bypasses it — add them to a FORCE sweep: {missing}"
    )


def test_the_document_registry_is_isolated():
    # Called out separately because it is the one that was actually open, and
    # because of what it holds: which client had which document issued, over
    # what hectares. A cross-tenant read here is the "data controversy" the
    # playbook rates as existential.
    assert "document_issues" in tables_with_a_policy()
    assert "document_issues" in forced_tables()


def test_the_registry_lookups_that_carry_no_tenant_predicate_are_still_guarded():
    # get_by_issue_number and mark_forwarded filter on issue_number alone. RLS
    # is now the backstop, but the route-level check is what produces the right
    # *status code*, so it has to stay too.
    routes = (ROOT / "document_routes.py").read_text()
    assert routes.count("_assert_visible(") >= 3, (
        "_assert_visible guards the registry lookups that have no tenant "
        "predicate in SQL; it is defined once and must still be called"
    )


def test_the_registry_arms_the_gucs_it_now_depends_on():
    # The policy reads app_tenant_ids(). If registry.py ever stops arming the
    # GUCs, every one of its queries starts returning zero rows — a failure that
    # would otherwise look like "no documents yet".
    registry = (ROOT / "services" / "documents" / "registry.py").read_text()
    assert "arm_rls_gucs" in registry


def test_the_guard_can_see_a_table_it_should_flag():
    # A guard that matches nothing passes forever. These are the real shapes.
    assert "fields" in tenant_scoped_tables()
    assert "document_issues" in tenant_scoped_tables()
    # And the sweep-array parsing actually works — 017 forces via a DO block,
    # so a naive ALTER-TABLE-only scan would report every one of its tables.
    assert "daily_logs" in forced_tables()


def test_rollback_comments_are_not_mistaken_for_statements():
    # Several migrations document their rollback as `--   ALTER TABLE ... NO
    # FORCE ...`. Counting those as live would mark a table isolated when it is
    # not — the exact false negative this file exists to prevent.
    assert "NO FORCE" not in _strip_comments(_sql()).upper()
