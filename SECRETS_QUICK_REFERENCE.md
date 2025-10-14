# 🔐 Шпаргалка по секретам - release/gold1

## ⚡ Быстрый доступ

### **Autodesk APS Credentials:**

```bash
Client ID:     m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4
Client Secret: tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW
Nickname:      BotBti
```

### **Activity ID (используется в коде):**

```
BotBti.SimpleDWG2DWG+v1
```

### **Где находятся секреты:**

```
Google Secret Manager (project: talkhint)
- FORGE_CLIENT_ID
- FORGE_CLIENT_SECRET  
- BOT_TOKEN
- FORGE_SERVICE_KEY
```

---

## 📋 Команды для проверки

### **Посмотреть секреты:**

```bash
# Список всех секретов
gcloud secrets list --project=talkhint

# Получить FORGE_CLIENT_ID
gcloud secrets versions access latest --secret="FORGE_CLIENT_ID" --project=talkhint

# Получить FORGE_CLIENT_SECRET
gcloud secrets versions access latest --secret="FORGE_CLIENT_SECRET" --project=talkhint
```

### **Проверить APS nickname:**

```bash
venv/bin/python setup_aps_nickname.py
```

### **Проверить Activity:**

```bash
venv/bin/python check_activity.py
```

---

## 🎯 Текущая конфигурация в forge_client.py

```python
# Строка 121
"activityId": "BotBti.SimpleDWG2DWG+v1"

# Параметры
"arguments": {
    "inputFile": {"url": input_url},
    "resultFile": {"url": output_url, "verb": "put"}
}
```

---

## ✅ Статус

- ✅ Client ID m6CK3... зарегистрирован для Design Automation API
- ✅ Nickname "BotBti" активен
- ✅ Activity BotBti.SimpleDWG2DWG+v1 существует и работает
- ✅ forge_client.py обновлен
- ✅ Все секреты в Secret Manager

---

Подробности смотри в: **GOLD1_SECRETS_CONFIG.md**

