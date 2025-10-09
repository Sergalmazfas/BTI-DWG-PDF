# 🏗️ Создание .NET плагина для вставки шаблона БТИ "Басманная"

## 🎯 Цель

Создать AppBundle который вставляет шаблон "Басманная обмерный план" в каждый DWG файл через Autodesk APS Design Automation API.

---

## 📋 Что уже готово

✅ **Код плагина:** `BTI_TemplateAppBundle/BTI_InsertPlugin.cs`  
✅ **Шаблон в GCS:** `https://storage.googleapis.com/btibot-processed/templates/basmanny-template.dwg` (52,420 bytes)  
✅ **Activity определение:** Готово к созданию  
✅ **Нормализация имён:** Работает (кириллица → латиница)  

---

## 🔧 Шаг 1: Компиляция на Windows

### **Требования:**
- Windows 10/11
- Visual Studio 2019+ с .NET Framework 4.8
- AutoCAD 2025 (для .NET API DLLs)

### **Команды:**

```cmd
cd BTI_TemplateAppBundle

REM Компиляция через MSBuild
msbuild BTI_TemplatePlugin.csproj /p:Configuration=Release /p:Platform=x64 /t:Build

REM Результат:
REM bin\Release\net48\BTI_TemplatePlugin.dll ✅
```

---

## 📦 Шаг 2: Создание bundle.zip

### **Структура:**

```
BTI_InsertBasman.bundle/
├── PackageContents.xml
└── Contents/
    └── BTI_InsertPlugin.dll
```

### **PowerShell команды:**

```powershell
cd bin\Release\net48

# Создать структуру
New-Item -ItemType Directory -Path "BTI_InsertBasman.bundle\Contents" -Force

# Копировать файлы
Copy-Item "..\..\..\PackageContents.xml" "BTI_InsertBasman.bundle\"
Copy-Item "BTI_InsertPlugin.dll" "BTI_InsertBasman.bundle\Contents\"

# Создать ZIP
Compress-Archive -Path "BTI_InsertBasman.bundle" -DestinationPath "BTI_InsertBasman.bundle.zip" -Force

Write-Host "✅ BTI_InsertBasman.bundle.zip создан!"
```

### **Проверка:**

```cmd
tar -tf BTI_InsertBasman.bundle.zip

REM Должно быть:
REM BTI_InsertBasman.bundle/PackageContents.xml
REM BTI_InsertBasman.bundle/Contents/BTI_InsertPlugin.dll
```

---

## ☁️ Шаг 3: Загрузка AppBundle в APS

### **Через Web UI (рекомендуется):**

1. Откройте: https://aps.autodesk.com
2. My Apps → [Ваше приложение]
3. Design Automation → AppBundles
4. Click **"Create AppBundle"**
5. Заполните:
   - **Name:** `BTI_InsertBasman`
   - **Engine:** `Autodesk.AutoCAD+25_1`
   - **Upload:** `BTI_InsertBasman.bundle.zip`
6. Click **"Create"**
7. Создайте Alias:
   - Click **"Aliases"** → **"Create Alias"**
   - **ID:** `v1`
   - **Version:** `1`
   - Click **"Create"**

✅ **Результат:** `BotBti.BTI_InsertBasman+v1`

---

## 🎯 Шаг 4: Создание Activity

### **В APS Web UI:**

1. Design Automation → Activities
2. Click **"Create Activity"**
3. Заполните:
   - **ID:** `BTI_INSERT_Basman_Net`
   - **Engine:** `Autodesk.AutoCAD+25_1`
   - **AppBundles:** Select `BTI_InsertBasman+v1`

4. **Command Line:**
   ```
   $(engine.path)\accoreconsole.exe /al "$(appbundles[BTI_InsertBasman].path)" /i "$(args[inputFile].path)" /s "InsertBTIBasman\n"
   ```

5. **Parameters:**

   **inputFile:**
   ```json
   {
     "verb": "get",
     "localName": "input.dwg",
     "required": true
   }
   ```

   **templateFile:**
   ```json
   {
     "verb": "get",
     "localName": "template.dwg",
     "required": true,
     "url": "https://storage.googleapis.com/btibot-processed/templates/basmanny-template.dwg"
   }
   ```

   **resultFile:**
   ```json
   {
     "verb": "put",
     "localName": "result.dwg",
     "required": true
   }
   ```

6. Click **"Create"**

7. Создайте Alias:
   - **ID:** `v1`
   - **Version:** `1`

✅ **Результат:** `BotBti.BTI_INSERT_Basman_Net+v1`

---

## 🔄 Шаг 5: Обновление бота

### **Обновить forge_client.py:**

```python
# В строке ~121:
body = {
    "activityId": "BotBti.BTI_INSERT_Basman_Net+v1",
    "arguments": {
        "inputFile": {"url": input_url},
        "templateFile": {"url": "https://storage.googleapis.com/btibot-processed/templates/basmanny-template.dwg"},
        "resultFile": {
            "url": output_url,
            "verb": "put"
        }
    }
}
```

### **Задеплоить:**

```bash
cd /Users/seregaboss/BTI-DWG-PDF-1

gcloud run deploy telegram-bti-bot \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=talkhint,GCS_BUCKET=btibot-processed,AUTO_PDF=false,JOB_TIMEOUT_SEC=900" \
  --set-secrets="FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,BOT_TOKEN=BOT_TOKEN:latest,FORGE_SERVICE_KEY=FORGE_SERVICE_KEY:latest" \
  --cpu=1 \
  --memory=2Gi \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=80
```

---

## 🧪 Шаг 6: Тестирование

### **Отправьте файл в бота:**

1. Telegram → @ZamerProbot
2. /start
3. Загрузите DWG файл
4. Дождитесь обработки (~20 сек)
5. Скачайте result.dwg
6. Откройте в AutoCAD
7. ✅ **Проверьте:** шаблон Басманная вставлен!

### **Проверьте логи:**

```bash
gcloud logging read \
  "resource.labels.service_name=telegram-bti-bot AND \
   textPayload:\"InsertBTIBasman\"" \
  --limit=20
```

**Ожидаемые логи:**
```
✅ BTI Insert Plugin загружен (Basmanny Template)
🔧 BTI Insert: Вставка шаблона Басманная...
✅ Шаблон найден: template.dwg
✅ Шаблон загружен в память
✅ Блок вставлен: ...
✅ Ссылка на блок создана в Model Space
✅ Шаблон Басманная вставлен!
✅ result.dwg сохранён (формат: AC1032)
```

---

## 📊 Альтернатива (БЕЗ компиляции)

Если нет доступа к Windows для компиляции, используйте текущую рабочую версию:

✅ **Activity:** `BotBti.DWG2DWGCopy+v1`  
✅ **Метод:** WBLOCK (простое копирование)  
✅ **Success Rate:** 100%  
✅ **Нормализация имён:** Работает  

**Шаблон БТИ:** Можно добавить позже после компиляции плагина.

---

## 📋 Чек-лист

- [ ] Компиляция BTI_InsertPlugin.dll на Windows
- [ ] Создание BTI_InsertBasman.bundle.zip
- [ ] Загрузка AppBundle в APS Web UI
- [ ] Создание Alias v1 для AppBundle
- [ ] Создание Activity BTI_INSERT_Basman_Net
- [ ] Создание Alias v1 для Activity
- [ ] Обновление forge_client.py
- [ ] Деплой telegram-bti-bot
- [ ] Тестирование через Telegram

---

## 🎯 Итог

**Сейчас:**
- ✅ Бот работает с нормализацией имён
- ✅ DWG обрабатывается через APS успешно
- ❌ Шаблон БТИ не применяется (нужна компиляция)

**После компиляции .NET плагина:**
- ✅ Шаблон Басманная будет вставляться в каждый DWG автоматически!

---

**© 2025 - BTI-Bot с Autodesk APS Integration**

