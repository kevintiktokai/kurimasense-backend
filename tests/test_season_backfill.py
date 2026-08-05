"""
Backfill planning tests — services/seasons/backfill.py.

Window chunking carries the most weight: a multi-year backfill is dozens of
requests per field, and a boundary bug silently drops or double-counts days,
which is invisible until someone notices a gap in a history chart months later.
"""

from datetime import date

import pytest

from services.seasons.backfill import (
    DEFAULT_WINDOW_DAYS,
    SENTINEL2_EPOCH,
    attribute_row_to_season,
    estimate_requests,
    plan_backfill_range,
    plan_windows,
    select_new_rows,
)


# --- Window chunking ---------------------------------------------------------

def test_a_short_range_is_a_single_window():
    w = plan_windows("2026-01-01", "2026-03-01", window_days=180)
    assert len(w) == 1
    assert w[0].start == date(2026, 1, 1)
    assert w[0].end == date(2026, 3, 1)


def test_windows_tile_the_range_without_gaps_or_overlaps():
    windows = plan_windows("2024-01-01", "2026-01-01", window_days=180)
    ordered = sorted(windows, key=lambda x: x.start)
    # Contiguous: each window starts the day after the previous one ends.
    for prev, nxt in zip(ordered, ordered[1:]):
        assert (nxt.start - prev.end).days == 1
    assert ordered[0].start == date(2024, 1, 1)
    assert ordered[-1].end == date(2026, 1, 1)


def test_every_day_in_the_range_is_covered_exactly_once():
    windows = plan_windows("2025-01-01", "2025-12-31", window_days=90)
    total = sum(w.days for w in windows)
    assert total == 365


def test_windows_come_back_newest_first():
    # An interrupted backfill should leave the recent history that matters,
    # not a decade of context with the current season missing.
    windows = plan_windows("2020-01-01", "2026-01-01")
    assert windows[0].start > windows[-1].start


def test_range_is_clamped_to_the_sentinel2_archive():
    # Requesting imagery from before the satellite existed burns quota for nothing.
    windows = plan_windows("2010-01-01", "2016-01-01")
    assert min(w.start for w in windows) == SENTINEL2_EPOCH


def test_a_range_entirely_before_the_archive_yields_nothing():
    assert plan_windows("2005-01-01", "2010-01-01") == []


def test_inverted_or_missing_ranges_are_rejected_not_guessed():
    assert plan_windows("2026-06-01", "2026-01-01") == []
    assert plan_windows(None, "2026-01-01") == []
    assert plan_windows("2026-01-01", None) == []
    assert plan_windows("nonsense", "2026-01-01") == []


def test_a_nonsensical_window_size_cannot_loop_forever():
    windows = plan_windows("2026-01-01", "2026-01-10", window_days=0)
    assert len(windows) == 10          # falls back to one day per window
    assert all(w.days == 1 for w in windows)


def test_single_day_range_is_one_window():
    w = plan_windows("2026-01-01", "2026-01-01")
    assert len(w) == 1
    assert w[0].days == 1


def test_windows_serialise_to_iso_for_the_api():
    w = plan_windows("2026-01-01", "2026-02-01")[0]
    assert w.as_iso() == ("2026-01-01", "2026-02-01")


# --- Depth planning ----------------------------------------------------------

def test_requested_depth_sets_the_start():
    start, end = plan_backfill_range(3, today=date(2026, 8, 5))
    assert end == date(2026, 8, 5)
    assert start.year == 2023


def test_depth_extends_to_cover_an_older_recorded_season():
    # A season the farmer told us about but with no imagery renders as an empty
    # line, which reads as a bad season rather than an unobserved one.
    start, _ = plan_backfill_range(
        2, today=date(2026, 8, 5), earliest_season_planting="2021-11-15"
    )
    assert start == date(2021, 11, 15)


def test_a_recent_season_does_not_shorten_the_requested_depth():
    start, _ = plan_backfill_range(
        5, today=date(2026, 8, 5), earliest_season_planting="2025-11-15"
    )
    assert start.year == 2021


def test_depth_is_clamped_to_the_archive():
    start, _ = plan_backfill_range(30, today=date(2026, 8, 5))
    assert start == SENTINEL2_EPOCH


# --- Idempotency -------------------------------------------------------------

def _row(day, ndvi=0.5):
    return (day, ndvi, None, 10.0)


def test_days_already_stored_are_not_refetched_into_duplicates():
    rows = select_new_rows(
        [_row("2026-01-01"), _row("2026-01-02"), _row("2026-01-03")],
        existing_dates=["2026-01-02"],
    )
    assert [r[0] for r in rows] == ["2026-01-01", "2026-01-03"]


def test_a_rerun_with_everything_stored_inserts_nothing():
    rows = select_new_rows(
        [_row("2026-01-01"), _row("2026-01-02")],
        existing_dates=["2026-01-01", "2026-01-02"],
    )
    assert rows == []


def test_duplicate_days_within_one_response_are_collapsed():
    rows = select_new_rows([_row("2026-01-01", 0.5), _row("2026-01-01", 0.6)], [])
    assert len(rows) == 1
    # First wins — later duplicates are dropped, not merged.
    assert rows[0][1] == 0.5


def test_rows_without_a_date_are_dropped():
    rows = select_new_rows([("", 0.5, None, None), _row("2026-01-01")], [])
    assert [r[0] for r in rows] == ["2026-01-01"]


# --- Season attribution ------------------------------------------------------

SEASONS = [
    {"id": "s1", "planting_date": "2026-11-15"},
    {"id": "s2", "planting_date": "2025-11-20"},
]


def test_a_day_is_attributed_to_the_season_running_at_the_time():
    assert attribute_row_to_season("2026-12-15", SEASONS) == "s1"
    assert attribute_row_to_season("2026-03-01", SEASONS) == "s2"


def test_planting_day_belongs_to_the_new_season():
    assert attribute_row_to_season("2026-11-15", SEASONS) == "s1"


def test_days_before_every_recorded_season_stay_unattributed():
    # Forcing them onto the oldest season would invent history.
    assert attribute_row_to_season("2024-01-01", SEASONS) is None


def test_attribution_handles_missing_data_safely():
    assert attribute_row_to_season(None, SEASONS) is None
    assert attribute_row_to_season("2026-12-15", []) is None
    assert attribute_row_to_season("2026-12-15", [{"id": "x", "planting_date": None}]) is None


# --- Quota -------------------------------------------------------------------

def test_request_count_is_reported_before_a_run():
    # A ten-year backfill across a large tenant should be a deliberate choice,
    # not a surprise bill.
    assert estimate_requests(21, 50) == 1050
    assert estimate_requests(0, 50) == 0
    assert estimate_requests(-3, 50) == 0


def test_default_window_keeps_a_decade_to_a_sane_request_count():
    start, end = plan_backfill_range(10, today=date(2026, 8, 5))
    windows = plan_windows(start, end, DEFAULT_WINDOW_DAYS)
    # Roughly two requests a year per field — bounded enough to run for a tenant.
    assert 15 <= len(windows) <= 30
