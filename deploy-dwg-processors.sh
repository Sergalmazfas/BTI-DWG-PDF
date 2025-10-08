#!/bin/bash

# Скрипт для деплоя dwg-processor сервисов

echo "🚀 Начинаем деплой dwg-processor сервисов..."

# Настройки
PROJECT_ID="talkhint"
REGION="europe-west1"
DW_PROCESSOR_IMAGE="gcr.io/talkhint/dwg-processor:latest"
DW_PROCESSOR_METADATA_IMAGE="gcr.io/talkhint/dwg-processor-metadata:latest"

echo "📦 Сборка образа dwg-processor..."
docker build -f Dockerfile.dwg-processor -t $DW_PROCESSOR_IMAGE .

echo "📦 Сборка образа dwg-processor-metadata..."
docker build -f Dockerfile.dwg-processor-metadata -t $DW_PROCESSOR_METADATA_IMAGE .

echo "⬆️ Отправка образа dwg-processor в GCR..."
docker push $DW_PROCESSOR_IMAGE

echo "⬆️ Отправка образа dwg-processor-metadata в GCR..."
docker push $DW_PROCESSOR_METADATA_IMAGE

echo "🚀 Деплой dwg-processor..."
gcloud run deploy dwg-processor \
  --image $DW_PROCESSOR_IMAGE \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --timeout 900 \
  --memory 2Gi \
  --cpu 2 \
  --set-secrets="FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,TELEGRAM_BOT_TOKEN=BOT_TOKEN:latest" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GCS_BUCKET=btibot-processed"

echo "🚀 Деплой dwg-processor-metadata..."
gcloud run deploy dwg-processor-metadata \
  --image $DW_PROCESSOR_METADATA_IMAGE \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --timeout 900 \
  --memory 2Gi \
  --cpu 2 \
  --set-secrets="FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,TELEGRAM_BOT_TOKEN=BOT_TOKEN:latest" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GCS_BUCKET=btibot-processed"

echo "✅ Деплой завершен!"
echo "🌐 dwg-processor: https://dwg-processor-637190449180.europe-west1.run.app"
echo "🌐 dwg-processor-metadata: https://dwg-processor-metadata-637190449180.europe-west1.run.app"
