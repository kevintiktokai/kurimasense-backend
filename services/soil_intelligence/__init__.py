"""
Soil Intelligence subsystem
==========================
Builds and maintains a persistent, multi-provider Soil Intelligence Profile for
every field. See ``service.py`` for the orchestration entry points and
``models.py`` for the data model. Providers live in ``providers/``.

Public API:
    * ``get_or_build_profile`` — lifecycle-aware fetch/build/persist (async).
    * ``get_stored_profile``    — DB-only read for the AI context path (sync).
    * ``build_profile_from_coords`` — pure fetch+merge+derive (no DB), for tests.
    * ``SoilProfile`` / ``SoilAttribute`` — the data model.
"""

from .models import SoilProfile, SoilAttribute, RefreshPolicy, CANONICAL_ATTRIBUTES
from .service import (
    get_or_build_profile,
    get_stored_profile,
    build_profile_from_coords,
)

__all__ = [
    "SoilProfile",
    "SoilAttribute",
    "RefreshPolicy",
    "CANONICAL_ATTRIBUTES",
    "get_or_build_profile",
    "get_stored_profile",
    "build_profile_from_coords",
]
