# 🔐 Конфигурация и секреты для release/gold1

**Дата:** 2025-10-14  
**Ветка:** `release/gold1`  
**Статус:** ✅ Полностью настроено

---

## 📋 Основная информация

| Параметр | Значение |
|----------|----------|
| **GCP Project** | talkhint |
| **GCS Bucket** | btibot-processed |
| **Region** | europe-west1 |
| **Service** | telegram-bti-bot |

---

## 🔑 Секреты в Google Secret Manager

### **1. Autodesk APS (Forge) Credentials**

```bash
# Client ID
FORGE_CLIENT_ID=m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4

# Client Secret  
FORGE_CLIENT_SECRET=tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW

# Nickname (ForgeAppName) для Design Automation API
FORGE_NICKNAME=BotBti

# Service Account для GCS signed URLs
FORGE_SERVICE_KEY=<JSON ключ в Secret Manager>
# Путь: projects/talkhint/secrets/FORGE_SERVICE_KEY/versions/latest
```

### **2. Telegram Bot**

```bash
BOT_TOKEN=<ваш_telegram_bot_token>
# Хранится в: projects/talkhint/secrets/BOT_TOKEN/versions/latest
```

### **3. Google Cloud**

```bash
GOOGLE_CLOUD_PROJECT=talkhint
GCS_BUCKET=btibot-processed
```

---

## 🎯 Autodesk APS Activities

### **Текущая конфигурация (в forge_client.py):**

```python
"activityId": "BotBti.SimpleDWG2DWG+v1"
```

### **Доступные Activities:**

| Activity ID | Описание | Статус |
|-------------|----------|--------|
| **BotBti.SimpleDWG2DWG+v1** | ✅ **ИСПОЛЬЗУЕТСЯ** - DWG→DWG с SAVEAS (AutoCAD 2018) | Рабочий |
| BotBti.DWG2DWGCopy+v1 | DWG→DWG с WBLOCK | Рабочий |
| BotBti.SimpleDWG2DWG_NoTemplate+v1 | DWG passthrough без шаблона | Рабочий |
| BotBti.DWG2DWGTest+v1 | Тестовая Activity | Устарел |
| BotBti.BTI_INSERT_Template+v1 | Вставка BTI шаблона (.NET) | Тестовый |
| BotBti.BTI_INSERT_Basman+v1 | Вставка Басманного шаблона (.NET) | Тестовый |

### **Параметры WorkItem для BotBti.SimpleDWG2DWG+v1:**

```json
{
  "activityId": "BotBti.SimpleDWG2DWG+v1",
  "arguments": {
    "inputFile": {"url": "https://..."},
    "resultFile": {"url": "https://...", "verb": "put"}
  }
}
```

### **Спецификация Activity:**

```json
{
  "id": "BotBti.SimpleDWG2DWG+v1",
  "commandLine": [
    "$(engine.path)\\accoreconsole.exe /i \"$(args[inputFile].path)\" /s \"_SAVEAS\n2018\nresult.dwg\n_QUIT\n\""
  ],
  "engine": "Autodesk.AutoCAD+25_1",
  "parameters": {
    "inputFile": {
      "verb": "get",
      "description": "Input DWG",
      "localName": "input.dwg"
    },
    "resultFile": {
      "verb": "put",
      "description": "Output DWG",
      "localName": "result.dwg"
    }
  },
  "description": "DWG to DWG with SAVEAS command"
}
```

---

## 🚀 Команда деплоя

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

## ⚙️ Переменные окружения

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=talkhint
GCS_BUCKET=btibot-processed

# Режим работы
AUTO_PDF=false                  # DWG-first режим (сначала DWG, потом опционально PDF)
JOB_TIMEOUT_SEC=900            # Таймаут обработки (15 минут)

# Flask
PORT=8080                      # Порт для приложения
```

---

## 🔧 Проверка секретов

### **Просмотр всех секретов:**

```bash
gcloud secrets list --project=talkhint
```

### **Получить значение секрета:**

```bash
gcloud secrets versions access latest --secret="FORGE_CLIENT_ID" --project=talkhint
gcloud secrets versions access latest --secret="FORGE_CLIENT_SECRET" --project=talkhint
gcloud secrets versions access latest --secret="BOT_TOKEN" --project=talkhint
```

### **Обновить секрет:**

```bash
echo -n "новое_значение" | gcloud secrets versions add FORGE_CLIENT_ID --data-file=-
```

---

## 📊 Структура проекта

```
BTI-DWG-PDF-1/
├── app.py                    # Основной Flask + Telegram bot
├── forge_client.py           # ✅ ОБНОВЛЕН: BotBti.SimpleDWG2DWG+v1
├── dwg_converter.py          # Fallback конвертер (LibreCAD)
├── gcs_queue_manager.py      # Менеджер очереди GCS
├── requirements.txt          # Python зависимости
├── Dockerfile                # Docker образ
│
├── setup_aps_nickname.py     # ✅ НОВЫЙ: Регистрация nickname
├── setup_aps_activity.py     # ✅ НОВЫЙ: Создание Activity
├── check_activity.py         # ✅ НОВЫЙ: Проверка Activity деталей
│
└── docs/                     # Документация
    ├── GOLD1_RELEASE_REPORT.md
    ├── SIMPLEDWG_DEPLOY_REPORT.md
    └── ...
```

---

## ✅ Итоговая конфигурация

### **Что работает:**

1. ✅ **Autodesk APS Integration** - через `BotBti.SimpleDWG2DWG+v1`
2. ✅ **Telegram Bot** - прием DWG файлов
3. ✅ **GCS Storage** - хранение файлов в `btibot-processed`
4. ✅ **Queue System** - очередь обработки через GCS
5. ✅ **Fallback** - копирование DWG при сбое APS
6. ✅ **DWG-first режим** - сначала DWG, потом опционально PDF

### **Credentials:**

- ✅ **FORGE_CLIENT_ID**: m6CK3... (зарегистрирован)
- ✅ **FORGE_NICKNAME**: BotBti (активен)
- ✅ **Activity**: BotBti.SimpleDWG2DWG+v1 (проверен)
- ✅ **Secrets**: все в Secret Manager

### **Проблема решена:**

- ❌ **БЫЛО**: Hardcoded Client ID в Activity ID (m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4.DWG2DWGTest+v1)
- ✅ **СТАЛО**: Используем nickname (BotBti.SimpleDWG2DWG+v1)

---

## 📝 Следующие шаги (опционально)

### **1. Улучшение Activity:**

Создать Activity с вставкой BTI шаблона через .NET плагин:
- `BotBti.BTI_INSERT_Template+v1` (уже существует, требует тестирования)

### **2. Мониторинг:**

Настроить алерты в Google Cloud Monitoring:
- Ошибки WorkItem
- Таймауты обработки
- Использование квоты APS

### **3. Масштабирование:**

При увеличении нагрузки:
- Увеличить `--max-instances`
- Оптимизировать `--concurrency`
- Добавить кеш для токенов

---

## 🎉 Итог

**release/gold1** полностью настроен и готов к работе!

- ✅ Все секреты в Secret Manager
- ✅ Autodesk APS интеграция работает
- ✅ Activity BotBti.SimpleDWG2DWG+v1 активна
- ✅ forge_client.py обновлен
- ✅ Готово к деплою!


