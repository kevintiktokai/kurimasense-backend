"""
Admin endpoints for managing institutional API keys.

All routes here require X-Admin-Token (validated against the
ADMIN_API_TOKEN env var by services.auth.require_admin). Issued raw keys
are returned only on POST and never reproducible afterwards.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status

from schemas import (
    ApiKeyMetadata,
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    ListApiKeysResponse,
    RevokeApiKeyResponse,
)
from services.auth import (
    generate_api_key,
    list_api_keys,
    require_admin,
    revoke_api_key,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"], dependencies=[Depends(require_admin)])


def _override_blob(req: CreateApiKeyRequest) -> Optional[Dict[str, int]]:
    blob: Dict[str, int] = {}
    if req.rate_limit_per_minute is not None:
        blob["per_minute"] = req.rate_limit_per_minute
    if req.rate_limit_per_day is not None:
        blob["per_day"] = req.rate_limit_per_day
    return blob or None


def _to_metadata(row: Dict[str, Any]) -> ApiKeyMetadata:
    def _iso(v: Any) -> Optional[str]:
        return v.isoformat() if hasattr(v, "isoformat") else (v if v is None else str(v))

    return ApiKeyMetadata(
        id=row["id"],
        tenant_id=row["tenant_id"],
        name=row["name"],
        created_at=_iso(row.get("created_at")),
        expires_at=_iso(row.get("expires_at")),
        last_used_at=_iso(row.get("last_used_at")),
        is_active=bool(row.get("is_active")),
        rate_limit_override=row.get("rate_limit_override"),
        key_id_hex=row.get("key_id_hex"),
    )


@router.post(
    "/admin/tenants/{tenant_id}/api_keys",
    response_model=CreateApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_api_key(
    body: CreateApiKeyRequest,
    tenant_id: str = Path(...),
) -> CreateApiKeyResponse:
    """Mint a new API key for a tenant. Raw key is shown ONCE."""
    override = _override_blob(body)
    raw_key, key_id = generate_api_key(
        tenant_id=tenant_id,
        name=body.name,
        expires_days=body.expires_days,
        rate_limit_override=override,
    )
    expires_at_str: Optional[str] = None
    if body.expires_days:
        from datetime import datetime, timedelta, timezone
        expires_at = datetime.now(timezone.utc) + timedelta(days=body.expires_days)
        expires_at_str = expires_at.isoformat()
    return CreateApiKeyResponse(
        key_id=key_id,
        tenant_id=tenant_id,
        name=body.name,
        raw_key=raw_key,
        expires_at=expires_at_str,
    )


@router.get(
    "/admin/tenants/{tenant_id}/api_keys",
    response_model=ListApiKeysResponse,
)
def list_tenant_api_keys(
    tenant_id: str = Path(...),
) -> ListApiKeysResponse:
    rows = list_api_keys(tenant_id)
    return ListApiKeysResponse(
        tenant_id=tenant_id,
        keys=[_to_metadata(r) for r in rows],
    )


@router.delete(
    "/admin/api_keys/{key_id}",
    response_model=RevokeApiKeyResponse,
)
def delete_api_key(
    key_id: str = Path(...),
) -> RevokeApiKeyResponse:
    revoked = revoke_api_key(key_id)
    if not revoked:
        raise HTTPException(404, "API key not found")
    return RevokeApiKeyResponse(key_id=key_id, revoked=True)
