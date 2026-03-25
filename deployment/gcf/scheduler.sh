#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-your-gcp-project}"
REGION="${REGION:-us-central1}"
JOB_NAME="kurimasense-proactive-daily"
TARGET_URL="${TARGET_URL:-https://REGION-PROJECT_ID.cloudfunctions.net/kurimasense-proactive}"
SCHEDULE="${SCHEDULE:-0 6 * * *}"

PAYLOAD_FILE="deployment/proactive_targets.json"

gcloud scheduler jobs create http "${JOB_NAME}" \
  --project "${PROJECT_ID}" \
  --location "${REGION}" \
  --schedule "${SCHEDULE}" \
  --http-method POST \
  --uri "${TARGET_URL}" \
  --message-body "$(cat "${PAYLOAD_FILE}")" \
  --headers "Content-Type=application/json"
