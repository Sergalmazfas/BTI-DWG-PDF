# 🔧 Подробное объяснение сервисов dwg-processor

## 📊 **Обнаруженные сервисы:**

### 🎯 **1. dwg-processor**
- **URL:** https://dwg-processor-7xj26ekbpa-ew.a.run.app
- **Статус:** Активен (обновлен 2 дня назад)
- **Контейнеры:** 0.27 CPU allocation

### 🎯 **2. dwg-processor-metadata** 
- **URL:** https://dwg-processor-metadata-7xj26ekbpa-ew.a.run.app
- **Статус:** Активен
- **Контейнеры:** 0.26 CPU allocation

---

## 🔍 **Что делает каждый сервис:**

### 🎯 **1. dwg-processor - Основной обработчик**

#### **Назначение:**
- **Основной сервис** для обработки DWG файлов
- **Интегрируется с Autodesk Forge API**
- **Конвертирует DWG в PDF**
- **Обрабатывает очередь файлов**

#### **Как работает:**
```python
# 1. Получает уведомления от GCS через Pub/Sub
def gcs_push():
    # Парсит Pub/Sub сообщение
    data = request.get_json()
    bucket, name, generation = parse_pubsub_message(data)
    
    # Проверяет что это DWG файл в папке raw/
    if name.endswith('.dwg') and name.startswith('raw/'):
        # Обрабатывает файл
        process_dwg_file(bucket, name)

# 2. Обрабатывает DWG файл
def process_dwg_file(bucket, name):
    # Получает метаданные файла (x-type: bti или tz)
    metadata = get_file_metadata(bucket, name)
    
    # Выбирает Activity в зависимости от метаданных
    if metadata.get("x-type") == "bti":
        activity_type = "BTI2PDFActivity"
    elif metadata.get("x-type") == "tz":
        activity_type = "TZ2PDFActivity"
    
    # Создает WorkItem в Forge API
    workitem = create_forge_workitem(activity_type, input_url, output_url)
    
    # Отслеживает статус обработки
    result = poll_workitem_status(workitem['id'])
    
    # Уведомляет пользователя о результате
    notify_user(result)
```

#### **Переменные окружения:**
```
GOOGLE_CLOUD_PROJECT=talkhint
GCS_BUCKET=btibot-processed
FORGE_CLIENT_ID=(пусто - нужно настроить!)
FORGE_CLIENT_SECRET=(пусто - нужно настроить!)
TELEGRAM_BOT_TOKEN=(пусто - нужно настроить!)
```

#### **Проблемы из логов:**
```
❌ DWG processing failed: Failed to create Forge workitem
❌ Forge access token obtained (но не может создать WorkItem)
```

---

### 🎯 **2. dwg-processor-metadata - Обработчик метаданных**

#### **Назначение:**
- **Обрабатывает метаданные** DWG файлов
- **Дополнительная обработка** файлов
- **Вспомогательный сервис** для dwg-processor
- **Fallback обработка** когда Forge API недоступен

#### **Как работает:**
```python
# 1. Получает те же уведомления от GCS
def gcs_push():
    # Парсит Pub/Sub сообщение
    data = request.get_json()
    bucket, name, generation = parse_pubsub_message(data)
    
    # Проверяет что это DWG файл
    if name.endswith('.dwg'):
        # Обрабатывает метаданные
        process_dwg_metadata(bucket, name)

# 2. Обрабатывает метаданные DWG
def process_dwg_metadata(bucket, name):
    # Читает метаданные файла
    metadata = get_file_metadata(bucket, name)
    
    # Пытается конвертировать локально (fallback)
    try:
        # Использует dwg_converter.py
        result = convert_dwg_to_pdf_local(input_file, output_file)
        
        if result:
            # Уведомляет пользователя об успехе
            notify_user_success(result)
        else:
            # Уведомляет пользователя об ошибке
            notify_user_error("Local conversion failed")
            
    except Exception as e:
        logger.error(f"❌ DWG→PDF: {e}")
        notify_user_error(str(e))
```

#### **Проблемы из логов:**
```
❌ DWG→PDF: Dependencies not available (ezdxf, matplotlib)
❌ DWG processing failed: conversion failed
```

---

## 🔄 **Взаимодействие сервисов:**

### **Архитектура системы:**
```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  telegram-bot-      │    │   dwg-processor     │    │dwg-processor-       │
│  commands           │───▶│                     │───▶│metadata             │
│  (основной)         │    │  (Forge API)        │    │ (локальная)         │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   GCS Storage       │    │   Forge API         │    │   dwg_converter.py  │
│ (файлы + очередь)   │    │  (конвертация)      │    │  (fallback)         │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

### **Поток данных:**
1. **Пользователь** загружает DWG → **telegram-bot-commands**
2. **telegram-bot-commands** сохраняет файл в GCS → **GCS Storage**
3. **GCS** отправляет уведомление → **Pub/Sub**
4. **Pub/Sub** уведомляет → **dwg-processor** и **dwg-processor-metadata**
5. **dwg-processor** пытается конвертировать через **Forge API**
6. **dwg-processor-metadata** пытается конвертировать локально (fallback)
7. **Результат** отправляется пользователю через **Telegram Bot**

---

## 🔧 **Текущие проблемы:**

### **1. dwg-processor:**
- ❌ **Пустые переменные окружения** для Forge API
- ❌ **Не может создать WorkItem** в Forge API
- ❌ **Нет доступа к секретам** (FORGE_CLIENT_ID, FORGE_CLIENT_SECRET)

### **2. dwg-processor-metadata:**
- ❌ **Отсутствуют зависимости** (ezdxf, matplotlib)
- ❌ **Локальная конвертация не работает**
- ❌ **Fallback механизм сломан**

---

## 🎯 **Роль в системе:**

### **dwg-processor - Основной путь:**
- **Первый выбор** для обработки DWG файлов
- **Использует Forge API** для профессиональной конвертации
- **Поддерживает BTI и TZ режимы**
- **Высокое качество** конвертации

### **dwg-processor-metadata - Fallback:**
- **Резервный вариант** когда Forge API недоступен
- **Локальная обработка** файлов
- **Обработка метаданных**
- **Простая конвертация** без шаблонов

---

## 🔧 **Что нужно исправить:**

### **1. Для dwg-processor:**
```bash
# Настроить переменные окружения
gcloud run services update dwg-processor \
  --set-env-vars="FORGE_CLIENT_ID=your_client_id" \
  --set-env-vars="FORGE_CLIENT_SECRET=your_client_secret" \
  --set-env-vars="TELEGRAM_BOT_TOKEN=your_bot_token"
```

### **2. Для dwg-processor-metadata:**
```bash
# Добавить зависимости в Dockerfile
RUN pip install ezdxf matplotlib
```

### **3. Синхронизация:**
- **Обновить образы** обоих сервисов
- **Настроить секреты** в Secret Manager
- **Проверить права** Service Accounts

---

## 🎉 **Заключение:**

**Эти два сервиса являются частью полной архитектуры системы:**

- **dwg-processor** - основной обработчик через Forge API
- **dwg-processor-metadata** - резервный обработчик локально

**Они работают параллельно и обеспечивают надежность системы обработки DWG файлов!** 🚀
