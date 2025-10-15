# 📮 Postman - Быстрый старт с типовым шаблоном BTI

## 🎯 Base URL

```
https://telegram-bti-bot-637190449180.europe-west1.run.app
```

---

## 📋 Основные запросы

### **1. Health Check**

```http
GET /health
```

**Response:**
```json
{"status": "OK"}
```

---

### **2. Process DWG с типовым шаблоном BTI**

```http
POST /process-dwg
Content-Type: application/json
```

**Body:**
```json
{
  "file_url": "gs://btibot-processed/raw/test/input.dwg",
  "mode": "bti",
  "chat_id": "postman_test",
  "job_id": "test_{{$timestamp}}"
}
```

**⚠️ Important:** На сервере должно быть `USE_BTI_TEMPLATE=true`

**Response:**
```json
{
  "success": true,
  "workitem_id": "abc123...",
  "result_url": "gs://btibot-processed/ready/.../bti_ready.dwg",
  "mode": "bti",
  "processing_time": 6.5
}
```

---

### **3. Process DWG простой режим (без шаблона)**

```http
POST /process-dwg
Content-Type: application/json
```

**Body:**
```json
{
  "file_url": "gs://btibot-processed/raw/test/input.dwg",
  "mode": "dwg2dwg",
  "chat_id": "postman_test"
}
```

---

## 🔧 Как работает с шаблоном

```
USE_BTI_TEMPLATE=true
↓
Activity: BotBti.BTI_INSERT_Basman+v1
↓
Загружается шаблон:
https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
↓
Шаблон вставляется в DWG (точка 0,0,0)
↓
Сохранение в AutoCAD 2018
```

---

## 🧪 Быстрый тест

### **В Postman:**

1. **Создать Request:**
   - Method: `POST`
   - URL: `{{base_url}}/process-dwg`

2. **Headers:**
   ```
   Content-Type: application/json
   ```

3. **Body (raw JSON):**
   ```json
   {
     "file_url": "https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg",
     "mode": "bti",
     "chat_id": "postman_test",
     "job_id": "test_{{$timestamp}}"
   }
   ```

4. **Send!**

**Ожидаемый результат:**
```json
{
  "success": true,
  "workitem_id": "...",
  "processing_time": 5-8 сек
}
```

---

## 📊 Сравнение режимов

| Параметр | Простой | С шаблоном BTI |
|----------|---------|----------------|
| `USE_BTI_TEMPLATE` | false | true |
| Activity | SimpleDWG2DWG+v1 | BTI_INSERT_Basman+v1 |
| Время | 3-5 сек | 5-8 сек |
| Результат | DWG | DWG + шаблон BTI |

---

## ✅ Checklist

- [ ] Сервер запущен
- [ ] `USE_BTI_TEMPLATE=true` установлено
- [ ] Шаблон доступен: https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
- [ ] Postman Environment настроен
- [ ] Тестовый файл готов

---

📚 **Полная документация:** `POSTMAN_BTI_TEMPLATE_GUIDE.md`


