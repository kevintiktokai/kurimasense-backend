# Cloud Functions Runbook

## Deploy
1. Update `deployment/gcf/env.yaml` with real keys.
2. Run `deployment/gcf/deploy.sh`.

## Configure Scheduler
1. Deploy `kurimasense-proactive` (HTTP) first.
2. Update `TARGET_URL` and run `deployment/gcf/scheduler.sh`.

## Update Targets
- Edit `deployment/proactive_targets.json` and set `PROACTIVE_TARGETS_JSON` env var.

## Rollback
- Redeploy previous revision using `gcloud functions deploy` with the prior source.

## Logs
- Cloud Functions logs in Cloud Logging (`gcloud logging read`).
- Scheduler logs in Cloud Scheduler history.
