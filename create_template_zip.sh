#!/bin/bash

# Скрипт для создания template_bti.zip с базовым шаблоном

echo "=================================================="
echo "📦 СОЗДАНИЕ TEMPLATE_BTI.ZIP"
echo "=================================================="

# Создать временную директорию
TEMP_DIR="temp_template"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# Создать PackageContents.xml
cat > $TEMP_DIR/PackageContents.xml << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<ApplicationPackage 
    SchemaVersion="1.0" 
    ProductType="Application"
    Name="BTI_Template" 
    Description="BTI Template AppBundle"
    Author="BTI Processor"
    ProductCode="BTI001"
    UpgradeCode="BTI001-2025">
    
    <CompanyDetails 
        Name="BTI Processor" 
        Url="https://btiprocessor.run.app" 
        Email="support@btiprocessor.run.app"/>
    
    <RuntimeRequirements 
        OS="Win64" 
        Platform="AutoCAD" 
        SeriesMin="R24.1" 
        SeriesMax="R25.1"/>
    
    <Components>
        <!-- BTI Template DWT file -->
        <ComponentEntry 
            AppName="BTI_Template" 
            Version="1.0" 
            ModuleName="./BTI_Template.dwt" 
            AppDescription="BTI Standard Template"
            LoadOnCommandInvocation="False" 
            LoadOnAutoCADStartup="False"/>
    </Components>
</ApplicationPackage>
EOF

echo "✅ PackageContents.xml создан"

# Проверить наличие BTI_Template.dwt
if [ ! -f "BTI_Template.dwt" ]; then
    echo "⚠️  BTI_Template.dwt не найден"
    echo "📝 Создаю placeholder файл..."
    
    # Создать placeholder (пустой текстовый файл, который будет замене на реальный DWT)
    cat > $TEMP_DIR/BTI_Template.dwt.placeholder << 'EOF'
ВАЖНО: Замените этот файл на реальный BTI_Template.dwt

Этот placeholder создан для тестирования структуры AppBundle.

Для production используйте настоящий файл BTI_Template.dwt:
1. Получите готовый DWT от архитектора
2. Или создайте в AutoCAD с необходимыми слоями/стилями
3. Замените этот файл
EOF
    
    echo "⚠️  ВНИМАНИЕ: Используется placeholder вместо реального DWT"
    echo "   Для production замените на настоящий BTI_Template.dwt"
else
    cp BTI_Template.dwt $TEMP_DIR/
    echo "✅ BTI_Template.dwt скопирован"
fi

# Создать ZIP
cd $TEMP_DIR
zip -r ../template_bti.zip .
cd ..

# Проверить результат
if [ -f "template_bti.zip" ]; then
    SIZE=$(ls -lh template_bti.zip | awk '{print $5}')
    echo ""
    echo "=================================================="
    echo "✅ template_bti.zip создан успешно!"
    echo "=================================================="
    echo "Размер: $SIZE"
    echo "Содержимое:"
    unzip -l template_bti.zip
    echo ""
    echo "📊 Следующие шаги:"
    echo "   1. Если используете placeholder - замените на реальный BTI_Template.dwt"
    echo "   2. Пересоздайте ZIP: ./create_template_zip.sh"
    echo "   3. Запустите: python3 setup_bti_template.py"
else
    echo "❌ Ошибка создания ZIP"
    exit 1
fi

# Очистить временную директорию
rm -rf $TEMP_DIR

echo ""
echo "🎯 Готово! Запустите: python3 setup_bti_template.py"

