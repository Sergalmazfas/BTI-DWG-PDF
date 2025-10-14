# 📮 Postman - Работа с типовым шаблоном BTI

**Дата:** 2025-10-14  
**Версия:** release/gold1  
**Service:** telegram-bti-bot

---

## 🎯 Обзор

Система поддерживает **два режима** обработки DWG файлов:

1. **Простой режим** - только обработка DWG (SAVEAS в AutoCAD 2018)
2. **С типовым шаблоном BTI** - вставка типового шаблона БТИ Басманный + обработка

---

## 🔧 Endpoints

### **Base URL:**

```
https://telegram-bti-bot-637190449180.europe-west1.run.app
```

или локально:
```
http://localhost:8080
```

---

## 📋 API Endpoints

### **1. Health Check**

```http
GET /health
```

**Response:**
```json
{
  "status": "OK",
  "message": "BTI DWG → PDF Converter is running"
}
```

---

### **2. Status Info**

```http
GET /status
```

**Response:**
```json
{
  "service": "BTI DWG → PDF Converter",
  "version": "1.0.0",
  "status": "running",
  "mode": "production",
  "supported_formats": ["dwg"],
  "max_file_size_mb": 100,
  "features": {
    "telegram_bot": true,
    "dwg_to_pdf": true,
    "gcs_storage": true,
    "pdf_conversion": true,
    "raw_file_backup": true
  },
  "endpoints": {
    "upload": "/upload",
    "health": "/health",
    "status": "/status",
    "process_queue": "/process-queue",
    "queue_status": "/queue-status"
  }
}
```

---

### **3. Process DWG (с поддержкой шаблона)**

```http
POST /process-dwg
Content-Type: application/json
```

#### **Простой режим (без шаблона):**

**Request Body:**
```json
{
  "file_url": "gs://btibot-processed/raw/1234567890/test.dwg",
  "mode": "dwg2dwg",
  "chat_id": "123456789",
  "job_id": "test_job_001"
}
```

**Environment Variables (должны быть установлены):**
```bash
USE_BTI_TEMPLATE=false  # или не указан
```

**Response:**
```json
{
  "success": true,
  "workitem_id": "abc123def456...",
  "result_url": "gs://btibot-processed/ready/123456789/test_job_001/bti_ready.dwg",
  "mode": "dwg2dwg",
  "processing_time": 4.5,
  "stats": {
    "timeInstructionsMs": 3500
  }
}
```

**Activity используется:** `BotBti.SimpleDWG2DWG+v1`

---

#### **С типовым шаблоном BTI:**

**Request Body:**
```json
{
  "file_url": "gs://btibot-processed/raw/1234567890/test.dwg",
  "mode": "bti",
  "chat_id": "123456789",
  "job_id": "test_job_bti_001"
}
```

**Environment Variables (должны быть установлены):**
```bash
USE_BTI_TEMPLATE=true  # ← Включить шаблон
```

**Response:**
```json
{
  "success": true,
  "workitem_id": "xyz789abc123...",
  "result_url": "gs://btibot-processed/ready/123456789/test_job_bti_001/bti_ready.dwg",
  "mode": "bti",
  "processing_time": 6.2,
  "stats": {
    "timeInstructionsMs": 5500
  }
}
```

**Activity используется:** `BotBti.BTI_INSERT_Basman+v1`

**Что происходит:**
1. Загружается входной DWG
2. Загружается типовой шаблон из: `https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg`
3. Шаблон вставляется в точку 0,0,0
4. Результат сохраняется в формате AutoCAD 2018

---

### **4. Upload File**

```http
POST /upload
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: DWG файл (binary)

**Response (простой режим):**
```json
{
  "success": true,
  "message": "DWG → PDF conversion successful",
  "pdf_url": "https://storage.googleapis.com/btibot-processed/processed/1234567890/plan.pdf",
  "raw_url": "https://storage.googleapis.com/btibot-processed/raw/1234567890/test.dwg",
  "file_info": {
    "original_filename": "test.dwg",
    "file_size": 52420,
    "format": "DWG → PDF"
  }
}
```

---

### **5. Queue Status**

```http
GET /queue-status
```

**Response:**
```json
{
  "pending_jobs": 0,
  "processing_locked": false,
  "queue": [],
  "stats": {
    "total_jobs": 10,
    "completed": 8,
    "failed": 2
  }
}
```

---

## 🧪 Postman Collection

### **Collection: BTI DWG Processor**

#### **Folder 1: Health Checks**

**1.1 Health Check**
```
GET {{base_url}}/health
```

**1.2 Status Info**
```
GET {{base_url}}/status
```

---

#### **Folder 2: Simple Mode (без шаблона)**

**2.1 Process DWG (Simple)**
```
POST {{base_url}}/process-dwg
Content-Type: application/json

Body:
{
  "file_url": "gs://btibot-processed/raw/test/input.dwg",
  "mode": "dwg2dwg",
  "chat_id": "api_test",
  "job_id": "simple_{{$timestamp}}"
}
```

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Success is true", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.success).to.eql(true);
});

pm.test("Has workitem_id", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.workitem_id).to.exist;
});

// Save workitem_id for later use
var jsonData = pm.response.json();
pm.environment.set("last_workitem_id", jsonData.workitem_id);
```

---

#### **Folder 3: BTI Template Mode (с шаблоном)**

**3.1 Process DWG with BTI Template**

**⚠️ Important:** Убедитесь что переменная окружения `USE_BTI_TEMPLATE=true` установлена на сервере!

```
POST {{base_url}}/process-dwg
Content-Type: application/json

Body:
{
  "file_url": "gs://btibot-processed/raw/test/input.dwg",
  "mode": "bti",
  "chat_id": "api_test",
  "job_id": "bti_template_{{$timestamp}}"
}
```

**Pre-request Script:**
```javascript
// Generate unique job ID
pm.environment.set("job_id", "bti_" + Date.now());
```

**Tests:**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Success is true", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.success).to.eql(true);
});

pm.test("Mode is bti", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.mode).to.eql("bti");
});

pm.test("Processing time is reasonable", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.processing_time).to.be.below(30);
});

// Save result URL
var jsonData = pm.response.json();
pm.environment.set("result_url", jsonData.result_url);
pm.environment.set("workitem_id", jsonData.workitem_id);

console.log("WorkItem ID:", jsonData.workitem_id);
console.log("Result URL:", jsonData.result_url);
console.log("Processing time:", jsonData.processing_time, "seconds");
```

---

#### **Folder 4: File Upload**

**4.1 Upload DWG File**
```
POST {{base_url}}/upload
Content-Type: multipart/form-data

Body:
file: [Select DWG file]
```

**Tests:**
```javascript
pm.test("Upload successful", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.success).to.eql(true);
});

pm.test("Has PDF URL", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.pdf_url).to.exist;
});

pm.test("Has raw URL", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.raw_url).to.exist;
});
```

---

## 🔑 Environment Variables

### **Postman Environment: BTI Production**

```json
{
  "base_url": "https://telegram-bti-bot-637190449180.europe-west1.run.app",
  "job_id": "",
  "workitem_id": "",
  "result_url": "",
  "last_workitem_id": ""
}
```

### **Postman Environment: BTI Local**

```json
{
  "base_url": "http://localhost:8080",
  "job_id": "",
  "workitem_id": "",
  "result_url": "",
  "last_workitem_id": ""
}
```

---

## 📊 Сравнение режимов

| Параметр | Простой режим | С шаблоном BTI |
|----------|---------------|----------------|
| **USE_BTI_TEMPLATE** | false или не указан | true |
| **Activity** | BotBti.SimpleDWG2DWG+v1 | BotBti.BTI_INSERT_Basman+v1 |
| **Команда AutoCAD** | SAVEAS 2018 | INSERT template + SAVEAS 2018 |
| **Параметры WorkItem** | inputFile, resultFile | inputFile, templateFile, resultFile |
| **Время обработки** | 3-5 сек | 5-8 сек |
| **Размер результата** | ≈ размер входа | + 51 KB (шаблон) |
| **Шаблон URL** | - | https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg |

---

## 🔍 Логи и отладка

### **Проверка режима в логах:**

**Простой режим:**
```
📐 Режим: простая обработка DWG (без шаблона)
📤 Отправка WorkItem с activityId: BotBti.SimpleDWG2DWG+v1
```

**С типовым шаблоном BTI:**
```
🏛️ Режим: с типовым шаблоном BTI Basmanny
📄 Шаблон: https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
📤 Отправка WorkItem с activityId: BotBti.BTI_INSERT_Basman+v1
```

### **Команда для проверки логов:**

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=telegram-bti-bot AND textPayload:\"типовым шаблоном\"" --limit=10
```

---

## 🧪 Пример теста в Postman

### **Collection Runner Scenario:**

1. **Health Check** → Проверка что сервис работает
2. **Process DWG (Simple)** → Тест простого режима
3. **Process DWG with BTI Template** → Тест с шаблоном
4. **Queue Status** → Проверка очереди

### **Runner Settings:**

```
Iterations: 1
Delay: 5000ms (между запросами)
Data: test_files.csv (опционально)
```

### **test_files.csv:**

```csv
file_url,mode,chat_id
gs://btibot-processed/raw/test/file1.dwg,dwg2dwg,test_1
gs://btibot-processed/raw/test/file2.dwg,bti,test_2
gs://btibot-processed/raw/test/file3.dwg,bti,test_3
```

---

## 📋 Checklist перед тестированием

### **На сервере должно быть:**

- [x] `USE_BTI_TEMPLATE=true` (для режима с шаблоном)
- [x] Секреты настроены (FORGE_CLIENT_ID, FORGE_CLIENT_SECRET, etc.)
- [x] Шаблон доступен: https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
- [x] Activity существует: `BotBti.BTI_INSERT_Basman+v1`

### **В Postman:**

- [x] Environment настроен (base_url)
- [x] Collection импортирован
- [x] Tests настроены
- [x] Переменные окружения установлены

---

## 🎯 Быстрый старт в Postman

### **1. Создать новый Request:**

```
Name: Process DWG with BTI Template
Method: POST
URL: {{base_url}}/process-dwg
```

### **2. Headers:**

```
Content-Type: application/json
```

### **3. Body (raw JSON):**

```json
{
  "file_url": "https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg",
  "mode": "bti",
  "chat_id": "postman_test",
  "job_id": "test_{{$timestamp}}"
}
```

### **4. Send!**

**Ожидаемый результат:**

```json
{
  "success": true,
  "workitem_id": "abc123...",
  "result_url": "gs://btibot-processed/ready/postman_test/test_1234567890/bti_ready.dwg",
  "mode": "bti",
  "processing_time": 6.5
}
```

---

## 🔗 Полезные ссылки

- **Шаблон BTI:** https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
- **Service URL:** https://telegram-bti-bot-637190449180.europe-west1.run.app
- **Health:** https://telegram-bti-bot-637190449180.europe-west1.run.app/health
- **Status:** https://telegram-bti-bot-637190449180.europe-west1.run.app/status

---

## 📚 Документация

- `BTI_TEMPLATE_SETUP.md` - подробная настройка шаблона
- `TEMPLATE_CONFIGURATION_COMPLETE.md` - итоговая конфигурация
- `GOLD1_FINAL_SUMMARY.md` - общий обзор
- `SECRETS_QUICK_REFERENCE.md` - шпаргалка по секретам

---

**🎉 Готово! Используйте Postman для тестирования обработки DWG с типовым шаблоном BTI!**


