# 📊 Разделение задач: Локально vs VM (Gemini)

**Дата:** 2025-10-14  
**Архитектура:** BTI с интеграцией Leica DISTO

---

## ✅ ЧТО СДЕЛАНО ЛОКАЛЬНО (МНО)

### **1. Создана структура проекта**

```
BTI-DWG-PDF-1/
├── templates/         ✅ Создано
│   ├── BTI_Template.dwg (51.2 KB)
│   └── README.md
├── scripts/           ✅ Создано
│   ├── BTI_APPLY.lsp (4.4 KB)
│   ├── BTI_CLEANUP.lsp (2.6 KB)
│   └── README.md
├── forge/             ✅ Создано
│   ├── activity_with_lisp.json
│   └── (forge_client.py уже есть в корне)
└── config/            ✅ Создано
    └── bti_layers.json
```

---

### **2. Создан LISP скрипт BTI_APPLY.lsp**

**Назначение:** Автоматическая вставка блоков БТИ по меткам от Leica

**Функции:**
- `BTI-CreateStandardLayers()` - создает слои БТИ (A-WALL, A-DOOR, A-WINDOW, и т.д.)
- `BTI-InsertFromLayer()` - находит метки и вставляет блоки
- `c:BTI_APPLY` - главная команда

**Процесс:**
```
MARK_DOOR (метки от Leica)
    ↓
BTI_APPLY.lsp находит метки
    ↓
Вставляет BTI_DOOR в центр каждой метки
    ↓
Результат: Типовые блоки БТИ вставлены
```

**Загружен в GCS:**
```
https://storage.googleapis.com/btibot-processed/scripts/BTI_APPLY.lsp
```

---

### **3. Создан LISP скрипт BTI_CLEANUP.lsp**

**Назначение:** Очистка временных слоев после обработки

**Функции:**
- `BTI-DeleteLayer()` - удаляет временные слои
- `BTI-PurgeAll()` - очистка неиспользуемых объектов
- `c:BTI_CLEANUP` - главная команда

**Загружен в GCS:**
```
https://storage.googleapis.com/btibot-processed/scripts/BTI_CLEANUP.lsp
```

---

### **4. Создана конфигурация слоев БТИ**

**Файл:** `config/bti_layers.json`

**Содержит:**
- Стандарты слоев БТИ (цвета, типы линий, толщины)
- Блоки (BTI_DOOR, BTI_WINDOW, BTI_SINK, BTI_TOILET)
- Настройки чертежа (единицы, масштаб, формат)

**Слои:**
- A-WALL (стены) - серый (8)
- A-DOOR (двери) - желтый (2)
- A-WINDOW (окна) - голубой (4)
- A-PLUMBING (сантехника) - зеленый (3)
- A-DIM (размеры) - красный (1)
- A-TEXT (текст) - белый (7)
- MARK_DOOR (метки дверей) - фиолетовый (5) - служебный
- MARK_WINDOW (метки окон) - фиолетовый (5) - служебный

---

### **5. Создана конфигурация Activity с LISP**

**Файл:** `forge/activity_with_lisp.json`

**Activity ID:** `BotBti.DWG2DWG_BTI_LISP`

**Параметры:**
- `inputFile` - входной DWG от Leica
- `scriptFile` - LISP скрипт (BTI_APPLY.lsp)
- `resultFile` - результат с блоками БТИ

---

### **6. Загружено в GCS**

```
✅ templates/BTI_Template.dwg
   → gs://btibot-processed/templates/bti_basmanny_template.dwg

✅ scripts/BTI_APPLY.lsp
   → gs://btibot-processed/scripts/BTI_APPLY.lsp

✅ scripts/BTI_CLEANUP.lsp
   → gs://btibot-processed/scripts/BTI_CLEANUP.lsp
```

**Все файлы публично доступны!**

---

### **7. Создана документация**

- `templates/README.md` - описание шаблонов
- `scripts/README.md` - описание LISP скриптов
- `PROJECT_RESTRUCTURE_PLAN.md` - план реструктуризации
- `GEMINI_FINAL_TASK.md` - задача для Gemini
- `FOR_GEMINI_FINAL.txt` - краткая задача (этот файл)
- `TASKS_DIVISION_REPORT.md` - разделение задач

---

## ⏳ ЧТО ДОЛЖЕН СДЕЛАТЬ GEMINI (VM)

### **ЗАДАЧА:**

Используя твой скрипт `build-windows.ps1`, создай AppBundle с LISP скриптами.

### **ШАГИ:**

```powershell
# 1. Скачать LISP скрипты
Invoke-WebRequest -Uri "https://storage.googleapis.com/btibot-processed/scripts/BTI_APPLY.lsp" `
  -OutFile "C:\BTI-DWG-PDF\scripts\BTI_APPLY.lsp"

Invoke-WebRequest -Uri "https://storage.googleapis.com/btibot-processed/scripts/BTI_CLEANUP.lsp" `
  -OutFile "C:\BTI-DWG-PDF\scripts\BTI_CLEANUP.lsp"

# 2. Запустить компиляцию (если AutoCAD есть)
cd C:\BTI-DWG-PDF
.\build-windows.ps1

# 3. Создать bundle с LISP
New-Item -Path "C:\out\BtiPlugin.bundle\Contents" -ItemType Directory -Force

# Копировать LISP (обязательно!)
Copy-Item "C:\BTI-DWG-PDF\scripts\*.lsp" -Destination "C:\out\BtiPlugin.bundle\Contents\"

# Копировать DLL (если скомпилировано)
Copy-Item "C:\out\BTI_InsertBasman.dll" -Destination "C:\out\BtiPlugin.bundle\Contents\" -ErrorAction SilentlyContinue

# Копировать шаблон
Copy-Item "C:\BTI-DWG-PDF\bti_basmanny_template.dwg" -Destination "C:\out\BtiPlugin.bundle\Contents\" -ErrorAction SilentlyContinue

# 4. Создать PackageContents.xml (см. GEMINI_FINAL_TASK.md)

# 5. Создать ZIP
Compress-Archive -Path "C:\out\BtiPlugin.bundle" -DestinationPath "C:\out\BtiPlugin.zip" -Force

# 6. Загрузить в GCS
gsutil cp C:\out\BtiPlugin.zip gs://btibot-processed/appbundles/

# 7. Зарегистрировать в APS (используй credentials выше)
```

---

## 📋 ПРОВЕРКА РЕЗУЛЬТАТА

После выполнения Gemini должно быть:

```
✅ C:\out\BtiPlugin.bundle\
   ├── PackageContents.xml
   └── Contents\
       ├── BTI_APPLY.lsp (4.4 KB)
       ├── BTI_CLEANUP.lsp (2.6 KB)
       ├── bti_basmanny_template.dwg (51.2 KB)
       └── BTI_InsertBasman.dll (опционально, если AutoCAD установлен)

✅ C:\out\BtiPlugin.zip (~80-120 KB)
✅ gs://btibot-processed/appbundles/BtiPlugin_v1.zip
✅ Autodesk APS: BotBti.BtiPlugin+v1 зарегистрирован
```

---

## 🎯 ПОСЛЕ ВЫПОЛНЕНИЯ

**На локальной машине я сделаю:**

1. ✅ Обновлю Activity для использования LISP
2. ✅ Задеплою с новым AppBundle
3. ✅ Протестирую обработку с LISP
4. ✅ Создам итоговый отчет

---

## 📊 ИТОГОВАЯ СХЕМА

```
[Leica DISTO]
    ↓ (экспорт DWG с метками)
[MARK_DOOR, MARK_WINDOW слои]
    ↓
[Telegram Bot] → Cloud Run
    ↓
[Autodesk APS Activity]
    ↓
[AppBundle: BotBti.BtiPlugin+v1]
    ├── BTI_APPLY.lsp (вставка блоков)
    ├── BTI_Template.dwg (типовые блоки)
    └── BTI_InsertBasman.dll (опционально)
    ↓
[AutoCAD Engine выполняет LISP]
    ↓
[Результат: DWG с блоками БТИ]
    ↓
[GCS Storage] → Telegram User
```

═══════════════════════════════════════════════════════════════

✅ ГОТОВО К ВЫПОЛНЕНИЮ!

Gemini, выполни шаги выше и сообщи результат.

╚══════════════════════════════════════════════════════════════╝

