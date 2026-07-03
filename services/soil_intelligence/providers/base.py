"""
Soil provider interface
=======================
Every data source that can contribute to a :class:`SoilProfile` implements
:class:`SoilProvider`. The service orchestrator runs the registered providers,
each returning a list of :class:`SoilAttribute` for a coordinate; the merger then
unions them into one profile.

Adding a provider is deliberately trivial — implement ``name`` and ``fetch`` and
register the instance in ``providers/__init__.py:default_providers()``. This is
the extension point the handoff calls for ("additional providers can easily be
added in the future").
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..models import SoilAttribute


class SoilProvider(ABC):
    """Abstract base for a soil/terrain data source."""

    #: Stable identifier recorded in every attribute's ``source`` field and in
    #: ``SoilProfile.provider_status``. Keep it short and human-readable.
    name: str = "base"

    #: Priority for conflict resolution when two providers supply the same
    #: attribute with equal confidence. Higher wins. Authoritative sources
    #: (user lab tests) should set this high; global models keep the default.
    priority: int = 0

    @abstractmethod
    async def fetch(self, lat: float, lon: float) -> List[SoilAttribute]:
        """Return attributes for the coordinate. Must never raise.

        Implementations should catch their own network/parse errors and return
        an empty list (the orchestrator records provider status separately). A
        raised exception is treated as a provider failure but should be avoided.
        """
        raise NotImplementedError
