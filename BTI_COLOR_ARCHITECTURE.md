# 🎨 BTI Color-Based Architecture - Финальная версия

**Дата:** 2025-10-14  
**Версия:** 2.0 (Color-based Recognition)  
**Статус:** ✅ Готово к реализации

---

## 🎯 Концепция

**Идея:** Leica DISTO размечает объекты **ЦВЕТАМИ** → Forge распознает цвета и вставляет блоки БТИ

**Преимущества:**
- ✅ Не требует AI или Computer Vision
- ✅ Не требует .NET компиляции
- ✅ Работает в Forge AutoCAD Core (LISP)
- ✅ Визуально понятно инженеру
- ✅ Легко расширяемо

---

## 🎨 Цветовая схема

| Цвет | Код | Leica объект | BTI блок | Слой БТИ |
|------|-----|--------------|----------|----------|
| 🟦 Синий | 5 | Окно | BTI_WINDOW | A-WINDOW |
| 🟧 Оранжевый | 30 | Дверь | BTI_DOOR | A-DOOR |
| 🟩 Зеленый | 3 | Унитаз | BTI_TOILET | A-PLUMBING |
| 🟥 Красный | 1 | Раковина | BTI_SINK | A-PLUMBING |
| 🟪 Фиолетовый | 6 | Душ | BTI_SHOWER | A-PLUMBING |
| ⚪ Белый | 7 | Стены/контуры | - | A-WALL |

---

## 🔄 Полный процесс

```
[Leica DISTO Plan]
    ↓ Размечает объекты цветами
    ↓ 🟦 = окно, 🟧 = дверь, 🟩 = унитаз
[DWG с цветными объектами]
    ↓ Telegram Bot
[Cloud Run: /process-dwg]
    ↓
[Autodesk APS Activity]
    ↓
[AppBundle: BotBti.BtiPlugin+v1]
    ├── BTI_APPLY_COLOR.lsp
    ├── BTI_Template.dwg (блоки)
    └── BTI_CLEANUP.lsp
    ↓
[AutoCAD Engine выполняет LISP]
    ├── Распознает цвет 5 → вставляет BTI_WINDOW
    ├── Распознает цвет 30 → вставляет BTI_DOOR
    └── Создает слои БТИ (A-WINDOW, A-DOOR, и т.д.)
    ↓
[Результат: DWG с блоками БТИ]
    ↓ Опционально
[PDF (A4, Landscape)]
    ↓
[GCS Storage]
    ↓
[Telegram: готовый БТИ-план]
```

---

## 📁 Структура проекта

```
BTI-DWG-PDF-1/
├── templates/
│   ├── BTI_Template.dwg          ← Блоки: BTI_DOOR, BTI_WINDOW, и т.д.
│   └── README.md
│
├── scripts/
│   ├── BTI_APPLY_COLOR.lsp       ← 🎨 Распознавание по цветам (НОВОЕ!)
│   ├── BTI_APPLY.lsp              ← Распознавание по слоям (старое)
│   ├── BTI_CLEANUP.lsp            ← Очистка временных объектов
│   └── README.md
│
├── config/
│   ├── bti_color_mapping.json    ← 🎨 Цветовая схема (НОВОЕ!)
│   └── bti_layers.json            ← Стандарты слоев БТИ
│
├── forge/
│   ├── activity_color_based.json ← 🎨 Activity с цветами (НОВОЕ!)
│   ├── activity_with_lisp.json   ← Activity со слоями (старое)
│   └── forge_client.py
│
├── cloudrun/
│   └── (будущая реорганизация кода)
│
└── telegram/
    └── (будущая реорганизация бота)
```

---

## 🧩 LISP скрипт BTI_APPLY_COLOR.lsp

**Главная функция:**
```lisp
(defun BTI-InsertByColor ()
  ; Проходим по всем объектам
  ; Для каждого объекта:
  ;   - Читаем цвет (vla-get-Color)
  ;   - Вычисляем центр (GetBoundingBox)
  ;   - Вставляем блок по таблице цветов:
  ;     color=5  → BTI_WINDOW
  ;     color=30 → BTI_DOOR
  ;     color=3  → BTI_TOILET
  ;     color=1  → BTI_SINK
)
```

**Команда:** `BTI_APPLY_COLOR`

**Что делает:**
1. Создает слои БТИ (A-WALL, A-DOOR, A-WINDOW, и т.д.)
2. Находит все объекты в чертеже
3. Для каждого объекта определяет цвет
4. Вставляет соответствующий блок БТИ
5. Перемещает блоки на правильные слои

---

## ☁️ Activity Configuration

**Файл:** `forge/activity_color_based.json`

```json
{
  "id": "BotBti.BTI_APPLY_COLOR",
  "engine": "Autodesk.AutoCAD+25_1",
  "appbundles": ["BotBti.BtiPlugin+v1"],
  "commandLine": [
    "$(engine.path)\\accoreconsole.exe /i \"$(args[inputFile].path)\" /s \"$(appbundles[BtiPlugin].path)/Contents/BTI_APPLY_COLOR.lsp\""
  ],
  "parameters": {
    "inputFile": {
      "verb": "get",
      "description": "Input DWG from Leica",
      "localName": "input.dwg"
    },
    "resultFile": {
      "verb": "put",
      "description": "Output DWG with BTI blocks",
      "localName": "result.dwg"
    }
  }
}
```

---

## 🌐 Файлы в GCS (публичные)

```
✅ BTI_APPLY_COLOR.lsp
   https://storage.googleapis.com/btibot-processed/scripts/BTI_APPLY_COLOR.lsp

✅ BTI_APPLY.lsp (слои)
   https://storage.googleapis.com/btibot-processed/scripts/BTI_APPLY.lsp

✅ BTI_CLEANUP.lsp
   https://storage.googleapis.com/btibot-processed/scripts/BTI_CLEANUP.lsp

✅ bti_color_mapping.json
   https://storage.googleapis.com/btibot-processed/config/bti_color_mapping.json

✅ BTI_Template.dwg
   https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg

✅ upload_bti_appbundle_windows.py
   https://storage.googleapis.com/btibot-processed/scripts/upload_bti_appbundle_windows.py
```

---

## 🚀 Что делать дальше

### **1. Gemini на VM:**

Создать AppBundle с LISP скриптами (включая BTI_APPLY_COLOR.lsp)

### **2. Я (локально):**

После создания AppBundle:
- Зарегистрировать Activity BotBti.BTI_APPLY_COLOR
- Обновить forge_client.py для цветовой логики
- Задеплоить
- Протестировать

---

## ✅ Преимущества Color-Based подхода

| Критерий | Layer-Based | Color-Based |
|----------|-------------|-------------|
| **Простота для Leica** | Нужны специальные слои | Просто раскрасить |
| **Визуальность** | Не видно в чертеже | Видно сразу |
| **Расширяемость** | Добавлять слои | Добавлять цвета |
| **Совместимость** | Зависит от слоев | Универсально |
| **LISP сложность** | Средняя | Простая |

**Color-Based ВЫИГРЫВАЕТ! 🎨**

---

**🎯 Готово к реализации через Gemini на VM!**


