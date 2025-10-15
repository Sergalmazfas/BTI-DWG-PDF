#!/bin/bash

# 🔍 Скрипт проверки отчёта WorkItem
# Проверяет наличие команд INSERTBTE, QSAVE, QUIT и других параметров

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка аргументов
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Использование: $0 <путь_к_отчёту.log>${NC}"
    exit 1
fi

REPORT_FILE="$1"

# Проверка существования файла
if [ ! -f "$REPORT_FILE" ]; then
    echo -e "${RED}❌ Файл не найден: $REPORT_FILE${NC}"
    exit 1
fi

echo "=================================="
echo "🔍 Проверка отчёта WorkItem"
echo "=================================="
echo "📄 Файл: $REPORT_FILE"
echo ""

# Счётчик успешных проверок
SUCCESS_COUNT=0
TOTAL_CHECKS=5

# 1. Проверка команды INSERTBTE
echo -n "🔹 Проверка команды INSERTBTE... "
if grep -q "Command: INSERTBTE\|INSERTBTE" "$REPORT_FILE"; then
    echo -e "${GREEN}✅${NC}"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    
    # Показываем строку с командой
    grep -i "INSERTBTE" "$REPORT_FILE" | head -3 | while read line; do
        echo "   ↳ $line"
    done
else
    echo -e "${RED}❌ Не найдена${NC}"
fi

# 2. Проверка команды QSAVE
echo -n "🔹 Проверка команды QSAVE... "
if grep -q "Command: QSAVE\|QSAVE" "$REPORT_FILE"; then
    echo -e "${GREEN}✅${NC}"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    
    # Показываем строку с командой
    grep -i "QSAVE" "$REPORT_FILE" | head -1 | while read line; do
        echo "   ↳ $line"
    done
else
    echo -e "${RED}❌ Не найдена${NC}"
fi

# 3. Проверка команды QUIT
echo -n "🔹 Проверка команды QUIT... "
if grep -q "Command: QUIT\|QUIT" "$REPORT_FILE"; then
    echo -e "${GREEN}✅${NC}"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    
    # Показываем строку с командой
    grep -i "QUIT" "$REPORT_FILE" | head -1 | while read line; do
        echo "   ↳ $line"
    done
else
    echo -e "${RED}❌ Не найдена${NC}"
fi

# 4. Проверка BytesDownloaded
echo -n "🔹 Проверка BytesDownloaded... "
if grep -q "BytesDownloaded\|Downloaded" "$REPORT_FILE"; then
    BYTES=$(grep -i "BytesDownloaded\|Downloaded" "$REPORT_FILE" | head -1)
    echo -e "${GREEN}✅${NC}"
    echo "   ↳ $BYTES"
    
    # Извлекаем число байтов
    NUM=$(echo "$BYTES" | grep -oE '[0-9]+' | head -1)
    if [ ! -z "$NUM" ] && [ "$NUM" -gt 10000 ]; then
        echo -e "   ↳ ${GREEN}Размер > 10000 байт (OK)${NC}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "   ↳ ${YELLOW}Размер < 10000 байт (возможна проблема)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Не найдено${NC}"
fi

# 5. Проверка времени выполнения
echo -n "🔹 Проверка времени выполнения... "
if grep -q "Duration\|TimeElapsed\|Elapsed" "$REPORT_FILE"; then
    DURATION=$(grep -i "Duration\|TimeElapsed\|Elapsed" "$REPORT_FILE" | head -1)
    echo -e "${GREEN}✅${NC}"
    echo "   ↳ $DURATION"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
else
    echo -e "${YELLOW}⚠️  Не найдено${NC}"
fi

# Проверка на ошибки
echo ""
echo -n "🔹 Проверка наличия ошибок... "
if grep -qi "error\|exception\|failed" "$REPORT_FILE"; then
    echo -e "${YELLOW}⚠️  Найдены возможные ошибки:${NC}"
    grep -i "error\|exception\|failed" "$REPORT_FILE" | head -5 | while read line; do
        echo "   ↳ $line"
    done
else
    echo -e "${GREEN}✅ Ошибок не найдено${NC}"
fi

# Итоговый результат
echo ""
echo "=================================="
echo "📊 Результат проверки"
echo "=================================="
echo "✅ Успешных проверок: $SUCCESS_COUNT из $TOTAL_CHECKS"

if [ $SUCCESS_COUNT -ge 4 ]; then
    echo -e "${GREEN}🎉 ПРОВЕРКА ПРОЙДЕНА УСПЕШНО!${NC}"
    exit 0
elif [ $SUCCESS_COUNT -ge 2 ]; then
    echo -e "${YELLOW}⚠️  ПРОВЕРКА ПРОЙДЕНА ЧАСТИЧНО${NC}"
    exit 1
else
    echo -e "${RED}❌ ПРОВЕРКА НЕ ПРОЙДЕНА${NC}"
    exit 1
fi

