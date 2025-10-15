#!/bin/bash

# 🚀 Полный тест AppBundle
# Автоматизирует весь процесс от скачивания до проверки результата

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================="
echo "🚀 Полный тест AppBundle"
echo "==================================${NC}"
echo ""

# Директории
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ARCHIVES_DIR="$PROJECT_DIR/bte-appbundle/archives"
REPORTS_DIR="$PROJECT_DIR/bte-appbundle/reports"
WORKITEMS_DIR="$PROJECT_DIR/bte-appbundle/workitems"

cd "$PROJECT_DIR"

# 1️⃣ Проверка наличия DWG файла
echo -e "${YELLOW}1️⃣  Проверка наличия DWG файла...${NC}"

DWG_FILE="$ARCHIVES_DIR/basmannyi_novyi_obmernyi.dwg"

if [ ! -f "$DWG_FILE" ]; then
    echo -e "${RED}❌ DWG файл не найден: $DWG_FILE${NC}"
    echo "Скачиваем из GCS..."
    
    gcloud storage cp "gs://btibot-processed/raw/1759861119/*" "$ARCHIVES_DIR/"
    
    # Переименовываем файл если нужно
    if [ -f "$ARCHIVES_DIR/Чертеж_Басманная_Новая_обмерный_план.dwg" ]; then
        mv "$ARCHIVES_DIR/Чертеж_Басманная_Новая_обмерный_план.dwg" "$DWG_FILE"
    fi
fi

if [ -f "$DWG_FILE" ]; then
    FILE_SIZE=$(du -h "$DWG_FILE" | cut -f1)
    echo -e "${GREEN}✅ DWG файл найден: $FILE_SIZE${NC}"
else
    echo -e "${RED}❌ Не удалось найти или скачать DWG файл${NC}"
    exit 1
fi

echo ""

# 2️⃣ Запуск теста
echo -e "${YELLOW}2️⃣  Запуск теста WorkItem...${NC}"
echo ""

python3 "$SCRIPT_DIR/test_workitem.py" --dwg "$DWG_FILE" --output-dir "$REPORTS_DIR"

TEST_EXIT_CODE=$?

echo ""

# 3️⃣ Проверка отчёта
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${YELLOW}3️⃣  Проверка отчёта...${NC}"
    echo ""
    
    # Находим последний отчёт
    LATEST_REPORT=$(ls -t "$REPORTS_DIR"/basmannyi_report_*.log 2>/dev/null | head -1)
    
    if [ ! -z "$LATEST_REPORT" ]; then
        bash "$SCRIPT_DIR/verify_report.sh" "$LATEST_REPORT"
        VERIFY_EXIT_CODE=$?
        
        echo ""
        
        # 4️⃣ Сохранение артефактов
        if [ $VERIFY_EXIT_CODE -eq 0 ]; then
            echo -e "${YELLOW}4️⃣  Сохранение артефактов в GCS...${NC}"
            
            # Находим последний ZIP
            LATEST_ZIP=$(ls -t "$ARCHIVES_DIR"/basmannyi_test_*.zip 2>/dev/null | head -1)
            
            if [ ! -z "$LATEST_ZIP" ]; then
                echo "📦 Загрузка архива..."
                gcloud storage cp "$LATEST_ZIP" gs://btibot-processed/archives/ || true
            fi
            
            # Загружаем отчёт
            echo "📋 Загрузка отчёта..."
            gcloud storage cp "$LATEST_REPORT" gs://btibot-processed/logs/ || true
            
            # Загружаем полный результат JSON
            LATEST_RESULT=$(ls -t "$REPORTS_DIR"/workitem_result_*.json 2>/dev/null | head -1)
            if [ ! -z "$LATEST_RESULT" ]; then
                echo "📊 Загрузка результата..."
                gcloud storage cp "$LATEST_RESULT" gs://btibot-processed/logs/ || true
            fi
            
            echo ""
            echo -e "${GREEN}✅ Артефакты сохранены в GCS${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Отчёт не найден для проверки${NC}"
    fi
fi

# Итоговый результат
echo ""
echo -e "${BLUE}=================================="
echo "🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ"
echo "==================================${NC}"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ ТЕСТ УСПЕШНО ЗАВЕРШЁН!${NC}"
    echo ""
    echo "📁 Артефакты:"
    echo "   • Архив: $ARCHIVES_DIR/"
    echo "   • Отчёты: $REPORTS_DIR/"
    echo "   • WorkItems: $WORKITEMS_DIR/"
    echo ""
    echo "☁️  Результаты в GCS:"
    echo "   • gs://btibot-processed/test_output/basmannyi_result_*.dwg"
    echo "   • gs://btibot-processed/logs/basmannyi_report_*.log"
    echo "   • gs://btibot-processed/archives/basmannyi_test_*.zip"
    echo ""
    echo -e "${BLUE}Готово к коммиту в GitHub!${NC}"
    exit 0
else
    echo -e "${RED}❌ ТЕСТ ЗАВЕРШИЛСЯ С ОШИБКОЙ${NC}"
    echo ""
    echo "Проверьте логи в $REPORTS_DIR/"
    exit 1
fi

