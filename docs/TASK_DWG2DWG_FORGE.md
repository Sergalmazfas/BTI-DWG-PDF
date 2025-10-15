# TASK: DWG→DWG через .NET AppBundle (БЕЗ PDF!)

## 🎯 Цель

**DWG → BTI Template → DWG**  
**НИКАКОГО PDF!**

---

## 📦 Деливеры

### **Созданные файлы:**
- ✅ `BTI_TemplateAppBundle/BTI_TemplatePlugin.cs` - .NET плагин
- ✅ `BTI_TemplateAppBundle/PackageContents.xml` - манифест
- ✅ `BTI_TemplateAppBundle/BTI_TemplatePlugin.csproj` - проект
- ✅ `forge/activity_bti_dwg2dwg.json` - JSON Activity
- ✅ `forge_client.py` - обновлен (УДАЛЕНЫ все упоминания PDF)

---

## 🔧 РЕАЛИЗАЦИЯ (ПОД КЛЮЧ)

### **1️⃣ Компиляция .NET плагина**

**Требования:**
- Windows 10/11
- Visual Studio 2019+ или MSBuild
- .NET Framework 4.8 SDK

**Команды:**
```cmd
cd BTI_TemplateAppBundle
dotnet restore
dotnet build -c Release -f net48
```

**Результат:**
```
bin/Release/net48/
├── BTI_TemplatePlugin.dll  ✅
├── PackageContents.xml
└── BTI_Template.dwt (добавить вручную)
```

---

### **2️⃣ Создание bundle.zip**

**Структура:**
```
BTI_TemplateAppBundle.bundle/
├── PackageContents.xml
└── Contents/
    ├── BTI_TemplatePlugin.dll
    └── BTI_Template.dwt
```

**Команды (Windows PowerShell):**
```powershell
cd bin/Release/net48
mkdir BTI_TemplateAppBundle.bundle\Contents

copy PackageContents.xml BTI_TemplateAppBundle.bundle\
copy BTI_TemplatePlugin.dll BTI_TemplateAppBundle.bundle\Contents\
copy BTI_Template.dwt BTI_TemplateAppBundle.bundle\Contents\

Compress-Archive -Path BTI_TemplateAppBundle.bundle -DestinationPath BTI_TemplateAppBundle.zip
```

**Команды (Linux/Mac с zip):**
```bash
cd bin/Release/net48
mkdir -p BTI_TemplateAppBundle.bundle/Contents

cp PackageContents.xml BTI_TemplateAppBundle.bundle/
cp BTI_TemplatePlugin.dll BTI_TemplateAppBundle.bundle/Contents/
cp BTI_Template.dwt BTI_TemplateAppBundle.bundle/Contents/

zip -r BTI_TemplateAppBundle.zip BTI_TemplateAppBundle.bundle/
```

---

### **3️⃣ Загрузка через APS Web UI** (РЕКОМЕНДУЕТСЯ)

**Причина:** API `/aliases` endpoint не работает с длинными Client IDs.

**Шаги:**

1. **Зайти в APS Console:**
   - https://aps.autodesk.com
   - Login → My Apps → [Ваше приложение]

2. **Design Automation → AppBundles:**
   - Click "Create AppBundle"
   - Name: `BTI_TemplateAppBundle`
   - Engine: `Autodesk.AutoCAD+25_1`
   - Upload: `BTI_TemplateAppBundle.zip`
   - Click "Create"

3. **Создать alias для AppBundle:**
   - В списке AppBundles найти `BTI_TemplateAppBundle`
   - Click "Aliases" → "Create Alias"
   - Alias ID: `v1`
   - Version: `1`
   - Click "Create"

4. **Design Automation → Activities:**
   - Click "Create Activity"
   - Name: `BTI_DWG2DWG`
   - Engine: `Autodesk.AutoCAD+25_1`
   - AppBundles: Select `BTI_TemplateAppBundle+v1`
   - Command Line:
     ```
     $(engine.path)\accoreconsole.exe /al "$(appbundles[BTI_TemplateAppBundle].path)" /i "$(args[inputFile].path)" /s "APPLYBTITEMPLATE\n"
     ```
   - Parameters:
     - **inputFile:** verb=get, localName=input.dwg
     - **resultFile:** verb=put, localName=output.dwg
   - Click "Create"

5. **Создать alias для Activity:**
   - В списке Activities найти `BTI_DWG2DWG`
   - Click "Aliases" → "Create Alias"
   - Alias ID: `v1`
   - Version: `1`
   - Click "Create"

---

### **4️⃣ Обновление кода бота**

**Файл: `forge_client.py`**

✅ **УЖЕ ОБНОВЛЕНО:**
```python
# DWG→DWG обработка через BTI_DWG2DWG Activity
# НИКАКОГО PDF! Только DWG с BTI Template
body = {
    "activityId": f"{self.client_id}.BTI_DWG2DWG+v1",
    "arguments": {
        "inputFile": {"url": input_url},
        "resultFile": {
            "url": output_url,
            "verb": "put",
            "headers": {
                "Content-Type": "application/octet-stream"
            }
        }
    }
}
```

**❌ УДАЛЕНО:**
- Все упоминания `AutoCAD.PlotToPDF+25_0`
- Все упоминания `HostDwg` и `Result`
- Все упоминания `application/pdf`

---

### **5️⃣ Тест-прогон**

**После создания Activity в Web UI:**

```bash
# 1. Создать тестовый job
cat > /tmp/test_bti_dwg.json << 'EOF'
{
  "job_id": "bti_dwg2dwg_test",
  "chat_id": "5265534096",
  "dwg_url": "gs://btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg",
  "auto_pdf": false,
  "created_at": "2025-10-07T15:30:00Z",
  "job_type": "bti_dwg",
  "filename": "Plan_test.dwg"
}
EOF

# 2. Добавить в очередь
gcloud storage cp /tmp/test_bti_dwg.json gs://btibot-queue/queue/bti_dwg2dwg_test.json

# 3. Подождать 30 сек (автоматическая обработка) или запустить вручную
curl -X POST https://telegram-bot-commands-637190449180.europe-west1.run.app/process-queue

# 4. Проверить логи
gcloud logging read "resource.labels.service_name=telegram-bot-commands AND textPayload:\"bti_dwg2dwg_test\"" --limit=20
```

---

## ✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

### **Логи Cloud Run должны показать:**
```
INFO:forge_client:📤 Отправка WorkItem с activityId: <client_id>.BTI_DWG2DWG+v1
INFO:forge_client:🚀 WorkItem запущен: <workitem_id>
INFO:forge_client:✅ WorkItem статус: success
INFO:__main__:✅ DWG обработан через Autodesk APS!
```

### **В GCS должен появиться:**
```
gs://btibot-processed/ready/5265534096/bti_dwg2dwg_test/bti_ready.dwg
```

### **Пользователь получит:**
```
🏁 Готово! DWG обработан через Autodesk APS!
📥 Скачать: <ссылка на bti_ready.dwg>

Хотите создать PDF?
[📄 Да, сделать PDF] [👌 Нет, только DWG]
```

---

## ❌ Если Activity еще не создана

**Временный fallback:**
```python
# В forge_client.py будет ошибка:
ERROR: Activity <client_id>.BTI_DWG2DWG+v1 could not be found

# Bot автоматически использует fallback:
INFO: DWG processed with fallback (Forge API unavailable)
```

**Решение:**
1. Создать Activity через Web UI (см. шаг 3️⃣)
2. Или подождать пока скомпилируется и загрузится AppBundle

---

## 🚨 КРИТИЧЕСКИЕ ПРОВЕРКИ

### **Перед деплоем убедитесь:**

- [ ] ❌ НЕТ упоминаний `PlotToPDF` в коде
- [ ] ❌ НЕТ упоминаний `application/pdf`
- [ ] ❌ НЕТ упоминаний `HostDwg` и `Result` parameters
- [ ] ✅ Используется `BTI_DWG2DWG+v1`
- [ ] ✅ Parameters: `inputFile` и `resultFile`
- [ ] ✅ Content-Type: `application/octet-stream`
- [ ] ✅ Signed URL для PUT с expiration ≥ 1 hour

---

## 📊 Текущий статус

| Компонент | Статус | Действие |
|-----------|--------|----------|
| .NET код | ✅ Создан | Требует компиляции на Windows |
| PackageContents.xml | ✅ Готов | - |
| .csproj | ✅ Готов | - |
| Activity JSON | ✅ Создан | Загрузить через Web UI |
| forge_client.py | ✅ Обновлен | PDF УДАЛЕН |
| AppBundle в APS | ⚠️ Нужна загрузка | Через Web UI |
| Activity в APS | ⚠️ Нужно создать | Через Web UI |
| Alias v1 | ⚠️ Нужно создать | Через Web UI |

---

## 🎯 СЛЕДУЮЩИЙ ШАГ

### **ВАРИАНТ 1: С .NET компиляцией (полное решение)**
1. Скомпилировать на Windows
2. Создать bundle.zip
3. Загрузить через Web UI
4. Создать Activity через Web UI
5. Создать aliases
6. Тестировать

**Время:** 1-2 дня

### **ВАРИАНТ 2: Без .NET (временное решение)**

Пока AppBundle не готов, Activity `BTI_DWG2DWG+v1` не существует.  
Bot будет использовать **fallback** (локальная обработка через ezdxf).

**Результат:**
- ✅ Bot работает
- ✅ DWG обрабатывается локально
- ✅ Пользователи получают результаты
- ⚠️ Без Autodesk APS (пока AppBundle не загружен)

---

## 🚀 ДЕПЛОЙ

```bash
# Деплоим обновленную версию (PDF удален, используется BTI_DWG2DWG+v1)
gcloud run deploy telegram-bot-commands \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=talkhint,GCS_BUCKET=btibot-processed,AUTO_PDF=false \
  --set-secrets FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,BOT_TOKEN=BOT_TOKEN:latest \
  --cpu 1 --memory 1Gi --timeout 300 \
  --min-instances 0 --max-instances 10
```

---

## 📋 ИТОГОВЫЙ ЧЕКЛИСТ

- [x] .NET код создан
- [x] PackageContents.xml создан
- [x] .csproj создан
- [x] Activity JSON создан
- [x] forge_client.py обновлен (PDF УДАЛЕН)
- [ ] Компиляция на Windows
- [ ] Создание bundle.zip
- [ ] Загрузка AppBundle через Web UI
- [ ] Создание Activity через Web UI
- [ ] Создание aliases через Web UI
- [ ] Тестирование с реальным DWG

**Архитектура готова! Требуется только компиляция и загрузка через Web UI.** 🎯

