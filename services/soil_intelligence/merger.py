"""
Profile merger
==============
Unions the attribute lists returned by every provider into a single
:class:`SoilProfile`. When two providers supply the same canonical attribute, the
winner is chosen by (1) higher provider ``priority``, then (2) higher confidence.
This is what lets an authoritative source (a future user lab test, priority 100)
override a global model without any special-casing at the call site.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .models import SoilAttribute, SoilProfile
from .providers.base import SoilProvider


def merge_attributes(
    contributions: List[Tuple[SoilProvider, List[SoilAttribute]]],
) -> Dict[str, SoilAttribute]:
    """Resolve one winning attribute per key across all provider contributions."""
    priority_by_source = {p.name: p.priority for p, _ in contributions}
    best: Dict[str, SoilAttribute] = {}
    for _provider, attrs in contributions:
        for attr in attrs:
            if attr.value is None:
                continue
            incumbent = best.get(attr.key)
            if incumbent is None:
                best[attr.key] = attr
                continue
            cur_pri = priority_by_source.get(attr.source, 0)
            inc_pri = priority_by_source.get(incumbent.source, 0)
            if cur_pri > inc_pri:
                best[attr.key] = attr
            elif cur_pri == inc_pri:
                if (attr.confidence or 0) > (incumbent.confidence or 0):
                    best[attr.key] = attr
    return best


def build_profile(
    field_id: str,
    lat: float,
    lon: float,
    contributions: List[Tuple[SoilProvider, List[SoilAttribute]]],
) -> SoilProfile:
    """Assemble a :class:`SoilProfile` from provider contributions, recording each
    provider's status (ok / partial / empty)."""
    profile = SoilProfile(field_id=field_id, lat=lat, lon=lon)
    profile.attributes = merge_attributes(contributions)

    contributed_sources = {a.source for a in profile.attributes.values()}
    for provider, attrs in contributions:
        non_null = [a for a in attrs if a.value is not None]
        if not attrs:
            profile.provider_status[provider.name] = "error"
        elif not non_null:
            profile.provider_status[provider.name] = "empty"
        elif provider.name in contributed_sources:
            profile.provider_status[provider.name] = "ok"
        else:
            # Contributed values but all were superseded by a higher-priority src.
            profile.provider_status[provider.name] = "partial"
    return profile
