"""
Sentinel Hub API client for KurimaSense.

Wraps the Sentinel Hub OAuth2, Process, and Statistical APIs with:
  - OAuth2 client credentials auth + auto-refresh before expiry
  - Exponential backoff on 429 (rate limit) and 503 (service unavailable)
  - Per-request logging of processing units consumed
  - Monthly quota tracking that raises SentinelHubQuotaError above 80%

HTTP client setup follows the patterns in climate_service.py
(lazy-initialised httpx.AsyncClient with explicit Timeout).
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import date
from typing import Any, Dict, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# Sentinel Hub endpoints
TOKEN_URL = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
PROCESS_URL = "https://services.sentinel-hub.com/api/v1/process"
STATISTICAL_URL = "https://services.sentinel-hub.com/api/v1/statistics"

# Refresh tokens this many seconds before expiry to avoid mid-request expiry.
TOKEN_REFRESH_LEEWAY_SECONDS = 60

# Backoff parameters for 429/503.
DEFAULT_MAX_RETRIES = 5
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 30.0  # seconds

# Quota threshold — raise above this fraction of the monthly limit.
QUOTA_THRESHOLD = 0.80

# Header Sentinel Hub uses to report PU consumption per response.
PU_HEADER = "x-processingunits-spent"


class SentinelHubError(Exception):
    """Base error for Sentinel Hub client failures."""


class SentinelHubAuthError(SentinelHubError):
    """Raised when OAuth2 token acquisition fails."""


class SentinelHubRateLimitError(SentinelHubError):
    """Raised when retries are exhausted on 429/503."""


class SentinelHubQuotaError(SentinelHubError):
    """Raised when monthly processing-unit usage exceeds the configured threshold."""


class SentinelHubClient:
    """
    Async Sentinel Hub client.

    Reads credentials from SH_CLIENT_ID and SH_CLIENT_SECRET unless explicitly
    passed. Reads monthly PU quota from SH_MONTHLY_PU_QUOTA (default 30000).
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        monthly_pu_quota: Optional[float] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_BASE_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
    ) -> None:
        self._client_id = client_id or os.environ.get("SH_CLIENT_ID")
        self._client_secret = client_secret or os.environ.get("SH_CLIENT_SECRET")
        if not self._client_id or not self._client_secret:
            raise SentinelHubAuthError(
                "SH_CLIENT_ID and SH_CLIENT_SECRET must be set in the environment "
                "or passed explicitly to SentinelHubClient."
            )

        if monthly_pu_quota is None:
            monthly_pu_quota = float(os.environ.get("SH_MONTHLY_PU_QUOTA", "30000"))
        self._monthly_pu_quota = monthly_pu_quota

        self._http = http_client
        self._owns_http = http_client is None

        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay

        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0
        self._token_lock = asyncio.Lock()

        # Monthly PU bookkeeping (calendar month, UTC).
        self._pu_period_key: str = self._current_period_key()
        self._pu_consumed: float = 0.0

    # ------------------------------------------------------------------ #
    # HTTP client lifecycle
    # ------------------------------------------------------------------ #
    def _get_http(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=5.0, read=60.0, write=30.0, pool=10.0)
            )
        return self._http

    async def aclose(self) -> None:
        if self._http is not None and self._owns_http:
            await self._http.aclose()
            self._http = None

    async def __aenter__(self) -> "SentinelHubClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    # ------------------------------------------------------------------ #
    # OAuth2
    # ------------------------------------------------------------------ #
    async def _ensure_token(self) -> str:
        """Return a valid access token, refreshing it if expired or near expiry."""
        now = time.time()
        if self._access_token and now < self._token_expiry - TOKEN_REFRESH_LEEWAY_SECONDS:
            return self._access_token

        async with self._token_lock:
            now = time.time()
            if self._access_token and now < self._token_expiry - TOKEN_REFRESH_LEEWAY_SECONDS:
                return self._access_token
            await self._fetch_token()
            assert self._access_token is not None
            return self._access_token

    async def _fetch_token(self) -> None:
        client = self._get_http()
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        try:
            response = await client.post(
                TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as e:
            raise SentinelHubAuthError(f"Token request failed: {e}") from e

        if response.status_code != 200:
            raise SentinelHubAuthError(
                f"Token request returned {response.status_code}: {response.text[:200]}"
            )

        payload = response.json()
        token = payload.get("access_token")
        expires_in = payload.get("expires_in")
        if not token or not expires_in:
            raise SentinelHubAuthError(
                f"Token response missing access_token/expires_in: {payload}"
            )

        self._access_token = token
        self._token_expiry = time.time() + float(expires_in)
        logger.info(
            "sentinel_hub.token_refreshed expires_in=%ss leeway=%ss",
            int(expires_in),
            TOKEN_REFRESH_LEEWAY_SECONDS,
        )

    # ------------------------------------------------------------------ #
    # Quota tracking
    # ------------------------------------------------------------------ #
    @staticmethod
    def _current_period_key() -> str:
        t = time.gmtime()
        return f"{t.tm_year:04d}-{t.tm_mon:02d}"

    def _roll_period_if_needed(self) -> None:
        period = self._current_period_key()
        if period != self._pu_period_key:
            logger.info(
                "sentinel_hub.quota_period_rollover from=%s to=%s prev_consumed=%.3f",
                self._pu_period_key,
                period,
                self._pu_consumed,
            )
            self._pu_period_key = period
            self._pu_consumed = 0.0

    def _record_pu(self, pu: float, endpoint: str) -> None:
        self._roll_period_if_needed()
        self._pu_consumed += pu
        usage_fraction = (
            self._pu_consumed / self._monthly_pu_quota if self._monthly_pu_quota > 0 else 0.0
        )
        logger.info(
            "sentinel_hub.request endpoint=%s pu=%.3f month=%s month_consumed=%.3f "
            "month_quota=%.3f usage_pct=%.1f%%",
            endpoint,
            pu,
            self._pu_period_key,
            self._pu_consumed,
            self._monthly_pu_quota,
            usage_fraction * 100,
        )
        if usage_fraction > QUOTA_THRESHOLD:
            raise SentinelHubQuotaError(
                f"Monthly Sentinel Hub PU usage at {usage_fraction * 100:.1f}% "
                f"of quota ({self._pu_consumed:.1f}/{self._monthly_pu_quota:.0f}); "
                f"threshold is {QUOTA_THRESHOLD * 100:.0f}%."
            )

    @property
    def pu_consumed_this_month(self) -> float:
        self._roll_period_if_needed()
        return self._pu_consumed

    # ------------------------------------------------------------------ #
    # Core request with backoff
    # ------------------------------------------------------------------ #
    async def _request_with_backoff(
        self,
        method: str,
        url: str,
        *,
        endpoint_label: str,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        client = self._get_http()
        attempt = 0
        while True:
            token = await self._ensure_token()
            headers = {"Authorization": f"Bearer {token}"}
            try:
                response = await client.request(
                    method, url, headers=headers, json=json_body
                )
            except httpx.HTTPError as e:
                # Network-level error — treat like a transient failure.
                if attempt >= self._max_retries:
                    raise SentinelHubError(
                        f"{endpoint_label} request failed after {attempt} retries: {e}"
                    ) from e
                delay = self._compute_delay(attempt, retry_after=None)
                logger.warning(
                    "sentinel_hub.network_error endpoint=%s attempt=%d delay=%.2fs error=%s",
                    endpoint_label,
                    attempt,
                    delay,
                    e,
                )
                await asyncio.sleep(delay)
                attempt += 1
                continue

            if response.status_code == 401:
                # Token may have been revoked early — force a refresh once.
                self._access_token = None
                self._token_expiry = 0.0
                if attempt >= self._max_retries:
                    raise SentinelHubAuthError(
                        f"{endpoint_label} returned 401 after refresh attempts"
                    )
                attempt += 1
                continue

            if response.status_code in (429, 503):
                if attempt >= self._max_retries:
                    raise SentinelHubRateLimitError(
                        f"{endpoint_label} returned {response.status_code} after "
                        f"{attempt} retries"
                    )
                retry_after = self._parse_retry_after(response)
                delay = self._compute_delay(attempt, retry_after=retry_after)
                logger.warning(
                    "sentinel_hub.backoff endpoint=%s status=%d attempt=%d delay=%.2fs",
                    endpoint_label,
                    response.status_code,
                    attempt,
                    delay,
                )
                await asyncio.sleep(delay)
                attempt += 1
                continue

            if response.status_code >= 400:
                raise SentinelHubError(
                    f"{endpoint_label} returned {response.status_code}: "
                    f"{response.text[:500]}"
                )

            return response

    def _compute_delay(self, attempt: int, retry_after: Optional[float]) -> float:
        exp_delay = min(self._base_delay * (2 ** attempt), self._max_delay)
        if retry_after is not None:
            return max(exp_delay, retry_after)
        return exp_delay

    @staticmethod
    def _parse_retry_after(response: httpx.Response) -> Optional[float]:
        header = response.headers.get("Retry-After")
        if header is None:
            return None
        try:
            return float(header)
        except ValueError:
            return None

    @staticmethod
    def _extract_pu(response: httpx.Response) -> float:
        raw = response.headers.get(PU_HEADER)
        if raw is None:
            return 0.0
        try:
            return float(raw)
        except ValueError:
            return 0.0

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    async def statistical_request(
        self,
        geometry: Dict[str, Any],
        time_range: Tuple[date, date],
        evalscript: str,
        collection: str,
    ) -> Dict[str, Any]:
        """Call the Statistical API and return aggregated stats per time period."""
        from_date, to_date = time_range
        body = {
            "input": {
                "bounds": {"geometry": geometry},
                "data": [
                    {
                        "type": collection,
                        "dataFilter": {
                            "timeRange": {
                                "from": f"{from_date.isoformat()}T00:00:00Z",
                                "to": f"{to_date.isoformat()}T23:59:59Z",
                            }
                        },
                    }
                ],
            },
            "aggregation": {
                "timeRange": {
                    "from": f"{from_date.isoformat()}T00:00:00Z",
                    "to": f"{to_date.isoformat()}T23:59:59Z",
                },
                "aggregationInterval": {"of": "P1D"},
                "evalscript": evalscript,
            },
        }
        response = await self._request_with_backoff(
            "POST", STATISTICAL_URL, endpoint_label="statistical", json_body=body
        )
        pu = self._extract_pu(response)
        self._record_pu(pu, "statistical")
        return response.json()

    async def process_request(
        self,
        geometry: Dict[str, Any],
        time_range: Tuple[date, date],
        evalscript: str,
        collection: str,
        width: int,
        height: int,
    ) -> bytes:
        """Call the Process API and return raster bytes (PNG/TIFF)."""
        from_date, to_date = time_range
        body = {
            "input": {
                "bounds": {"geometry": geometry},
                "data": [
                    {
                        "type": collection,
                        "dataFilter": {
                            "timeRange": {
                                "from": f"{from_date.isoformat()}T00:00:00Z",
                                "to": f"{to_date.isoformat()}T23:59:59Z",
                            }
                        },
                    }
                ],
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [
                    {"identifier": "default", "format": {"type": "image/tiff"}}
                ],
            },
            "evalscript": evalscript,
        }
        response = await self._request_with_backoff(
            "POST", PROCESS_URL, endpoint_label="process", json_body=body
        )
        pu = self._extract_pu(response)
        self._record_pu(pu, "process")
        return response.content
