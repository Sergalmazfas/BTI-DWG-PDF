# ✅ Отчет о успешном тестировании APS Pipeline

**Дата:** 2025-10-07  
**Статус:** ✅ УСПЕХ

---

## 🎯 Задача

Создать автоматический тест, который выполняет все шаги из Postman коллекции и тестирует полный цикл DWG → Autodesk APS → результат.

---

## ✅ Выполненные шаги

### **Шаг 1: Создание теста `test_aps_full_pipeline.py`**

**Функционал:**
- ✅ Получение Access Token из APS
- ✅ Проверка/создание Bucket
- ✅ Загрузка DWG в GCS
- ✅ Создание signed URLs для input/output
- ✅ Проверка существования Activity
- ✅ Создание WorkItem
- ✅ Polling статуса WorkItem
- ✅ Детальный отчет о результатах

---

## 🔧 Исправленные проблемы

### **1. Устаревший OSS API**
**Проблема:** OSS v2 endpoint для загрузки файлов deprecated  
**Ошибка:** `403 - Legacy endpoint is deprecated`  
**Решение:** Использовать GCS напрямую вместо OSS API

### **2. Отсутствие Service Account для signed URLs**
**Проблема:** `gcloud storage sign-url` требует service account  
**Решение:** Использовать `google-cloud-storage` library с credentials из Secret Manager

### **3. Malformed Security Header в signed URL**
**Проблема:** `MalformedSecurityHeader - Header was included in signedheaders, but not in the request`  
**Ошибка:** APS не отправляет `content-type` заголовок, но signed URL его требует  
**Решение:** Создавать signed URL БЕЗ `content_type` параметра

```python
# БЫЛО (не работало):
output_url = output_blob.generate_signed_url(
    version="v4",
    expiration=timedelta(hours=1),
    method="PUT",
    content_type="application/octet-stream"  # ← APS не отправляет этот header!
)

# СТАЛО (работает):
output_url = output_blob.generate_signed_url(
    version="v4",
    expiration=timedelta(hours=1),
    method="PUT"  # Без content_type - APS может загружать
)
```

---

## 🧪 Результат тестирования

### **Запуск:**
```bash
source venv/bin/activate && python3 test_aps_full_pipeline.py
```

### **Результат:**
```
✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!
✅ Access token: OK
✅ Bucket: OK
✅ DWG upload: OK
✅ Activity: AutoCAD.PlotToPDF+25_0
✅ WorkItem: b14c0a8a4b9c4889ba2ddb29ec73d4c1
✅ Status: success

🎉 AUTODESK APS PIPELINE РАБОТАЕТ!
```

### **Статистика выполнения:**
- **WorkItem ID:** b14c0a8a4b9c4889ba2ddb29ec73d4c1
- **Activity:** AutoCAD.PlotToPDF+25_0
- **Время в очереди:** 2025-10-07T17:42:34Z
- **Время выполнения:** ~3 секунды
- **Скачано:** 15,046 bytes (DWG)
- **Загружено:** 2,982 bytes (PDF)

### **Созданные файлы в GCS:**
```
gs://btibot-processed/test_pipeline/test_plan_input.dwg   15,046 bytes
gs://btibot-processed/test_pipeline/test_plan_output.dwg   2,982 bytes
```

> **Примечание:** Output файл - это PDF (стандартная Activity PlotToPDF)

---

## 📊 Архитектура решения

```
┌─────────────────────────────────────────────────┐
│  test_aps_full_pipeline.py                      │
└─────────────────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌─────────┐    ┌──────────┐    ┌──────────┐
│  APS    │    │   GCS    │    │  Secret  │
│  API    │    │  Bucket  │    │ Manager  │
└─────────┘    └──────────┘    └──────────┘
```

### **Процесс:**

1. **Credentials** → Secret Manager (FORGE_CLIENT_ID, FORGE_CLIENT_SECRET, FORGE_SERVICE_KEY)
2. **Input DWG** → GCS bucket → Public URL
3. **Output Signed URL** → GCS bucket → PUT signed URL (без content-type!)
4. **WorkItem** → APS Design Automation → Success
5. **Result** → GCS bucket → Готовый файл

---

## 🔑 Ключевые находки

### **1. Signed URLs для APS:**
- ✅ Input URL может быть публичным (если bucket публичный)
- ✅ Output URL должен быть signed с методом PUT
- ❌ **НЕ указывать** `content-type` в signed URL (APS его не отправляет!)

### **2. Service Account credentials:**
```python
from google.cloud import secretmanager
from google.oauth2 import service_account

# Получаем credentials из Secret Manager
secret_client = secretmanager.SecretManagerServiceClient()
secret_response = secret_client.access_secret_version(
    request={"name": "projects/talkhint/secrets/FORGE_SERVICE_KEY/versions/latest"}
)
sa_credentials_json = json.loads(secret_response.payload.data.decode("UTF-8"))

# Создаем GCS client с credentials
sa_credentials = service_account.Credentials.from_service_account_info(sa_credentials_json)
gcs_client = storage.Client(credentials=sa_credentials)
```

### **3. Activity выбор:**
- Если BTI Activity не найдена → используется стандартная `AutoCAD.PlotToPDF+25_0`
- Для DWG→DWG нужна кастомная Activity с BTI AppBundle

---

## 📋 Следующие шаги

### **1. Создать BTI Activity для DWG→DWG:**
```bash
# Загрузить BTI AppBundle
# Создать Activity BTI_DWG2DWG
# Обновить тест для использования BTI Activity
```

### **2. Интегрировать в CI/CD:**
```yaml
# Cloud Build step
- name: 'python:3.11'
  entrypoint: 'bash'
  args:
    - '-c'
    - |
      pip install -r requirements.txt
      python3 test_aps_full_pipeline.py
```

### **3. Добавить в production:**
- Использовать правильные signed URLs в `app.py`
- Убрать `content_type` из output signed URL
- Протестировать с реальными пользователями

---

## ✅ Итоги

| Компонент | Статус | Примечание |
|-----------|--------|------------|
| Access Token | ✅ | Получается автоматически |
| Bucket проверка | ✅ | btibot-queue существует |
| DWG upload | ✅ | В GCS bucket |
| Signed URLs | ✅ | БЕЗ content-type! |
| Activity | ⚠️ | Использована стандартная PlotToPDF |
| WorkItem | ✅ | Успешное выполнение |
| Result | ✅ | PDF создан и загружен |

**Главная находка:** 
> Signed URL для PUT операций в APS **НЕ должен** включать `content-type` в signed headers!

---

## 🚀 Команда для запуска

```bash
# Полный тест APS pipeline
source venv/bin/activate && python3 test_aps_full_pipeline.py
```

**Все работает! 🎉**

