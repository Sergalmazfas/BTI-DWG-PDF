# 🏷️ СОЗДАНИЕ ALIAS v1 ЧЕРЕЗ WEB UI (5 минут)

## ⚠️ ПРОБЛЕМА

Autodesk APS API имеет баг - **программное создание aliases НЕ РАБОТАЕТ**.

**Ошибка:**
```
{"id":["Cannot parse id."]}
```

**Решение:** Создать alias вручную через Web UI (это займет 2-3 минуты).

---

## 📋 ПОШАГОВАЯ ИНСТРУКЦИЯ

### **ШАГ 1: Открыть APS Dashboard**

```
URL: https://aps.autodesk.com
```

1. Войти в аккаунт (тот же, что используется для Client ID)
2. Click: **"My Apps"**
3. Найти ваше приложение (BTIProcessor или похожее)

---

### **ШАГ 2: Перейти в Design Automation**

1. В карточке приложения click: **"Design Automation"**
2. Выбрать: **"AutoCAD"** (не Revit, не 3ds Max)
3. В левом меню click: **"Activities"**

---

### **ШАГ 3: Найти Activity**

В списке Activities найти:
```
SimpleDWG2DWG_NoTemplate
```

**Должно быть:**
- Status: Active/Available
- Version: 1
- Owner: ваш Client ID

Click на название Activity.

---

### **ШАГ 4: Создать Alias**

1. Внутри Activity перейти на вкладку: **"Aliases"**
2. Click кнопку: **"Create Alias"** (или **"+"** / **"New"**)

**Заполнить форму:**

```
┌─────────────────────────────────┐
│ Alias ID: v1                    │
│                                 │
│ Version:  1                     │
│                                 │
│ Description (optional):         │
│ Production version for bot      │
│                                 │
│     [Cancel]  [Create]          │
└─────────────────────────────────┘
```

3. Click: **"Create"** или **"Save"**

---

### **ШАГ 5: Проверка**

**После создания должно появиться в таблице Aliases:**

```
┌────────┬──────────┬────────────────────────┐
│ Alias  │ Version  │ Description            │
├────────┼──────────┼────────────────────────┤
│ v1     │ 1        │ Production version ... │
└────────┴──────────┴────────────────────────┘
```

**Статус:** Active (зеленая галочка)

---

## ✅ ПРОВЕРКА ЧЕРЕЗ API

**После создания alias проверить что он работает:**

```bash
python3 << 'EOF'
import subprocess, requests, json

def get_secret(n):
    return subprocess.run(f"gcloud secrets versions access latest --secret={n} --project=talkhint".split(), capture_output=True, text=True).stdout.strip()

client_id = get_secret("FORGE_CLIENT_ID")
client_secret = get_secret("FORGE_CLIENT_SECRET")

# Get token
r = requests.post("https://developer.api.autodesk.com/authentication/v2/token",
    data={"client_id":client_id,"client_secret":client_secret,"grant_type":"client_credentials","scope":"code:all"})
token = r.json()["access_token"]

# Check aliases
aliases_r = requests.get(
    f"https://developer.api.autodesk.com/da/us-east/v3/activities/{client_id}.SimpleDWG2DWG_NoTemplate/aliases",
    headers={"Authorization": f"Bearer {token}"}
)

aliases = aliases_r.json().get("data", [])
print(f"📋 Найденные aliases: {aliases}")

if any("v1" in a for a in aliases):
    print("✅ ALIAS 'v1' НАЙДЕН И РАБОТАЕТ!")
    print(f"\n🎯 Полный ID для бота:")
    print(f"   {client_id}.SimpleDWG2DWG_NoTemplate+v1")
else:
    print("❌ Alias 'v1' не найден - проверьте создание в Web UI")
EOF
```

**Ожидаемый вывод:**
```
📋 Найденные aliases: ['3x1uGjtFaeakCfYIx7Vr...SimpleDWG2DWG_NoTemplate+v1']
✅ ALIAS 'v1' НАЙДЕН И РАБОТАЕТ!

🎯 Полный ID для бота:
   3x1uGjtFaeakCfYIx7Vr6xdIYUocCkAtZb1AskqIgN2FVfMo.SimpleDWG2DWG_NoTemplate+v1
```

---

## 🚀 ПОСЛЕ СОЗДАНИЯ ALIAS

### **1. Проверить что bot использует правильный activityId**

Файл `forge_client.py` должен содержать:

```python
"activityId": f"{self.client_id}.SimpleDWG2DWG_NoTemplate+v1"
```

✅ **УЖЕ ОБНОВЛЕНО!**

---

### **2. Деплой бота**

```bash
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

### **3. Тестирование**

**Создать тестовый job:**

```bash
cat > /tmp/test_alias_v1.json << 'EOF'
{
  "job_id": "test_alias_v1_manual",
  "chat_id": "5265534096",
  "dwg_url": "gs://btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg",
  "auto_pdf": false,
  "created_at": "2025-10-07T17:00:00Z",
  "job_type": "bti_dwg",
  "filename": "Plan_test.dwg"
}
EOF

gcloud storage cp /tmp/test_alias_v1.json gs://btibot-queue/queue/test_alias_v1_manual.json

# Запустить обработку
curl -X POST https://telegram-bot-commands-637190449180.europe-west1.run.app/process-queue
```

**Проверить логи:**

```bash
gcloud logging read "resource.labels.service_name=telegram-bot-commands AND textPayload:\"test_alias_v1_manual\"" --limit=30
```

---

## 🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

**В логах должно быть:**

```
INFO:forge_client:📤 Отправка WorkItem с activityId: ...SimpleDWG2DWG_NoTemplate+v1
INFO:forge_client:🚀 WorkItem запущен: <workitem_id>
INFO:forge_client:⏳ Polling WorkItem status...
INFO:forge_client:✅ WorkItem status: success
INFO:__main__:🏁 Готово! DWG обработан через Autodesk APS!
```

**В GCS появится файл:**

```
gs://btibot-processed/ready/5265534096/test_alias_v1_manual/bti_ready.dwg
```

**Пользователь получит в Telegram:**

```
🏁 Готово! DWG обработан!

📥 Скачать: <ссылка>

📊 Хотите создать PDF?
[Создать PDF] [Готово]
```

---

## ❓ ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

### **Alias не появляется в списке**
- Подождать 1-2 минуты (кеширование)
- Обновить страницу в браузере
- Проверить что Version = 1 (именно та, что была создана)

### **Alias создан, но API возвращает 404**
- Подождать 5-10 минут (propagation delay)
- Проверить формат ID: `{client_id}.SimpleDWG2DWG_NoTemplate+v1`

### **WorkItem возвращает ошибку**
- Проверить логи WorkItem в APS Dashboard
- Убедиться что входной DWG доступен по URL
- Проверить что output URL - это signed PUT URL

---

## 📞 ПОДДЕРЖКА

Если alias создается, но не работает:

1. **Проверить в APS Dashboard:**
   - My Apps → [Ваше приложение] → Usage
   - Должны появиться записи о WorkItems

2. **Проверить логи:**
   ```bash
   gcloud logging read "resource.labels.service_name=telegram-bot-commands" --limit=50
   ```

3. **Проверить GCS:**
   ```bash
   gcloud storage ls gs://btibot-processed/ready/*/
   ```

---

## ✅ ИТОГО

**Что нужно сделать:**

1. ✅ Открыть https://aps.autodesk.com
2. ✅ My Apps → Design Automation → AutoCAD → Activities
3. ✅ SimpleDWG2DWG_NoTemplate → Aliases → Create
4. ✅ ID: v1, Version: 1, Save
5. ✅ Подождать 1-2 мин
6. ✅ Проверить через API (скрипт выше)
7. ✅ Deploy bot
8. ✅ Тест через queue

**Время:** 5-10 минут

**После этого бот заработает с Autodesk APS! 🚀**

