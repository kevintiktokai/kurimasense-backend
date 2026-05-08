# KurimaSense Deployment Guide 🚀

Follow these steps to deploy the KurimaSense platform. Each part of the system is hosted separately to ensure maximum performance and scalability.

## 1. Frontend: Vercel Setup
**Repository**: [kevintiktokai/kurima-sense](https://github.com/kevintiktokai/kurima-sense)

### Configuration
- **Framework Preset**: Next.js
- **Root Directory**: `./` (The repo root)
- **Build Command**: `npm run build`
- **Output Directory**: `.next`

### Environment Variables
Click on "Settings" > "Environment Variables" and add:
- `NEXT_PUBLIC_API_URL`: The URL of your Render backend (e.g., `https://kurimasense-backend.onrender.com`)
- `NEXT_PUBLIC_MAPBOX_TOKEN`: (Optional) If you use Mapbox for high-res sat view.

---

## 2. Backend: Render Setup
**Repository**: [kevintiktokai/kurimasense-backend](https://github.com/kevintiktokai/kurimasense-backend)

### Configuration
1. Create a "Web Service" on Render.
2. **Runtime**: Python 3
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`

### Environment Variables
Add these in the "Environment" tab:
- `OPENAI_API_KEY`: Your OpenAI API Key for the Agronomist engine.
- `DATABASE_URL`: **IMPORTANT: Use the IPv4 Pooler URL**
  > [!WARNING]
  > Render does not support IPv6. In Supabase Settings > Database, look for the **Connection Pooling** section and use the **Pooler** URL (usually port 6543 or with a hostname like `pooler.supabase.com`). 
  > DO NOT use the "Direct Connection" URL (`db.xxxx.supabase.co`) as it will result in a "Network is unreachable" error.
- `CORS_ORIGINS`: Your Vercel frontend URL (e.g., `https://kurima-sense.vercel.app`)

---

## 3. Database: Supabase
Ensure your Postgres database is running and the `init_knowledge_base.sql` has been run. 

### Troubleshooting the "Network is unreachable" Error
If you see this error in Render logs, it means your `DATABASE_URL` is pointing to an IPv6 address.
1. Go to Supabase > Settings > Database.
2. Under **Connection Pooler**, toggle it to **Enabled**.
3. Copy the **Transaction Mode** connection string.
4. Update the `DATABASE_URL` on Render.

---

## ✅ Deployment Checklist
> [!IMPORTANT]
> - Ensure `NEXT_PUBLIC_API_URL` on Vercel matches your Render URL.
> - Ensure `CORS_ORIGINS` on Render includes your Vercel URL.
> - Verify that the OpenAI API key is active.

### Root Directory Clarification
For Vercel, since the repository `kurima-sense` was created directly from the `frontend` folder, you do **not** need to change the root directory setting. It should remain as **`./`**.

---

## 4. Daily Satellite Ingestion Worker

The daily worker (`workers/daily_ingestion.py`) pulls Sentinel Hub statistics for every active field once per day. It is idempotent: a missed run is recovered on the next invocation, and re-running mid-day is a no-op for fields whose last successful ingestion is < 12 hours old.

### Required environment variables

| Variable | Required | Notes |
|----------|----------|-------|
| `DATABASE_URL` | yes | Same Supabase pooler URL the API uses. |
| `SATELLITE_API_CLIENT_ID` | yes | Sentinel Hub OAuth2 client id. (Legacy name `SH_CLIENT_ID` also accepted.) |
| `SATELLITE_API_CLIENT_SECRET` | yes | Sentinel Hub OAuth2 client secret. (Legacy name `SH_CLIENT_SECRET` also accepted.) |
| `SATELLITE_API_MONTHLY_PU_QUOTA` | no | Defaults to `30000`. Worker raises `SentinelHubQuotaError` once usage exceeds 80 %. (Legacy name `SH_MONTHLY_PU_QUOTA` also accepted.) |
| `GEE_SERVICE_ACCOUNT_KEY` | optional | Path to a service-account JSON. Only needed for the on-demand backfill (`workers/backfill_ingestion.py`); not used by the daily worker. |

### Option A — Cron (in-container)

The repo's `Dockerfile` already installs `cron`, copies `deployment/cron/daily_ingestion.cron` to `/etc/cron.d/kurima_daily_ingestion`, and creates `/var/log/kurima_ingestion.log`. The crontab runs `python /app/workers/daily_ingestion.py` at **03:00 UTC** every day.

To run cron alongside uvicorn in a single container, override the entrypoint at `docker run` time:

```bash
docker run -d --name kurima \
  --env-file .env \
  -p 8000:8000 \
  kurimasense-backend \
  bash -c "cron && uvicorn app:app --host 0.0.0.0 --port 8000"
```

For platform-managed deployments (Render, Fly, Railway, etc.) the in-container cron daemon is usually ignored — instead, configure a platform-native scheduled job that runs `python /app/workers/daily_ingestion.py` on the same `0 3 * * *` schedule.

### Option B — systemd timer (bare-metal / VM)

For deployments running directly on a Linux host, use the systemd unit + timer in `deployment/systemd/`:

```bash
sudo cp deployment/systemd/kurima-ingestion.service /etc/systemd/system/
sudo cp deployment/systemd/kurima-ingestion.timer   /etc/systemd/system/

# Service env file (chmod 600 to protect SATELLITE_API_CLIENT_SECRET)
sudo install -m 600 /dev/null /etc/default/kurima-ingestion
sudo tee /etc/default/kurima-ingestion >/dev/null <<'EOF'
DATABASE_URL=postgres://...
SATELLITE_API_CLIENT_ID=...
SATELLITE_API_CLIENT_SECRET=...
SATELLITE_API_MONTHLY_PU_QUOTA=30000
EOF

sudo useradd --system --no-create-home --shell /usr/sbin/nologin kurima || true
sudo systemctl daemon-reload
sudo systemctl enable --now kurima-ingestion.timer
```

Verify:

```bash
sudo systemctl list-timers kurima-ingestion.timer
sudo systemctl status kurima-ingestion.service        # last invocation
sudo journalctl -u kurima-ingestion.service -n 100    # last 100 log lines
```

### Manual one-off trigger

For testing or to backfill a missed run:

```bash
# Single field (verify config end-to-end without spending PU on every field)
python workers/daily_ingestion.py --field-id <UUID> --dry-run
python workers/daily_ingestion.py --field-id <UUID>

# Reduced batch size, full dry run
python workers/daily_ingestion.py --batch-size 10 --dry-run
```

The worker emits one JSON log line per event; pipe through `jq` for readability:

```bash
python workers/daily_ingestion.py --dry-run | jq .
```

### Logs and rotation

| Path | Source |
|------|--------|
| `/var/log/kurima_ingestion.log` | Cron and systemd both append here. |
| `journalctl -u kurima-ingestion.service` | systemd journal mirror. |

Set up logrotate (recommended for cron deployments):

```bash
sudo tee /etc/logrotate.d/kurima-ingestion >/dev/null <<'EOF'
/var/log/kurima_ingestion.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    create 0640 kurima kurima
    sharedscripts
}
EOF
```

### Verifying the worker is actually running

The API exposes `GET /health/ingestion` which reads `daily_logs` and reports:

```json
{
  "last_run_at": "2026-05-08T03:02:14+00:00",
  "fresh": true,
  "freshness_window_hours": 36,
  "rows_last_24h": 12345,
  "fields_with_data_24h": 217,
  "rejected_observations_24h": 31,
  "status": "ok",
  "checked_at": "2026-05-08T18:00:00+00:00"
}
```

`status` is one of:

- `ok` — newest `daily_logs` row is within the freshness window (36 h)
- `stale` — there are rows but the newest is older than the window
- `unknown` — no rows at all

Wire this endpoint into your uptime monitor (Pingdom, Better Uptime, etc.) and alert on `status != "ok"` or `rows_last_24h == 0`.
