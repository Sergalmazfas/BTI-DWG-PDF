#!/bin/bash
set -e

echo "🚀 Деплой telegram-bti-bot с DWG fallback..."
echo ""

cd /Users/seregaboss/BTI-DWG-PDF-1

gcloud run deploy telegram-bti-bot \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=talkhint,GCS_BUCKET=btibot-processed,AUTO_PDF=false,JOB_TIMEOUT_SEC=900" \
  --set-secrets="FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,BOT_TOKEN=BOT_TOKEN:latest,FORGE_SERVICE_KEY=FORGE_SERVICE_KEY:latest" \
  --cpu=1 \
  --memory=2Gi \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=80

echo ""
echo "✅ Деплой завершён! Новая ревизия будет получать 100% трафика"
echo "🔍 Проверь логи: gcloud logging tail --service=telegram-bti-bot"

