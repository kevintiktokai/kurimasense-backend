"""
The bootstrap schema builds a working database on its own.

`015_bootstrap_schema.sql` opens with "The complete runtime schema". That claim
is the whole point of the file — it is what lets an operator set
DB_SELF_HEAL_SCHEMA=false and stop the backend issuing DDL at boot. If it is
not actually complete, the flag is a trap.

WHAT THIS EXISTS TO STOP
------------------------
It was not complete. It created 19 tables, and `growers` was not one of them —
while carrying `ALTER TABLE growers ADD COLUMN timb_grower_number` and two
`CREATE INDEX ... ON growers`. It never added `fields.tenant_id`, the column
every scoped read in the product filters on, while carrying
`CREATE INDEX idx_fields_tenant ON fields (tenant_id)`.

Both objects came from `migrate_fields_to_tenants.py` — a standalone script,
run by hand, outside the numbered sequence. Every environment to date was built
by running that script against a database that already had rows in it, and 015
was captured from the result, so the omission never surfaced. A database built
from the documented path would have failed on the first index that touched a
column nobody had created.

Nothing failed. That is the point: an incomplete bootstrap is indistinguishable
from a complete one until someone stands up a fresh environment — a staging
database, a second region, a restore drill — which is exactly the moment you
least want to find out.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOOTSTRAP = (ROOT / "migrations" / "015_bootstrap_schema.sql").read_text()


def _statements(sql: str) -> list[str]:
    """Statements in file order, comments stripped. Order is the whole test."""
    body = "\n".join(
        line for line in sql.splitlines() if not line.strip().startswith("--")
    )
    return [s.strip() for s in body.split(";") if s.strip()]


#: Tables the bootstrap legitimately does not create.
#:
#: `profiles` is Supabase's, created by the auth schema. `tenants` and
#: `tenant_members` predate this file and are the bootstrap exemption RLS
#: depends on (docs/rls_force_runbook.md) — every policy derives the caller's
#: scope from them, so they must exist before any of this runs.
EXTERNALLY_OWNED = {"profiles", "tenants", "tenant_members"}


def created_before(index: int, statements: list[str]) -> set[str]:
    """Tables created at or before `index`, plus the externally-owned ones."""
    created = set(EXTERNALLY_OWNED)
    for statement in statements[: index + 1]:
        match = re.search(
            r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(?:public\.)?(\w+)",
            statement,
            re.IGNORECASE,
        )
        if match:
            created.add(match.group(1).lower())
    return created


def _referenced_table(statement: str) -> str | None:
    """The table a statement operates on, for the statements that touch one."""
    for pattern in (
        r"ALTER TABLE\s+(?:public\.)?(\w+)",
        r"CREATE (?:UNIQUE )?INDEX(?:\s+IF NOT EXISTS)?\s+\w+\s+ON\s+(?:public\.)?(\w+)",
        r"CREATE POLICY\s+\w+\s+ON\s+(?:public\.)?(\w+)",
        r"DROP POLICY(?:\s+IF EXISTS)?\s+\w+\s+ON\s+(?:public\.)?(\w+)",
        r"COMMENT ON COLUMN\s+(?:public\.)?(\w+)\.",
    ):
        match = re.search(pattern, statement, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    return None


def test_the_bootstrap_never_references_a_table_it_has_not_created():
    statements = _statements(BOOTSTRAP)
    problems = []
    for i, statement in enumerate(statements):
        table = _referenced_table(statement)
        if table and table not in created_before(i, statements):
            problems.append(f"{table}: {' '.join(statement.split())[:80]}")
    assert problems == [], (
        "the bootstrap operates on tables it never creates, so a database built "
        "from it alone fails here:\n  " + "\n  ".join(problems)
    )


def test_fields_gets_the_column_the_whole_product_scopes_on():
    # Called out separately because it is the one that was missing, and because
    # of what depends on it: tenancy.field_scope_sql() is on the path of every
    # institutional read in the product.
    assert re.search(
        r"ALTER TABLE fields ADD COLUMN IF NOT EXISTS tenant_id",
        BOOTSTRAP,
        re.IGNORECASE,
    ), "015 indexes fields.tenant_id but never adds it"


def test_growers_is_created_not_just_altered():
    assert re.search(
        r"CREATE TABLE IF NOT EXISTS growers", BOOTSTRAP, re.IGNORECASE
    ), "015 alters and indexes growers but never creates it"


def test_the_tenancy_ddl_is_in_the_numbered_sequence_not_only_a_script():
    # The root cause, stated as a test. A schema object that exists only in a
    # hand-run script is an object no fresh environment has.
    migration = ROOT / "migrations" / "025_bootstrap_the_tenancy_columns.sql"
    assert migration.exists()
    body = migration.read_text()
    assert "ADD COLUMN IF NOT EXISTS tenant_id" in body
    assert "CREATE TABLE IF NOT EXISTS growers" in body


def test_the_standalone_script_still_owns_the_backfill():
    # 025 deliberately took only the DDL. The backfill reads live rows, reports
    # orphaned fields, and sets NOT NULL only once none remain — operator work
    # with a judgement call in it, not something to run unattended at boot.
    script = (ROOT / "migrate_fields_to_tenants.py").read_text()
    assert "UPDATE fields f" in script
    assert "SET NOT NULL" in script or "SET_NOT_NULL_SQL" in script


def test_the_guard_can_see_the_bug_it_was_written_for():
    # The original file, reduced. If this stops failing, the detection broke.
    broken = _statements(
        """
        CREATE TABLE IF NOT EXISTS fields (id UUID PRIMARY KEY);
        ALTER TABLE growers ADD COLUMN IF NOT EXISTS timb_grower_number TEXT;
        CREATE INDEX IF NOT EXISTS idx_fields_tenant ON fields (tenant_id);
        """
    )
    offenders = [
        _referenced_table(s)
        for i, s in enumerate(broken)
        if _referenced_table(s) and _referenced_table(s) not in created_before(i, broken)
    ]
    assert offenders == ["growers"]
