"""
Field State Aggregator package
==============================
Canonical "state of this field" service. Every consumer screen (and every future
institutional screen) reads from :func:`build_field_state`, so two screens can
never disagree about a field by construction.

Public surface:
    * :func:`aggregator.build_field_state` — full async pipeline (DB + climate + …)
    * :func:`aggregator.assemble_field_state` — pure, I/O-free assembly (testable)
    * :class:`models.FieldState` — the response contract
    * :exc:`aggregator.FieldNotFound` / :exc:`aggregator.FieldAccessDenied`
"""

from .models import FieldState  # noqa: F401
from .aggregator import (  # noqa: F401
    build_field_state,
    assemble_field_state,
    resolve_access,
    FieldNotFound,
    FieldAccessDenied,
)

__all__ = [
    "FieldState",
    "build_field_state",
    "assemble_field_state",
    "resolve_access",
    "FieldNotFound",
    "FieldAccessDenied",
]
