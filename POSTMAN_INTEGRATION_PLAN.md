# 📮 План интеграции с aps-tutorial-postman

## 🎯 Что полезно из репозитория Sergalmazfas/aps-tutorial-postman

---

## ✅ ЧТО СОЗДАНО

### **1. Автоматический тест (аналог Postman):**
```
✅ test_aps_full_pipeline.py
   - Выполняет все шаги из Postman коллекции
   - Тестирует полный цикл DWG → APS → DWG
   - Не требует UI, полностью автоматический
```

### **2. Чек-лист для Postman:**
```
✅ CURSOR_APS_POSTMAN_CHECKLIST.md
   - Пошаговые инструкции для Postman
   - Все запросы с примерами
   - Проверки на каждом шаге
```

---

## 📊 ДВА СПОСОБА ТЕСТИРОВАНИЯ

### **СПОСОБ A: Через Postman (ручной)**

**Преимущества:**
- ✅ Визуальный интерфейс
- ✅ Легко отлаживать
- ✅ Можно изменять параметры на лету
- ✅ Сохранение истории запросов

**Инструкция:**
```
1. Установить Postman
2. Импортировать коллекцию из aps-tutorial-postman
3. Настроить Environment (CLIENT_ID, SECRET)
4. Выполнить запросы по порядку
5. Проверить результаты
```

**См.:** `CURSOR_APS_POSTMAN_CHECKLIST.md`

---

### **СПОСОБ B: Через Python скрипт (автоматический)**

**Преимущества:**
- ✅ Полностью автоматический
- ✅ CI/CD friendly
- ✅ Repeatable
- ✅ Можно запускать в Cloud Build

**Запуск:**
```bash
python3 test_aps_full_pipeline.py
```

**Что делает:**
```
1. Получает access token ✅
2. Проверяет/создает bucket ✅
3. Загружает DWG в bucket ✅
4. Проверяет существование Activity ✅
5. Создает WorkItem ✅
6. Проверяет статус (polling) ✅
7. Выводит результат ✅
```

---

## 🔧 РЕКОМЕНДУЕМЫЙ WORKFLOW

### **ДЛЯ ПЕРВОГО РАЗА (через Postman):**

```
1. Установить Postman
2. Импортировать DA4ACAD collection
3. Настроить credentials
4. Пройти все шаги вручную
5. Убедиться что WorkItem = success
6. Понять как работает API
```

**Время:** 30-40 минут  
**Результат:** Понимание API + проверка что все работает

---

### **ДЛЯ АВТОМАТИЗАЦИИ (через Python):**

```
1. Запустить test_aps_full_pipeline.py
2. Проверить что все шаги проходят
3. Интегрировать в CI/CD
4. Использовать для regression testing
```

**Время:** 5 минут  
**Результат:** Автоматическая проверка pipeline

---

## 🎯 ПРЕДЛОЖЕНИЯ ДЛЯ НАШЕГО ПРОЕКТА

### **1. Health Check Endpoint**

**Добавить в `app.py`:**
```python
@app.route('/health/aps', methods=['GET'])
def aps_health():
    """Проверяет статус APS интеграции"""
    try:
        token = forge_client.get_access_token()
        activity_exists = check_activity_exists(token)
        
        return jsonify({
            "status": "OK" if activity_exists else "DEGRADED",
            "activity": "BTI_DWG2DWG+v1",
            "exists": activity_exists,
            "mode": "aps" if activity_exists else "fallback"
        })
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)}), 500
```

**Применение:**
- Cloud Monitoring alerts
- Uptime checks
- Dashboard статус

---

### **2. Автоматическая синхронизация AppBundle**

**Создать:** `forge_auto_sync.py`

**Функции:**
```python
def sync_appbundle_from_gcs():
    """
    1. Проверяет gs://btibot-processed/system/appbundles/BTI_TemplateAppBundle.bundle.zip
    2. Если файл обновлен → загружает новую версию в APS
    3. Обновляет alias на новую версию
    4. Уведомляет в Telegram
    """
```

**Триггер:**
```yaml
# Cloud Build trigger on GCS change
# cloudbuild_appbundle_sync.yaml
steps:
  - name: 'python:3.11'
    entrypoint: 'python3'
    args: ['forge_auto_sync.py']
```

---

### **3. Webhook для мгновенных уведомлений**

**Добавить endpoint:**
```python
@app.route('/forge/callback', methods=['POST'])
def forge_callback():
    """Autodesk вызывает этот URL при завершении WorkItem"""
    data = request.json
    
    workitem_id = data.get('id')
    status = data.get('status')
    job_id = data.get('context', {}).get('job_id')  # Передаем в WorkItem
    
    if status == 'success':
        # Отправить результат пользователю
        notify_user_success(job_id)
    else:
        # Fallback или уведомление об ошибке
        notify_user_failure(job_id, status)
    
    return jsonify({"status": "OK"})
```

**Обновить WorkItem creation:**
```python
body = {
    "activityId": f"{self.client_id}.BTI_DWG2DWG+v1",
    "arguments": {...},
    "callback": "https://telegram-bot-commands.../forge/callback",  # ← Webhook
    "context": {"job_id": job_id}  # Передаем контекст
}
```

---

### **4. Детальное логирование ошибок**

**Обновить `forge_client.py`:**
```python
def get_workitem_report(self, workitem_id):
    """Получает детальный отчет об ошибке"""
    status_response = self.check_status(workitem_id)
    
    if status_response.get('reportUrl'):
        report_response = requests.get(status_response['reportUrl'])
        return report_response.text
    
    return None

# Использование в wait_for_completion:
if status in ['failed', ...]:
    report = self.get_workitem_report(workitem_id)
    logger.error(f"📋 Детальный report:\n{report}")
```

---

## 🚀 ПЛАН ДЕЙСТВИЙ

### **СЕЙЧАС (для теста):**

**Вариант 1: Postman (рекомендуется для первого раза)**
```bash
# Следовать CURSOR_APS_POSTMAN_CHECKLIST.md
# Выполнить все шаги вручную
# Понять как работает API
```

**Вариант 2: Автоматический скрипт**
```bash
# Запустить полный тест
python3 test_aps_full_pipeline.py

# Проверить результат
echo $?  # 0 = success, 1 = failure
```

---

### **ПОТОМ (автоматизация):**

1. **Health checks:**
   ```bash
   # Добавить /health/aps endpoint
   # Настроить Cloud Monitoring alerts
   ```

2. **Auto-sync:**
   ```bash
   # Создать forge_auto_sync.py
   # Настроить Cloud Build trigger
   ```

3. **Webhooks:**
   ```bash
   # Добавить /forge/callback endpoint
   # Обновить WorkItem creation
   ```

4. **Detailed errors:**
   ```bash
   # Добавить get_workitem_report()
   # Логировать в Cloud Logging
   # Отправлять админу в Telegram
   ```

---

## 📋 ИТОГОВЫЕ РЕКОМЕНДАЦИИ

### **Из aps-tutorial-postman берем:**

| Что | Зачем | Приоритет |
|-----|-------|-----------|
| DA4ACAD Collection | Ручное тестирование API | 🔴 Высокий |
| Workflow примеры | Понимание API flow | 🔴 Высокий |
| Error handling patterns | Robustness | 🟡 Средний |
| Webhook integration | Performance | 🟢 Низкий |
| Auto-sync примеры | CI/CD | 🟢 Низкий |

---

### **Для нашего проекта создано:**

- ✅ `CURSOR_APS_POSTMAN_CHECKLIST.md` - пошаговый чек-лист
- ✅ `test_aps_full_pipeline.py` - автоматический тест
- ✅ Все необходимые инструкции

---

## 🎉 ЗАКЛЮЧЕНИЕ

**aps-tutorial-postman очень полезен для:**
- ✅ Понимания API workflow
- ✅ Ручного тестирования
- ✅ Отладки параметров
- ✅ Примеров автоматизации

**Мы создали:**
- ✅ Python аналог Postman requests
- ✅ Автоматический тест pipeline
- ✅ Чек-лист для ручной проверки

**Следующий шаг:**
- Запустить `python3 test_aps_full_pipeline.py`
- Или пройти чек-лист в Postman вручную
- Убедиться что APS работает
- Интегрировать в production

**Все готово для тестирования! 🚀**

