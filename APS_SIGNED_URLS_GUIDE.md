# 🔐 Руководство по Signed URLs для Autodesk APS

## ⚠️ ВАЖНО: Content-Type в Signed URLs

### ❌ **НЕ РАБОТАЕТ:**
```python
output_url = output_blob.generate_signed_url(
    version="v4",
    expiration=timedelta(hours=1),
    method="PUT",
    content_type="application/octet-stream"  # ← APS НЕ отправляет этот header!
)
```

**Ошибка:**
```
MalformedSecurityHeader - Header was included in signedheaders, 
but not in the request
```

### ✅ **РАБОТАЕТ:**
```python
output_url = output_blob.generate_signed_url(
    version="v4",
    expiration=timedelta(hours=1),
    method="PUT"  # БЕЗ content_type!
)
```

---

## 📋 Правила для Signed URLs в APS

### **Input URLs (GET):**

**Вариант 1: Публичный bucket**
```python
# Если bucket публичный - используем прямой URL
input_url = f"https://storage.googleapis.com/bucket-name/path/to/file.dwg"
```

**Вариант 2: Signed URL для приватного bucket**
```python
input_blob = bucket.blob("path/to/file.dwg")
input_url = input_blob.generate_signed_url(
    version="v4",
    expiration=timedelta(hours=1),
    method="GET"
)
```

### **Output URLs (PUT):**

**Всегда используем Signed URL БЕЗ content_type:**
```python
output_blob = bucket.blob("path/to/output.dwg")
output_url = output_blob.generate_signed_url(
    version="v4",
    expiration=timedelta(hours=1),
    method="PUT"  # ← Важно: БЕЗ content_type!
)
```

---

## 🔧 Service Account Credentials

### **Получение из Secret Manager:**
```python
from google.cloud import secretmanager
from google.oauth2 import service_account
from google.cloud import storage
from datetime import timedelta
import json

# 1. Получаем credentials из Secret Manager
secret_client = secretmanager.SecretManagerServiceClient()
secret_name = "projects/PROJECT_ID/secrets/FORGE_SERVICE_KEY/versions/latest"
secret_response = secret_client.access_secret_version(request={"name": secret_name})
sa_credentials_json = json.loads(secret_response.payload.data.decode("UTF-8"))

# 2. Создаем Service Account credentials
sa_credentials = service_account.Credentials.from_service_account_info(
    sa_credentials_json
)

# 3. Создаем GCS client с credentials
gcs_client = storage.Client(credentials=sa_credentials)
bucket = gcs_client.bucket("your-bucket-name")

# 4. Создаем signed URL
blob = bucket.blob("path/to/file.dwg")
signed_url = blob.generate_signed_url(
    version="v4",
    expiration=timedelta(hours=1),
    method="PUT"
)
```

---

## 🧪 Тестирование

### **Автоматический тест:**
```bash
source venv/bin/activate
python3 test_aps_full_pipeline.py
```

### **Проверка signed URL вручную:**
```bash
# Создать тестовый файл
echo "test" > test.txt

# Загрузить через signed URL
curl -X PUT -H "Content-Type: application/octet-stream" \
     --data-binary @test.txt \
     "SIGNED_URL"
```

---

## 📚 Референсы

### **Файлы с правильной реализацией:**
- ✅ `test_aps_full_pipeline.py` - автоматический тест
- ✅ `app.py` - production код (исправлен)
- ✅ `forge_controller.py` - контроллер для Forge

### **Документация:**
- [Google Cloud Storage Signed URLs](https://cloud.google.com/storage/docs/access-control/signed-urls)
- [Autodesk APS Design Automation](https://aps.autodesk.com/en/docs/design-automation/v3)

---

## 🚨 Частые ошибки

### **1. MalformedSecurityHeader**
**Причина:** Signed URL требует header, который APS не отправляет  
**Решение:** Убрать `content_type` из `generate_signed_url()`

### **2. 403 Forbidden**
**Причина:** Service Account не имеет прав на bucket  
**Решение:** Добавить роль `Storage Object Admin` для SA

### **3. Expired Signature**
**Причина:** Signed URL истек  
**Решение:** Увеличить `expiration` или создать новый URL

### **4. Wrong Method**
**Причина:** Signed URL создан для GET, но используется PUT  
**Решение:** Указать правильный `method` при создании

---

## ✅ Чек-лист для Production

- [ ] Service Account credentials в Secret Manager
- [ ] Signed URLs **БЕЗ** `content_type` для PUT
- [ ] Expiration ≥ 1 час для долгих WorkItems
- [ ] Bucket permissions настроены
- [ ] Тест `test_aps_full_pipeline.py` проходит
- [ ] Логирование signed URLs (первые 80 символов)
- [ ] Error handling для expired URLs

---

## 🔑 Ключевой вывод

> **При создании signed URLs для Autodesk APS:**
> - ✅ Input (GET): Можно публичный URL или signed GET
> - ✅ Output (PUT): Только signed PUT **БЕЗ content_type**
> - ❌ Никогда не указывать `content_type` в signed URL для APS!

**Протестировано и работает!** 🎉

