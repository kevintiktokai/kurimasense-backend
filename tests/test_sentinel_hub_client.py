"""
Unit tests for services/satellite/sentinel_hub_client.py.

Run:
    cd backend
    python -m pytest tests/test_sentinel_hub_client.py -v
"""
from __future__ import annotations

import os
import sys
from datetime import date
from typing import Any, Callable, Dict, List, Optional

import httpx
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.satellite.sentinel_hub_client import (  # noqa: E402
    PU_HEADER,
    SentinelHubAuthError,
    SentinelHubClient,
    SentinelHubError,
    SentinelHubQuotaError,
    SentinelHubRateLimitError,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _token_response(expires_in: int = 3600, token: str = "tok-1") -> httpx.Response:
    return httpx.Response(
        200,
        json={"access_token": token, "expires_in": expires_in, "token_type": "bearer"},
    )


def _make_transport(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def _make_client(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    monthly_pu_quota: float = 100.0,
    base_delay: float = 0.0,
    max_delay: float = 0.0,
    max_retries: int = 3,
) -> SentinelHubClient:
    transport = _make_transport(handler)
    http_client = httpx.AsyncClient(transport=transport)
    return SentinelHubClient(
        client_id="id",
        client_secret="secret",
        monthly_pu_quota=monthly_pu_quota,
        http_client=http_client,
        base_delay=base_delay,
        max_delay=max_delay,
        max_retries=max_retries,
    )


GEOMETRY = {
    "type": "Polygon",
    "coordinates": [[[31.0, -17.8], [31.1, -17.8], [31.1, -17.7], [31.0, -17.7], [31.0, -17.8]]],
}
TIME_RANGE = (date(2026, 4, 1), date(2026, 4, 30))
EVALSCRIPT = "// dummy"


# --------------------------------------------------------------------------- #
# Construction / auth
# --------------------------------------------------------------------------- #

def test_missing_credentials_raises(monkeypatch):
    monkeypatch.delenv("SH_CLIENT_ID", raising=False)
    monkeypatch.delenv("SH_CLIENT_SECRET", raising=False)
    with pytest.raises(SentinelHubAuthError):
        SentinelHubClient()


@pytest.mark.asyncio
async def test_token_fetched_on_first_request_and_cached():
    calls: List[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            calls.append("token")
            return _token_response()
        calls.append("statistical")
        return httpx.Response(
            200,
            json={"data": []},
            headers={PU_HEADER: "0.5"},
        )

    client = _make_client(handler)
    try:
        await client.statistical_request(GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a")
        await client.statistical_request(GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a")
    finally:
        await client.aclose()

    assert calls.count("token") == 1
    assert calls.count("statistical") == 2


@pytest.mark.asyncio
async def test_token_refreshed_when_expired():
    tokens_issued: List[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            tok = f"tok-{len(tokens_issued) + 1}"
            tokens_issued.append(tok)
            # Expire immediately so the next call must refresh.
            return _token_response(expires_in=1, token=tok)
        return httpx.Response(200, json={"ok": True}, headers={PU_HEADER: "0.1"})

    client = _make_client(handler)
    try:
        await client.statistical_request(GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a")
        await client.statistical_request(GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a")
    finally:
        await client.aclose()

    # leeway is 60s and expires_in=1 => second call must re-fetch.
    assert len(tokens_issued) == 2


@pytest.mark.asyncio
async def test_token_endpoint_failure_raises_auth_error():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return httpx.Response(401, text="bad creds")
        return httpx.Response(200, json={})

    client = _make_client(handler)
    try:
        with pytest.raises(SentinelHubAuthError):
            await client.statistical_request(
                GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a"
            )
    finally:
        await client.aclose()


# --------------------------------------------------------------------------- #
# Statistical / process API success
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_statistical_request_returns_json():
    expected = {"data": [{"interval": {"from": "2026-04-01"}, "outputs": {}}]}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        assert request.url.path.endswith("/statistics")
        body = request.read()
        assert b"sentinel-2-l2a" in body
        return httpx.Response(200, json=expected, headers={PU_HEADER: "1.0"})

    client = _make_client(handler)
    try:
        result = await client.statistical_request(
            GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a"
        )
    finally:
        await client.aclose()

    assert result == expected


@pytest.mark.asyncio
async def test_process_request_returns_raster_bytes():
    raster = b"\x89PNG\r\n\x1a\n" + b"fake-png-bytes"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        assert request.url.path.endswith("/process")
        return httpx.Response(
            200,
            content=raster,
            headers={PU_HEADER: "2.5", "Content-Type": "image/png"},
        )

    client = _make_client(handler)
    try:
        result = await client.process_request(
            GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a", width=512, height=512
        )
    finally:
        await client.aclose()

    assert result == raster


# --------------------------------------------------------------------------- #
# Backoff on 429 / 503
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_retries_on_429_then_succeeds():
    state = {"calls": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        state["calls"] += 1
        if state["calls"] < 3:
            return httpx.Response(429, text="slow down", headers={"Retry-After": "0"})
        return httpx.Response(200, json={"ok": True}, headers={PU_HEADER: "0.1"})

    client = _make_client(handler, base_delay=0.0, max_delay=0.0, max_retries=5)
    try:
        result = await client.statistical_request(
            GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a"
        )
    finally:
        await client.aclose()

    assert result == {"ok": True}
    assert state["calls"] == 3


@pytest.mark.asyncio
async def test_retries_on_503_then_succeeds():
    state = {"calls": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        state["calls"] += 1
        if state["calls"] < 2:
            return httpx.Response(503, text="unavailable")
        return httpx.Response(200, json={"ok": True}, headers={PU_HEADER: "0.1"})

    client = _make_client(handler, base_delay=0.0, max_delay=0.0, max_retries=5)
    try:
        await client.statistical_request(
            GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a"
        )
    finally:
        await client.aclose()

    assert state["calls"] == 2


@pytest.mark.asyncio
async def test_exhausts_retries_raises_rate_limit_error():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        return httpx.Response(429, text="nope", headers={"Retry-After": "0"})

    client = _make_client(handler, base_delay=0.0, max_delay=0.0, max_retries=2)
    try:
        with pytest.raises(SentinelHubRateLimitError):
            await client.statistical_request(
                GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a"
            )
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_non_retryable_4xx_raises_immediately():
    state = {"calls": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        state["calls"] += 1
        return httpx.Response(400, text="bad request")

    client = _make_client(handler, base_delay=0.0, max_delay=0.0, max_retries=5)
    try:
        with pytest.raises(SentinelHubError):
            await client.statistical_request(
                GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a"
            )
    finally:
        await client.aclose()

    assert state["calls"] == 1


# --------------------------------------------------------------------------- #
# Quota tracking
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_pu_consumption_accumulates():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        return httpx.Response(200, json={"ok": True}, headers={PU_HEADER: "10"})

    client = _make_client(handler, monthly_pu_quota=1000.0)
    try:
        await client.statistical_request(GEOMETRY, TIME_RANGE, EVALSCRIPT, "s2")
        await client.statistical_request(GEOMETRY, TIME_RANGE, EVALSCRIPT, "s2")
        assert client.pu_consumed_this_month == pytest.approx(20.0)
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_quota_error_raised_above_80_percent():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        # 85 PU consumed in one shot, quota=100 → 85% > 80% threshold.
        return httpx.Response(200, json={"ok": True}, headers={PU_HEADER: "85"})

    client = _make_client(handler, monthly_pu_quota=100.0)
    try:
        with pytest.raises(SentinelHubQuotaError):
            await client.statistical_request(
                GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a"
            )
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_quota_error_not_raised_at_or_below_threshold():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        return httpx.Response(200, json={"ok": True}, headers={PU_HEADER: "80"})

    client = _make_client(handler, monthly_pu_quota=100.0)
    try:
        # Exactly 80% — must NOT raise (threshold is strict >).
        await client.statistical_request(
            GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a"
        )
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_logs_pu_per_request(caplog):
    import logging

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            return _token_response()
        return httpx.Response(200, json={"ok": True}, headers={PU_HEADER: "1.25"})

    client = _make_client(handler, monthly_pu_quota=1000.0)
    try:
        with caplog.at_level(logging.INFO, logger="services.satellite.sentinel_hub_client"):
            await client.statistical_request(
                GEOMETRY, TIME_RANGE, EVALSCRIPT, "sentinel-2-l2a"
            )
    finally:
        await client.aclose()

    assert any(
        "sentinel_hub.request" in r.message and "pu=1.250" in r.message
        for r in caplog.records
    )
