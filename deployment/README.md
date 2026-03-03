# Deployment (AWS Lambda + EventBridge)

## Overview
This folder contains serverless artifacts for deploying KurimaSense AI to Google Cloud Functions (2nd gen) and scheduling proactive alerts with Cloud Scheduler. AWS Lambda artifacts are retained for reference.

## Files
- `gcf/main.py`: Google Cloud Functions handlers
- `gcf/requirements.txt`: Cloud Functions dependencies
- `gcf/deploy.sh`: gcloud deploy script
- `gcf/scheduler.sh`: Cloud Scheduler setup script
- `gcf/env.yaml`: Environment variable template
- `gcf/RUNBOOK.md`: Operations runbook
- `template.yaml`: AWS SAM template for Lambda + schedule (legacy)
- `lambda_handler.py`: HTTP + scheduled handlers (legacy)
- `eventbridge_daily.json`: Sample schedule rule payload (legacy)

## Environment Variables
- `OPENAI_API_KEY`
- `WEATHER_API_KEY`
- `SATELLITE_API_CLIENT_ID`
- `SATELLITE_API_CLIENT_SECRET`
- `PROACTIVE_TARGETS_JSON` (JSON array of Seed objects, see `deployment/proactive_targets.json`)

## Notes
- `PROACTIVE_TARGETS_JSON` should contain a list of Seed objects that will be checked on schedule.
- Use `.tmp/` for any intermediate artifacts generated in Cloud Functions.
