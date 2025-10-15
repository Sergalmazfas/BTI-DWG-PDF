# 🔧 Обновление AppBundle через Postman

## Проблема
API возвращает ошибку `"Cannot parse id"` при попытке создать версию через Python.

## ✅ Решение: Использовать Postman

### 1️⃣ Получить токен

```http
POST https://developer.api.autodesk.com/authentication/v2/token
Content-Type: application/x-www-form-urlencoded

client_id={{FORGE_CLIENT_ID}}
client_secret={{FORGE_CLIENT_SECRET}}
grant_type=client_credentials
scope=code:all
```

Ответ:
```json
{
  "access_token": "eyJhbGc...",
  "expires_in": 3599
}
```

### 2️⃣ Создать новую версию AppBundle

```http
POST https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin/versions
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "engine": "Autodesk.AutoCAD+25_1",
  "description": "BTI with BTI_AUTO_APPLY.lsp autorun"
}
```

Ответ:
```json
{
  "uploadParameters": {
    "endpointURL": "https://...",
    "formData": {...}
  },
  "version": 3,
  "id": "BotBti.BtiPlugin"
}
```

### 3️⃣ Загрузить ZIP файл

Используй данные из `uploadParameters`:

```http
POST {{endpointURL}}
Content-Type: multipart/form-data

// Добавь все поля из formData
// Затем добавь file: BtiPlugin_auto.zip
```

**Файл:** `/tmp/bti_auto/BtiPlugin_auto.zip` (54 KB)

### 4️⃣ Обновить alias $LATEST

```http
PATCH https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin/aliases/$LATEST
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "version": 3
}
```

### 5️⃣ Создать Activity BTI_AUTO_PROCESS

```http
POST https://developer.api.autodesk.com/da/us-east/v3/activities
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "id": "BotBti.BTI_AUTO_PROCESS",
  "engine": "Autodesk.AutoCAD+25_1",
  "appbundles": ["BotBti.BtiPlugin+$LATEST"],
  "commandLine": [
    "$(engine.path)\\\\accoreconsole.exe",
    "/i", "\"$(args[inputFile].path)\"",
    "/s", "\"$(appbundles[BtiPlugin].path)/Contents/BTI_AUTO_APPLY.lsp\"",
    "/o", "\"$(args[outputFile].path)\""
  ],
  "parameters": {
    "inputFile": {
      "localName": "input.dwg",
      "verb": "get",
      "description": "Input DWG file",
      "required": true
    },
    "outputFile": {
      "localName": "result.dwg",
      "verb": "put",
      "description": "Output BTI DWG file",
      "required": true
    }
  },
  "description": "BTI Auto Process - Automatic LISP execution"
}
```

### 6️⃣ Создать alias для Activity

```http
POST https://developer.api.autodesk.com/da/us-east/v3/activities/BotBti.BTI_AUTO_PROCESS/aliases
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "id": "$LATEST",
  "version": 1
}
```

---

## 🚀 Альтернатива: Через Web UI

1. Зайти на https://aps.autodesk.com
2. Design Automation → AppBundles
3. Найти `BotBti.BtiPlugin`
4. Create New Version
5. Загрузить `/tmp/bti_auto/BtiPlugin_auto.zip`
6. Update alias `$LATEST` на новую версию

Затем:
7. Design Automation → Activities
8. Create Activity: `BotBti.BTI_AUTO_PROCESS`
9. Использовать конфигурацию из `forge/activity_bti_auto.json`

---

## 📋 Credentials

```bash
# Получить из Secret Manager:
gcloud secrets versions access latest --secret=FORGE_CLIENT_ID --project=talkhint
gcloud secrets versions access latest --secret=FORGE_CLIENT_SECRET --project=talkhint
```

---

## ✅ После обновления APS

Задеплой Cloud Run:

```bash
gcloud run deploy telegram-bti-bot \
  --source . \
  --region us-central1 \
  --set-env-vars='BTI_PROCESSING_MODE=auto'
```

Готово! 🎉

