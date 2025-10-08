# 🔄 ПЕРЕСОЗДАНИЕ AUTODESK APS ПРИЛОЖЕНИЯ С NICKNAME

## ⚠️ ПРОБЛЕМА

**Текущее приложение:**
- ❌ Nickname НЕ установлен
- ❌ Уже имеет ресурсы (AppBundles, Activities)
- ❌ Не может получить nickname через API (`409 already has resources`)

**Результат:**
- ❌ Alias нельзя создать через API (`400 Cannot parse id`)
- ⏳ Требуется ручное создание alias через Web UI

---

## ✅ РЕШЕНИЕ: Пересоздать приложение с nickname

### **Почему это необходимо:**

1. **Nickname обязателен** для программного создания aliases через API
2. **Nickname можно установить** только при создании приложения или ДО создания ресурсов
3. **Текущее приложение** уже имеет ресурсы → nickname установить нельзя

### **Что даст пересоздание:**

✅ Полная автоматизация через API (без Web UI)  
✅ Alias создается программно  
✅ WorkItem запускается автоматически  
✅ Никаких ручных действий после initial setup

---

## 📋 ПОШАГОВАЯ ИНСТРУКЦИЯ (10 минут)

### **ШАГ 1: Удалить текущее приложение**

```
1. Открыть: https://aps.autodesk.com
2. Login в аккаунт
3. My Apps → Найти текущее приложение
4. Click "⋮" (три точки) → Delete
5. Подтвердить удаление
```

**Важно:** Это удалит все AppBundles и Activities, но они будут автоматически пересозданы скриптом.

---

### **ШАГ 2: Создать новое приложение**

```
1. My Apps → Create App

2. Заполнить форму:
   ┌─────────────────────────────────────────────────┐
   │ App Name: BTI Processor                         │
   │                                                 │
   │ App Type: ☑ Design Automation API              │
   │                                                 │
   │ Callback URL:                                   │
   │ https://telegram-bot-commands-637190449180.     │
   │ europe-west1.run.app/callback                   │
   │                                                 │
   │ Description:                                    │
   │ BTI DWG Template Processor                      │
   └─────────────────────────────────────────────────┘

3. Click "Create App"
```

---

### **ШАГ 3: ⚠️ КРИТИЧНО - Установить Nickname СРАЗУ**

**После создания приложения откроется страница с credentials.**

```
1. ⚠️  НЕ ЗАКРЫВАЙТЕ ЭТУ СТРАНИЦУ!
   Client Secret показывается только один раз!

2. Найти поле "Nickname" (обычно внизу страницы)

3. Ввести ТОЧНО: Forgecloudrun

4. Click "Save" или "Update"

5. Убедиться что nickname сохранен
```

**Проверка:**
```
✅ Поле "Nickname" должно показывать: Forgecloudrun
```

---

### **ШАГ 4: Скопировать новые credentials**

```
Client ID: [скопировать полностью]
Client Secret: [скопировать - показывается только один раз!]
```

**Сохраните в безопасное место!** Client Secret больше не будет показан.

---

### **ШАГ 5: Обновить Google Secret Manager**

**Замените `YOUR_CLIENT_ID` и `YOUR_CLIENT_SECRET` на скопированные значения:**

```bash
# Обновить Client ID
echo -n 'YOUR_CLIENT_ID' | gcloud secrets versions add FORGE_CLIENT_ID --data-file=- --project=talkhint

# Обновить Client Secret
echo -n 'YOUR_CLIENT_SECRET' | gcloud secrets versions add FORGE_CLIENT_SECRET --data-file=- --project=talkhint
```

**Пример:**
```bash
echo -n '4a2bXcYz9eDfG...' | gcloud secrets versions add FORGE_CLIENT_ID --data-file=- --project=talkhint
echo -n 'sK7mNpQrTvW...' | gcloud secrets versions add FORGE_CLIENT_SECRET --data-file=- --project=talkhint
```

---

### **ШАГ 6: Проверка настройки**

```bash
python3 << 'EOF'
import subprocess, requests

def get_secret(n):
    return subprocess.run(f"gcloud secrets versions access latest --secret={n} --project=talkhint".split(), capture_output=True, text=True).stdout.strip()

client_id = get_secret("FORGE_CLIENT_ID")
client_secret = get_secret("FORGE_CLIENT_SECRET")

print(f"Client ID: {client_id[:30]}...")

# Get token
r = requests.post("https://developer.api.autodesk.com/authentication/v2/token",
    data={"client_id":client_id,"client_secret":client_secret,"grant_type":"client_credentials","scope":"code:all"})

if r.status_code == 200:
    token = r.json()["access_token"]
    print("✅ Авторизация успешна")
    
    # Check nickname
    me = requests.get("https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me",
        headers={"Authorization": f"Bearer {token}"})
    
    if me.status_code == 200:
        app_info = me.json()
        nickname = app_info.get("nickname") if isinstance(app_info, dict) else None
        print(f"✅ Nickname: {nickname}")
        
        if nickname == "Forgecloudrun":
            print("\n🎉 ВСЕ ГОТОВО! Nickname установлен правильно!")
            print("\n🚀 Запустите полную автоматизацию:")
            print("   python3 setup_bti_template.py")
        else:
            print(f"\n⚠️  Nickname неправильный или не установлен!")
            print(f"   Ожидается: 'Forgecloudrun'")
            print(f"   Получено: '{nickname}'")
            print("\n   Вернитесь в Web UI и установите nickname")
    else:
        print(f"❌ Ошибка проверки приложения: {me.status_code}")
        print(f"   {me.text}")
else:
    print(f"❌ Ошибка авторизации: {r.status_code}")
    print(f"   Проверьте что credentials скопированы правильно")
EOF
```

**Ожидаемый вывод:**
```
Client ID: 4a2bXcYz9eDfG...
✅ Авторизация успешна
✅ Nickname: Forgecloudrun

🎉 ВСЕ ГОТОВО! Nickname установлен правильно!

🚀 Запустите полную автоматизацию:
   python3 setup_bti_template.py
```

---

## 🚀 ПОСЛЕ УСПЕШНОЙ ПРОВЕРКИ

### **1. Запустить полную автоматизацию**

```bash
python3 setup_bti_template.py
```

**Ожидается:**
```
✅ AppBundle создан: BTI_Template+1
✅ ZIP загружен
✅ Activity создана: BTI_DWG2DWG+1
✅ Alias создан: v1  ← ТЕПЕРЬ БЕЗ ОШИБОК!
🚀 WorkItem запущен: <id>
🎉 УСПЕХ! WorkItem выполнен!
```

---

### **2. Тестирование**

```bash
python3 test_bti_workitem.py
```

**Проверяет:**
- ✅ Alias v1 существует
- ✅ WorkItem создается
- ✅ DWG обрабатывается
- ✅ Результат сохраняется в GCS

---

### **3. Обновить bot**

```python
# forge_client.py, строка ~119
"activityId": f"{self.client_id}.BTI_DWG2DWG+v1"
```

---

### **4. Deploy**

```bash
gcloud run deploy telegram-bot-commands \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=talkhint,GCS_BUCKET=btibot-processed,AUTO_PDF=false \
  --set-secrets FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,BOT_TOKEN=BOT_TOKEN:latest \
  --cpu 1 --memory 1Gi --timeout 300
```

---

### **5. Тест через Telegram**

```bash
# Создать job
cat > /tmp/test_new_app.json << 'EOF'
{
  "job_id": "test_new_app_with_nickname",
  "chat_id": "5265534096",
  "dwg_url": "gs://btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg",
  "auto_pdf": false,
  "created_at": "2025-10-07T19:00:00Z",
  "job_type": "bti_dwg",
  "filename": "Plan_test.dwg"
}
EOF

gcloud storage cp /tmp/test_new_app.json gs://btibot-queue/queue/test_new_app_with_nickname.json

# Запустить
curl -X POST https://telegram-bot-commands-637190449180.europe-west1.run.app/process-queue
```

---

## ✅ КРИТЕРИИ УСПЕХА

| Проверка | Ожидается | Команда |
|----------|-----------|---------|
| Nickname установлен | `Forgecloudrun` | См. Шаг 6 |
| AppBundle создан | `BTI_Template+1` | `setup_bti_template.py` |
| Activity создана | `BTI_DWG2DWG+1` | `setup_bti_template.py` |
| **Alias создан через API** | `v1` **БЕЗ ОШИБОК** | `setup_bti_template.py` |
| WorkItem успешен | `status: success` | `test_bti_workitem.py` |
| Bot работает | Файл в GCS + сообщение в Telegram | Manual test |

---

## ⚠️ ЧАСТЫЕ ОШИБКИ

### **1. Nickname не сохранился**

**Проблема:** После сохранения nickname поле пустое  
**Причина:** Возможно nickname уже занят другим приложением  
**Решение:** Попробуйте другой nickname (например, `ForgecloudrunBTI`)

---

### **2. Client Secret потерян**

**Проблема:** Закрыли страницу, не скопировав Client Secret  
**Решение:** 
```
1. В приложении: Settings → Generate New Secret
2. Скопировать новый secret
3. Обновить в Secret Manager
```

---

### **3. Alias все еще не создается**

**Проблема:** `400 Cannot parse id` даже после установки nickname  
**Проверка:**
```bash
# Убедитесь что nickname точно установлен
python3 -c "import subprocess, requests; ..." # См. Шаг 6
```

**Решение:**
- Убедитесь что nickname = `Forgecloudrun` (без опечаток)
- Подождите 5-10 минут (кеширование в APS)
- Перезапустите `setup_bti_template.py`

---

## 📊 TIMELINE

| Этап | Время | Действие |
|------|-------|----------|
| Удаление старого App | 1 мин | Web UI |
| Создание нового App | 2 мин | Web UI |
| Установка nickname | 1 мин | Web UI |
| Копирование credentials | 1 мин | Manual |
| Обновление Secret Manager | 2 мин | Terminal |
| Проверка | 1 мин | Script |
| Автоматизация | 2 мин | `setup_bti_template.py` |
| **ИТОГО** | **~10 мин** | |

---

## 🎯 РЕЗУЛЬТАТ

После выполнения всех шагов:

✅ Приложение с nickname `Forgecloudrun`  
✅ AppBundle + Activity созданы автоматически  
✅ **Alias создается через API БЕЗ ОШИБОК**  
✅ WorkItem работает end-to-end  
✅ Bot обрабатывает DWG через Autodesk APS  
✅ **100% автоматизация, никаких ручных действий в Web UI**

---

**Создано:** Cursor AI  
**Дата:** 2025-10-07  
**Цель:** Решение проблемы создания alias через API  
**Статус:** ⏳ Ожидает пересоздания приложения с nickname

