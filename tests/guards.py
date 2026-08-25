"""
Shared machinery for the lint-shaped guard tests.

Six of those tests each grew their own copy of "skip the comment lines", and
two grew their own copy of "walk the source files". Small duplication, but the
wrong kind: every guard here exists to catch a pattern in source text, so a
subtle difference between six scanners means six different ideas about what
counts as code — and a guard that reads a comment as a live statement reports a
violation that isn't there, which is exactly how a guard earns enough false
positives to get deleted.

Every one of these guards has already been bitten by that. `test_rls_coverage`
had to learn that a `-- ALTER TABLE ... NO FORCE` rollback note is not a live
statement. `test_daily_log_window` and `test_error_disclosure` both matched
their own fix's explanatory comment. One implementation, fixed once.
"""

import pathlib
from typing import Iterator

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Comment markers, by the kind of file being scanned.
PYTHON = "#"
SQL = "--"


def code_lines(text: str, marker: str = PYTHON) -> Iterator[tuple[int, str]]:
    """
    ``(line_number, line)`` for every line that is not a whole-line comment.

    Line numbers are 1-indexed and count comment lines, so a reported offender
    points at the right line in the real file.
    """
    for number, line in enumerate(text.splitlines(), start=1):
        if line.strip().startswith(marker):
            continue
        yield number, line


def without_comments(text: str, marker: str = PYTHON) -> str:
    """The same text with whole-line comments removed, still newline-joined."""
    return "\n".join(line for _, line in code_lines(text, marker))


def python_sources(*globs: str) -> Iterator[pathlib.Path]:
    """
    Repository Python files, excluding the tests themselves.

    Tests are excluded because they quote the very patterns the guards look for
    — a guard that scans its own assertions always fails.
    """
    patterns = globs or ("*.py", "services/**/*.py")
    seen = set()
    for pattern in patterns:
        for path in sorted(ROOT.glob(pattern)):
            if path in seen or "test" in path.name or ".venv" in str(path):
                continue
            seen.add(path)
            yield path
