"""
Provider registry
=================
``default_providers()`` returns the ordered list of providers the orchestrator
runs. To add a source, implement :class:`SoilProvider` in a new module here and
append an instance below — nothing else in the pipeline changes.
"""

from __future__ import annotations

from typing import List

from .base import SoilProvider
from .soilgrids import SoilGridsProvider
from .terrain import TerrainClimateProvider


def default_providers() -> List[SoilProvider]:
    return [
        SoilGridsProvider(),
        TerrainClimateProvider(),
    ]


__all__ = ["SoilProvider", "SoilGridsProvider", "TerrainClimateProvider", "default_providers"]
