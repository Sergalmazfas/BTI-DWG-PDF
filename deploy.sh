#!/bin/bash

# Deploy BTI DWG → PDF Converter to Cloud Run
# Скрипт для деплоя bti-dwg-pdf сервиса

set -e

echo "🚀 Deploying BTI DWG → PDF Converter to Cloud Run"
echo "=================================================="

# Переменные
PROJECT_ID="talkhint"  # Замените на ваш проект
SERVICE_NAME="bti-dwg-pdf"
REGION="europe-west1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "📦 Building Docker image..."
docker build -t ${IMAGE_NAME} .

echo "📤 Pushing to Google Container Registry..."
docker push ${IMAGE_NAME}

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --timeout 900 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --min-instances 0 \
  --concurrency 1 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GCS_BUCKET=btibot-processed" \
  --set-secrets="BOT_TOKEN=BOT_TOKEN:latest" \
  --service-account="bti-dwg-pdf-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "✅ BTI DWG → PDF Converter deployed successfully!"
echo "🔗 Service URL: https://${SERVICE_NAME}-${PROJECT_ID}.${REGION}.run.app"

echo ""
echo "📋 Next steps:"
echo "1. Set up Telegram webhook: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://${SERVICE_NAME}-${PROJECT_ID}.${REGION}.run.app/"
echo "2. Test file processing: curl -X POST -F 'file=@test.dwg' https://${SERVICE_NAME}-${PROJECT_ID}.${REGION}.run.app/upload"
echo "3. Monitor logs: gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}' --limit=10"
