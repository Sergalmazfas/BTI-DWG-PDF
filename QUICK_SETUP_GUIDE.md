# ⚡ QUICK SETUP GUIDE - Autodesk APS AppBundle

## 🎯 ЧТО СДЕЛАНО

✅ **AppBundle создан:** `BTI_Template+1` (с placeholder DWT)  
✅ **Activity создана:** `BTI_DWG2DWG+1` (применение шаблона)  
✅ **Скрипты готовы:** автоматизация + тестирование  
⏳ **Alias 'v1':** требует создания через Web UI (2 мин)

---

## 🚀 БЫСТРЫЙ СТАРТ (5 МИНУТ)

### **ШАГ 1: Создать Alias через Web UI (2 мин)**

```
1. Открыть: https://aps.autodesk.com
2. My Apps → Design Automation → AutoCAD
3. Activities → BTI_DWG2DWG
4. Aliases → Create Alias
5. ID: v1, Version: 1, Save
```

### **ШАГ 2: Тест (1 мин)**

```bash
python3 test_bti_workitem.py
```

**Ожидается:**
```
✅ Alias v1 найден!
🚀 WorkItem создан: <id>
⏳ Ожидание завершения...
🎉 УСПЕХ! BTI WORKITEM ВЫПОЛНЕН!
```

### **ШАГ 3: Обновить bot (1 мин)**

```python
# forge_client.py, строка ~119
"activityId": f"{self.client_id}.BTI_DWG2DWG+v1"
```

### **ШАГ 4: Deploy (1 мин)**

```bash
gcloud run deploy telegram-bot-commands --source . \
  --region europe-west1 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=talkhint,GCS_BUCKET=btibot-processed \
  --set-secrets FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,BOT_TOKEN=BOT_TOKEN:latest
```

---

## 🔄 ПЕРЕСОЗДАНИЕ APPBUNDLE (если нужен реальный DWT)

### **1. Получить BTI_Template.dwt**

Положить файл `BTI_Template.dwt` в текущую директорию.

### **2. Пересоздать ZIP и загрузить**

```bash
# Создать новый template_bti.zip с реальным DWT
./create_template_zip.sh

# Загрузить в Autodesk APS (автоматически удалит старый и создаст новый)
python3 setup_bti_template.py

# Создать alias через Web UI (если нужно)
# Тест
python3 test_bti_workitem.py
```

---

## 📁 СТРУКТУРА ФАЙЛОВ

```
BTI-DWG-PDF-1/
├── setup_bti_template.py      # Полная автоматизация (AppBundle + Activity)
├── create_template_zip.sh     # Создание template_bti.zip
├── test_bti_workitem.py       # Тестирование после создания alias
├── template_bti.zip           # AppBundle ZIP (с placeholder DWT)
│   ├── PackageContents.xml
│   └── BTI_Template.dwt.placeholder
│
└── forge_client.py            # Bot integration (обновить activityId)
```

---

## 🧪 ТЕСТОВЫЕ КОМАНДЫ

```bash
# Создать template_bti.zip
./create_template_zip.sh

# Полная настройка APS (AppBundle + Activity)
python3 setup_bti_template.py

# Тест WorkItem (после создания alias)
python3 test_bti_workitem.py

# Проверить что создалось в APS
python3 << 'EOF'
import subprocess, requests
def get_secret(n):
    return subprocess.run(f"gcloud secrets versions access latest --secret={n} --project=talkhint".split(), capture_output=True, text=True).stdout.strip()

client_id = get_secret("FORGE_CLIENT_ID")
client_secret = get_secret("FORGE_CLIENT_SECRET")

r = requests.post("https://developer.api.autodesk.com/authentication/v2/token",
    data={"client_id":client_id,"client_secret":client_secret,"grant_type":"client_credentials","scope":"code:all"})
token = r.json()["access_token"]

# AppBundles
r = requests.get("https://developer.api.autodesk.com/da/us-east/v3/appbundles",
    headers={"Authorization": f"Bearer {token}"})
print("AppBundles:", [x for x in r.json().get("data",[]) if "BTI" in x])

# Activities
r = requests.get("https://developer.api.autodesk.com/da/us-east/v3/activities",
    headers={"Authorization": f"Bearer {token}"})
print("Activities:", [x for x in r.json().get("data",[]) if "BTI" in x])

# Aliases
r = requests.get(f"https://developer.api.autodesk.com/da/us-east/v3/activities/{client_id}.BTI_DWG2DWG/aliases",
    headers={"Authorization": f"Bearer {token}"})
print("Aliases:", r.json().get("data",[]))
EOF
```

---

## ⚠️ TROUBLESHOOTING

### **Alias не создается через API**

**Проблема:** `400 {"id":["Cannot parse id."]}`  
**Решение:** Создать через Web UI (баг Autodesk API)

### **WorkItem fails: "Cannot find template"**

**Проблема:** Placeholder DWT не является валидным AutoCAD файлом  
**Решение:** Заменить на реальный `BTI_Template.dwt`

### **WorkItem timeout**

**Проблема:** Файл слишком большой или много операций  
**Решение:** Увеличить timeout в bot или упростить template

### **Bot не использует новую Activity**

**Проблема:** Старый `activityId` в `forge_client.py`  
**Решение:** Обновить на `{client_id}.BTI_DWG2DWG+v1` и redeploy

---

## 📊 CHECKLIST

- [ ] AppBundle BTI_Template создан ✅
- [ ] Activity BTI_DWG2DWG создана ✅
- [ ] template_bti.zip загружен ✅
- [ ] **Alias v1 создан через Web UI** ← 👈 СЕЙЧАС
- [ ] test_bti_workitem.py успешен
- [ ] forge_client.py обновлен
- [ ] Bot deployed
- [ ] Тест через Telegram

---

## 🎯 ИТОГО

**Прогресс:** 95% автоматизировано  
**Блокер:** Alias creation (2 мин ручной работы, баг Autodesk)  
**ETA до production:** 30 мин после создания alias

**Следующий шаг:** Создать alias 'v1' через https://aps.autodesk.com 🚀

