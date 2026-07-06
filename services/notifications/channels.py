"""
Delivery channel adapters.

Each outbound channel implements ``send(payload) -> ChannelResult`` and is
registered in ``CHANNEL_ADAPTERS``. The dispatcher (service.dispatch_pending)
is channel-agnostic: adding SMS/WhatsApp later is one new adapter + one
registry entry — no changes to storage, preferences, or the dispatch loop.

* **in_app** has no adapter: the ``notifications`` row *is* the delivery.
* **email** sends via SMTP configured from env (``SMTP_HOST``, ``SMTP_PORT``,
  ``SMTP_USER``, ``SMTP_PASSWORD``, ``EMAIL_FROM``). Unconfigured → 'skipped',
  never an error, so environments without email stay healthy.
* **push** looks up the user's registered device tokens; actual FCM/APNs wiring
  lands with mobile release credentials (``FCM_SERVICE_ACCOUNT_JSON``) — until
  then it reports 'skipped' with a clear reason. The mobile app already
  registers tokens, so enabling push is server-config only.
"""

from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Callable, Dict, Optional

from . import repository

APP_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "https://kurima-sense.vercel.app")


@dataclass
class ChannelResult:
    status: str                 # sent | skipped | failed
    error: Optional[str] = None
    retriable: bool = False


# ── email ────────────────────────────────────────────────────────────────────

def _smtp_config() -> Optional[Dict[str, Any]]:
    host = os.environ.get("SMTP_HOST")
    if not host:
        return None
    return {
        "host": host,
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER"),
        "password": os.environ.get("SMTP_PASSWORD"),
        "sender": os.environ.get("EMAIL_FROM", "KurimaSense <no-reply@kurimasense.com>"),
        "use_tls": os.environ.get("SMTP_STARTTLS", "true").strip().lower() in ("1", "true", "yes"),
    }


def _render_email(payload: Dict[str, Any]) -> MIMEMultipart:
    severity = payload.get("severity", "info")
    color = {"critical": "#C0392B", "warning": "#B7791F"}.get(severity, "#2F6B3C")
    action_url = payload.get("action_url")
    link = f"{APP_BASE_URL}{action_url}" if action_url and action_url.startswith("/") else action_url

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"KurimaSense: {payload.get('title', 'Notification')}"

    text = payload.get("body", "")
    if link:
        text += f"\n\nOpen KurimaSense: {link}"
    msg.attach(MIMEText(text, "plain", "utf-8"))

    button = (
        f'<p style="margin-top:16px"><a href="{link}" '
        f'style="background:{color};color:#fff;padding:10px 18px;border-radius:8px;'
        f'text-decoration:none">Open KurimaSense</a></p>'
    ) if link else ""
    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:auto">
      <h2 style="color:{color};margin-bottom:4px">{payload.get('title', '')}</h2>
      <p style="color:#333;font-size:15px;line-height:1.5;white-space:pre-line">{payload.get('body', '')}</p>
      {button}
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0 8px"/>
      <p style="color:#999;font-size:12px">You receive this because of your KurimaSense
      notification settings. Manage them under Settings → Notifications.</p>
    </div>
    """
    msg.attach(MIMEText(html, "html", "utf-8"))
    return msg


def send_email(payload: Dict[str, Any]) -> ChannelResult:
    config = _smtp_config()
    if not config:
        return ChannelResult(status="skipped", error="SMTP not configured")

    recipient = repository.get_user_email(payload["user_id"])
    if not recipient:
        return ChannelResult(status="skipped", error="no email address for user")

    msg = _render_email(payload)
    msg["From"] = config["sender"]
    msg["To"] = recipient
    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=15) as smtp:
            if config["use_tls"]:
                smtp.starttls()
            if config["user"] and config["password"]:
                smtp.login(config["user"], config["password"])
            smtp.sendmail(config["sender"], [recipient], msg.as_string())
        return ChannelResult(status="sent")
    except Exception as e:
        return ChannelResult(status="failed", error=str(e)[:400], retriable=True)


# ── push (mobile) ────────────────────────────────────────────────────────────

def send_push(payload: Dict[str, Any]) -> ChannelResult:
    tokens = repository.list_devices(payload["user_id"])
    if not tokens:
        return ChannelResult(status="skipped", error="no registered devices")
    if not os.environ.get("FCM_SERVICE_ACCOUNT_JSON"):
        # Token pipeline is live (mobile app registers devices); transport ships
        # with store credentials. Skipping keeps deliveries observable.
        return ChannelResult(status="skipped", error="FCM not configured")
    # FCM HTTP v1 integration point — implemented when credentials exist.
    return ChannelResult(status="skipped", error="FCM transport not yet enabled")


# ── registry ─────────────────────────────────────────────────────────────────

CHANNEL_ADAPTERS: Dict[str, Callable[[Dict[str, Any]], ChannelResult]] = {
    "email": send_email,
    "push": send_push,
}


def register_channel(key: str, adapter: Callable[[Dict[str, Any]], ChannelResult]) -> None:
    """Extension hook for future channels (SMS, WhatsApp, webhooks…)."""
    CHANNEL_ADAPTERS[key] = adapter
