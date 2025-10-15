# 📐 BTI Templates

Типовые шаблоны БТИ для автоматической обработки чертежей.

---

## 📁 Файлы

### **BTI_Template.dwg**

**Назначение:** Типовой чертёж БТИ Басманный  
**Размер:** 51.2 KB  
**Содержит:**
- Стандартные слои БТИ (A-WALL, A-DOOR, A-WINDOW, и т.д.)
- Типовые блоки (BTI_DOOR, BTI_WINDOW, BTI_SINK, BTI_TOILET)
- Штамп и рамку чертежа

**URL в GCS:**
```
https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
```

---

## 🏛️ Стандартные слои БТИ

| Слой | Назначение | Цвет | Linetype |
|------|-----------|------|----------|
| **A-WALL** | Стены | 8 (серый) | Continuous |
| **A-DOOR** | Двери | 2 (желтый) | Continuous |
| **A-WINDOW** | Окна | 4 (голубой) | Continuous |
| **A-PLUMBING** | Сантехника | 3 (зеленый) | Continuous |
| **A-DIM** | Размеры | 1 (красный) | Continuous |
| **A-TEXT** | Текст/штамп | 7 (белый) | Continuous |

---

## 🧩 Блоки в шаблоне

- **BTI_DOOR** - типовая дверь
- **BTI_WINDOW** - типовое окно
- **BTI_SINK** - раковина
- **BTI_TOILET** - унитаз
- **BTI_FRAME** - рамка чертежа

---

## 📊 Использование

### **Вариант 1: В Activity (Autodesk APS)**

```json
{
  "templateFile": {
    "url": "https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg"
  }
}
```

### **Вариант 2: Локально**

Открыть в AutoCAD и использовать как шаблон для новых чертежей.

---

**💡 Шаблон готов к использованию в Activity с LISP скриптами!**

