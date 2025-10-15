#!/bin/bash
# Валидация структуры проекта

echo "🔍 Проверка структуры проекта..."
echo ""

files=(
    "scripts/BTI_APPLY_COLOR.lsp"
    "scripts/BTI_APPLY.lsp"
    "scripts/BTI_CLEANUP.lsp"
    "templates/BTI_Template.dwg"
    "config/bti_color_mapping.json"
    "config/bti_layers.json"
    "forge/activity_color_based.json"
    "forge_client.py"
    "app.py"
)

all_found=true
for f in "${files[@]}"; do
    if [ -f "$f" ]; then
        size=$(ls -lh "$f" | awk '{print $5}')
        echo "✅ $f ($size)"
    else
        echo "❌ $f ОТСУТСТВУЕТ"
        all_found=false
    fi
done

echo ""
if [ "$all_found" = true ]; then
    echo "✅ Все файлы на месте!"
    exit 0
else
    echo "❌ Некоторые файлы отсутствуют"
    exit 1
fi

