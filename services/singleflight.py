"""
One producer call per key, however many callers ask at once.

WHY THIS EXISTS
---------------
A dashboard with ten fields fires ten `/field/{id}/state` requests at mount,
and the field page fires two or three more for the field already on screen.
There is a ten-minute cache on that endpoint, and it does not help on the first
request: every one of those callers misses simultaneously, every one does the
full computation — four weather calls, the yield projection, the alert pass —
and every one writes the same answer into the same cache slot.

Production shows it plainly. Ten requests completing within half a millisecond
of each other after twelve seconds is not ten slow requests; it is one piece of
work done ten times, with nine of them queued behind the contention the other
nine created. Later in the same log the same field returns at 38s, 19s and 4.7s
— three overlapping requests, the last one finally cheap because by then a
cache entry existed.

The client gives up at twenty seconds, so past a certain fan-out the farmer
sees a connection error on a backend that is working — just doing the same job
N times.

`climate_service._cached` already solved this for weather, and this is that
mechanism lifted out so the field-state path can use it too, rather than a
second implementation drifting away from the first.

WHAT THIS IS NOT
----------------
Not a cache. It coalesces *concurrent* callers onto one in-flight producer and
nothing more; once that call finishes the entry is released and the next caller
runs the producer again. Caching is the caller's business, and layering the two
is the point: the cache handles the second minute, this handles the second
millisecond.
"""

import asyncio
from typing import Any, Awaitable, Callable, Dict, MutableMapping

#: key -> the future every concurrent caller for that key is waiting on.
InflightMap = MutableMapping[str, "asyncio.Future"]


def new_inflight_map() -> Dict[str, "asyncio.Future"]:
    """A fresh map. Callers own theirs, so two subsystems never share a key."""
    return {}


async def coalesce(
    key: str,
    inflight: InflightMap,
    producer: Callable[[], Awaitable[Any]],
) -> Any:
    """
    Run ``producer`` once for ``key``; concurrent callers await that same call.

    The first caller becomes the producer. Everyone who arrives while it is
    running awaits its future and gets its result — or its exception, which
    matters: a coalesced failure must fail every waiter rather than leaving them
    hanging, and hanging is precisely the symptom this endpoint already had.

    The entry is always released, including on failure. An in-flight map that
    leaks a key would pin one answer there forever and every later caller would
    get that stale value back — worse than the stampede.
    """
    existing = inflight.get(key)
    if existing is not None:
        return await existing

    loop = asyncio.get_event_loop()
    future: "asyncio.Future" = loop.create_future()
    # Mark any exception retrieved, so a producer failure with no waiter does
    # not emit asyncio's "Future exception was never retrieved" warning. Real
    # waiters still receive it through `await existing` above.
    future.add_done_callback(lambda f: f.cancelled() or f.exception())
    inflight[key] = future

    try:
        value = await producer()
        if not future.done():
            future.set_result(value)
        return value
    except Exception as error:
        if not future.done():
            future.set_exception(error)
        raise
    finally:
        inflight.pop(key, None)
