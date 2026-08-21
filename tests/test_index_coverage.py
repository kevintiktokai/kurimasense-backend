"""
Every column the app scopes or joins on is indexed.

Lint-shaped, like the secret-comparison guard, and for the same reason: a
missing index does not fail anything. It just makes the busiest table in the
product sequentially scanned on every request, invisibly, until a real
customer's data arrives.

`fields` had exactly one index — on `user_id`, the *legacy* consumer column —
while every institutional query scopes by `tenant_id`. That is the shape this
file exists to stop coming back.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
BOOTSTRAP = (ROOT / "migrations" / "015_bootstrap_schema.sql").read_text()
MIGRATIONS = ROOT / "migrations"

#: (table, leading column) pairs the hot paths depend on. Leading column,
#: because Postgres can only use an index for a predicate on its first column.
REQUIRED_LEADING_COLUMNS = [
    # tenancy.field_scope_sql — on the path of every scoped read in the product.
    ("fields", "tenant_id"),
    # The legacy consumer fallback in the same predicate.
    ("fields", "user_id"),
    # The evidence pack and portfolio report join fields to their grower.
    ("fields", "grower_id"),
    # The grower roster.
    ("growers", "tenant_id"),
    # Per-field reads.
    ("daily_logs", "field_id"),
    ("field_inputs", "field_id"),
    ("field_activities", "field_id"),
    ("seasons", "field_id"),
    ("soil_profiles", "field_id"),
    ("field_section_analysis", "field_id"),
    # The registry.
    ("document_issues", "tenant_id"),
]


def _indexed_leading_columns() -> set[tuple[str, str]]:
    """(table, first indexed column) for every index in the bootstrap schema."""
    found = set()
    for match in re.finditer(
        r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:CONCURRENTLY\s+)?"
        r"(?:IF\s+NOT\s+EXISTS\s+)?\w+\s+ON\s+(\w+)\s*\(([^)]*)\)",
        BOOTSTRAP,
        re.IGNORECASE | re.DOTALL,
    ):
        table = match.group(1).lower()
        first = match.group(2).split(",")[0].strip().split()[0].lower()
        found.add((table, first))
    return found


def test_every_hot_path_column_leads_an_index():
    indexed = _indexed_leading_columns()
    missing = [pair for pair in REQUIRED_LEADING_COLUMNS if pair not in indexed]
    assert missing == [], (
        "these are scoped or joined on with no index leading with that column: "
        f"{missing}"
    )


def test_the_tenant_scope_column_is_indexed_on_fields():
    # Called out separately because it is the one that was actually missing, and
    # because it is on the path of every institutional request. A regression
    # here is a sequential scan of the busiest table in the product.
    assert ("fields", "tenant_id") in _indexed_leading_columns()


def test_the_scope_predicate_still_leads_with_tenant_id():
    # If field_scope_sql is ever rewritten to lead with something else, the
    # index above stops helping and this test should fail rather than the
    # performance quietly regressing.
    source = (ROOT / "tenancy.py").read_text()
    fragment = source.split("def field_scope_sql", 1)[1]
    assert "tenant_id = ANY(" in fragment


def test_the_newest_migration_is_mirrored_into_the_bootstrap():
    # Same rule the schema guard applies to tables, extended to indexes: a
    # migration that is not mirrored is lost the moment DB_SELF_HEAL_SCHEMA is
    # turned off.
    latest = sorted(MIGRATIONS.glob("023_*.sql"))
    assert latest, "migration 023 is missing"
    for match in re.finditer(r"CREATE INDEX IF NOT EXISTS (\w+)", latest[0].read_text()):
        assert match.group(1) in BOOTSTRAP, f"{match.group(1)} not mirrored into 015"


def test_partial_indexes_match_the_predicate_they_serve():
    # A partial index only helps when the query carries the same predicate.
    # These two are partial for a reason and the reason has to stay true.
    assert "WHERE deleted_at IS NULL" in BOOTSTRAP
    roster = (ROOT / "grower_routes.py").read_text()
    assert "deleted_at IS NULL" in roster
