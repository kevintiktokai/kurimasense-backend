"""
Soil Intelligence orchestrator
=============================
The public entry point for the subsystem. Coordinates the data lifecycle the
handoff specifies:

    Field created → coordinates obtained → retrieve baseline profile →
    store permanently → reuse locally → refresh only when necessary.

``get_or_build_profile`` is the workhorse:
  1. Try the stored profile (``repository.load_profile``). If present, fresh, and
     no refresh is forced → return it (zero external calls — the common path).
  2. Otherwise run every registered provider concurrently, merge their
     contributions (confidence/priority resolution), enrich with locally derived
     attributes, persist, and set ``refresh_after`` from the soonest attribute TTL.

Providers are best-effort and run under ``asyncio.gather(return_exceptions=True)``
so one slow/failed source never blocks the others or the caller.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from .models import SoilProfile, RefreshPolicy
from .merger import build_profile
from .derive import enrich_with_derived
from .providers import default_providers
from .providers.base import SoilProvider
from . import repository


# A profile with at least these many attributes counts as "usable" — below this
# we treat providers as having failed and allow a rebuild on next access.
_MIN_USABLE_ATTRS = 3


def _soonest_refresh(profile: SoilProfile) -> Optional[datetime]:
    """Compute the earliest time any non-derived attribute becomes stale."""
    now = datetime.now(timezone.utc)
    soonest: Optional[datetime] = None
    for a in profile.attributes.values():
        if a.derived:
            continue
        try:
            policy = RefreshPolicy(a.refresh_policy)
        except ValueError:
            policy = RefreshPolicy.MULTI_YEAR
        ttl = policy.ttl()
        if ttl is None:
            continue
        try:
            acquired = datetime.fromisoformat(a.acquired_at)
            if acquired.tzinfo is None:
                acquired = acquired.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            acquired = now
        due = acquired + ttl
        if soonest is None or due < soonest:
            soonest = due
    return soonest


async def build_profile_from_coords(
    field_id: Optional[str],
    lat: float,
    lon: float,
    providers: Optional[List[SoilProvider]] = None,
    slope_deg: Optional[float] = None,
) -> SoilProfile:
    """Run providers, merge, and derive — a pure fetch with no DB access.

    Exposed separately so it can be unit-tested with fake providers and reused by
    any caller that wants a profile without persistence.
    """
    providers = providers if providers is not None else default_providers()

    async def _run(p: SoilProvider) -> Tuple[SoilProvider, list]:
        try:
            attrs = await p.fetch(lat, lon)
            return (p, attrs or [])
        except Exception as e:  # defensive; providers shouldn't raise
            print(f"[soil.service] provider {p.name} raised: {e}")
            return (p, [])

    results = await asyncio.gather(*(_run(p) for p in providers), return_exceptions=True)
    contributions: List[Tuple[SoilProvider, list]] = []
    for r in results:
        if isinstance(r, tuple):
            contributions.append(r)

    profile = build_profile(field_id or "", lat, lon, contributions)
    enrich_with_derived(profile, slope_deg=slope_deg)
    return profile


async def get_or_build_profile(
    field_id: str,
    lat: Optional[float],
    lon: Optional[float],
    user_id: Optional[str] = None,
    tenant_ids: Optional[List[str]] = None,
    *,
    force_refresh: bool = False,
    persist: bool = True,
) -> Optional[SoilProfile]:
    """Return the field's soil profile, building & persisting it if necessary.

    The common path (a previously built, still-fresh profile) does zero external
    work. A rebuild happens only when the profile is absent, stale, or
    ``force_refresh`` is set.
    """
    # 1. Reuse a stored, fresh profile when we can.
    if not force_refresh:
        stored = repository.load_profile(field_id, user_id, tenant_ids)
        if stored and not stored.is_empty() and not stored.needs_refresh():
            return stored

    # 2. Need coordinates to (re)build. Without them, fall back to whatever we had.
    if lat is None or lon is None:
        return repository.load_profile(field_id, user_id, tenant_ids)

    profile = await build_profile_from_coords(field_id, lat, lon)

    # 3. If providers produced too little to be useful, keep any prior profile.
    if len(profile.attributes) < _MIN_USABLE_ATTRS:
        prior = repository.load_profile(field_id, user_id, tenant_ids)
        if prior and not prior.is_empty():
            return prior

    # 4. Persist for local reuse and set the next refresh horizon.
    if persist and profile.attributes:
        refresh_after = _soonest_refresh(profile)
        repository.save_profile(profile, refresh_after, user_id, tenant_ids)

    return profile


def get_stored_profile(
    field_id: str,
    user_id: Optional[str] = None,
    tenant_ids: Optional[List[str]] = None,
) -> Optional[SoilProfile]:
    """Synchronous, DB-only read for the AI context path (no network)."""
    return repository.load_profile(field_id, user_id, tenant_ids)
