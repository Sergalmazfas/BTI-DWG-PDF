# ✅ Деплой с типовым шаблоном BTI - УСПЕШНО!

**Дата:** 2025-10-14  
**Ревизия:** telegram-bti-bot-00031-qgj  
**Region:** europe-west1  
**Статус:** ✅ Running (100% traffic)

---

## 🎯 Что задеплоено

### **Конфигурация:**

```yaml
Service: telegram-bti-bot
Region: europe-west1
URL: https://telegram-bti-bot-637190449180.europe-west1.run.app

Environment Variables:
  - GOOGLE_CLOUD_PROJECT=talkhint
  - GCS_BUCKET=btibot-processed
  - AUTO_PDF=false
  - JOB_TIMEOUT_SEC=900
  - USE_BTI_TEMPLATE=true  ← ТИПОВОЙ ШАБЛОН ВКЛЮЧЕН!

Secrets:
  - FORGE_CLIENT_ID (latest)
  - FORGE_CLIENT_SECRET (latest)
  - BOT_TOKEN (latest)
  - FORGE_SERVICE_KEY (latest)

Resources:
  - CPU: 1
  - Memory: 2Gi
  - Timeout: 300s
  - Min instances: 0
  - Max instances: 10
  - Concurrency: 80
```

---

## 🏛️ Типовой шаблон BTI

### **Конфигурация:**

```
Шаблон URL: https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
Размер: 51.2 KB
Activity: BotBti.BTI_INSERT_Basman+v1
Режим: Активен (USE_BTI_TEMPLATE=true)
```

### **Что происходит при обработке:**

```
1. Пользователь отправляет DWG → Telegram Bot
   ↓
2. Файл загружается в GCS (raw/)
   ↓
3. Создается WorkItem в Autodesk APS
   Activity: BotBti.BTI_INSERT_Basman+v1
   ↓
4. APS загружает:
   - inputFile: входной DWG
   - templateFile: типовой шаблон BTI (из GCS)
   ↓
5. AutoCAD выполняет:
   _INSERT templateFile at 0,0,0
   _SAVEAS 2018 result.dwg
   ↓
6. Результат: DWG + типовой шаблон БТИ
   ↓
7. Сохраняется в GCS (ready/)
   ↓
8. Уведомление пользователю в Telegram
```

---

## 📊 Логи инициализации

```
✅ Bot initialized and started on background loop
✅ GCS Queue Manager initialized for bucket: btibot-queue
✅ Application started
✅ Queue worker started
✅ Flask app running on 0.0.0.0:8080
✅ Default STARTUP TCP probe succeeded
```

---

## 🧪 Проверка работы

### **1. Health Check:**

```bash
curl https://telegram-bti-bot-637190449180.europe-west1.run.app/health
```

**Результат:**
```json
{
  "status": "OK",
  "message": "BTI DWG → PDF Converter is running"
}
```

✅ Работает!

---

### **2. Тест с типовым шаблоном (Postman):**

```http
POST https://telegram-bti-bot-637190449180.europe-west1.run.app/process-dwg
Content-Type: application/json

{
  "file_url": "https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg",
  "mode": "bti",
  "chat_id": "test_deploy",
  "job_id": "test_template_001"
}
```

**Ожидаемый результат:**
```json
{
  "success": true,
  "workitem_id": "...",
  "result_url": "gs://btibot-processed/ready/test_deploy/test_template_001/bti_ready.dwg",
  "mode": "bti",
  "processing_time": 5-8
}
```

---

### **3. Проверка логов типового шаблона:**

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=telegram-bti-bot AND textPayload:типовым" --limit=5
```

**Ожидается в логах:**
```
🏛️ Режим: с типовым шаблоном BTI Basmanny
📄 Шаблон: https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
📤 Отправка WorkItem с activityId: BotBti.BTI_INSERT_Basman+v1
```

---

## 🔧 Исправления при деплое

### **Проблема:**
```
ModuleNotFoundError: No module named 'bti_template_config'
```

### **Решение:**
Встроил код конфигурации прямо в `forge_client.py`:

```python
# Конфигурация типового шаблона BTI
BTI_TEMPLATE_URL = "https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg"
BTI_TEMPLATE_ACTIVITY = "BotBti.BTI_INSERT_Basman+v1"
BTI_SIMPLE_ACTIVITY = "BotBti.SimpleDWG2DWG+v1"

# Inline код вместо внешних функций
if use_template:
    body = {
        "activityId": BTI_TEMPLATE_ACTIVITY,
        "arguments": {
            "inputFile": {"url": input_url},
            "templateFile": {"url": BTI_TEMPLATE_URL},
            "resultFile": {"url": output_url, "verb": "put"}
        }
    }
else:
    body = {
        "activityId": BTI_SIMPLE_ACTIVITY,
        "arguments": {
            "inputFile": {"url": input_url},
            "resultFile": {"url": output_url, "verb": "put"}
        }
    }
```

---

## 📋 Итоговые файлы

### **Изменения в коде:**

1. ✅ `forge_client.py` - встроен код конфигурации шаблона
2. ✅ `app.py` - добавлена поддержка USE_BTI_TEMPLATE

### **Деплой:**

```bash
Revision: telegram-bti-bot-00031-qgj
Traffic: 100%
Status: ✅ Serving
```

---

## ✅ Итог

### **Успешно задеплоено:**

- ✅ Сервис работает
- ✅ USE_BTI_TEMPLATE=true активирован
- ✅ Типовой шаблон BTI настроен
- ✅ Activity: BotBti.BTI_INSERT_Basman+v1
- ✅ Шаблон URL: https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg

### **Режимы работы:**

1. **Простой (по умолчанию):**
   - Activity: BotBti.SimpleDWG2DWG+v1
   - Результат: DWG в формате AutoCAD 2018

2. **С типовым шаблоном BTI (сейчас активен):**
   - Activity: BotBti.BTI_INSERT_Basman+v1
   - Результат: DWG + типовой шаблон БТИ в точке 0,0,0

---

## 🧪 Следующие шаги

1. **Протестировать через Telegram** - отправить DWG файл боту
2. **Протестировать через Postman** - использовать POSTMAN_BTI_TEMPLATE_GUIDE.md
3. **Проверить результаты** - скачать DWG и проверить в AutoCAD
4. **Проверить логи** - убедиться что шаблон вставляется

---

**🎉 release/gold1 с типовым шаблоном BTI задеплоен и работает!**


