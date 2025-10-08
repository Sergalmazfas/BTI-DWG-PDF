# 🚀 ПОДКЛЮЧЕНИЕ FORGECLOUDRUN К AUTODESK APS

**Дата:** 2025-10-07  
**Задача:** Подключить новое приложение Forgecloudrun без шаблона (простая Activity)  
**Статус:** ✅ Credentials обновлены, ⏳ Ожидает установки nickname

---

## ✅ ВЫПОЛНЕНО

### **1. Новое приложение создано**

```
Client ID: JGxQP39dH2ajFnE9lm2UCChjvtkXS5...
Client Secret: [обновлен в Secret Manager]
Status: Active
Nickname: ❌ НЕ УСТАНОВЛЕН
```

### **2. Credentials обновлены в Google Secret Manager**

```bash
✅ FORGE_CLIENT_ID → новый Client ID
✅ FORGE_CLIENT_SECRET → новый Client Secret
✅ Авторизация работает
```

### **3. Скрипты автоматизации готовы**

| Файл | Назначение |
|------|------------|
| `setup_forgecloudrun_simple.py` | Полная автоматизация (Activity + Alias + Test) |
| `check_nickname_loop.sh` | Автопроверка nickname каждые 10 сек |

---

## ⏳ ПОСЛЕДНИЙ ШАГ: УСТАНОВИТЬ NICKNAME (1 МИНУТА)

### **Вручную через Web UI:**

```
1. Открыть: https://aps.autodesk.com

2. Login в аккаунт

3. My Apps → Выбрать ваше приложение

4. Найти поле "Nickname" 
   (может быть в Settings или внизу страницы)

5. Ввести ТОЧНО: Forgecloudrun

6. Click "Save" или "Update"

7. Убедиться что сохранилось
```

---

## 🚀 АВТОМАТИЗАЦИЯ ПОСЛЕ УСТАНОВКИ NICKNAME

### **Вариант 1: Автоматическая проверка (рекомендуется)**

Запустить скрипт, который будет проверять nickname каждые 10 сек:

```bash
./check_nickname_loop.sh
```

**Скрипт автоматически:**
- Проверяет nickname каждые 10 секунд
- Как только `Forgecloudrun` обнаружен → запускает полную автоматизацию
- Создает Activity + Alias + тестирует WorkItem
- Готовит к deploy

---

### **Вариант 2: Ручной запуск**

После установки nickname:

```bash
python3 setup_forgecloudrun_simple.py
```

**Выполнит:**

1. ✅ Проверка nickname
2. ✅ Создание Activity `SimpleDWG2DWG_NoTemplate`
3. ✅ Создание Alias `v1`
4. ✅ Тестирование WorkItem
5. ✅ Обновление `forge_client.py`
6. ✅ Инструкции по deploy

---

## 📊 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

### **Логи успешного выполнения:**

```
🚀 ПОДКЛЮЧЕНИЕ FORGECLOUDRUN К AUTODESK APS

📋 Получение credentials...
   Client ID: JGxQP39dH2ajFnE9lm2...
🔑 Получение access token...
   ✅ Token получен
🏷️  Проверка nickname...
   ✅ Nickname правильный: Forgecloudrun

═══════════════════════════════════════════════════════════════════
📐 ШАГ 1: Создание Activity SimpleDWG2DWG_NoTemplate
═══════════════════════════════════════════════════════════════════

✅ Activity создана:
   ID: JGxQP39dH2ajFnE9lm2UCChjvtkXS5Eb.SimpleDWG2DWG_NoTemplate
   Version: 1
   Engine: Autodesk.AutoCAD+25_1

═══════════════════════════════════════════════════════════════════
🏷️  ШАГ 2: Создание Alias v1
═══════════════════════════════════════════════════════════════════

✅ Alias создан/обновлен:
   Alias: v1
   Version: 1
   Full ID: ...SimpleDWG2DWG_NoTemplate+v1

═══════════════════════════════════════════════════════════════════
🧪 ШАГ 3: Тестирование WorkItem
═══════════════════════════════════════════════════════════════════

✅ WorkItem создан: <workitem_id>
   Status: pending

⏳ Ожидание завершения (max 2 мин)...
   [5s] Status: pending
   [10s] Status: inprogress
   [15s] Status: success

🎉 УСПЕХ! WorkItem выполнен!
   Результат: .../forgecloudrun_test.dwg

═══════════════════════════════════════════════════════════════════
🔧 ШАГ 4: Обновление forge_client.py
═══════════════════════════════════════════════════════════════════

   ✅ forge_client.py обновлен автоматически

═══════════════════════════════════════════════════════════════════
✅ ВСЕ ГОТОВО! FORGECLOUDRUN ПОДКЛЮЧЕН К APS
═══════════════════════════════════════════════════════════════════

📊 Созданные ресурсы:
   ✅ Activity: ...SimpleDWG2DWG_NoTemplate+1
   ✅ Alias: v1 → version 1
   ✅ WorkItem: <id> (success)

🚀 Следующие шаги:

1. Проверить forge_client.py:
   grep "activityId" forge_client.py

2. Deploy бота:
   gcloud run deploy telegram-bot-commands ...

3. Тест через Telegram

🎉 ГОТОВО К PRODUCTION!
```

---

## 🔧 DEPLOY ПОСЛЕ УСПЕШНОЙ АВТОМАТИЗАЦИИ

### **1. Проверить forge_client.py**

```bash
grep "activityId" forge_client.py
```

**Должно быть:**
```python
"activityId": "JGxQP39dH2ajFnE9lm2UCChjvtkXS5Eb.SimpleDWG2DWG_NoTemplate+v1"
```

---

### **2. Deploy бота**

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

### **3. Тест через Telegram**

```bash
# Создать тестовый job
cat > /tmp/test_forgecloudrun.json << 'EOF'
{
  "job_id": "test_forgecloudrun_final",
  "chat_id": "5265534096",
  "dwg_url": "gs://btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg",
  "auto_pdf": false,
  "created_at": "2025-10-07T20:00:00Z",
  "job_type": "bti_dwg",
  "filename": "Plan_test.dwg"
}
EOF

gcloud storage cp /tmp/test_forgecloudrun.json gs://btibot-queue/queue/test_forgecloudrun_final.json

# Запустить обработку
curl -X POST https://telegram-bot-commands-637190449180.europe-west1.run.app/process-queue

# Проверить логи
gcloud logging read "resource.labels.service_name=telegram-bot-commands AND textPayload:\"test_forgecloudrun_final\"" --limit=20
```

---

## ✅ КРИТЕРИИ УСПЕХА

| Проверка | Ожидается | Статус |
|----------|-----------|--------|
| Credentials обновлены | ✅ | ✅ Готово |
| **Nickname установлен** | `Forgecloudrun` | ⏳ **В процессе** |
| Activity создана | `SimpleDWG2DWG_NoTemplate+1` | ⏳ После nickname |
| Alias создан через API | `v1` БЕЗ ОШИБОК | ⏳ После nickname |
| WorkItem успешен | `status: success` | ⏳ После nickname |
| forge_client.py обновлен | Новый activityId | ⏳ После nickname |
| Bot deployed | Работает end-to-end | ⏳ После nickname |

---

## ⚠️ TROUBLESHOOTING

### **Nickname не сохраняется**

**Проблема:** После ввода nickname поле остается пустым  
**Решение:** 
- Попробуйте другой nickname (например, `ForgecloudrunBTI`)
- Убедитесь что нет других приложений с таким nickname

### **Alias не создается (400 Cannot parse id)**

**Проблема:** Даже после установки nickname  
**Проверка:**
```bash
python3 setup_forgecloudrun_simple.py
```

**Решение:**
- Убедитесь что nickname = `Forgecloudrun` (без опечаток)
- Подождите 5-10 минут (кеширование в APS)
- Перезапустите скрипт

### **WorkItem fails**

**Проблема:** WorkItem возвращает `failed`  
**Решение:**
- Проверить reportUrl в response
- Убедиться что входной DWG доступен
- Проверить что output URL корректный

---

## 📁 ФАЙЛЫ

```
BTI-DWG-PDF-1/
├── setup_forgecloudrun_simple.py    # Полная автоматизация
├── check_nickname_loop.sh           # Автопроверка nickname
├── FORGECLOUDRUN_SETUP.md          # Эта инструкция
└── forge_client.py                 # Будет обновлен автоматически
```

---

## 🎯 ТЕКУЩИЙ СТАТУС

**Прогресс:** 90% готово  
**Блокер:** Установка nickname через Web UI (1 мин)  
**ETA:** 5 мин после установки nickname

---

## 🚀 СЛЕДУЮЩИЕ ШАГИ

### **СЕЙЧАС:**

1. ✅ Открыть https://aps.autodesk.com
2. ✅ Установить nickname: `Forgecloudrun`
3. ✅ Запустить: `./check_nickname_loop.sh` или `python3 setup_forgecloudrun_simple.py`

### **ПОСЛЕ АВТОМАТИЗАЦИИ:**

1. ✅ Проверить `forge_client.py`
2. ✅ Deploy бота
3. ✅ Тест через Telegram
4. ✅ **PRODUCTION!**

---

**Создано:** Cursor AI  
**Дата:** 2025-10-07  
**Проект:** BTI-DWG-PDF-1 / Forgecloudrun Integration  
**Status:** ⏳ Waiting for nickname setup

