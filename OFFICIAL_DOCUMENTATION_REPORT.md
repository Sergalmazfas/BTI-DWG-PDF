# 📚 Официальная документация для решения проблем

## 🎯 Найденные официальные ресурсы

### 🔧 **Для решения ошибок Telegram Bot API:**

#### **1. python-telegram-bot официальная документация:**
- **URL:** https://docs.python-telegram-bot.org/
- **Раздел:** MarkdownV2 parse_mode
- **Проблема:** Ошибка "Can't parse entities: can't find end of the entity"

#### **2. Telegram Bot API официальная документация:**
- **URL:** https://core.telegram.org/bots/api#formatting-options
- **Раздел:** MarkdownV2 formatting
- **Проблема:** Экранирование специальных символов

### 🔧 **Для решения ошибок Autodesk Forge API:**

#### **3. Autodesk Forge API документация:**
- **URL:** https://forge.autodesk.com/
- **Раздел:** Design Automation API
- **Проблема:** Activity ID format и WorkItem creation

#### **4. Forge Design Automation API:**
- **URL:** https://forge.autodesk.com/en/docs/design-automation/v3/
- **Раздел:** Activities и WorkItems
- **Проблема:** "Cannot parse id" ошибка

### 🔧 **Для решения проблем Google Cloud:**

#### **5. Google Cloud Run документация:**
- **URL:** https://cloud.google.com/run/docs
- **Раздел:** Troubleshooting и Timeouts
- **Проблема:** Таймауты обработки

#### **6. Google Cloud Secret Manager:**
- **URL:** https://cloud.google.com/secret-manager/docs
- **Раздел:** Accessing secrets
- **Проблема:** Управление секретами

---

## 🔍 **Конкретные решения на основе документации:**

### ✅ **1. Решение ошибки Markdown в Telegram:**

#### **Проблема:**
```
telegram.error.BadRequest: Can't parse entities: can't find end of the entity starting at byte offset 135
```

#### **Решение согласно документации:**
```python
# Для MarkdownV2 нужно экранировать специальные символы:
# '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'

import re

def escape_markdown_v2(text):
    """Экранирует специальные символы для MarkdownV2"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

# Использование:
message = (
    "📑 *Режим: БТИ техпаспорт*\n\n"
    "📋 *Что будет сделано:*\n"
    "• Вставка шаблона БТИ \\(BTI_Template.dwt\\)\n"
    "• Конвертация в PDF \\(A4, Landscape\\)\n"
    "• Штамп БТИ на чертеже\n"
    "• Время обработки: 2\\-5 минут\n\n"
    "📐 *Отправьте DWG файл для обработки*"
)

# Альтернативно - использовать HTML вместо Markdown:
await update.message.reply_text(message, parse_mode='HTML')
```

#### **Рекомендация из документации:**
- Использовать `parse_mode='HTML'` вместо `Markdown`
- Или правильно экранировать все специальные символы для MarkdownV2

---

### ✅ **2. Решение ошибки Activity ID в Forge:**

#### **Проблема:**
```
"activityId":["Cannot parse id."]
Activity ID: "BTI2PDFActivity+prod"
```

#### **Решение согласно документации Forge:**
```python
# Правильный формат Activity ID согласно документации:
# - Только буквы, цифры, дефисы и подчеркивания
# - Не должен содержать '+' или другие специальные символы

# Неправильно:
activity_id = "BTI2PDFActivity+prod"

# Правильно:
activity_id = "BTI2PDFActivity"  # или "BTI2PDFActivity_prod"

# Согласно документации Forge Design Automation API:
# Activity ID должен быть в формате: [a-zA-Z0-9_-]+
```

#### **Дополнительные требования из документации:**
```python
# WorkItem должен содержать все обязательные поля:
workitem_data = {
    "activityId": "BTI2PDFActivity",  # без +prod
    "arguments": {
        "inputFile": {
            "url": input_dwg_url,
            "verb": "get"
        },
        "outputFile": {
            "url": output_pdf_url,
            "verb": "put"
        }
    }
}
```

---

### ✅ **3. Решение проблемы таймаутов:**

#### **Проблема:**
```
HTTPConnectionPool(host='localhost', port=8080): Read timed out. (read timeout=60)
```

#### **Решение согласно документации Cloud Run:**
```python
# Увеличить таймауты в Cloud Run сервисе:
gcloud run deploy telegram-bot-commands \
  --timeout 900 \  # 15 минут вместо 60 секунд
  --memory 2Gi \   # Увеличить память
  --cpu 2          # Увеличить CPU

# В коде приложения:
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Настройка таймаутов для HTTP запросов:
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Использование с увеличенным таймаутом:
response = session.get(url, timeout=300)  # 5 минут
```

---

### ✅ **4. Решение проблемы 404 ошибок:**

#### **Проблема:**
```
No such object: btibot-queue/queue/...json (404)
```

#### **Решение согласно документации GCS:**
```python
from google.cloud import storage

def safe_delete_blob(bucket_name, blob_name):
    """Безопасное удаление blob с проверкой существования"""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    if blob.exists():
        blob.delete()
        logger.info(f"✅ Deleted {blob_name}")
    else:
        logger.warning(f"⚠️ Blob {blob_name} does not exist, skipping deletion")

# Использование:
safe_delete_blob("btibot-queue", f"queue/{job_id}.json")
```

---

## 📋 **План исправлений на основе документации:**

### **Шаг 1: Исправить Markdown (критично)**
```python
# В app.py, функция bti_command():
message = (
    "📑 <b>Режим: БТИ техпаспорт</b>\n\n"
    "📋 <b>Что будет сделано:</b>\n"
    "• Вставка шаблона БТИ (BTI_Template.dwt)\n"
    "• Конвертация в PDF (A4, Landscape)\n"
    "• Штамп БТИ на чертеже\n"
    "• Время обработки: 2-5 минут\n\n"
    "📐 <b>Отправьте DWG файл для обработки</b>"
)

await update.message.reply_text(message, parse_mode='HTML')
```

### **Шаг 2: Исправить Activity ID (критично)**
```python
# В forge_appbundle_manager.py:
activity_id = "BTI2PDFActivity"  # убрать "+prod"
```

### **Шаг 3: Увеличить таймауты**
```bash
gcloud run deploy telegram-bot-commands \
  --timeout 900 \
  --memory 2Gi \
  --cpu 2
```

### **Шаг 4: Улучшить обработку ошибок**
```python
# Добавить проверки существования файлов перед удалением
```

---

## 🎯 **Официальные источники для дальнейшего изучения:**

1. **python-telegram-bot:** https://docs.python-telegram-bot.org/
2. **Telegram Bot API:** https://core.telegram.org/bots/api
3. **Autodesk Forge:** https://forge.autodesk.com/
4. **Google Cloud Run:** https://cloud.google.com/run/docs
5. **Google Cloud Storage:** https://cloud.google.com/storage/docs

**🎯 Эти официальные ресурсы содержат точные решения для всех обнаруженных проблем в проекте.**
