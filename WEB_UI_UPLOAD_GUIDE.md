# 🌐 Инструкция: Загрузка AppBundle через APS Web UI

## 📍 URL для входа
```
https://aps.autodesk.com
```

---

## 🔐 Шаг 1: Вход в APS Dashboard

1. Открыть https://aps.autodesk.com
2. Login (используйте аккаунт с Client ID: `3x1uGjtFaeakCfYIx7Vr6xdIYUocCkAtZb1AskqIgN2FVfMo`)
3. My Apps → [Ваше приложение]
4. Design Automation → AutoCAD

---

## 📦 Шаг 2: Загрузка AppBundle

### **2.1. Открыть раздел AppBundles:**
```
Design Automation → AutoCAD → AppBundles
```

### **2.2. Create New AppBundle:**
- Click **"Create AppBundle"** или **"+"**

### **2.3. Заполнить форму:**
```
Name: BTI_TemplateAppBundle
Engine: Autodesk.AutoCAD+25_1
Description: BTI Template inserter for DWG to DWG processing
```

### **2.4. Upload ZIP:**
```
File: BTI_TemplateAppBundle.bundle.zip
(созданный на Windows через команды из BUILD.md)
```

### **2.5. Submit:**
- Click **"Create"** или **"Upload"**
- Дождаться завершения загрузки
- Статус должен стать: **"Active"** или **"Available"**

---

## 🏷️ Шаг 3: Создание Alias для AppBundle

### **3.1. В списке AppBundles:**
```
Найти: BTI_TemplateAppBundle
Status: Active
Version: 1
```

### **3.2. Create Alias:**
- Click на `BTI_TemplateAppBundle`
- Tab **"Aliases"** → **"Create Alias"**

### **3.3. Заполнить:**
```
Alias ID: v1
Version: 1
Description: Production version
```

### **3.4. Submit:**
- Click **"Create"**
- Проверка: должно появиться `BTI_TemplateAppBundle+v1` ✅

---

## ⚙️ Шаг 4: Создание Activity

### **4.1. Открыть раздел Activities:**
```
Design Automation → AutoCAD → Activities
```

### **4.2. Create New Activity:**
- Click **"Create Activity"** или **"+"**

### **4.3. Заполнить форму:**

**Basic Info:**
```
ID: BTI_DWG2DWG
Engine: Autodesk.AutoCAD+25_1
Description: BTI Template DWG to DWG processing (NO PDF)
```

**AppBundles:**
```
Select: BTI_TemplateAppBundle+v1
```

**Command Line:**
```
$(engine.path)\accoreconsole.exe /al "$(appbundles[BTI_TemplateAppBundle].path)" /i "$(args[inputFile].path)" /s "APPLYBTITEMPLATE\n"
```

**Parameters:**

1. **inputFile:**
   ```
   Name: inputFile
   Verb: get
   Local Name: input.dwg
   Description: Input DWG file
   Required: ✅
   ```

2. **resultFile:**
   ```
   Name: resultFile
   Verb: put
   Local Name: output.dwg
   Description: Output DWG file with BTI Template
   Required: ✅
   ```

### **4.4. Submit:**
- Click **"Create"**
- Статус должен стать: **"Active"**

---

## 🏷️ Шаг 5: Создание Alias для Activity

### **5.1. В списке Activities:**
```
Найти: BTI_DWG2DWG
Status: Active
Version: 1
```

### **5.2. Create Alias:**
- Click на `BTI_DWG2DWG`
- Tab **"Aliases"** → **"Create Alias"**

### **5.3. Заполнить:**
```
Alias ID: v1
Version: 1
Description: Production version
```

### **5.4. Submit:**
- Click **"Create"**
- Проверка: должно появиться `BTI_DWG2DWG+v1` ✅

---

## 🧪 Шаг 6: Тестирование через curl

### **6.1. Получить access token:**
```bash
python3 << 'EOF'
import subprocess
import requests

def get_secret(name):
    cmd = f"gcloud secrets versions access latest --secret={name} --project=talkhint"
    return subprocess.run(cmd.split(), capture_output=True, text=True).stdout.strip()

client_id = get_secret("FORGE_CLIENT_ID")
client_secret = get_secret("FORGE_CLIENT_SECRET")

response = requests.post(
    "https://developer.api.autodesk.com/authentication/v2/token",
    data={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
)

token = response.json()["access_token"]
print(f"ACCESS_TOKEN={token}")
print(f"CLIENT_ID={client_id}")
EOF
```

### **6.2. Создать тестовый WorkItem:**
```bash
# Скопировать ACCESS_TOKEN и CLIENT_ID из вывода выше

curl -X POST "https://developer.api.autodesk.com/da/us-east/v3/workitems" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "activityId": "'$CLIENT_ID'.BTI_DWG2DWG+v1",
    "arguments": {
      "inputFile": {
        "url": "https://storage.googleapis.com/btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg"
      },
      "resultFile": {
        "url": "https://storage.googleapis.com/btibot-processed/processed/manual_test_result.dwg",
        "verb": "put"
      }
    }
  }'
```

### **6.3. Проверить статус:**
```bash
# Скопировать WorkItem ID из ответа

curl -X GET "https://developer.api.autodesk.com/da/us-east/v3/workitems/$WORKITEM_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### **6.4. Ожидаемый результат:**
```json
{
  "status": "success",
  "id": "<workitem_id>",
  "activityId": "<CLIENT_ID>.BTI_DWG2DWG+v1"
}
```

---

## ✅ Шаг 7: Проверка в GCS

```bash
# Проверить появился ли результат
gcloud storage ls gs://btibot-processed/processed/

# Должен появиться файл:
# gs://btibot-processed/processed/manual_test_result.dwg
```

---

## 🤖 Шаг 8: Тестирование через Telegram Bot

### **8.1. Отправить DWG в бота:**
```
1. Открыть @YourBotName в Telegram
2. /start → /bti
3. Загрузить любой DWG файл
```

### **8.2. Проверить логи:**
```bash
gcloud logging read "resource.labels.service_name=telegram-bot-commands AND textPayload:\"BTI_DWG2DWG\"" --limit=10 --project=talkhint
```

### **8.3. Ожидаемые логи:**
```
INFO:forge_client:📤 Отправка WorkItem с activityId: <CLIENT_ID>.BTI_DWG2DWG+v1
INFO:forge_client:🚀 WorkItem запущен: <workitem_id>
INFO:forge_client:✅ WorkItem status: success
INFO:__main__:🏁 Готово! DWG обработан через Autodesk APS!
```

### **8.4. Пользователь получит:**
```
🏁 Готово! DWG обработан через Autodesk APS!
📥 Скачать: <ссылка на bti_ready.dwg>

Хотите создать PDF?
[📄 Да, сделать PDF] [👌 Нет, только DWG]
```

---

## 🎯 ФИНАЛЬНАЯ ПРОВЕРКА

### **После всех шагов проверить:**

- [ ] AppBundle загружен: `BTI_TemplateAppBundle+v1` ✅
- [ ] Activity создана: `BTI_DWG2DWG+v1` ✅
- [ ] Тестовый WorkItem: status = success ✅
- [ ] Результат в GCS: `output.dwg` существует ✅
- [ ] Bot отправил DWG пользователю ✅
- [ ] Usage > 0 в панели APS ✅

---

## 📊 После успешной загрузки

### **Обновить документацию:**
```bash
echo "✅ AppBundle активирован: BTI_TemplateAppBundle+v1" >> docs/TASK_DWG2DWG_FORGE.md
echo "✅ Activity создана: BTI_DWG2DWG+v1" >> docs/TASK_DWG2DWG_FORGE.md
echo "✅ Дата активации: $(date)" >> docs/TASK_DWG2DWG_FORGE.md
```

### **Создать alias 'prod' для стабильности:**
В Web UI:
```
AppBundle: Create Alias → id: prod → version: 1
Activity: Create Alias → id: prod → version: 1
```

### **Обновить код (опционально):**
```python
# Можно переключиться на prod alias
activityId = f"{self.client_id}.BTI_DWG2DWG+prod"
```

---

## 🎉 РЕЗУЛЬТАТ

**После выполнения всех шагов:**

✅ Bot автоматически переключится на Autodesk APS  
✅ DWG→DWG обработка в облаке с BTI Template  
✅ Usage > 0 в панели APS  
✅ Production-ready система  

**Это продакшн-уровень! 🚀**

