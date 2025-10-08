# 🎯 Простая DWG→DWG обработка БЕЗ шаблона

## Цель

Протестировать Autodesk APS с минимальной Activity - просто открыть DWG и сохранить обратно.  
**БЕЗ шаблона, БЕЗ AppBundle, БЕЗ сложной логики.**

---

## ✅ Используем стандартную команду AutoCAD

### **Вместо AppBundle используем простой script:**

```
Activity: SimpleDWG2DWG
CommandLine: $(engine.path)\accoreconsole.exe /i "$(args[inputFile].path)" /s "_QSAVE\n_QUIT\n"
```

**Что делает:**
1. Открывает input.dwg
2. Выполняет команду QSAVE (быстрое сохранение)
3. Выполняет команду QUIT (выход)
4. Результат: output.dwg (копия исходного файла)

---

## 📝 Activity JSON (БЕЗ AppBundle)

```json
{
  "id": "SimpleDWG2DWG_NoTemplate",
  "commandLine": [
    "$(engine.path)\\accoreconsole.exe /i \"$(args[inputFile].path)\" /s \"_QSAVE\\n_QUIT\\n\""
  ],
  "engine": "Autodesk.AutoCAD+25_1",
  "parameters": {
    "inputFile": {
      "verb": "get",
      "localName": "input.dwg",
      "description": "Input DWG file"
    },
    "resultFile": {
      "verb": "put",
      "localName": "result.dwg",
      "description": "Output DWG file"
    }
  },
  "description": "Simple DWG passthrough without template"
}
```

**НИКАКОГО AppBundle! НИКАКОГО шаблона! Просто проверка что система работает.**

---

## 🚀 Как создать через API

```python
import requests
import subprocess

def get_secret(name):
    cmd = f"gcloud secrets versions access latest --secret={name} --project=talkhint"
    return subprocess.run(cmd.split(), capture_output=True, text=True).stdout.strip()

# Get credentials
client_id = get_secret("FORGE_CLIENT_ID")
client_secret = get_secret("FORGE_CLIENT_SECRET")

# Get token
auth_response = requests.post(
    "https://developer.api.autodesk.com/authentication/v2/token",
    data={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
)
access_token = auth_response.json()["access_token"]

# Create Activity (БЕЗ AppBundle!)
activity_data = {
    "id": f"{client_id}.SimpleDWG2DWG_NoTemplate",
    "commandLine": [
        "$(engine.path)\\accoreconsole.exe /i \"$(args[inputFile].path)\" /s \"_QSAVE\\n_QUIT\\n\""
    ],
    "engine": "Autodesk.AutoCAD+25_1",
    "parameters": {
        "inputFile": {
            "verb": "get",
            "localName": "input.dwg",
            "description": "Input DWG"
        },
        "resultFile": {
            "verb": "put",
            "localName": "result.dwg",
            "description": "Output DWG"
        }
    },
    "description": "Simple DWG passthrough no template"
}

response = requests.post(
    "https://developer.api.autodesk.com/da/us-east/v3/activities",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    json=activity_data
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

---

## 🧪 Тестирование

### **Создать WorkItem:**
```python
workitem_data = {
    "activityId": f"{client_id}.SimpleDWG2DWG_NoTemplate+1",
    "arguments": {
        "inputFile": {
            "url": "https://storage.googleapis.com/btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg"
        },
        "resultFile": {
            "url": "https://storage.googleapis.com/btibot-processed/processed/test_no_template.dwg",
            "verb": "put"
        }
    }
}
```

---

## ✅ Преимущества подхода БЕЗ шаблона

- ✅ Не нужна компиляция .NET
- ✅ Не нужен AppBundle
- ✅ Не нужна Windows машина
- ✅ Можно создать через API
- ✅ Работает сразу
- ✅ Проверяет что APS вообще работает

**После проверки - можно добавить шаблон позже!**

---

## 🎯 РЕКОМЕНДАЦИЯ

**Сначала протестировать БЕЗ шаблона:**
1. Создать SimpleDWG2DWG_NoTemplate Activity
2. Проверить что WorkItem = success
3. Проверить что результат загружается в GCS
4. Убедиться что Usage > 0

**Потом добавить шаблон:**
1. Когда базовая система работает
2. Создать AppBundle с шаблоном
3. Обновить Activity
4. Протестировать с шаблоном

**Идем пошагово - сначала самое простое! 🎯**

