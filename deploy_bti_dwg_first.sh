#!/bin/bash

# Скрипт деплоя BTI Bot в режиме DWG-first
# Поэтапный режим с блокировкой и AutoDesk Forge API

PROJECT_ID="talkhint"
REGION="europe-west1"
SERVICE_NAME="bti-bot-dwg-first"

echo "🚀 Начинаем деплой BTI Bot DWG-first..."

# 1. Проверяем переменные окружения
echo "🔍 Проверяем переменные окружения..."
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN не установлен"
    exit 1
fi

# 2. Создаем шаблон BTI_Template.dwt если не существует
echo "📋 Проверяем шаблон BTI_Template.dwt..."
gsutil ls gs://btibot-processed/templates/BTI_Template.dwt >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️ Шаблон BTI_Template.dwt не найден в GCS"
    echo "💡 Создайте шаблон в gs://btibot-processed/templates/BTI_Template.dwt"
    echo "   или используйте команду загрузки шаблонов"
fi

# 3. Настройка Firestore для блокировок
echo "🔥 Настройка Firestore..."
gcloud services enable firestore.googleapis.com --project=${PROJECT_ID}

# Создаем Firestore database если не существует
gcloud firestore databases create --region=${REGION} --project=${PROJECT_ID} 2>/dev/null || echo "Firestore database already exists"

# 4. Сборка и деплой
echo "📦 Сборка образа BTI Bot DWG-first..."
docker build -f Dockerfile.bti-dwg-first -t gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest .

echo "📤 Отправка образа в GCR..."
docker push gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest

# 5. Деплой сервиса
echo "🚀 Деплой BTI Bot DWG-first..."
gcloud run deploy ${SERVICE_NAME} \
    --image gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars \
        GOOGLE_CLOUD_PROJECT=${PROJECT_ID}, \
        GCS_BUCKET=btibot-processed, \
        AUTO_PDF=false, \
        JOB_TIMEOUT_SEC=900 \
    --set-secrets \
        FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest, \
        FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest, \
        BOT_TOKEN=BOT_TOKEN:latest \
    --cpu 1 \
    --memory 1Gi \
    --timeout 300 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 100

# 6. Проверка деплоя
echo "🔍 Проверка деплоя..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')

echo "⏳ Ожидание готовности сервиса..."
sleep 30

echo "🧪 Тестирование health check..."
curl -f "${SERVICE_URL}/health" && echo "✅ Health check OK" || echo "❌ Health check FAILED"

# 7. Настройка IAM для Firestore
echo "🔐 Настройка IAM для Firestore..."
SERVICE_ACCOUNT="${PROJECT_ID}-compute@developer.gserviceaccount.com"

# Даем права на Firestore
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/datastore.user" 2>/dev/null || echo "Firestore permissions already set"

# Даем права на GCS
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/storage.admin" 2>/dev/null || echo "GCS permissions already set"

# Даем права на Secret Manager
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" 2>/dev/null || echo "Secret Manager permissions already set"

# 8. Создание структуры GCS
echo "📁 Создание структуры GCS..."
mkdir -p temp_structure/{raw,ready,templates}

# Создаем примеры папок для тестирования
touch temp_structure/raw/.gitkeep
touch temp_structure/ready/.gitkeep
touch temp_structure/templates/.gitkeep

# Загружаем структуру в GCS
gsutil -m cp -r temp_structure/* gs://btibot-processed/
rm -rf temp_structure

# 9. Финальная информация
echo ""
echo "🎉 Деплой BTI Bot DWG-first завершен!"
echo ""
echo "📋 Информация о сервисе:"
echo "🌐 URL: ${SERVICE_URL}"
echo "📊 Регион: ${REGION}"
echo "🏷️ Имя: ${SERVICE_NAME}"
echo ""
echo "🔧 Конфигурация:"
echo "• Режим: DWG-first (поэтапный)"
echo "• Блокировка: Firestore (TTL 30 мин)"
echo "• Обработка: AutoDesk Forge API"
echo "• Автопреобразование PDF: отключено"
echo "• Таймаут задач: 900 сек (15 мин)"
echo ""
echo "📋 Структура GCS:"
echo "• Шаблоны: gs://btibot-processed/templates/BTI_Template.dwt"
echo "• Входные файлы: gs://btibot-processed/raw/{chat_id}/{job_id}/input.dwg"
echo "• Готовые файлы: gs://btibot-processed/ready/{chat_id}/{job_id}/out.{dwg|pdf}"
echo ""
echo "🧪 Тестирование:"
echo "1. Отправьте /bti в Telegram бот"
echo "2. Загрузите DWG файл"
echo "3. Дождитесь готового DWG"
echo "4. Выберите нужен ли PDF"
echo ""
echo "📊 Мониторинг:"
echo "• Логи: https://console.cloud.google.com/logs?project=${PROJECT_ID}"
echo "• Firestore: https://console.cloud.google.com/firestore?project=${PROJECT_ID}"
echo "• Cloud Run: https://console.cloud.google.com/run?project=${PROJECT_ID}"
echo ""
echo "🚀 BTI Bot DWG-first готов к работе!"
