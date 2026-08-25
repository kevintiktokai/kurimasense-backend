"""
The shared guard machinery works, because six guards now depend on it.

Consolidating six copies of "skip the comment lines" into one helper is only a
win if the one is right. If `code_lines` ever stops skipping comments, every
lint-shaped guard in this suite starts matching its own explanatory prose and
reporting violations that do not exist — and a guard with that failure mode
gets suppressed rather than fixed.

If it stops yielding *code*, the reverse happens and they all silently pass.
That is the worse direction, and the reason this file exists.
"""

from tests.guards import PYTHON, SQL, code_lines, python_sources, without_comments


def test_comment_lines_are_skipped():
    source = "alpha = 1\n# alpha = 2\n   # indented comment\nbeta = 3\n"
    assert [line for _, line in code_lines(source)] == ["alpha = 1", "beta = 3"]


def test_line_numbers_still_point_at_the_real_file():
    # The numbers are what a failing guard prints. If they shifted to count only
    # code lines, every offender it reported would point at the wrong line.
    source = "# one\n# two\nreal = 3\n"
    assert list(code_lines(source)) == [(3, "real = 3")]


def test_sql_comments_use_a_different_marker():
    # `--` in SQL, and it matters: several migrations document their rollback as
    # `--   ALTER TABLE ... NO FORCE ...`, and counting those as live statements
    # marks a table isolated when it is not.
    sql = "ALTER TABLE x ENABLE ROW LEVEL SECURITY;\n--   ALTER TABLE x NO FORCE;\n"
    assert "NO FORCE" not in without_comments(sql, SQL)
    assert "ENABLE ROW LEVEL SECURITY" in without_comments(sql, SQL)


def test_a_trailing_comment_is_left_alone():
    # Only whole-line comments are dropped. A trailing `# ...` sits on a line
    # that still contains code, and removing the line would hide the code.
    source = "value = compute()  # explains why\n"
    assert without_comments(source) == "value = compute()  # explains why"


def test_the_python_marker_is_the_default():
    assert PYTHON == "#"
    assert without_comments("# gone\nkept\n") == "kept"


def test_source_walk_excludes_the_tests_themselves():
    # A guard that scans its own assertions always fails — the test file quotes
    # the very pattern the guard hunts for.
    paths = list(python_sources())
    assert paths, "the walk found nothing, so every guard using it passes vacuously"
    assert not any("test" in p.name for p in paths)


def test_source_walk_reaches_the_files_the_guards_care_about():
    # The counterpart. If the globs ever stop matching, the guards keep passing
    # while checking nothing at all.
    names = {p.name for p in python_sources()}
    assert "app.py" in names
    assert "tenancy.py" in names
