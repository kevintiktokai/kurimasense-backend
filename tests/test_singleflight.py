"""
One producer call per key, however many callers arrive at once.

Production evidence for why this exists, from a real log: ten
`/field/{id}/state` responses landing within half a millisecond of each other,
twelve seconds in. That is not ten slow requests — it is one computation done
ten times, each queued behind the contention the others created. Later in the
same log, one field returned at 38s, 19s and 4.7s from three overlapping
requests.

The client gives up at twenty seconds, so past a certain fan-out a working
backend reads to the farmer as a connection failure.
"""

import asyncio

import pytest

from services.singleflight import coalesce, new_inflight_map


def run(coro):
    return asyncio.run(coro)


def test_concurrent_callers_share_one_producer_call():
    # The whole point. Ten callers, one computation.
    calls = 0
    inflight = new_inflight_map()

    async def producer():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)
        return "computed"

    async def scenario():
        results = await asyncio.gather(
            *(coalesce("field:x", inflight, producer) for _ in range(10))
        )
        return results

    results = run(scenario())
    assert results == ["computed"] * 10
    assert calls == 1, f"expected one producer call, got {calls}"


def test_different_keys_do_not_coalesce():
    # Two fields are two computations. Collapsing them would serve one field's
    # state for another, which is far worse than the stampede.
    seen = []
    inflight = new_inflight_map()

    async def producer(name):
        seen.append(name)
        await asyncio.sleep(0.01)
        return name

    async def scenario():
        return await asyncio.gather(
            coalesce("field:a", inflight, lambda: producer("a")),
            coalesce("field:b", inflight, lambda: producer("b")),
        )

    assert run(scenario()) == ["a", "b"]
    assert sorted(seen) == ["a", "b"]


def test_a_later_caller_runs_the_producer_again():
    # Not a cache. Once a flight lands, the next caller does the work — caching
    # is the caller's business and layering the two is deliberate.
    calls = 0
    inflight = new_inflight_map()

    async def producer():
        nonlocal calls
        calls += 1
        return calls

    async def scenario():
        first = await coalesce("k", inflight, producer)
        second = await coalesce("k", inflight, producer)
        return first, second

    assert run(scenario()) == (1, 2)


def test_a_failure_reaches_every_waiter():
    # A coalesced failure must fail everyone waiting on it. Leaving waiters
    # hanging is precisely the symptom this endpoint already had.
    inflight = new_inflight_map()

    async def producer():
        await asyncio.sleep(0.01)
        raise RuntimeError("upstream said no")

    async def scenario():
        return await asyncio.gather(
            *(coalesce("k", inflight, producer) for _ in range(5)),
            return_exceptions=True,
        )

    results = run(scenario())
    assert len(results) == 5
    assert all(isinstance(r, RuntimeError) for r in results), results


def test_the_key_is_released_after_success():
    # A leaked key would pin one answer there forever and every later caller
    # would get that value back — worse than the stampede it replaced.
    inflight = new_inflight_map()

    async def scenario():
        await coalesce("k", inflight, lambda: _immediately("v"))
        return dict(inflight)

    assert run(scenario()) == {}


def test_the_key_is_released_after_failure():
    inflight = new_inflight_map()

    async def producer():
        raise ValueError("no")

    async def scenario():
        with pytest.raises(ValueError):
            await coalesce("k", inflight, producer)
        return dict(inflight)

    assert run(scenario()) == {}


def test_a_failure_does_not_poison_the_next_caller():
    # The follow-on from release: after a failure the key is free, so the next
    # caller genuinely retries rather than inheriting the error.
    attempts = 0
    inflight = new_inflight_map()

    async def producer():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("transient")
        return "recovered"

    async def scenario():
        with pytest.raises(RuntimeError):
            await coalesce("k", inflight, producer)
        return await coalesce("k", inflight, producer)

    assert run(scenario()) == "recovered"
    assert attempts == 2


async def _immediately(value):
    return value
