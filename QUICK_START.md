# ⚡ QUICK START - Запуск Autodesk APS для BTI Bot

## 🎯 ЧТО НУЖНО СДЕЛАТЬ (5 минут)

### **1. Создать alias в Autodesk Web UI**

```
https://aps.autodesk.com
→ My Apps
→ Design Automation
→ AutoCAD
→ Activities
→ SimpleDWG2DWG_NoTemplate
→ Aliases
→ Create: v1 → version 1
→ Save
```

### **2. Проверить что alias работает**

```bash
python3 << 'EOF'
import subprocess, requests
def get_secret(n):
    return subprocess.run(f"gcloud secrets versions access latest --secret={n} --project=talkhint".split(), capture_output=True, text=True).stdout.strip()

client_id = get_secret("FORGE_CLIENT_ID")
client_secret = get_secret("FORGE_CLIENT_SECRET")

r = requests.post("https://developer.api.autodesk.com/authentication/v2/token",
    data={"client_id":client_id,"client_secret":client_secret,"grant_type":"client_credentials","scope":"code:all"})
token = r.json()["access_token"]

aliases_r = requests.get(
    f"https://developer.api.autodesk.com/da/us-east/v3/activities/{client_id}.SimpleDWG2DWG_NoTemplate/aliases",
    headers={"Authorization": f"Bearer {token}"}
)

aliases = aliases_r.json().get("data", [])
if any("v1" in a for a in aliases):
    print("✅ ALIAS v1 РАБОТАЕТ!")
else:
    print("❌ Alias не найден - создайте в Web UI")
EOF
```

### **3. Deploy bot**

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

### **4. Тест**

```bash
# Создать job
cat > /tmp/test_v1.json << 'EOF'
{
  "job_id": "test_v1_quickstart",
  "chat_id": "5265534096",
  "dwg_url": "gs://btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg",
  "auto_pdf": false,
  "created_at": "2025-10-07T17:10:00Z",
  "job_type": "bti_dwg",
  "filename": "Plan_test.dwg"
}
EOF

gcloud storage cp /tmp/test_v1.json gs://btibot-queue/queue/test_v1_quickstart.json

# Запустить
curl -X POST https://telegram-bot-commands-637190449180.europe-west1.run.app/process-queue

# Логи
gcloud logging read "resource.labels.service_name=telegram-bot-commands AND textPayload:\"test_v1_quickstart\"" --limit=20
```

---

## ✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

**Логи:**
```
✅ WorkItem status: success
🏁 Готово! DWG обработан через Autodesk APS!
```

**GCS:**
```
gs://btibot-processed/ready/5265534096/test_v1_quickstart/bti_ready.dwg
```

**Telegram:**
```
🏁 Готово! DWG обработан!
📥 Скачать: <ссылка>
```

---

## 📚 ПОДРОБНЫЕ ИНСТРУКЦИИ

- **Создание alias:** `MANUAL_ALIAS_CREATION.md`
- **Web UI guide:** `CREATE_ALIAS_WEB_UI.md`
- **Activity info:** `SIMPLE_DWG2DWG_NO_TEMPLATE.md`

---

## 🔧 СТАТУС ИНТЕГРАЦИИ

- ✅ Activity `SimpleDWG2DWG_NoTemplate` создана (version 1)
- ⏳ Alias `v1` → нужно создать через Web UI (баг Autodesk API)
- ✅ Bot код обновлен для использования `+v1`
- ✅ forge_client.py готов
- ✅ Deployment готов

**Осталось:** Создать alias в Web UI (2 мин) → Deploy → Тест → ✅

