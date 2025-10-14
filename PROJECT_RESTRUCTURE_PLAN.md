# 🏗️ План реструктуризации проекта под BTI Architecture

**Цель:** Привести проект к архитектуре с Leica интеграцией  
**Задачи разделены:** Локально (я) | VM (Gemini)

---

## 📊 Целевая структура

```
BTI-DWG-PDF-1/
├── templates/          ← BTI шаблоны
├── scripts/            ← LISP скрипты
├── forge/              ← Forge конфигурация
├── cloudrun/           ← Cloud Run код
├── telegram/           ← Telegram bot
├── storage/            ← GCS структура (virtual)
└── config/             ← Конфигурация слоев
```

---

## 🔵 ЗАДАЧИ ДЛЯ МЕНЯ (ЛОКАЛЬНО)

### **1. Создать структуру папок** ✅

```bash
mkdir -p templates scripts forge cloudrun telegram config
```

### **2. Создать LISP скрипты**

**scripts/BTI_APPLY.lsp** - вставка блоков по меткам:
- Находит MARK_DOOR → вставляет BTI_DOOR
- Находит MARK_WINDOW → вставляет BTI_WINDOW
- Создает слои A-WALL, A-DOOR, A-WINDOW

**scripts/BTI_CLEANUP.lsp** - очистка временных слоев

### **3. Создать конфигурацию слоев**

**config/bti_layers.json** - стандарты БТИ:
- Слои (цвета, типы линий)
- Блоки (двери, окна, сантехника)

### **4. Переместить код в папки**

```
app.py → cloudrun/main.py
forge_client.py → forge/forge_client.py
bti_template_config.py → config/bti_template_config.py
```

### **5. Обновить Activity для LISP**

**forge/activity.json** - конфигурация Activity с LISP скриптами

### **6. Документация**

README.md в каждой папке

---

## 🟢 ЗАДАЧИ ДЛЯ GEMINI (WINDOWS VM)

### **1. Компиляция .NET плагина (если есть AutoCAD)**

```powershell
# Запустить существующий скрипт
.\build-fixed.ps1

# Или build-windows.ps1 от Gemini
.\build-windows.ps1
```

**Результат:**
- ✅ BTI_InsertBasman.dll
- ✅ BtiPlugin.zip

### **2. Создать AppBundle с LISP**

**Если .NET не работает** - создать AppBundle только с LISP:

```
BtiPlugin.bundle/
├── PackageContents.xml
└── Contents/
    ├── BTI_APPLY.lsp
    ├── BTI_CLEANUP.lsp
    └── bti_basmanny_template.dwg
```

### **3. Загрузить в APS**

```powershell
# Через Python скрипт
python .\upload_bti_appbundle.py --bundle C:\out\BtiPlugin.zip
```

---

## 🎯 Что делать СЕЙЧАС

### **Я делаю (локально):**

1. ✅ Создаю структуру папок
2. ✅ Создаю LISP скрипты BTI_APPLY.lsp
3. ✅ Создаю конфигурацию bti_layers.json
4. ✅ Обновляю Activity для LISP
5. ✅ Реорганизую код

### **Gemini делает (на VM):**

1. ⏳ Запускает build-windows.ps1
2. ⏳ Компилирует .NET плагин
3. ⏳ Создает AppBundle
4. ⏳ Загружает в GCS
5. ⏳ Регистрирует в APS

---

**Начинаю выполнение локальных задач!**


