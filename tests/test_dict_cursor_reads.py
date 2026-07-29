"""Row reads must use a dict cursor wherever columns are read by NAME.

REGRESSION (July 2026): five hot code paths opened a PLAIN psycopg2 cursor
(which yields TUPLES) and then read the rows by column name — row['ndvi'],
row.get('breeder'), row['role']. Every one raised

    TypeError: tuple indices must be integers or slices, not str

on EVERY call. All five sat inside a broad `except Exception` that logged and
returned an empty result, so nothing 500'd and nothing looked broken — the
features just silently produced nothing:

  * ai_brain.get_history            -> assistant had NO conversation memory
  * ai_brain._get_variety_details   -> no variety intelligence in AI answers
  * database.get_recent_field_activity -> AI never saw a field's recent inputs
  * yield_model.get_field_ndvi_history -> yield model ran with NO NDVI history
  * proactive_intelligence.get_variety_info -> no variety data in alerts

The first test below is the general proof (real psycopg2 behaviour, not a
mock); the rest are source invariants so a plain cursor cannot be reintroduced
at these call sites.
"""

import ast
import os
import pathlib
import pytest

psycopg2 = pytest.importorskip("psycopg2")
from psycopg2.extras import RealDictCursor  # noqa: E402

DSN = os.environ.get("POSTGRES_TEST_DSN")

REPO = pathlib.Path(__file__).resolve().parent.parent

# (file, function) pairs that read rows by column name.
NAME_READING_FUNCS = [
    ("ai_brain.py", "get_history"),
    ("ai_brain.py", "_get_variety_details"),
    ("database.py", "get_recent_field_activity"),
    ("yield_model.py", "get_field_ndvi_history"),
    ("proactive_intelligence.py", "get_variety_info"),
    ("climate_service.py", "calculate_gdd"),
]


@pytest.mark.skipif(not DSN, reason="needs POSTGRES_TEST_DSN")
def test_plain_cursor_breaks_name_access_but_dict_cursor_does_not():
    """Pins down the actual psycopg2 behaviour the bug relied on."""
    conn = psycopg2.connect(DSN)
    try:
        cur = conn.cursor()
        cur.execute("SELECT 0.42::float AS ndvi")
        row = cur.fetchone()
        with pytest.raises(TypeError, match="tuple indices must be integers"):
            _ = row["ndvi"]
        cur.close()

        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT 0.42::float AS ndvi")
        row = cur.fetchone()
        assert row["ndvi"] == pytest.approx(0.42)
        assert row.get("ndvi") == pytest.approx(0.42)
        cur.close()
    finally:
        conn.close()


def _function_source(filename: str, funcname: str) -> str:
    path = REPO / filename
    src = path.read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == funcname:
            seg = ast.get_source_segment(src, node)
            if seg:
                return seg
    raise AssertionError(f"{funcname} not found in {filename}")


@pytest.mark.parametrize("filename,funcname", NAME_READING_FUNCS)
def test_name_reading_functions_use_a_dict_cursor(filename, funcname):
    src = _function_source(filename, funcname)
    assert "cursor_factory=RealDictCursor" in src, (
        f"{filename}:{funcname} reads rows by column name and MUST open its "
        f"cursor with cursor_factory=RealDictCursor"
    )
    assert "conn.cursor()" not in src, (
        f"{filename}:{funcname} still opens a plain (tuple) cursor"
    )


def test_no_new_plain_cursor_reads_rows_by_name():
    """Sweep the runtime modules for the same mistake anywhere else.

    Scripts, one-shot migrations and tests are excluded — they are not on a
    request path and several legitimately read by index.
    """
    skip = ("scripts/", "migrate_", "fix_", "debug_db", "tests/", ".venv", "seed_")
    offenders = []
    for path in sorted(REPO.rglob("*.py")):
        rel = str(path.relative_to(REPO))
        if any(k in rel for k in skip):
            continue
        src = path.read_text()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            seg = ast.get_source_segment(src, node) or ""
            if "conn.cursor()" not in seg or "RealDictCursor" in seg:
                continue
            # Does it subscript anything with a string literal, or call .get()?
            reads_by_name = any(
                isinstance(n, ast.Subscript)
                and isinstance(n.slice, ast.Constant)
                and isinstance(n.slice.value, str)
                for n in ast.walk(node)
            )
            # `row["x"] if isinstance(row, dict) else row[0]` is a deliberate
            # both-ways read and is safe.
            if reads_by_name and "isinstance(row, dict)" not in seg:
                offenders.append(f"{rel}:{node.lineno} {node.name}")

    assert not offenders, (
        "plain (tuple) cursor used with column-name row access:\n  "
        + "\n  ".join(offenders)
    )
