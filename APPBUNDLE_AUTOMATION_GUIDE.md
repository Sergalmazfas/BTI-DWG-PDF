# 🚀 Автоматизация создания AppBundle - Полное руководство

**Скрипт:** Create-And-Upload-AppBundle.ps1  
**Платформа:** Windows VM (с AutoCAD)  
**Цель:** Полная автоматизация создания и загрузки AppBundle

---

## 🎯 Что делает скрипт

```
1. ✅ Компилирует .NET плагин
2. ✅ Создает структуру .bundle
3. ✅ Генерирует PackageContents.xml
4. ✅ Копирует DLL и шаблон
5. ✅ Создает .zip архив
6. ✅ Получает APS токен
7. ✅ Регистрирует AppBundle в Forge API
8. ✅ Загружает архив на S3
9. ✅ Создает alias (v1)
10. ✅ Проверяет результат
```

**Результат:** Готовый AppBundle в Autodesk APS!

---

## ⚡ Быстрый старт (на Windows VM)

### **Шаг 1: Установить credentials**

```powershell
# В PowerShell на VM
$env:APS_CLIENT_ID = "m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4"
$env:APS_CLIENT_SECRET = "tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW"
```

### **Шаг 2: Запустить скрипт**

```powershell
cd C:\BTI-DWG-PDF
pwsh .\Create-And-Upload-AppBundle.ps1
```

**Готово!** Скрипт сделает всё автоматически!

---

## 🔧 Параметры скрипта (опциональные)

```powershell
pwsh .\Create-And-Upload-AppBundle.ps1 `
  -ProjectPath "C:\BTI-DWG-PDF\BTI_TemplateAppBundle" `
  -OutputPath "C:\out" `
  -AppBundleName "BtiPlugin" `
  -PluginDllName "BTI_InsertBasman.dll" `
  -CommandName "BTI_INSERT_TEMPLATE"
```

**Параметры:**
- `ProjectPath` - путь к .csproj проекту
- `OutputPath` - куда сохранять результаты
- `AppBundleName` - имя AppBundle (без расширения)
- `PluginDllName` - имя DLL файла плагина
- `CommandName` - имя команды AutoCAD

---

## 📋 Что создается

### **Структура .bundle:**

```
C:\out\BtiPlugin.bundle\
├── PackageContents.xml       ← Автоматически сгенерирован
└── Contents\
    ├── BTI_InsertBasman.dll  ← Скомпилированный плагин
    └── bti_basmanny_template.dwg  ← Типовой шаблон BTI
```

### **Файлы:**

```
C:\out\
├── BtiPlugin.bundle\         (директория)
├── BtiPlugin.zip             (архив для APS)
├── BTI_InsertBasman.dll      (скомпилированный DLL)
└── appbundle_report.json     (отчет о создании)
```

### **В APS:**

```
AppBundle ID: BotBti.BtiPlugin+v1
Engine: Autodesk.AutoCAD+25_1
Status: ✅ Зарегистрирован и загружен
```

---

## ✅ Ожидаемый вывод скрипта

```
╔══════════════════════════════════════════════════════════════╗
║     🚀 Создание и загрузка AppBundle в Autodesk APS         ║
╚══════════════════════════════════════════════════════════════╝

ℹ️  ШАГ 1: Проверка окружения
✅ Credentials найдены
   Client ID: m6CK3EHpibW1XrHpPFiO...
✅ .NET SDK установлен: 8.0.100

ℹ️  ШАГ 2: Компиляция .NET плагина
   Проект: C:\BTI-DWG-PDF\BTI_TemplateAppBundle\BTI_InsertBasman.csproj
   Компиляция...
✅ Плагин скомпилирован: BTI_InsertBasman.dll (45.23 KB)

ℹ️  ШАГ 3: Создание структуры .bundle
✅ Структура .bundle создана

ℹ️  ШАГ 4: Создание PackageContents.xml
✅ PackageContents.xml создан

ℹ️  ШАГ 5: Копирование файлов в .bundle
✅ DLL скопирован: BTI_InsertBasman.dll
✅ Шаблон BTI скопирован

ℹ️  ШАГ 6: Создание .zip архива
✅ Архив создан: BtiPlugin.zip (78.45 KB)
   SHA256: abc123def456...

ℹ️  ШАГ 7: Получение APS токена
✅ APS токен получен

ℹ️  ШАГ 8: Получение nickname (ForgeAppName)
✅ Nickname: BotBti

ℹ️  ШАГ 9: Регистрация AppBundle в APS
   Создание AppBundle: BotBti.BtiPlugin
✅ AppBundle зарегистрирован
   Upload URL: https://dasprod-store.s3.amazonaws.com...

ℹ️  ШАГ 10: Загрузка архива на S3
   Загрузка BtiPlugin.zip на S3...
✅ Архив загружен на S3

ℹ️  ШАГ 11: Создание alias 'v1'
✅ Alias 'v1' создан
   Full ID: BotBti.BtiPlugin+v1

ℹ️  ШАГ 12: Проверка AppBundle
✅ AppBundle проверен и работает

   📋 Детали:
      ID: BotBti.BtiPlugin+v1
      Engine: Autodesk.AutoCAD+25_1
      Version: 1
      Description: BTI Plugin для вставки типового шаблона БТИ Басманный

╔══════════════════════════════════════════════════════════════╗
║                  ✅ УСПЕХ! AppBundle готов!                  ║
╚══════════════════════════════════════════════════════════════╝

📦 AppBundle ID: BotBti.BtiPlugin+v1
📁 Архив: C:\out\BtiPlugin.zip
🔑 SHA256: abc123def456...

🎯 Следующий шаг: Обновить Activity

   Используйте этот AppBundle в Activity:
   "appbundles": [ "BotBti.BtiPlugin+v1" ]

   Или запустите:
   pwsh .\Update-Activity.ps1 -ActivityId "BotBti.DWG2DWGCopy+v1" -AppBundleFull "BotBti.BtiPlugin+v1"
```

---

## 🔍 Проверка результата

### **1. Проверить что AppBundle создан:**

```powershell
# Список всех AppBundles
$token = "<ваш_токен>"
Invoke-RestMethod `
  -Uri "https://developer.api.autodesk.com/da/us-east/v3/appbundles" `
  -Headers @{"Authorization"="Bearer $token"} | 
  ConvertTo-Json

# Должен быть BotBti.BtiPlugin в списке
```

### **2. Проверить детали:**

```powershell
Invoke-RestMethod `
  -Uri "https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin+v1" `
  -Headers @{"Authorization"="Bearer $token"} |
  ConvertTo-Json
```

### **3. Проверить файлы:**

```powershell
# Проверить созданные файлы
Get-ChildItem C:\out

# Проверить содержимое bundle
Expand-Archive C:\out\BtiPlugin.zip -DestinationPath C:\temp\check -Force
Get-ChildItem C:\temp\check\BtiPlugin.bundle -Recurse
```

---

## ⚙️ Следующий шаг: Обновить Activity

После успешного создания AppBundle нужно обновить Activity:

```powershell
# Обновить Activity BotBti.DWG2DWGCopy для использования нового AppBundle
pwsh .\Update-Activity.ps1 `
  -AccessToken $token `
  -ActivityId "BotBti.DWG2DWGCopy+v1" `
  -AppBundleFull "BotBti.BtiPlugin+v1"
```

---

## 🧪 Тестирование

После обновления Activity протестировать через API:

```powershell
$testBody = @{
    file_url = "gs://btibot-processed/templates/bti_basmanny_template.dwg"
    mode = "bti"
    chat_id = "test_appbundle"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "https://telegram-bti-bot-637190449180.europe-west1.run.app/process-dwg" `
  -Method Post `
  -ContentType "application/json" `
  -Body $testBody
```

**Ожидается:**
```json
{
  "success": true,
  "workitem_id": "...",
  "result_url": "gs://..."
}
```

---

## ⚠️ Возможные проблемы

### **Проблема 1: AutoCAD DLL не найдены**

```powershell
# Найти AutoCAD DLL
Get-ChildItem "C:\Program Files\Autodesk" -Recurse -Filter "acdbmgd.dll"
```

**Решение:** Обновить пути в `.csproj` файле

### **Проблема 2: Компиляция не удалась**

```powershell
# Детальный вывод компиляции
dotnet build BTI_InsertBasman.csproj -c Release -o C:\out -v detailed
```

### **Проблема 3: AppBundle уже существует**

```
⚠️ AppBundle уже существует, обновляем версию...
✅ Новая версия AppBundle создана
```

Это нормально - скрипт автоматически обновляет версию!

---

## 📊 Итоговая схема

```
[Windows VM]
    ↓
Create-And-Upload-AppBundle.ps1
    ↓
1. Компиляция .NET → BTI_InsertBasman.dll
2. Создание .bundle структуры
3. PackageContents.xml (автогенерация)
4. Архивирование → BtiPlugin.zip
    ↓
[Autodesk APS API]
    ↓
5. POST /appbundles → Регистрация
6. Upload to S3 → Загрузка архива
7. POST /aliases → Создание v1
    ↓
[AppBundle: BotBti.BtiPlugin+v1]
    ↓
Готов к использованию в Activity!
```

---

## ✅ Итог

**Один скрипт делает всё:**
- Компиляция ✅
- Упаковка ✅
- Регистрация ✅
- Загрузка ✅
- Alias ✅
- Проверка ✅

**Запуск:**
```powershell
pwsh .\Create-And-Upload-AppBundle.ps1
```

**Результат:**
```
AppBundle ID: BotBti.BtiPlugin+v1
Статус: ✅ Готов к использованию
```

---

**🎉 Готово! Полная автоматизация AppBundle!**


