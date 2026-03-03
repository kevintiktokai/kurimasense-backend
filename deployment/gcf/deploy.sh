#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-your-gcp-project}"
REGION="${REGION:-us-central1}"
RUNTIME="python311"

ENV_VARS="OPENAI_API_KEY,WEATHER_API_KEY,SATELLITE_API_CLIENT_ID,SATELLITE_API_CLIENT_SECRET,PROACTIVE_TARGETS_JSON,AGRONOMY_KB_PATH,OPENAI_TTS_MODEL,OPENAI_TTS_VOICE"

gcloud functions deploy kurimasense-router \
  --gen2 \
  --region "${REGION}" \
  --runtime "${RUNTIME}" \
  --source . \
  --entry-point router_http \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars-file deployment/gcf/env.yaml \
  --set-env-vars "LOG_LEVEL=INFO,ENVIRONMENT=production"

gcloud functions deploy kurimasense-proactive \
  --gen2 \
  --region "${REGION}" \
  --runtime "${RUNTIME}" \
  --source . \
  --entry-point proactive_http \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars-file deployment/gcf/env.yaml \
  --set-env-vars "LOG_LEVEL=INFO,ENVIRONMENT=production"

gcloud functions deploy kurimasense-proactive-cron \
  --gen2 \
  --region "${REGION}" \
  --runtime "${RUNTIME}" \
  --source . \
  --entry-point proactive_cron \
  --trigger-topic kurimasense-proactive-cron \
  --set-env-vars-file deployment/gcf/env.yaml \
  --set-env-vars "LOG_LEVEL=INFO,ENVIRONMENT=production"
