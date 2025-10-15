# 📮 Рекомендации из APS Tutorial Postman для нашего проекта

## 🎯 Что можно использовать из aps-tutorial-postman

Официальный репозиторий Autodesk содержит Postman коллекции для тестирования Design Automation API.  
**URL:** https://github.com/autodesk-platform-services/aps-tutorial-postman

---

## 📦 Полезные коллекции для нашего проекта

### **1. DA4ACAD (Design Automation for AutoCAD)**

**Что там есть:**
```
✅ Authentication workflow
✅ AppBundle registration
✅ AppBundle upload (signed URL)
✅ Activity creation
✅ WorkItem submission
✅ Status checking
✅ Result download
```

**Как использовать для BTI-Bot:**

#### **A. Тестирование нашего AppBundle:**
```
1. Import DA4ACAD collection в Postman
2. Настроить Environment:
   - client_id: {{FORGE_CLIENT_ID}}
   - client_secret: {{FORGE_CLIENT_SECRET}}
3. Выполнить последовательно:
   - 01. Authentication → получить access_token
   - 02. AppBundles → GET (проверить BTI_TemplateAppBundle)
   - 03. Activities → GET (проверить BTI_DWG2DWG)
   - 04. WorkItems → POST (создать тестовый WorkItem)
   - 05. WorkItems → GET (проверить status)
```

#### **B. Отладка наших WorkItems:**
```
Если WorkItem failed:
- Использовать Postman для GET /workitems/{id}
- Получить reportUrl
- Скачать report для детального анализа ошибки
```

---

## 🔧 Что можно взять для автоматизации

### **1. Скрипт автоматической регистрации AppBundle**

**Из примера Postman → Python скрипт:**

```python
# forge_appbundle_sync.py (новый файл)
import requests
import json

def register_appbundle(client_id, access_token, zip_path):
    """
    Регистрирует AppBundle через API
    Взято из aps-tutorial-postman/DA4ACAD
    """
    url = "https://developer.api.autodesk.com/da/us-east/v3/appbundles"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "id": f"{client_id}.BTI_TemplateAppBundle",
        "engine": "Autodesk.AutoCAD+25_1",
        "description": "BTI Template DWG processor"
    }
    
    # 1. Create AppBundle
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        upload_params = result.get('uploadParameters')
        
        # 2. Upload ZIP
        upload_url = upload_params.get('endpointURL')
        form_data = upload_params.get('formData', {})
        
        with open(zip_path, 'rb') as f:
            files = {'file': f}
            upload_response = requests.post(upload_url, data=form_data, files=files)
            
        return upload_response.status_code in [200, 201, 204]
    
    return False
```

**Применение:**
- ✅ Автоматическая загрузка AppBundle из CI/CD
- ✅ Обновление AppBundle при изменениях
- ✅ Не нужно заходить в Web UI каждый раз

---

### **2. Проверка статуса Activity**

**Из Postman коллекции:**

```python
def check_activity_status(client_id, access_token):
    """Проверяет что Activity активна и готова"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    activities = response.json().get('data', [])
    
    target = f"{client_id}.BTI_DWG2DWG+v1"
    return target in activities
```

**Применение:**
- ✅ Health check для Forge integration
- ✅ Автоматическая проверка перед созданием WorkItem
- ✅ Alerting если Activity удалена или неактивна

---

### **3. Получение детального report при ошибках**

**Из примеров Postman:**

```python
def get_workitem_report(workitem_id, access_token):
    """Получает детальный отчет о WorkItem"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    result = response.json()
    
    if result.get('status') in ['failed', 'failedInstructions', 'failedDownload', 'failedUpload']:
        report_url = result.get('reportUrl')
        if report_url:
            report_response = requests.get(report_url)
            return report_response.text
    
    return None
```

**Применение:**
- ✅ Детальная диагностика ошибок
- ✅ Логирование в Cloud Logging
- ✅ Отправка детальных ошибок в Telegram админу

---

### **4. Webhook notifications вместо polling**

**Из Postman examples:**

```python
# Вместо polling каждые 10 секунд:
def submit_workitem_with_webhook(input_url, output_url, callback_url):
    """Создает WorkItem с webhook уведомлением"""
    body = {
        "activityId": f"{client_id}.BTI_DWG2DWG+v1",
        "arguments": {
            "inputFile": {"url": input_url},
            "resultFile": {"url": output_url, "verb": "put"}
        },
        "callback": callback_url  # Autodesk вызовет этот URL при завершении
    }
```

**Применение:**
- ✅ Нет polling - меньше нагрузка
- ✅ Instant notification при завершении
- ✅ Можно использовать Cloud Run endpoint

---

## 🎯 ЧТО РЕАЛИЗОВАТЬ ДЛЯ НАШЕГО ПРОЕКТА

### **ПРИОРИТЕТ 1: Автоматическая загрузка AppBundle**

**Создать:** `forge_appbundle_sync.py`

**Функции:**
```python
- register_appbundle() - создает AppBundle через API
- upload_bundle_zip() - загружает ZIP
- create_alias() - создает alias v1
- check_appbundle_exists() - проверка перед загрузкой
```

**Применение:**
```bash
# Автоматическая загрузка после компиляции
python3 forge_appbundle_sync.py --zip BTI_TemplateAppBundle.bundle.zip
```

---

### **ПРИОРИТЕТ 2: Health check для Forge**

**Добавить в:** `app.py`

**Endpoint:**
```python
@app.route('/health/forge', methods=['GET'])
def forge_health():
    """Проверяет статус Forge интеграции"""
    try:
        # Проверка Activity
        activity_exists = check_activity_status(client_id, get_token())
        
        return jsonify({
            "status": "OK" if activity_exists else "DEGRADED",
            "activity": "BTI_DWG2DWG+v1",
            "exists": activity_exists,
            "fallback": "enabled"
        })
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)}), 500
```

**Применение:**
```bash
# Мониторинг Forge интеграции
curl https://telegram-bot-commands.../health/forge
```

---

### **ПРИОРИТЕТ 3: Детальные ошибки в Telegram**

**Обновить:** `forge_client.py`

**Добавить:**
```python
def wait_for_completion(self, workitem_id, timeout_minutes=5):
    # ... существующий код ...
    
    if status in ['failed', 'failedInstructions', 'failedDownload', 'failedUpload']:
        # Получить детальный report
        report = self.get_workitem_report(workitem_id)
        logger.error(f"📋 WorkItem report:\n{report}")
        
        # Отправить админу в Telegram
        if ADMIN_CHAT_ID:
            send_admin_notification(
                f"❌ WorkItem failed: {workitem_id}\n"
                f"Status: {status}\n"
                f"Report: {report[:500]}"
            )
```

---

### **ПРИОРИТЕТ 4: Webhook вместо polling**

**Создать endpoint:** `/forge/webhook`

```python
@app.route('/forge/webhook', methods=['POST'])
def forge_webhook():
    """Получает уведомления от Autodesk о завершении WorkItem"""
    data = request.json
    
    workitem_id = data.get('id')
    status = data.get('status')
    
    if status == 'success':
        # Обработать успешный результат
        process_forge_success(workitem_id)
    else:
        # Обработать ошибку
        process_forge_failure(workitem_id, status)
    
    return jsonify({"status": "OK"})
```

**Обновить WorkItem creation:**
```python
body = {
    "activityId": f"{self.client_id}.BTI_DWG2DWG+v1",
    "arguments": {...},
    "callback": "https://telegram-bot-commands.../forge/webhook"  # ← Webhook
}
```

---

## 📊 РЕКОМЕНДУЕМАЯ АРХИТЕКТУРА

### **С использованием примеров из Postman:**

```
┌─────────────────┐
│ Telegram Bot    │
└────────┬────────┘
         │ DWG upload
         ▼
┌─────────────────┐     ┌──────────────────┐
│ Cloud Run       │────▶│ Autodesk APS     │
│ forge_client.py │     │ BTI_DWG2DWG+v1   │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         │ ◄─────────────────────┘ Webhook
         │ (completion notify)
         ▼
┌─────────────────┐
│ GCS Storage     │
│ result.dwg      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User (Telegram) │
└─────────────────┘
```

---

## 🎯 ИТОГОВЫЕ РЕКОМЕНДАЦИИ

### **ЧТО ВЗЯТЬ ИЗ aps-tutorial-postman:**

1. **✅ Workflow для тестирования:**
   - Импортировать DA4ACAD collection
   - Тестировать наш AppBundle вручную
   - Отлаживать параметры Activity

2. **✅ Примеры error handling:**
   - Как обрабатывать failedUpload
   - Как получать reportUrl
   - Как retry при временных ошибках

3. **✅ Webhook integration:**
   - Заменить polling на webhooks
   - Instant notifications
   - Меньше нагрузка на API

4. **✅ Автоматическая синхронизация:**
   - Скрипт для upload AppBundle
   - Проверка версий
   - Auto-update при изменениях

---

## 🚀 СЛЕДУЮЩИЕ ШАГИ

### **Сейчас:**
1. Скомпилировать .NET проект на Windows
2. Загрузить AppBundle через Web UI
3. Создать Activity через Web UI
4. Протестировать

### **Потом (автоматизация):**
1. Создать `forge_appbundle_sync.py` (по примерам из Postman)
2. Добавить `/health/forge` endpoint
3. Добавить webhook `/forge/webhook`
4. Настроить auto-sync через CI/CD

---

## 📋 ПОЛЕЗНЫЕ ССЫЛКИ

**Официальные примеры:**
- [APS Tutorial Postman](https://github.com/autodesk-platform-services/aps-tutorial-postman)
- [DA4ACAD Collection](https://github.com/autodesk-platform-services/aps-tutorial-postman/tree/master/DA4ACAD)
- [Design Automation Docs](https://aps.autodesk.com/en/docs/design-automation/v3)

**Наши файлы:**
- `test_bti_workitem.py` - аналог Postman requests в Python
- `WEB_UI_UPLOAD_GUIDE.md` - ручная загрузка
- `BTI_APS_TASK_CHECKLIST.md` - пошаговый план

---

## 🎉 ЗАКЛЮЧЕНИЕ

**Из aps-tutorial-postman наиболее полезно:**

1. **DA4ACAD Postman Collection** - для ручного тестирования
2. **Workflow примеры** - для автоматизации upload
3. **Webhook pattern** - для замены polling
4. **Error handling** - для robustness

**Можем реализовать постепенно после загрузки базового AppBundle! 🎯**

