#!/bin/bash

# Скрипт развертывания Forge сервисов
# AutoDesk Design Automation Integration для BTI Processor

PROJECT_ID="talkhint"
REGION="europe-west1"

echo "🚀 Начинаем развертывание Forge сервисов..."

# 1. Создание Pub/Sub топиков
echo "📡 Создание Pub/Sub топиков..."
gcloud pubsub topics create bti-jobs-create --project=${PROJECT_ID} || echo "Topic already exists"
gcloud pubsub topics create bti-jobs-done --project=${PROJECT_ID} || echo "Topic already exists"

# 2. Создание подписок
echo "📬 Создание Pub/Sub подписок..."
gcloud pubsub subscriptions create bti-jobs-done-subscription \
    --topic=bti-jobs-done \
    --project=${PROJECT_ID} || echo "Subscription already exists"

# 3. Создание GCS бакетов
echo "🪣 Создание GCS бакетов..."
gsutil mb gs://btibot-processed || echo "Bucket already exists"
gsutil mb gs://bti-templates || echo "Templates bucket already exists"

# 4. Настройка прав доступа
echo "🔐 Настройка прав доступа..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${PROJECT_ID}-compute@developer.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${PROJECT_ID}-compute@developer.gserviceaccount.com" \
    --role="roles/pubsub.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${PROJECT_ID}-compute@developer.gserviceaccount.com" \
    --role="roles/monitoring.metricWriter"

# 5. Сборка и деплой Forge Controller
echo "📦 Сборка образа Forge Controller..."
docker build -f Dockerfile.forge-controller -t gcr.io/${PROJECT_ID}/forge-controller:latest .
docker push gcr.io/${PROJECT_ID}/forge-controller:latest

echo "🚀 Деплой Forge Controller..."
gcloud run deploy forge-controller \
    --image gcr.io/${PROJECT_ID}/forge-controller:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
    --set-secrets=FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest \
    --cpu 1 \
    --memory 1Gi \
    --timeout 300 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 100

# 6. Сборка и деплой Forge Poller
echo "📦 Сборка образа Forge Poller..."
docker build -f Dockerfile.forge-poller -t gcr.io/${PROJECT_ID}/forge-poller:latest .
docker push gcr.io/${PROJECT_ID}/forge-poller:latest

echo "🚀 Деплой Forge Poller..."
gcloud run deploy forge-poller \
    --image gcr.io/${PROJECT_ID}/forge-poller:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
    --set-secrets=FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest \
    --cpu 1 \
    --memory 1Gi \
    --timeout 60 \
    --min-instances 1 \
    --max-instances 3 \
    --concurrency 1

# 7. Настройка Cloud Scheduler для polling
echo "⏰ Настройка Cloud Scheduler..."
gcloud scheduler jobs create http forge-poller-cron \
    --schedule="*/1 * * * *" \
    --uri="https://forge-poller-${PROJECT_ID}.${REGION}.run.app/forge/poll" \
    --http-method=POST \
    --time-zone="Europe/Moscow" \
    --project=${PROJECT_ID} || echo "Scheduler job already exists"

# 8. Создание шаблонов БТИ (базовая структура)
echo "📋 Создание структуры шаблонов БТИ..."
mkdir -p bti-templates-prep/{moscow,mo,default}/{examples,blocks,templates,configs}

# Создаем базовые конфигурации
cat > bti-templates-prep/moscow/configs/layer_map.yaml << 'EOF'
layers_map:
  - match: ["walls", "стены", "wall*"]
    to: "A-WALL"
  - match: ["doors", "двери", "door*"]
    to: "A-DOOR"
  - match: ["windows", "окна", "win*"]
    to: "A-WIND"
  - match: ["dim*", "размер*"]
    to: "A-DIMS"
default: "A-MISC"
EOF

cat > bti-templates-prep/moscow/configs/style.json << 'EOF'
{
  "text_style": {
    "name": "BTI-TXT",
    "font": "gosttypea.shx",
    "height_mm": 2.5
  },
  "dim_style": {
    "name": "BTI-DIM",
    "arrow": "oblique",
    "precision": 0,
    "unit": "mm"
  },
  "line_types": {
    "walls": "0.50",
    "partitions": "0.30",
    "furniture": "0.18"
  },
  "scale_default": "1:100"
}
EOF

cat > bti-templates-prep/templates.json << 'EOF'
{
  "moscow": "gs://bti-templates/moscow",
  "mo": "gs://bti-templates/mo",
  "default": "gs://bti-templates/default"
}
EOF

# Загружаем шаблоны в GCS
echo "📤 Загрузка шаблонов в GCS..."
gsutil -m cp -r bti-templates-prep/* gs://bti-templates/

# 9. Настройка мониторинга
echo "📊 Настройка мониторинга..."
python3 -c "
from forge_monitoring import ForgeAlertManager
alert_manager = ForgeAlertManager('${PROJECT_ID}')
alert_manager.setup_forge_alerts('admin@example.com')
print('✅ Alerts configured')
"

# 10. Тестирование сервисов
echo "🧪 Тестирование сервисов..."

# Тест Forge Controller
FORGE_CONTROLLER_URL="https://forge-controller-${PROJECT_ID}.${REGION}.run.app"
echo "🔍 Тестируем Forge Controller..."
curl -f "${FORGE_CONTROLLER_URL}/health" && echo "✅ Forge Controller: OK" || echo "❌ Forge Controller: FAIL"

# Тест Forge Poller
FORGE_POLLER_URL="https://forge-poller-${PROJECT_ID}.${REGION}.run.app"
echo "🔍 Тестируем Forge Poller..."
curl -f "${FORGE_POLLER_URL}/health" && echo "✅ Forge Poller: OK" || echo "❌ Forge Poller: FAIL"

# 11. Интеграция с Telegram Bot
echo "🤖 Интеграция с Telegram Bot..."

# Обновляем app.py для поддержки Forge
if [ -f "app.py" ]; then
    echo "📝 Обновляем Telegram Bot для поддержки Forge..."
    
    # Создаем backup
    cp app.py app.py.backup
    
    # Добавляем импорт интеграции
    if ! grep -q "telegram_forge_integration" app.py; then
        echo "
# Forge Integration
from telegram_forge_integration import add_forge_integration_to_bot

# Добавляем Forge интеграцию
forge_functions = add_forge_integration_to_bot(app)
forge_notification_handler = forge_functions['forge_notification_handler']
forge_status_command = forge_functions['forge_status_command']
forge_integration = forge_functions['forge_integration']

# Добавляем обработчик команды /forge_status
application.add_handler(CommandHandler('forge_status', forge_status_command))
" >> app.py
    fi
    
    echo "✅ Telegram Bot обновлен для поддержки Forge"
fi

# 12. Финальная информация
echo ""
echo "🎉 Развертывание Forge сервисов завершено!"
echo ""
echo "📋 Информация о сервисах:"
echo "🌐 Forge Controller: ${FORGE_CONTROLLER_URL}"
echo "🌐 Forge Poller: ${FORGE_POLLER_URL}"
echo ""
echo "📊 Мониторинг:"
echo "🔗 Cloud Monitoring: https://console.cloud.google.com/monitoring?project=${PROJECT_ID}"
echo "📈 Логи: https://console.cloud.google.com/logs?project=${PROJECT_ID}"
echo ""
echo "🧪 Для тестирования используйте:"
echo "python3 test_forge_integration.py"
echo ""
echo "📋 Следующие шаги:"
echo "1. Загрузите эталонные БТИ-DWG в gs://bti-templates/examples/"
echo "2. Создайте DWT шаблоны в gs://bti-templates/templates/"
echo "3. Настройте Activity 'btiProcessor.AutoCAD+prod' в Forge"
echo "4. Протестируйте полный workflow"
echo ""
echo "🚀 Система готова к обработке БТИ-чертежей через AutoDesk Design Automation!"
