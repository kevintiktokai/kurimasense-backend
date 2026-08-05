"""
Seasons — the temporal crop record.

Before this package a field *was* its current season: ``crop_type``,
``planting_date`` and ``variety`` were single-valued columns on ``fields``, so
planting a new crop overwrote the previous one. That one design choice blocked
multi-season history, rotation-aware advice, residue-inoculum disease risk,
pre-plant planning and yield-gap attribution simultaneously.

Layout:

* :mod:`.lifecycle`  — pure status rules + rotation analysis (unit-tested)
* :mod:`.repository` — SQL, including the ``fields`` read-through mirror
* :mod:`.service`    — orchestration and the side effects each transition implies

Only :mod:`.lifecycle` is re-exported here. ``service`` and ``repository`` reach
for ``database``/``psycopg2`` at import time, so they are imported directly by
the routes rather than pulled in whenever anything touches the pure rules.
"""

from .lifecycle import (
    ALL_STATUSES,
    STATUS_ABANDONED,
    STATUS_ACTIVE,
    STATUS_CLOSED,
    STATUS_HARVESTED,
    STATUS_PLANNED,
    InvalidTransition,
    RotationSummary,
    assert_transition,
    can_transition,
    crop_family,
    derive_season_label,
    is_break_crop,
    is_live,
    summarise_rotation,
)

__all__ = [
    "ALL_STATUSES",
    "STATUS_ABANDONED",
    "STATUS_ACTIVE",
    "STATUS_CLOSED",
    "STATUS_HARVESTED",
    "STATUS_PLANNED",
    "InvalidTransition",
    "RotationSummary",
    "assert_transition",
    "can_transition",
    "crop_family",
    "derive_season_label",
    "is_break_crop",
    "is_live",
    "summarise_rotation",
]
