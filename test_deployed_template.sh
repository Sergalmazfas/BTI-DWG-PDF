#!/bin/bash
# Быстрый тест задеплоенного сервиса с типовым шаблоном BTI

SERVICE_URL="https://telegram-bti-bot-637190449180.europe-west1.run.app"

echo "🧪 Тест задеплоенного сервиса с типовым шаблоном BTI"
echo ""

# 1. Health Check
echo "1️⃣ Health Check..."
HEALTH=$(curl -s "$SERVICE_URL/health")
echo "   $HEALTH"

if echo "$HEALTH" | grep -q "OK"; then
    echo "   ✅ Сервис работает"
else
    echo "   ❌ Сервис не отвечает"
    exit 1
fi

echo ""

# 2. Process DWG с типовым шаблоном BTI
echo "2️⃣ Тест обработки DWG с типовым шаблоном BTI..."
echo "   (используем сам шаблон как тестовый файл)"

TEST_PAYLOAD=$(cat <<EOF
{
  "file_url": "gs://btibot-processed/templates/bti_basmanny_template.dwg",
  "mode": "bti",
  "chat_id": "test_deploy",
  "job_id": "test_$(date +%s)"
}
EOF
)

echo "   Запрос:"
echo "$TEST_PAYLOAD" | jq '.'

echo ""
echo "   Отправка..."

RESPONSE=$(curl -s -X POST "$SERVICE_URL/process-dwg" \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD")

echo "   Ответ:"
echo "$RESPONSE" | jq '.'

# Проверка результата
if echo "$RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    echo ""
    echo "   ✅ Тест пройден!"
    
    WORKITEM_ID=$(echo "$RESPONSE" | jq -r '.workitem_id')
    RESULT_URL=$(echo "$RESPONSE" | jq -r '.result_url')
    PROCESSING_TIME=$(echo "$RESPONSE" | jq -r '.processing_time')
    
    echo ""
    echo "   📋 Детали:"
    echo "      WorkItem ID: $WORKITEM_ID"
    echo "      Результат: $RESULT_URL"
    echo "      Время: $PROCESSING_TIME сек"
    
else
    echo ""
    echo "   ❌ Тест провален!"
    echo "   Ошибка: $(echo "$RESPONSE" | jq -r '.error // .message')"
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        ✅ Типовой шаблон BTI работает!                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"

