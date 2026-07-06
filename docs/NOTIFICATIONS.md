# Centralized Notification Service

`services/notifications` is the single hub every subsystem uses to reach a
farmer. Producers emit an event; the service decides **whether** (preferences,
dedupe), **where** (channel adapters) and **when** (quiet hours) to deliver.
No feature embeds its own delivery logic.

```
producer (planner / climatology / irrigation engine / accounts / future AI)
   │  NotificationEvent ──► notify()
   ▼
preference resolution (preferences.py — pure, unit-tested)
   │  channels + quiet-hours deferral
   ▼
notifications row (= the in-app inbox)  +  notification_deliveries rows (email/push/…)
   │
   ▼
dispatch_pending() ──► channel adapters (channels.py) with retry/backoff
```

## Pieces

| File | Responsibility |
| --- | --- |
| `models.py` | Category registry (`CATEGORIES`), channel keys, `NotificationEvent` |
| `preferences.py` | Pure resolution: channel toggles, group opt-outs, quiet hours (critical bypasses) |
| `repository.py` | Persistence; schema self-heals on boot (canonical DDL: `migrations/014_notifications.sql`) |
| `channels.py` | Adapter registry — email (SMTP env), push (token pipeline live, FCM transport pending creds) |
| `service.py` | `notify()` + `dispatch_pending()` + `run_generation_cycle()` |
| `generators.py` | Scheduled rules: task reminders, overdue, weather alerts, dry spells, irrigation, weekly/monthly summaries |
| `scheduler.py` | In-process asyncio loop, advisory-locked (single-flight across replicas) |
| `notification_routes.py` | REST surface: inbox, read, preferences, catalog, devices, admin run-cycle |

## Extending

* **New notification type** → add one `Category` to `CATEGORIES`. Preferences,
  storage, API and channels pick it up automatically.
* **New scheduled rule** → add a function to `generators.REGISTRY`. Use a
  dedupe key so re-runs are idempotent (`notifications` has a unique index on
  `(user_id, dedupe_key)`).
* **New channel** (SMS/WhatsApp/webhooks) → implement an adapter and
  `register_channel()`. Preference documents already carry per-channel toggles.
* **Interactive events** (e.g. account/subscription): call `notify()` inline —
  delivery is immediate when outside quiet hours.

## Scheduling & operations

The scheduler runs every `NOTIFICATIONS_INTERVAL_SECONDS` (default 900s) under
a Postgres transaction-scoped advisory lock, so multiple API instances never
double-send. Generators gate themselves on the user's local clock
(`preferences.timezone`, default `Africa/Harare`) and rely on dedupe keys —
cadence and correctness are decoupled.

Alternative: set `NOTIFICATIONS_SCHEDULER_ENABLED=false` and drive
`POST /notifications/admin/run-cycle` (X-Admin-Token) from external cron; both
paths share `run_generation_cycle()`.

Email env: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`,
`EMAIL_FROM`, optional `FRONTEND_BASE_URL` for deep links. Unconfigured email
⇒ deliveries marked `skipped`, everything else unaffected. Push tokens are
registered by the mobile app via `POST /notifications/devices`; enabling FCM
(`FCM_SERVICE_ACCOUNT_JSON`) is server config, no schema/API change.

## Targeting note

Consumer notifications key off `fields.user_id` / `farm_tasks.user_id`.
Institutional fan-out (notify all tenant officers) plugs into
`generators.py` targeting queries only — the rest of the pipeline is
user-agnostic.
