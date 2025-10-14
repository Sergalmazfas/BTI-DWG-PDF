# ✅ Типовой шаблон BTI - Настройка завершена

**Дата:** 2025-10-14  
**Ветка:** `release/gold1`  
**Статус:** ✅ Полностью настроено и готово к использованию

---

## 🎯 Что сделано

### **1. Загружен типовой шаблон BTI**

```
📄 Файл: bti_basmanny_template.dwg
📏 Размер: 51.2 KB
🔗 URL: https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
✅ Доступ: Публичный (AllUsers:R)
```

### **2. Настроены Activities**

| Activity | Описание | Шаблон |
|----------|----------|--------|
| **BotBti.BTI_INSERT_Basman+v1** | Вставка типового шаблона БТИ | ✅ Да |
| **BotBti.SimpleDWG2DWG+v1** | Простая обработка DWG | ❌ Нет |

### **3. Создана конфигурация**

**Файлы:**
- ✅ `bti_template_config.py` - конфигурация режимов
- ✅ `forge_client.py` - обновлен для поддержки шаблона
- ✅ `app.py` - добавлена переменная окружения `USE_BTI_TEMPLATE`
- ✅ `test_bti_template.py` - тестовый скрипт
- ✅ `BTI_TEMPLATE_SETUP.md` - документация

---

## 🔧 Как использовать

### **Вариант 1: Переменная окружения (рекомендуется)**

```bash
# При деплое в Cloud Run
gcloud run deploy telegram-bti-bot \
  --source . \
  --region europe-west1 \
  --set-env-vars="USE_BTI_TEMPLATE=true"  # ← Включить типовой шаблон
```

### **Вариант 2: Изменить конфигурацию**

В файле `bti_template_config.py`:

```python
BTI_MODE = "template"  # Включить режим с шаблоном
```

### **Вариант 3: Программно в коде**

```python
from forge_client import ForgeClient

client = ForgeClient()

# С типовым шаблоном BTI
workitem = client.submit_workitem(input_url, output_url, use_template=True)

# Без шаблона (по умолчанию)
workitem = client.submit_workitem(input_url, output_url, use_template=False)
```

---

## 🧪 Тестирование

### **Запуск тестов:**

```bash
# Полный тест с шаблоном и без
venv/bin/python test_bti_template.py
```

### **Ожидаемый результат:**

```
✅ С типовым шаблоном BTI: PASS
✅ Простой режим (без шаблона): PASS
🎉 Все тесты пройдены успешно!
```

---

## 📊 Сравнение режимов

| Параметр | Простой | С шаблоном BTI |
|----------|---------|----------------|
| **Activity** | SimpleDWG2DWG+v1 | BTI_INSERT_Basman+v1 |
| **Команда** | SAVEAS 2018 | INSERT + SAVEAS 2018 |
| **Параметры** | inputFile, resultFile | inputFile, templateFile, resultFile |
| **Время** | 3-5 сек | 5-8 сек |
| **Размер результата** | ≈ входной файл | + 51 KB (шаблон) |
| **Содержимое** | Только входной DWG | Входной DWG + BTI шаблон в точке 0,0,0 |

---

## 🚀 Деплой с типовым шаблоном

### **Команда деплоя:**

```bash
cd /Users/seregaboss/BTI-DWG-PDF-1

gcloud run deploy telegram-bti-bot \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=talkhint,GCS_BUCKET=btibot-processed,AUTO_PDF=false,JOB_TIMEOUT_SEC=900,USE_BTI_TEMPLATE=true" \
  --set-secrets="FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,BOT_TOKEN=BOT_TOKEN:latest,FORGE_SERVICE_KEY=FORGE_SERVICE_KEY:latest" \
  --cpu=1 \
  --memory=2Gi \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=80
```

### **Переменные окружения:**

```bash
GOOGLE_CLOUD_PROJECT=talkhint
GCS_BUCKET=btibot-processed
AUTO_PDF=false
JOB_TIMEOUT_SEC=900
USE_BTI_TEMPLATE=true          # ← Включить типовой шаблон BTI
```

---

## 🔍 Проверка работы

### **1. Проверить логи:**

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=telegram-bti-bot AND textPayload:\"типовым шаблоном\"" --limit=10
```

### **Должно быть в логах:**

```
🏛️ Режим: с типовым шаблоном BTI Basmanny
📄 Шаблон: https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
📤 Отправка WorkItem с activityId: BotBti.BTI_INSERT_Basman+v1
```

### **2. Проверить результат:**

```bash
# Скачать результат из GCS
gsutil ls gs://btibot-processed/ready/*/*/bti_ready.dwg

# Скачать и открыть в AutoCAD
gsutil cp gs://btibot-processed/ready/.../bti_ready.dwg ./result.dwg
```

**В AutoCAD должно быть:**
- Исходный чертеж
- Вставленный блок типового шаблона БТИ в точке 0,0,0

---

## 📁 Структура проекта

```
BTI-DWG-PDF-1/
├── bti_template_config.py          # ✅ Конфигурация шаблона
├── forge_client.py                 # ✅ Обновлен (use_template)
├── app.py                          # ✅ Обновлен (USE_BTI_TEMPLATE)
├── test_bti_template.py            # ✅ Тесты
│
├── BTI_TEMPLATE_SETUP.md           # ✅ Документация
├── TEMPLATE_CONFIGURATION_COMPLETE.md  # ✅ Этот файл
│
└── GCS: btibot-processed/
    └── templates/
        └── bti_basmanny_template.dwg  # ✅ Типовой шаблон
```

---

## ⚙️ Технические детали

### **Activity BotBti.BTI_INSERT_Basman+v1:**

```json
{
  "id": "BotBti.BTI_INSERT_Basman+v1",
  "commandLine": [
    "$(engine.path)\\accoreconsole.exe /i \"$(args[inputFile].path)\" /s \"$(settings[script].path)\""
  ],
  "engine": "Autodesk.AutoCAD+25_1",
  "parameters": {
    "inputFile": {"verb": "get", "description": "Input DWG file"},
    "templateFile": {"verb": "get", "description": "BTI Basmanny Template"},
    "resultFile": {"verb": "put", "description": "Output DWG with template"}
  },
  "settings": {
    "script": {
      "value": "_INSERT\n$(args[templateFile].path)\n0,0,0\n1\n1\n0\n_SAVEAS\n2018\nresult.dwg\n\n_QUIT\n"
    }
  }
}
```

### **Команда AutoCAD:**

```lisp
_INSERT                              ; Вставить блок
$(args[templateFile].path)           ; Путь к шаблону
0,0,0                               ; Точка вставки (X,Y,Z)
1                                   ; X масштаб
1                                   ; Y масштаб
0                                   ; Угол поворота
_SAVEAS                             ; Сохранить как
2018                                ; Формат AutoCAD 2018
result.dwg                          ; Имя файла
_QUIT                               ; Выход
```

---

## ✅ Итог

### **Готово к использованию:**

1. ✅ Типовой шаблон BTI загружен в GCS
2. ✅ Activity настроен и протестирован
3. ✅ Код обновлен для поддержки шаблона
4. ✅ Переменная окружения `USE_BTI_TEMPLATE` добавлена
5. ✅ Тестовый скрипт создан
6. ✅ Документация готова

### **Для активации:**

```bash
# Установить переменную окружения при деплое
--set-env-vars="USE_BTI_TEMPLATE=true"
```

### **Для отключения:**

```bash
# Убрать переменную или установить в false
--set-env-vars="USE_BTI_TEMPLATE=false"
```

---

## 📚 Документация

| Файл | Описание |
|------|----------|
| `BTI_TEMPLATE_SETUP.md` | Подробная настройка и использование |
| `TEMPLATE_CONFIGURATION_COMPLETE.md` | Этот файл - итоговый отчет |
| `SECRETS_QUICK_REFERENCE.md` | Шпаргалка по секретам |
| `GOLD1_SECRETS_CONFIG.md` | Полная конфигурация |

---

## 🎉 Заключение

**Типовой шаблон BTI полностью настроен и готов к продакшену!**

🏛️ **Шаблон:** https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg  
🔧 **Activity:** BotBti.BTI_INSERT_Basman+v1  
⚙️ **Режим:** Управляется через `USE_BTI_TEMPLATE=true/false`  
✅ **Статус:** Production Ready


