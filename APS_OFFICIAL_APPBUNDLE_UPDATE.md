# 📚 Официальная документация Autodesk APS - Обновление AppBundle

**Источник:** https://aps.autodesk.com/en/docs/design-automation/v3/reference/http/appbundles-id-versions-POST/

---

## 🔍 Проблема: "Cannot parse id"

Эта ошибка возникает когда:
1. ❌ Неправильный формат `id` в теле запроса
2. ❌ `id` содержит недопустимые символы
3. ❌ При создании версии НЕ НУЖНО указывать `id` в теле запроса!

---

## ✅ Правильный способ создания версии

### **Endpoint:**
```
POST https://developer.api.autodesk.com/da/us-east/v3/appbundles/{id}/versions
```

### **Path Parameter:**
- `{id}` - полный ID AppBundle, например: `BotBti.BtiPlugin`

### **Body (БЕЗ поля id!):**
```json
{
  "engine": "Autodesk.AutoCAD+25_1",
  "description": "BTI with auto-apply LISP script"
}
```

**⚠️ ВАЖНО:** В теле НЕ должно быть поля `id`!

---

## 📋 Полный процесс обновления

### Шаг 1: Получить токен

```bash
curl -X POST https://developer.api.autodesk.com/authentication/v2/token \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "grant_type=client_credentials" \
  -d "scope=code:all"
```

### Шаг 2: Проверить существующий AppBundle

```bash
curl -H "Authorization: Bearer TOKEN" \
  https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin
```

### Шаг 3: Создать новую версию

```bash
curl -X POST \
  https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin/versions \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "engine": "Autodesk.AutoCAD+25_1",
    "description": "BTI AUTO with BTI_AUTO_APPLY.lsp"
  }'
```

**Ответ:**
```json
{
  "uploadParameters": {
    "endpointURL": "https://dasprod-store.s3.amazonaws.com/",
    "formData": {
      "key": "apps/BotBti/BtiPlugin/...",
      "policy": "...",
      "x-amz-signature": "...",
      "x-amz-credential": "...",
      "x-amz-algorithm": "AWS4-HMAC-SHA256",
      "x-amz-date": "..."
    }
  },
  "version": 3,
  "id": "BotBti.BtiPlugin"
}
```

### Шаг 4: Загрузить ZIP на S3

```bash
# Используй формат multipart/form-data
# Сначала все поля из formData, затем file

curl -X POST "https://dasprod-store.s3.amazonaws.com/" \
  -F "key=apps/BotBti/BtiPlugin/..." \
  -F "policy=..." \
  -F "x-amz-signature=..." \
  -F "x-amz-credential=..." \
  -F "x-amz-algorithm=AWS4-HMAC-SHA256" \
  -F "x-amz-date=..." \
  -F "file=@/tmp/bti_auto/BtiPlugin_auto.zip"
```

### Шаг 5: Обновить alias $LATEST

```bash
curl -X PATCH \
  https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin/aliases/\$LATEST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version": 3}'
```

---

## 🔧 Если нужно удалить старые версии

### Просмотреть все версии:

```bash
curl -H "Authorization: Bearer TOKEN" \
  https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin/versions
```

### Удалить конкретную версию:

```bash
curl -X DELETE \
  -H "Authorization: Bearer TOKEN" \
  https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin/versions/2
```

### Удалить весь AppBundle:

```bash
curl -X DELETE \
  -H "Authorization: Bearer TOKEN" \
  https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin
```

**⚠️ Осторожно!** Это удалит все версии и aliases!

---

## 🐍 Python скрипт (исправленный)

```python
import requests, subprocess

def get_secret(n):
    r = subprocess.run(['gcloud', 'secrets', 'versions', 'access', 'latest', 
                       f'--secret={n}', '--project=talkhint'], 
                       capture_output=True, text=True)
    return r.stdout.strip()

# Token
cid = get_secret('FORGE_CLIENT_ID')
cs = get_secret('FORGE_CLIENT_SECRET')
tr = requests.post('https://developer.api.autodesk.com/authentication/v2/token',
    data={'client_id': cid, 'client_secret': cs, 
          'grant_type': 'client_credentials', 'scope': 'code:all'})
token = tr.json()['access_token']

# Создать версию (БЕЗ поля id в body!)
vr = requests.post(
    'https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin/versions',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    json={'engine': 'Autodesk.AutoCAD+25_1', 'description': 'BTI AUTO'}  # ← НЕТ id!
)

result = vr.json()
version = result['version']

# Загрузить ZIP
upload_params = result['uploadParameters']
with open('/tmp/bti_auto/BtiPlugin_auto.zip', 'rb') as f:
    requests.post(upload_params['endpointURL'], 
                 data=upload_params.get('formData', {}), 
                 files={'file': f})

# Обновить alias
requests.patch(
    'https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin/aliases/$LATEST',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    json={'version': version}
)

print(f"✅ AppBundle обновлен: BotBti.BtiPlugin+$LATEST (v{version})")
```

---

## 📝 Файл готов к загрузке:

```
/tmp/bti_auto/BtiPlugin_auto.zip (54 KB)

Содержит:
- BTI_AUTO_APPLY.lsp ⭐ (автозапуск!)
- BTI_APPLY.lsp
- BTI_APPLY_COLOR.lsp
- BTI_APPLY_OBJECTS.lsp
- BTI_ORTHO_ADJUST.lsp
- BTI_DIM_AREA.lsp
- BTI_CLEANUP.lsp
- bti_basmanny_template.dwg
- PackageContents.xml
```

---

## ✅ Проверка после обновления

```bash
curl -H "Authorization: Bearer TOKEN" \
  https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin
```

Должно показать новую версию с `BTI_AUTO_APPLY.lsp`!

