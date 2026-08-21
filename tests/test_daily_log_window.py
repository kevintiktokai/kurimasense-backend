"""
The field card shows the *latest* satellite pass.

`assemble_field_state` reads `logs[-1]` as the current observation, after
sorting ascending by date. Whatever fetches those logs therefore has to hand it
the newest ones. `_fetch_daily_logs` asked for:

    ORDER BY log_date ASC LIMIT 90

which is the ninety **oldest** passes. So on any field with more than ninety
observations on record, `logs[-1]` was not the latest pass — it was the
ninetieth one, from however many months back.

WHAT THAT LOOKED LIKE TO A FARMER
---------------------------------
Everything downstream of `latest` reads from the wrong date:

  - `current_ndvi` is a reading from months ago, labelled current
  - `days_since_pass` is inflated by the length of the whole gap
  - `observation_quality` degrades to stale, and `has_recent_pass` goes False
  - the trend window `logs[-30:]` covers the wrong month entirely

The card says the satellite has not looked at the field in months, on a field
being imaged every five days. And it gets worse the longer a field is on the
platform — a second-season field is exactly where a contractor is least willing
to hear "no recent data".

Sentinel-2's revisit is about five days, so ninety passes is roughly fifteen
months: the bug is invisible for a field's first season and permanent after it.

`yield_model._recent_ndvi` already did this correctly — `ORDER BY log_date DESC`
then `reversed(rows)` — which is what makes the ASC in the aggregator an
oversight rather than a decision.
"""

import pathlib
import re
from datetime import date, timedelta

ROOT = pathlib.Path(__file__).resolve().parent.parent
AGGREGATOR = (ROOT / "services" / "field_state" / "aggregator.py").read_text()


def _fetch_daily_logs_sql() -> str:
    """The query text inside _fetch_daily_logs."""
    body = AGGREGATOR.split("def _fetch_daily_logs", 1)[1].split("def ", 1)[0]
    return " ".join(body.split())


def test_the_log_window_takes_the_newest_passes_not_the_oldest():
    sql = _fetch_daily_logs_sql()
    assert re.search(r"ORDER BY log_date DESC LIMIT 90", sql), (
        "ASC LIMIT 90 returns the ninety oldest passes, and assemble_field_state "
        "reads logs[-1] as the latest one"
    )


def test_the_window_is_handed_back_in_chronological_order():
    # assemble_field_state sorts defensively, but every other caller and the
    # trend slice logs[-30:] assume oldest-first. DESC in SQL means the reversal
    # has to happen in Python.
    body = AGGREGATOR.split("def _fetch_daily_logs", 1)[1].split("def ", 1)[0]
    assert "reversed(" in body


def test_the_yield_model_agrees_on_the_direction():
    # The reference implementation. If this ever flips, the two disagree about
    # which ninety observations describe a field, and they feed the same card.
    yield_model = (ROOT / "yield_model.py").read_text()
    assert "ORDER BY log_date DESC" in yield_model
    assert "reversed(rows)" in yield_model


def test_no_caller_anywhere_still_takes_the_oldest_passes():
    # The window is fetched in four places — the aggregator, the yield model,
    # the exposure endpoint and the score-recompute diagnostic — because each
    # has its own connection story. Four copies of one decision is three
    # chances to disagree, and they did: two had it right and two had it
    # backwards. Until they are one function, this is what keeps them aligned.
    offenders = []
    for path in sorted(ROOT.glob("**/*.py")):
        if "test" in path.name or ".venv" in str(path):
            continue
        # Comment lines excluded: the fixes' own comments quote the bad SQL to
        # explain what it did.
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            if line.strip().startswith("#"):
                continue
            if re.search(r"ORDER BY log_date ASC LIMIT", line):
                offenders.append(f"{path.relative_to(ROOT)}:{number}")
    assert offenders == [], (
        "these take the oldest passes, and every consumer reads the last row as "
        f"the latest one: {offenders}"
    )


def test_the_score_diagnostic_agrees_too():
    # Read-only, but it prints the score and observation quality an operator
    # trusts when asking why a field is scoring low.
    script = (ROOT / "scripts" / "recompute_kurima_scores.py").read_text()
    assert "ORDER BY log_date DESC LIMIT 90" in script
    assert "reversed(" in script


def test_the_exposure_endpoint_uses_the_same_window():
    # It fetched every daily_log ever recorded for every field in the tenant —
    # no window, no limit — and passed them to the same assemble_field_state.
    # Unbounded, and growing with every satellite pass.
    financial = (ROOT / "financial_routes.py").read_text()
    exposure = financial.split("def get_exposure", 1)[1]
    logs_query = exposure.split("daily_logs", 1)[1][:600]
    assert "ROW_NUMBER() OVER" in exposure and "rn <= 90" in exposure, (
        "the per-field window is missing: " + " ".join(logs_query.split())[:200]
    )
    assert "ORDER BY log_date DESC" in exposure


def test_the_exposure_endpoint_stops_selecting_every_column():
    # `SELECT f.*` pulled polygon_coordinates — a boundary polygon per field —
    # for every field in the book, on an endpoint that never reads it.
    financial = (ROOT / "financial_routes.py").read_text()
    exposure = financial.split("def get_exposure", 1)[1]
    # Comments stripped: the fix's own comment explains what `f.*` was doing.
    code = "\n".join(
        line for line in exposure.splitlines() if not line.strip().startswith("#")
    )
    assert "f.*" not in code


def test_what_the_wrong_window_did_to_the_card():
    # The behavioural half: same field, same history, two windows. This is the
    # difference the fix makes, expressed in the number the farmer reads.
    from services.field_state import classifiers

    today = date(2026, 8, 21)
    # Five-day revisit, 200 passes on record — a field in its second season.
    passes = [today - timedelta(days=5 * i) for i in range(200)]
    chronological = sorted(passes)

    oldest_90 = chronological[:90]        # what ASC LIMIT 90 returned
    newest_90 = chronological[-90:]       # what DESC LIMIT 90 + reverse returns

    stale_gap = (today - oldest_90[-1]).days
    fresh_gap = (today - newest_90[-1]).days

    assert fresh_gap == 0
    assert stale_gap > 500, "the oldest-90 window put the 'latest' pass this far back"

    # And that gap is what the quality classifier saw.
    assert classifiers.observation_quality(fresh_gap, 0) in ("good", "fair")
    assert classifiers.observation_quality(stale_gap, 0) not in ("good", "fair")
