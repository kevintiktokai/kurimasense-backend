"""
The notification generators can actually execute.

Every generator query carried:

    WHERE user_id IS NOT NULL AND user_id <> ''

`fields.user_id` is a uuid column, and Postgres cannot cast `''` to uuid. So
every generator failed on every run with:

    invalid input syntax for type uuid: ""

Notifications were not degraded. They were **entirely dead**, and had been for
as long as that clause existed. The only trace was a repeating line in the log
that reads like noise next to a healthy `/health` 200 beside it.

`IS NOT NULL` alone was always sufficient — a uuid column has no empty string
to exclude. The extra clause was defending against a case the type system had
already made impossible, and cost the whole feature to do it.

This guard is lint-shaped like the others here, for the usual reason: nothing
fails. The endpoint returns 200 with an empty list, which is indistinguishable
from a user who genuinely has no notifications.
"""

import pathlib
import re

from tests.guards import code_lines

ROOT = pathlib.Path(__file__).resolve().parent.parent
GENERATORS = ROOT / "services" / "notifications" / "generators.py"

#: Columns that are uuid-typed in the schema. Comparing any of them to a string
#: literal is a runtime error, not a type warning.
UUID_COLUMNS = ("user_id", "tenant_id", "field_id", "grower_id")


def test_no_uuid_column_is_compared_to_an_empty_string():
    offenders = []
    for path in sorted(ROOT.glob("services/**/*.py")) + sorted(ROOT.glob("*.py")):
        if "test" in path.name:
            continue
        for number, line in code_lines(path.read_text()):
            for column in UUID_COLUMNS:
                if re.search(rf"{column}\s*(<>|!=|=)\s*''", line):
                    offenders.append(f"{path.relative_to(ROOT)}:{number}  {line.strip()}")
    assert offenders == [], (
        "Postgres cannot cast '' to uuid, so these fail the whole query at "
        f"runtime rather than filtering anything: {offenders}"
    )


def test_the_generators_still_filter_out_rows_with_no_owner():
    # The clause was wrong, not pointless — a field with a NULL user_id has
    # nobody to notify. Dropping the guard entirely would send those rows into
    # the per-user grouping and key a notification on None.
    source = GENERATORS.read_text()
    assert source.count("WHERE user_id IS NOT NULL") >= 2


def test_the_guard_can_see_the_bug_it_was_written_for():
    # The exact line that shipped.
    bad = "        WHERE user_id IS NOT NULL AND user_id <> ''"
    assert any(
        re.search(rf"{column}\s*(<>|!=|=)\s*''", bad) for column in UUID_COLUMNS
    ), "detection broke — the original line no longer matches"
