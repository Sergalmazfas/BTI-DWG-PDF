# 🏷️ ИНСТРУКЦИЯ: Создание alias v1 через APS Web UI

## 🎯 Цель

Создать alias `v1` для Activity `SimpleDWG2DWG_NoTemplate` чтобы bot мог использовать её для обработки DWG.

---

## 📍 ПОШАГОВАЯ ИНСТРУКЦИЯ

### **Шаг 1: Вход в APS Dashboard**

1. Открыть: **https://aps.autodesk.com**
2. Login (используйте аккаунт с Client ID: `3x1uGjtFaeakCfYIx7Vr...`)
3. My Apps → Выбрать ваше приложение
4. Design Automation → **AutoCAD**

---

### **Шаг 2: Найти Activity**

1. В левом меню: **Activities**
2. В списке найти: **SimpleDWG2DWG_NoTemplate**
3. Статус должен быть: **Active** или **Available**
4. Version: **1**

---

### **Шаг 3: Создать Alias**

1. Click на Activity **SimpleDWG2DWG_NoTemplate**
2. Перейти на вкладку: **Aliases**
3. Click кнопку: **"Create Alias"** или **"+"**

4. Заполнить форму:
   ```
   Alias ID: v1
   Version: 1
   Description: Production version for bot
   ```

5. Click: **"Create"** или **"Save"**

---

### **Шаг 4: Проверка**

**После создания должно появиться:**
```
Alias: v1
Points to: SimpleDWG2DWG_NoTemplate version 1
Status: Active
```

**Полный ID для использования:**
```
3x1uGjtFaeakCfYIx7Vr6xdIYUocCkAtZb1AskqIgN2FVfMo.SimpleDWG2DWG_NoTemplate+v1
```

---

### **Шаг 5: Проверка через API**

**После создания alias в Web UI, проверить через curl:**

```bash
# Получить токен
python3 << 'EOF'
import subprocess, requests
def get_secret(n):
    return subprocess.run(f"gcloud secrets versions access latest --secret={n} --project=talkhint".split(), capture_output=True, text=True).stdout.strip()

client_id = get_secret("FORGE_CLIENT_ID")
client_secret = get_secret("FORGE_CLIENT_SECRET")

r = requests.post("https://developer.api.autodesk.com/authentication/v2/token",
    data={"client_id":client_id,"client_secret":client_secret,"grant_type":"client_credentials","scope":"code:all"})
print(f"export ACCESS_TOKEN={r.json()['access_token']}")
print(f"export CLIENT_ID={client_id}")
EOF

# Проверить что alias работает
curl -X POST "https://developer.api.autodesk.com/da/us-east/v3/workitems" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"activityId\": \"$CLIENT_ID.SimpleDWG2DWG_NoTemplate+v1\",
    \"arguments\": {
      \"inputFile\": {\"url\": \"https://storage.googleapis.com/btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg\"},
      \"resultFile\": {\"url\": \"https://storage.googleapis.com/btibot-processed/processed/test_alias_v1.dwg\", \"verb\": \"put\"}
    }
  }"
```

**Ожидаемый результат:**
```json
{
  "id": "abc123...",
  "status": "pending",
  "activityId": "...SimpleDWG2DWG_NoTemplate+v1"
}
```

**Если получили `200 OK` и WorkItem ID → ALIAS РАБОТАЕТ! ✅**

---

## 🚀 Шаг 6: Деплой обновленного бота

**После создания alias:**

```bash
# Деплоим бота с SimpleDWG2DWG_NoTemplate+v1
gcloud run deploy telegram-bot-commands \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=talkhint,GCS_BUCKET=btibot-processed,AUTO_PDF=false \
  --set-secrets FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,BOT_TOKEN=BOT_TOKEN:latest \
  --cpu 1 --memory 1Gi --timeout 300 \
  --min-instances 0 --max-instances 10
```

---

## 🧪 Шаг 7: Тестирование через бота

```bash
# Создать тестовый job
cat > /tmp/test_with_alias.json << 'EOF'
{
  "job_id": "test_alias_v1_bot",
  "chat_id": "5265534096",
  "dwg_url": "gs://btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg",
  "auto_pdf": false,
  "created_at": "2025-10-07T16:40:00Z",
  "job_type": "bti_dwg",
  "filename": "Plan_test.dwg"
}
EOF

gcloud storage cp /tmp/test_with_alias.json gs://btibot-queue/queue/test_alias_v1_bot.json

# Подождать 30 сек или запустить вручную
curl -X POST https://telegram-bot-commands-637190449180.europe-west1.run.app/process-queue
```

**Проверить логи:**
```bash
gcloud logging read "resource.labels.service_name=telegram-bot-commands AND textPayload:\"test_alias_v1_bot\"" --limit=20
```

---

## ✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

### **Логи должны показать:**
```
INFO:forge_client:📤 Отправка WorkItem с activityId: ...SimpleDWG2DWG_NoTemplate+v1
INFO:forge_client:🚀 WorkItem запущен: <workitem_id>
INFO:forge_client:✅ WorkItem status: success
INFO:__main__:🏁 Готово! DWG обработан через Autodesk APS!
```

### **В GCS появится:**
```
gs://btibot-processed/ready/5265534096/test_alias_v1_bot/bti_ready.dwg
```

### **Пользователь получит:**
```
🏁 Готово! DWG обработан!
📥 Скачать: <ссылка>
```

### **В панели APS:**
```
Usage > 0 ✅
Processing hours > 0 ✅
```

---

## 🎉 ПОСЛЕ УСПЕШНОГО ТЕСТА

**Можно будет:**
1. ✅ Добавить шаблон BTI Template.dwt
2. ✅ Создать AppBundle с шаблоном
3. ✅ Обновить Activity
4. ✅ Полноценная BTI обработка

**НО СНАЧАЛА - ПРОВЕРИМ ЧТО БАЗОВАЯ СИСТЕМА РАБОТАЕТ! 🎯**

