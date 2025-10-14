#!/bin/bash
# Test script for POINT solution
# Тестирует новое решение с POINT командами вместо INSERT

echo "🧪 Тестирование POINT решения для BTI обработки"
echo "============================================="

# Устанавливаем переменные
SERVICE_URL="https://telegram-bot-commands-637190449180.europe-west1.run.app"
TEST_FILE_URL="gs://btibot-processed/raw/1759861119/basmannyi_novyi_obmernyi.dwg"

echo ""
echo "🔧 Конфигурация теста:"
echo "Service: $SERVICE_URL"
echo "Test file: $TEST_FILE_URL"
echo "Mode: point (POINT команды вместо INSERT)"

echo ""
echo "1. 🏥 Проверка health endpoint..."
curl -f "$SERVICE_URL/health" || {
    echo "❌ Service не доступен"
    exit 1
}
echo "✅ Service работает"

echo ""
echo "2. 📊 Проверка статуса сервиса..."
curl -s "$SERVICE_URL/status" | jq .version

echo ""
echo "3. 🚀 Запуск обработки с POINT режимом..."

# Создаем JSON payload для тестирования
TEST_PAYLOAD='{
  "file_url": "'"$TEST_FILE_URL"'",
  "mode": "point",
  "chat_id": "test_point_solution",
  "job_id": "point_test_'$(date +%s)'"
}'

echo "📋 Payload:"
echo "$TEST_PAYLOAD" | jq .

echo ""
echo "📤 Отправка запроса..."

# Отправляем запрос
RESPONSE=$(curl -X POST "$SERVICE_URL/process-dwg" \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD" \
  -w "%{http_code}")

HTTP_CODE="${RESPONSE: -3}"
BODY="${RESPONSE%???}"

echo ""
echo "📨 Ответ сервиса:"
echo "HTTP Code: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Запрос успешен!"
    echo "$BODY" | jq .
    
    # Извлекаем workitem_id для мониторинга
    WORKITEM_ID=$(echo "$BODY" | jq -r .workitem_id 2>/dev/null)
    
    if [ "$WORKITEM_ID" != "null" ] && [ "$WORKITEM_ID" != "" ]; then
        echo ""
        echo "🔍 WorkItem ID: $WORKITEM_ID"
        echo "⏳ Мониторинг обработки..."
        
        # Простой мониторинг (показываем, что нужно отслеживать)
        echo "💡 Для отслеживания используйте:"
        echo "   curl '$SERVICE_URL/queue-status' | jq"
        echo "   или проверяйте логи APS в консоли Autodesk"
    fi
else
    echo "❌ Ошибка запроса!"
    echo "$BODY"
fi

echo ""
echo "🎯 Тест завершен!"
echo ""
echo "📋 Что проверить:"
echo "1. WorkItem создался с activityId: BotBti.BTI_AUTO_PROCESS+v1"
echo "2. Обработка проходит без ошибок INSERT команд"
echo "3. Результат содержит POINT метки вместо блоков"
echo "4. Время обработки ~1 минута (как в статистике)"

echo ""
echo "📚 Документация:"
echo "- POINT_SOLUTION_REPORT.md - полное описание решения"
echo "- bti_point_markers.scr - AutoCAD скрипт с POINT командами"