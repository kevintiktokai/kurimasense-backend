"""
Notification API — the frontend/mobile surface of the centralized notification
service (services/notifications).

  GET    /notifications                    inbox (paginated) + unread count
  POST   /notifications/{id}/read          mark one read
  POST   /notifications/read-all           mark everything read
  GET    /notifications/preferences        effective preference document
  PUT    /notifications/preferences        update preferences (partial ok)
  GET    /notifications/catalog            category/channel registry (drives the settings UI)
  POST   /notifications/devices            register a push token (mobile app)
  DELETE /notifications/devices/{token}    unregister a push token
  POST   /notifications/admin/run-cycle    run generators+dispatch now (X-Admin-Token;
                                           also the hook for external cron)
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from auth_roles import require_admin_token
from deps import verify_token
from services.notifications import CATEGORIES, CATEGORY_GROUPS, IMPLEMENTED_CHANNELS
from services.notifications import repository
from services.notifications.preferences import DEFAULT_PREFERENCES, merged_preferences
from services.notifications.scheduler import run_cycle_with_lock

router = APIRouter(tags=["notifications"])


@router.get("/notifications")
async def get_notifications(
    limit: int = Query(default=30, ge=1, le=100),
    unread_only: bool = Query(default=False),
    before: Optional[str] = Query(default=None, description="ISO timestamp cursor"),
    user_id: str = Depends(verify_token),
):
    items = await run_in_threadpool(
        repository.list_notifications, user_id, limit, unread_only, before
    )
    unread = await run_in_threadpool(repository.unread_count, user_id)
    return {"notifications": items, "unread_count": unread}


@router.post("/notifications/{notification_id}/read")
async def read_notification(notification_id: str, user_id: str = Depends(verify_token)):
    ok = await run_in_threadpool(repository.mark_read, user_id, notification_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "ok"}


@router.post("/notifications/read-all")
async def read_all_notifications(user_id: str = Depends(verify_token)):
    updated = await run_in_threadpool(repository.mark_all_read, user_id)
    return {"status": "ok", "updated": updated}


# ── preferences ──────────────────────────────────────────────────────────────

@router.get("/notifications/preferences")
async def get_preferences(user_id: str = Depends(verify_token)):
    stored = await run_in_threadpool(repository.get_preferences_row, user_id)
    return {"preferences": merged_preferences(stored), "defaults": DEFAULT_PREFERENCES}


@router.put("/notifications/preferences")
async def put_preferences(
    body: Dict[str, Any] = Body(...),
    user_id: str = Depends(verify_token),
):
    """Merge the submitted (possibly partial) document over what is stored, so
    clients can PUT just the section they changed."""
    stored = await run_in_threadpool(repository.get_preferences_row, user_id)
    current = merged_preferences(stored)
    for key, value in (body or {}).items():
        if key not in DEFAULT_PREFERENCES:
            continue  # ignore unknown top-level keys defensively
        if isinstance(value, dict) and isinstance(current.get(key), dict):
            current[key].update(value)
        else:
            current[key] = value
    ok = await run_in_threadpool(repository.upsert_preferences, user_id, current)
    if not ok:
        raise HTTPException(status_code=500, detail="Could not save preferences")
    return {"preferences": current}


@router.get("/notifications/catalog")
async def get_catalog():
    """Static registry of categories/groups/channels — lets the settings UI
    render toggles without hardcoding the taxonomy."""
    return {
        "groups": CATEGORY_GROUPS,
        "channels": IMPLEMENTED_CHANNELS,
        "categories": [asdict(c) for c in CATEGORIES.values()],
    }


# ── push device registration ─────────────────────────────────────────────────

class DeviceRegistration(BaseModel):
    token: str = Field(min_length=8, max_length=4096)
    platform: str = Field(default="android", pattern="^(android|ios|web)$")


@router.post("/notifications/devices", status_code=201)
async def register_device(body: DeviceRegistration, user_id: str = Depends(verify_token)):
    ok = await run_in_threadpool(repository.register_device, user_id, body.platform, body.token)
    if not ok:
        raise HTTPException(status_code=500, detail="Could not register device")
    return {"status": "registered"}


@router.delete("/notifications/devices/{token}", status_code=204)
async def unregister_device(token: str, user_id: str = Depends(verify_token)):
    await run_in_threadpool(repository.delete_device, user_id, token)
    return None


# ── ops ──────────────────────────────────────────────────────────────────────

@router.post("/notifications/admin/run-cycle")
async def admin_run_cycle(_: None = Depends(require_admin_token)):
    """Run one generation+dispatch cycle immediately. Safe to call from cron —
    dedupe keys make repeated runs idempotent, and the advisory lock serializes
    it against the in-process scheduler."""
    stats = await run_in_threadpool(run_cycle_with_lock)
    return {"status": "ok", "stats": stats}
