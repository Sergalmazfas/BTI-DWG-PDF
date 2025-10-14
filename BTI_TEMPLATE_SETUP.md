# 🏛️ Настройка типового шаблона BTI

**Дата:** 2025-10-14  
**Ветка:** `release/gold1`  
**Статус:** ✅ Настроен и готов к использованию

---

## 📋 Что настроено

### **1. Типовой шаблон BTI Basmanny**

| Параметр | Значение |
|----------|----------|
| **Файл** | bti_basmanny_template.dwg |
| **Источник** | basmannyi_novyi_obmernyi.dwg |
| **URL** | https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg |
| **Размер** | 51.2 KB |
| **Доступ** | Публичный (AllUsers:R) |

### **2. Activity для вставки шаблона**

```
Activity ID: BotBti.BTI_INSERT_Basman+v1
Описание: Insert BTI Basmanny template (English URL, works!)
Engine: Autodesk.AutoCAD+25_1
```

### **3. Параметры WorkItem:**

```json
{
  "activityId": "BotBti.BTI_INSERT_Basman+v1",
  "arguments": {
    "inputFile": {"url": "<input_dwg_url>"},
    "templateFile": {"url": "https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg"},
    "resultFile": {"url": "<output_dwg_url>", "verb": "put"}
  }
}
```

---

## 🔧 Как работает

### **Команда AutoCAD (в Activity):**

```lisp
_INSERT
$(args[templateFile].path)
0,0,0    ; Точка вставки (0,0,0)
1        ; X scale
1        ; Y scale
0        ; Rotation angle
_SAVEAS
2018     ; AutoCAD 2018 format
result.dwg
_QUIT
```

### **Процесс обработки:**

1. 📥 **Загрузка** входного DWG (`inputFile`)
2. 📄 **Загрузка** шаблона BTI (`templateFile`)
3. 🔧 **Вставка** шаблона в точку 0,0,0
4. 💾 **Сохранение** результата в формате AutoCAD 2018
5. 📤 **Выгрузка** результата (`resultFile`)

---

## 💻 Использование в коде

### **1. Конфигурация (bti_template_config.py):**

```python
# URL типового шаблона
BTI_TEMPLATE_URL = "https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg"

# Activity IDs
BTI_TEMPLATE_ACTIVITY = "BotBti.BTI_INSERT_Basman+v1"  # С шаблоном
BTI_SIMPLE_ACTIVITY = "BotBti.SimpleDWG2DWG+v1"        # Без шаблона
```

### **2. Использование в forge_client.py:**

```python
# Простой режим (БЕЗ шаблона) - по умолчанию
workitem = forge_client.submit_workitem(input_url, output_url)

# С типовым шаблоном BTI
workitem = forge_client.submit_workitem(input_url, output_url, use_template=True)
```

### **3. Переменная окружения для режима:**

```bash
# В bti_template_config.py
BTI_MODE = "simple"    # Простой режим (по умолчанию)
BTI_MODE = "template"  # С типовым шаблоном BTI
```

---

## 🚀 Активация типового шаблона

### **Вариант 1: Через параметр функции**

```python
# В app.py, функция process_queue() или process_dwg()
# Добавить параметр use_template=True

workitem = forge_client.submit_workitem(
    input_url, 
    output_url, 
    use_template=True  # ← Включить типовой шаблон
)
```

### **Вариант 2: Через конфигурацию**

Изменить в `bti_template_config.py`:

```python
BTI_MODE = "template"  # Включить режим с шаблоном
```

И использовать:

```python
from bti_template_config import BTI_MODE

use_template = (BTI_MODE == "template")
workitem = forge_client.submit_workitem(input_url, output_url, use_template=use_template)
```

### **Вариант 3: Через переменную окружения**

```bash
# При деплое в Cloud Run
--set-env-vars="USE_BTI_TEMPLATE=true"
```

В коде:

```python
use_template = os.getenv('USE_BTI_TEMPLATE', 'false').lower() == 'true'
workitem = forge_client.submit_workitem(input_url, output_url, use_template=use_template)
```

---

## ✅ Доступные режимы

| Режим | Activity | Описание | Шаблон |
|-------|----------|----------|--------|
| **simple** | BotBti.SimpleDWG2DWG+v1 | Простая обработка DWG (SAVEAS 2018) | ❌ Нет |
| **template** | BotBti.BTI_INSERT_Basman+v1 | DWG с вставкой типового шаблона БТИ | ✅ Да |

---

## 📝 Проверка настройки

### **1. Проверить доступность шаблона:**

```bash
curl -I https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
# Должен вернуть: HTTP/1.1 200 OK
```

### **2. Проверить Activity:**

```bash
venv/bin/python check_template_details.py
# Должен показать: BotBti.BTI_INSERT_Basman+v1 ✅
```

### **3. Тестовый запуск:**

```python
# test_bti_template.py
from forge_client import ForgeClient

client = ForgeClient()

# Тестовые URLs
input_url = "https://storage.googleapis.com/btibot-processed/raw/test/input.dwg"
output_url = "https://storage.googleapis.com/btibot-processed/test/output_with_template.dwg"

# Запуск с шаблоном
workitem = client.submit_workitem(input_url, output_url, use_template=True)
print(f"WorkItem ID: {workitem['id']}")

# Проверка результата
result = client.wait_for_completion(workitem['id'])
print(f"Status: {result['status']}")
```

---

## 🔍 Отладка

### **Проверить логи в Cloud Run:**

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=telegram-bti-bot AND textPayload:\"типовым шаблоном\"" --limit=10
```

### **Проверить параметры WorkItem:**

В логах должно быть:

```
🏛️ Режим: с типовым шаблоном BTI Basmanny
📄 Шаблон: https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
📤 Отправка WorkItem с activityId: BotBti.BTI_INSERT_Basman+v1
```

---

## 📊 Сравнение результатов

| Параметр | Без шаблона | С шаблоном BTI |
|----------|-------------|----------------|
| **Activity** | SimpleDWG2DWG+v1 | BTI_INSERT_Basman+v1 |
| **Команда** | SAVEAS 2018 | INSERT + SAVEAS 2018 |
| **Размер результата** | ≈ размер входа | + 51 KB (шаблон) |
| **Время обработки** | 3-5 сек | 5-8 сек |
| **Содержимое** | Только входной DWG | Входной DWG + BTI шаблон |

---

## 🎯 Итог

✅ **Типовой шаблон BTI настроен и готов к использованию!**

**Для активации:**
1. Установить `use_template=True` в вызове `submit_workitem()`
2. Или изменить `BTI_MODE = "template"` в `bti_template_config.py`
3. Или добавить переменную окружения `USE_BTI_TEMPLATE=true`

**Файлы:**
- 📄 `bti_template_config.py` - конфигурация
- 🔧 `forge_client.py` - обновлен для поддержки шаблона
- 📝 `BTI_TEMPLATE_SETUP.md` - эта документация

**Шаблон:**
- 🏛️ https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg


