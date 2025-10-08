#!/bin/bash
# Создание финального ZIP-пакета APS Integration

set -e

PACKAGE_NAME="bti-aps-integration-$(date +%Y%m%d).zip"
TEMP_DIR="bti-aps-package"

echo "📦 Создание пакета: $PACKAGE_NAME"

# Создаем временную директорию
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Копируем основные файлы
echo "📁 Копирование файлов..."

# Основной код
cp app.py "$TEMP_DIR/"
cp test_aps_full_pipeline.py "$TEMP_DIR/"
cp forge_client.py "$TEMP_DIR/"
cp dwg_converter.py "$TEMP_DIR/"
cp gcs_queue_manager.py "$TEMP_DIR/"
cp requirements.txt "$TEMP_DIR/"
cp Dockerfile "$TEMP_DIR/"
cp cloudbuild.yaml "$TEMP_DIR/"

# Документация
cp APS_INTEGRATION_README.md "$TEMP_DIR/README.md"
cp APS_PIPELINE_TEST_SUCCESS_REPORT.md "$TEMP_DIR/"
cp APS_SIGNED_URLS_GUIDE.md "$TEMP_DIR/"
cp POSTMAN_PIPELINE_COMPLETE.md "$TEMP_DIR/"
cp POSTMAN_INTEGRATION_PLAN.md "$TEMP_DIR/"

# Создаем ZIP
echo "🗜️ Создание архива..."
cd "$TEMP_DIR"
zip -r "../$PACKAGE_NAME" ./*
cd ..

# Удаляем временную директорию
rm -rf "$TEMP_DIR"

# Показываем информацию
echo "✅ Пакет создан: $PACKAGE_NAME"
ls -lh "$PACKAGE_NAME"

echo ""
echo "📋 Содержимое пакета:"
unzip -l "$PACKAGE_NAME"

echo ""
echo "🎉 Готово! Пакет: $PACKAGE_NAME"

