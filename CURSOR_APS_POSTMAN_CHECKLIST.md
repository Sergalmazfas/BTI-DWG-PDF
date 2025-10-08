# 📋 CURSOR CHECKLIST: APS POSTMAN TEST PIPELINE

## 🔹 Цель

Протестировать полный цикл Design Automation API (APS / Forge) для DWG-файла и убедиться, что AppBundle и Activity работают корректно **до интеграции в dwg-processor**.

---

## 🔸 Шаг 1. Установить окружение

### **1.1. Склонировать коллекцию:**
```bash
git clone https://github.com/Sergalmazfas/aps-tutorial-postman.git
cd aps-tutorial-postman
```

### **1.2. Импортировать в Postman:**
- Открыть Postman
- File → Import
- Выбрать: `APS Tutorial.postman_collection.json`
- Click "Import"

### **1.3. Создать Environment:**
- В Postman: Environments → Create New
- Name: `BTI Processor Environment`

### **1.4. Задать переменные:**
```json
{
  "APS_CLIENT_ID": "{{получить из Secret Manager}}",
  "APS_CLIENT_SECRET": "{{получить из Secret Manager}}",
  "BUCKET_KEY": "btibot-queue",
  "APPBUNDLE_NAME": "BTIProcessorApp",
  "ACTIVITY_NAME": "BTIProcessorActivity",
  "DWG_FILE": "Plan_2025-10-03_155019_export_2D_room_height.dwg"
}
```

**Команда для получения secrets:**
```bash
echo "APS_CLIENT_ID=$(gcloud secrets versions access latest --secret=FORGE_CLIENT_ID --project=talkhint)"
echo "APS_CLIENT_SECRET=$(gcloud secrets versions access latest --secret=FORGE_CLIENT_SECRET --project=talkhint)"
```

**Статус:** [ ] 1.1-1.4 выполнены

---

## 🔸 Шаг 2. Получить токен APS

### **2.1. Выполнить запрос:**
```
Postman Collection → Authentication → Get Access Token
```

**Request:**
```http
POST https://developer.api.autodesk.com/authentication/v2/token
Content-Type: application/x-www-form-urlencoded

client_id={{APS_CLIENT_ID}}
client_secret={{APS_CLIENT_SECRET}}
grant_type=client_credentials
scope=code:all data:read data:write bucket:create bucket:read
```

### **2.2. Проверить ответ:**
```json
{
  "access_token": "eyJhbGci...",
  "expires_in": 3599,
  "token_type": "Bearer"
}
```

### **2.3. Токен автоматически сохранится в Environment:**
```
{{access_token}} = eyJhbGci...
```

**Статус:** [ ] 2.1-2.3 выполнены

---

## 🔸 Шаг 3. Проверить и/или создать Bucket

### **3.1. Проверить существующие Buckets:**
```
Postman → Buckets → GET Buckets
```

**Request:**
```http
GET https://developer.api.autodesk.com/oss/v2/buckets
Authorization: Bearer {{access_token}}
```

### **3.2. Если `btibot-queue` не существует - создать:**
```
Postman → Buckets → Create Bucket
```

**Request:**
```http
POST https://developer.api.autodesk.com/oss/v2/buckets
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "bucketKey": "btibot-queue",
  "policyKey": "persistent"
}
```

**Статус:** [ ] 3.1-3.2 выполнены

---

## 🔸 Шаг 4. Загрузить DWG в Bucket

### **4.1. Подготовить DWG файл:**
```bash
# Скачать тестовый файл из GCS
gcloud storage cp "gs://btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg" /tmp/test_plan.dwg
```

### **4.2. Загрузить через Postman:**
```
Postman → Objects → PUT Object
```

**Request:**
```http
PUT https://developer.api.autodesk.com/oss/v2/buckets/{{BUCKET_KEY}}/objects/{{DWG_FILE}}
Authorization: Bearer {{access_token}}
Content-Type: application/octet-stream

Body → Binary → Select file: test_plan.dwg
```

### **4.3. Проверить ответ:**
```json
{
  "objectKey": "Plan_2025-10-03_155019_export_2D_room_height.dwg",
  "size": 15046,
  "location": "https://developer.api.autodesk.com/oss/v2/buckets/btibot-queue/objects/..."
}
```

**Статус:** [ ] 4.1-4.3 выполнены

---

## 🔸 Шаг 5. Создать или проверить AppBundle

### **5.1. Проверить существующие AppBundles:**
```
Postman → Design Automation → AppBundles → GET AppBundles
```

**Request:**
```http
GET https://developer.api.autodesk.com/da/us-east/v3/appbundles
Authorization: Bearer {{access_token}}
```

### **5.2. Если BTIProcessorApp нет - создать:**

**Option A: Использовать SimpleDWG2DWG (уже создана):**
```
Используем существующую Activity:
{{APS_CLIENT_ID}}.SimpleDWG2DWG+$LATEST
```

**Option B: Создать новый AppBundle:**
```
Postman → AppBundles → POST Create AppBundle
```

**Request:**
```http
POST https://developer.api.autodesk.com/da/us-east/v3/appbundles
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "id": "{{APS_CLIENT_ID}}.BTIProcessorApp",
  "engine": "Autodesk.AutoCAD+25_1",
  "description": "BTI Processor AppBundle"
}
```

### **5.3. Загрузить ZIP (если создали новый):**
```
Из response взять uploadParameters.endpointURL
Upload через POST multipart/form-data
```

**Статус:** [ ] 5.1-5.3 выполнены

---

## 🔸 Шаг 6. Создать Activity

### **6.1. Проверить существующие Activities:**
```
Postman → Activities → GET Activities
```

### **6.2. Создать BTI Activity:**
```
Postman → Activities → POST Create Activity
```

**Request:**
```http
POST https://developer.api.autodesk.com/da/us-east/v3/activities
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "id": "{{APS_CLIENT_ID}}.BTIProcessorActivity",
  "commandLine": [
    "$(engine.path)\\accoreconsole.exe /i \"$(args[inputFile].path)\" /s \"_QSAVE\\n_QUIT\\n\""
  ],
  "engine": "Autodesk.AutoCAD+25_1",
  "parameters": {
    "inputFile": {
      "verb": "get",
      "localName": "input.dwg"
    },
    "resultFile": {
      "verb": "put",
      "localName": "output.dwg"
    }
  },
  "description": "BTI DWG to DWG processor"
}
```

**Статус:** [ ] 6.1-6.2 выполнены

---

## 🔸 Шаг 7. Создать WorkItem

### **7.1. Подготовить URLs:**
```bash
# Input URL (из bucket)
INPUT_URL="https://developer.api.autodesk.com/oss/v2/buckets/btibot-queue/objects/Plan_2025-10-03_155019_export_2D_room_height.dwg"

# Output URL (signed для записи)
OUTPUT_URL="https://developer.api.autodesk.com/oss/v2/buckets/btibot-queue/objects/result_plan.dwg"
```

### **7.2. Создать WorkItem:**
```
Postman → WorkItems → POST Submit WorkItem
```

**Request:**
```http
POST https://developer.api.autodesk.com/da/us-east/v3/workitems
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "activityId": "{{APS_CLIENT_ID}}.BTIProcessorActivity+1",
  "arguments": {
    "inputFile": {
      "url": "{{INPUT_URL}}"
    },
    "resultFile": {
      "url": "{{OUTPUT_URL}}",
      "verb": "put"
    }
  }
}
```

### **7.3. Сохранить WorkItem ID:**
```json
Response:
{
  "id": "abc123def456...",
  "status": "pending"
}
```

**Статус:** [ ] 7.1-7.3 выполнены

---

## 🔸 Шаг 8. Проверить статус WorkItem

### **8.1. Polling статуса:**
```
Postman → WorkItems → GET WorkItem Status
```

**Request:**
```http
GET https://developer.api.autodesk.com/da/us-east/v3/workitems/{{WORKITEM_ID}}
Authorization: Bearer {{access_token}}
```

### **8.2. Ожидаемые статусы:**
```
pending → inprogress → success ✅

ИЛИ

pending → failed ❌ (проверить reportUrl)
```

### **8.3. При success:**
```json
{
  "id": "abc123...",
  "status": "success",
  "stats": {
    "timeQueued": "...",
    "timeFinished": "...",
    "bytesDownloaded": 15046,
    "bytesUploaded": 15200
  }
}
```

**Статус:** [ ] 8.1-8.3 выполнены

---

## 🔸 Шаг 9. Скачать результат

### **9.1. Получить результат из bucket:**
```
Postman → Objects → GET Object
```

**Request:**
```http
GET https://developer.api.autodesk.com/oss/v2/buckets/btibot-queue/objects/result_plan.dwg
Authorization: Bearer {{access_token}}
```

### **9.2. Сохранить файл:**
```
Postman → Send and Download
Save response as: result_plan.dwg
```

### **9.3. Проверить файл:**
```bash
# Проверить размер
ls -lh result_plan.dwg

# Открыть в AutoCAD (если доступен)
# Или загрузить в online DWG viewer
```

**Статус:** [ ] 9.1-9.3 выполнены

---

## 🔸 Шаг 10. Интеграция в наш проект

### **10.1. Обновить forge_client.py:**
```python
# Использовать проверенные параметры из Postman
body = {
    "activityId": f"{self.client_id}.BTIProcessorActivity+1",
    "arguments": {
        "inputFile": {"url": input_url},
        "resultFile": {"url": output_url, "verb": "put"}
    }
}
```

### **10.2. Тестировать через бота:**
```bash
# Создать job
python3 test_bti_workitem.py

# Проверить логи
gcloud logging read "resource.labels.service_name=telegram-bot-commands AND textPayload:\"WorkItem\"" --limit=10
```

**Статус:** [ ] 10.1-10.2 выполнены

---

## ✅ ФИНАЛЬНАЯ ПРОВЕРКА

### **После всех шагов проверить:**

- [ ] ✅ Access token получается успешно
- [ ] ✅ Bucket создан или существует
- [ ] ✅ DWG файл загружен в bucket
- [ ] ✅ AppBundle создан (или используем существующий)
- [ ] ✅ Activity создана
- [ ] ✅ WorkItem создан успешно
- [ ] ✅ WorkItem status = success
- [ ] ✅ Результат загружен из bucket
- [ ] ✅ Файл корректный (можно открыть)
- [ ] ✅ Usage > 0 в APS панели

---

## 🚨 Если ошибки

### **WorkItem failed:**
```
1. Получить reportUrl из response
2. GET reportUrl
3. Проверить ошибку в report.txt
4. Исправить параметры Activity
5. Retry WorkItem
```

### **Activity not found:**
```
1. Проверить правильность activityId
2. Проверить что alias существует
3. Создать alias через Web UI
4. Retry WorkItem
```

### **Failed upload/download:**
```
1. Проверить signed URLs
2. Проверить права на bucket
3. Проверить Content-Type headers
4. Retry с правильными URLs
```

---

## 📊 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

### **После прохождения всех шагов:**

```
✅ Postman коллекция работает
✅ Autodesk APS обрабатывает DWG
✅ WorkItems создаются и выполняются
✅ Результат скачивается
✅ Usage > 0 в панели

→ Готово к интеграции в dwg-processor!
```

---

## 🎯 ИНТЕГРАЦИЯ В НАШ ПРОЕКТ

### **После успешного Postman теста:**

**Обновить код:**
```python
# forge_client.py
# Использовать проверенные через Postman параметры
self.activity_id = f"{self.client_id}.BTIProcessorActivity+1"
```

**Тестировать:**
```bash
# Через бота
python3 test_bti_workitem.py

# Проверить что Usage > 0
# Проверить что результат в GCS
```

---

## 📝 ПРИМЕЧАНИЯ

- **Postman Test First:** Всегда тестируем через Postman перед интеграцией в код
- **Signed URLs:** Для output нужен signed URL с PUT методом
- **Bucket Policy:** Используем `persistent` для долгого хранения
- **Engine Version:** Autodesk.AutoCAD+25_1 (актуальная)

---

## 🔗 ССЫЛКИ

- [APS Dashboard](https://aps.autodesk.com)
- [Postman Collection](https://github.com/Sergalmazfas/aps-tutorial-postman)
- [Design Automation Docs](https://aps.autodesk.com/en/docs/design-automation/v3)

---

**Дата создания:** 2025-10-07  
**Статус:** Ready for Postman testing  
**Next step:** Выполнить шаги 1-10 в Postman

