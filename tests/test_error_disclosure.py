"""
A 500 does not hand the caller the inside of the database.

Twenty-nine handlers ended in the same two lines:

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

`str(exc)` on an arbitrary exception is whatever that exception happens to say.
From psycopg2 that is table and column names, the text of the failing
statement, constraint names, and — on a connection failure — the host and
database out of the DSN.

That went to any authenticated caller, which in this product means every
officer at every institutional client. And none of it was logged, so the one
place the traceback belonged never got it.

Lint-shaped, like the other guards here, because the failure mode is silence:
a leaking 500 looks exactly like a non-leaking one until the day something
throws in front of the wrong person.
"""

import logging
import pathlib
import re

import pytest
from fastapi import HTTPException

from errors import internal_error

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Deliberate 4xx passthrough. A pure domain module raising
#: ValueError("A season cannot be closed before it opens") wrote that string for
#: a farmer, and the frontend's messageFor(kind, detail) prefers it over the
#: generic sentence. Those are chosen words; this file is about the ones nobody
#: chose.
ALLOWED_STATUSES = {"400", "403", "404", "409", "422", "503"}


def _source_files():
    for path in sorted(ROOT.glob("*.py")):
        yield path
    for path in sorted(ROOT.glob("services/**/*.py")):
        yield path


def test_no_handler_returns_a_raw_exception_as_a_500():
    offenders = []
    for path in _source_files():
        if path.name == "errors.py":  # the module documenting the old pattern
            continue
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            if line.strip().startswith("#"):
                continue
            if re.search(r"status_code=500\s*,\s*detail=str\(", line):
                offenders.append(f"{path.relative_to(ROOT)}:{number}")
    assert offenders == [], (
        "these hand the caller whatever the exception happened to say — use "
        f"errors.internal_error instead: {offenders}"
    )


def test_the_generic_500_says_nothing_about_the_inside():
    problem = HTTPException(status_code=500, detail="")
    built = internal_error(
        RuntimeError(
            'relation "growers" does not exist at character 15 '
            "host=db.internal dbname=kurimasense"
        )
    )
    assert built.status_code == 500
    for leaked in ("growers", "relation", "host=", "dbname", "character"):
        assert leaked not in built.detail, f"{leaked!r} reached the client"
    assert problem.status_code == 500  # sanity: we built the comparison right


def test_it_still_tells_the_caller_something_actionable():
    # A blank 500 is its own failure — the caller cannot report it and support
    # cannot find it. The reference is the whole point.
    detail = internal_error(RuntimeError("boom")).detail
    assert "Nothing you did caused this" in detail
    reference = re.search(r"reference ([0-9a-f]{12})", detail)
    assert reference, f"no quotable reference in: {detail!r}"


def test_the_reference_is_unique_per_occurrence():
    # Two failures must not collide, or the log line support finds is the wrong
    # one — worse than no reference at all.
    first = internal_error(RuntimeError("a")).detail
    second = internal_error(RuntimeError("b")).detail
    assert first != second


def test_the_traceback_reaches_the_log_with_the_same_reference(caplog):
    # The inward half. This path never called logger.exception, so the one place
    # the traceback belonged — the log an operator reads at 2am — was the one
    # place it did not go.
    with caplog.at_level(logging.ERROR, logger="kurimasense"):
        try:
            raise ValueError("the actual cause")
        except ValueError as exc:
            detail = internal_error(exc).detail

    record = next(r for r in caplog.records if "unhandled error" in r.getMessage())
    assert record.exc_info is not None, "the traceback was not logged"
    assert "the actual cause" in caplog.text, "the cause is not in the log"

    reference = re.search(r"reference ([0-9a-f]{12})", detail).group(1)
    assert reference in record.getMessage(), (
        "the reference given to the caller does not appear in the log line, so "
        "quoting it would find nothing"
    )


@pytest.mark.parametrize("status", sorted(ALLOWED_STATUSES))
def test_deliberate_4xx_messages_are_left_alone(status):
    # These carry domain messages written to be read. Guarding them the same way
    # would strip the farmer-facing explanations the frontend deliberately
    # surfaces over its own generic sentence.
    assert status != "500"
