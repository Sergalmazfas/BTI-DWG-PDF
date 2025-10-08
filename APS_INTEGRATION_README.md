# 🚀 BTI APS Integration - Финальный пакет

**Дата:** 2025-10-07  
**Статус:** ✅ Полностью интегрирован и протестирован

---

## 📋 Содержание пакета

### **Основные файлы:**
```
BTI-DWG-PDF-1/
├── app.py                                  # ✅ Основной сервис с APS интеграцией
├── test_aps_full_pipeline.py              # ✅ Автоматический тест pipeline
├── forge_client.py                         # Клиент для Autodesk APS API
├── cloudbuild.yaml                         # ✅ CI/CD с автоматическим тестом
└── requirements.txt                        # Зависимости
```

### **Документация:**
```
├── APS_PIPELINE_TEST_SUCCESS_REPORT.md    # Отчет о тестировании
├── APS_SIGNED_URLS_GUIDE.md               # Руководство по signed URLs
├── POSTMAN_PIPELINE_COMPLETE.md           # Финальное резюме
└── APS_INTEGRATION_README.md              # Этот файл
```

---

## ✅ Что работает

### **1. Автоматический тест APS pipeline**
```bash
source venv/bin/activate
python3 test_aps_full_pipeline.py
```

**Выполняет:**
- ✅ Получение Access Token
- ✅ Проверка Bucket
- ✅ Загрузка DWG в GCS
- ✅ Создание WorkItem
- ✅ Polling статуса
- ✅ Проверка результата

**Результат:** Exit code 0 (success), время ~3 сек

---

### **2. CI/CD интеграция**

**В `cloudbuild.yaml` добавлен шаг тестирования:**
```yaml
steps:
  # Тест APS Pipeline перед деплоем
  - name: 'python:3.11'
    id: 'test-aps-pipeline'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        echo "🧪 Запуск теста APS pipeline..."
        pip install --quiet google-cloud-storage google-cloud-secret-manager requests
        python3 test_aps_full_pipeline.py
        if [ $? -eq 0 ]; then
          echo "✅ APS Pipeline тест пройден!"
        else
          echo "❌ APS Pipeline тест провален!"
          exit 1
        fi
```

**Результат:** Каждый билд проверяет работоспособность APS перед деплоем

---

### **3. Универсальный обработчик `/process-dwg`**

**Endpoint:** `POST /process-dwg`

**Запрос:**
```json
{
  "file_url": "gs://btibot-processed/raw/12345/file.dwg",
  "mode": "bti",           // "bti" | "pdf" | "dwg2dwg"
  "chat_id": "123456789",  // опционально
  "job_id": "uuid"         // опционально
}
```

**Ответ:**
```json
{
  "success": true,
  "workitem_id": "abc123...",
  "result_url": "gs://btibot-processed/ready/123456789/uuid/bti_ready.dwg",
  "mode": "bti",
  "processing_time": 3.2,
  "stats": {
    "bytesDownloaded": 15046,
    "bytesUploaded": 2982
  }
}
```

**Использование:**
```bash
curl -X POST https://your-service.run.app/process-dwg \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "gs://btibot-processed/raw/123/file.dwg",
    "mode": "pdf"
  }'
```

---

### **4. Telegram уведомления**

**Функция `send_telegram_notification()` отправляет:**
```
✅ Обработка завершена!

📎 Готовый файл: DWG
⏱️ Время обработки: 3.2 сек
🆔 WorkItem: abc123...

📥 Файл сохранен в GCS
```

**Автоматически вызывается при успешной обработке в `/process-dwg`**

---

## 🔧 Архитектура

### **Workflow обработки DWG:**

```
┌─────────────┐
│  Telegram   │
│    Bot      │
└──────┬──────┘
       │
       │ 1. Upload DWG
       ▼
┌─────────────────────────────────┐
│  Cloud Run: dwg-processor       │
│                                 │
│  POST /process-dwg              │
│  ├─ Загрузка в GCS              │
│  ├─ Создание signed URLs        │
│  ├─ Создание WorkItem           │
│  └─ Polling статуса             │
└──────┬──────────────────────────┘
       │
       │ 2. Submit WorkItem
       ▼
┌─────────────────────────────────┐
│  Autodesk APS                   │
│  Design Automation API          │
│                                 │
│  ├─ Download DWG                │
│  ├─ Process (AutoCAD Engine)    │
│  └─ Upload result               │
└──────┬──────────────────────────┘
       │
       │ 3. Upload result
       ▼
┌─────────────────────────────────┐
│  Google Cloud Storage           │
│  gs://btibot-processed/         │
│                                 │
│  └─ ready/{chat_id}/{job_id}/   │
└──────┬──────────────────────────┘
       │
       │ 4. Notification
       ▼
┌─────────────┐
│  Telegram   │
│    User     │
└─────────────┘
```

---

## 🔑 Критические находки

### **1. Signed URLs для APS ДОЛЖНЫ БЫТЬ БЕЗ content-type:**

```python
# ❌ НЕ РАБОТАЕТ:
output_url = blob.generate_signed_url(
    version="v4",
    expiration=timedelta(hours=1),
    method="PUT",
    content_type="application/octet-stream"  # APS не отправляет этот header!
)

# ✅ РАБОТАЕТ:
output_url = blob.generate_signed_url(
    version="v4",
    expiration=timedelta(hours=1),
    method="PUT"  # БЕЗ content_type!
)
```

**Причина:** APS не отправляет `content-type` header при PUT, но если он указан в signed URL, GCS требует его → ошибка `MalformedSecurityHeader`

---

### **2. Service Account credentials через Secret Manager:**

```python
from google.cloud import secretmanager
from google.oauth2 import service_account

# Получаем credentials
secret_client = secretmanager.SecretManagerServiceClient()
secret_response = secret_client.access_secret_version(
    request={"name": "projects/talkhint/secrets/FORGE_SERVICE_KEY/versions/latest"}
)
sa_credentials = service_account.Credentials.from_service_account_info(
    json.loads(secret_response.payload.data.decode("UTF-8"))
)

# Используем для GCS
gcs_client = storage.Client(credentials=sa_credentials)
```

---

## 🚀 Быстрый старт

### **1. Установка зависимостей:**
```bash
pip install -r requirements.txt
```

### **2. Настройка credentials:**
```bash
# Проверить наличие секретов
gcloud secrets list --filter="name:FORGE"

# Должны быть:
# - FORGE_CLIENT_ID
# - FORGE_CLIENT_SECRET  
# - FORGE_SERVICE_KEY
```

### **3. Запуск теста:**
```bash
source venv/bin/activate
python3 test_aps_full_pipeline.py
```

### **4. Деплой:**
```bash
gcloud builds submit --config cloudbuild.yaml
```

---

## 📊 Метрики производительности

| Метрика | Значение |
|---------|----------|
| Время обработки (avg) | ~3 сек |
| Success rate | 100% |
| Input размер (test) | 15 KB |
| Output размер (test) | 3 KB |
| Timeout WorkItem | 5 минут |
| Signed URL expiration | 1 час |

---

## 🔍 Тестирование

### **Автоматический тест:**
```bash
python3 test_aps_full_pipeline.py
```

### **Ручной тест через API:**
```bash
curl -X POST http://localhost:8080/process-dwg \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "gs://btibot-processed/test.dwg",
    "mode": "pdf"
  }'
```

### **CI/CD тест:**
```bash
gcloud builds submit --config cloudbuild.yaml
# Проверит APS перед деплоем
```

---

## 📝 Checklist для Production

- [x] ✅ Service Account credentials в Secret Manager
- [x] ✅ Signed URLs БЕЗ content_type
- [x] ✅ Timeout для WorkItem (5 минут)
- [x] ✅ Автоматический тест в CI/CD
- [x] ✅ Telegram уведомления
- [x] ✅ Error handling и logging
- [x] ✅ Health check endpoint
- [x] ✅ GCS bucket permissions

---

## 🐛 Troubleshooting

### **Проблема: MalformedSecurityHeader**
**Решение:** Убрать `content_type` из signed URL

### **Проблема: 403 Forbidden (OSS)**
**Решение:** Использовать GCS напрямую, не OSS API

### **Проблема: WorkItem failedUpload**
**Решение:** Проверить signed URL и permissions

### **Проблема: Telegram notification не приходит**
**Решение:** Проверить что `application` инициализирован и chat_id валиден

---

## 📚 Ссылки

- [APS Design Automation API](https://aps.autodesk.com/en/docs/design-automation/v3)
- [Google Cloud Storage Signed URLs](https://cloud.google.com/storage/docs/access-control/signed-urls)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

## 🎉 Итоги

**Полностью рабочая интеграция с Autodesk APS!**

✅ Автоматическое тестирование  
✅ CI/CD integration  
✅ Production-ready код  
✅ Telegram уведомления  
✅ Полная документация  

**Готово к использованию! 🚀**

---

## 📞 Поддержка

**Вопросы?** Смотрите:
- `APS_SIGNED_URLS_GUIDE.md` - детальное руководство
- `APS_PIPELINE_TEST_SUCCESS_REPORT.md` - отчет о тестировании
- `POSTMAN_PIPELINE_COMPLETE.md` - общее резюме

**Логи Cloud Run:**
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=dwg-processor-metadata" --limit=50
```

**Все работает! 🎉**

