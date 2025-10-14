#!/bin/bash
# Деплой telegram-bti-bot с типовым шаблоном BTI

echo "🚀 Деплой telegram-bti-bot с типовым шаблоном BTI"
echo ""

# Проверка что мы в правильной директории
if [ ! -f "app.py" ]; then
    echo "❌ Ошибка: app.py не найден. Запустите из корня проекта."
    exit 1
fi

echo "📋 Конфигурация:"
echo "   - Region: europe-west1"
echo "   - Mode: DWG-first (AUTO_PDF=false)"
echo "   - Template: ВКЛЮЧЕН (USE_BTI_TEMPLATE=true)"
echo "   - Activity: BotBti.BTI_INSERT_Basman+v1"
echo ""

echo "🔧 Запуск деплоя..."
echo ""

gcloud run deploy telegram-bti-bot \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=talkhint,GCS_BUCKET=btibot-processed,AUTO_PDF=false,JOB_TIMEOUT_SEC=900,USE_BTI_TEMPLATE=true" \
  --set-secrets="FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,BOT_TOKEN=BOT_TOKEN:latest,FORGE_SERVICE_KEY=FORGE_SERVICE_KEY:latest" \
  --cpu=1 \
  --memory=2Gi \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=80

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Деплой успешно завершен!"
    echo ""
    echo "🔍 Проверка сервиса..."
    
    SERVICE_URL="https://telegram-bti-bot-637190449180.europe-west1.run.app"
    
    echo "   Health: $SERVICE_URL/health"
    curl -s "$SERVICE_URL/health" | jq '.'
    
    echo ""
    echo "📊 Переменные окружения:"
    echo "   ✅ USE_BTI_TEMPLATE=true"
    echo "   ✅ AUTO_PDF=false"
    echo "   ✅ GOOGLE_CLOUD_PROJECT=talkhint"
    echo ""
    echo "🏛️ Типовой шаблон BTI:"
    echo "   URL: https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg"
    echo "   Activity: BotBti.BTI_INSERT_Basman+v1"
    echo ""
    echo "📝 Для проверки логов:"
    echo "   gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=telegram-bti-bot AND textPayload:типовым\" --limit=10"
    echo ""
    echo "🎉 Готово! Типовой шаблон BTI активирован!"
else
    echo ""
    echo "❌ Ошибка при деплое"
    exit 1
fi

