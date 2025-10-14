# 🏆 BTI AUTO MODE - ПОЛНОСТЬЮ ГОТОВ!

**Дата:** 2025-10-15  
**Ветка:** forge-plugin-gold  
**Cloud Run:** telegram-bti-bot-00007-kl2  
**Статус:** ✅ РАБОТАЕТ С ОБРАБОТКОЙ

---

## ✅ Создано в Autodesk APS

### 1. AppBundle: BotBti.BtiAutoProcess+v1
- **ID:** BotBti.BtiAutoProcess  
- **Alias:** v1
- **Engine:** Autodesk.AutoCAD+25_1
- **Размер:** 54 KB
- **Содержит:**
  - ✅ BTI_AUTO_APPLY.lsp (автозапуск!)
  - BTI_APPLY.lsp
  - BTI_CLEANUP.lsp
  - BTI_APPLY_COLOR.lsp (не используется)
  - BTI_ORTHO_ADJUST.lsp (не используется)
  - BTI_APPLY_OBJECTS.lsp (не используется)
  - BTI_DIM_AREA.lsp (не используется)
  - bti_basmanny_template.dwg

### 2. Activity: BotBti.BTI_AUTO_PROCESS+v1
- **ID:** BotBti.BTI_AUTO_PROCESS
- **Alias:** v1
- **Engine:** Autodesk.AutoCAD+25_1
- **AppBundle:** BotBti.BtiAutoProcess+v1
- **Command Line:**
  ```
  accoreconsole.exe
    /i "input.dwg"
    /s "BTI_AUTO_APPLY.lsp"
    /o "result.dwg"
  ```

---

## ✅ Задеплоено в Cloud Run

- **Service:** telegram-bti-bot
- **Revision:** telegram-bti-bot-00007-kl2
- **URL:** https://telegram-bti-bot-637190449180.us-central1.run.app
- **Region:** us-central1
- **Memory:** 2 GB
- **Timeout:** 540s (9 минут)
- **Max Instances:** 10
- **Environment:**
  - `BTI_PROCESSING_MODE=auto` ✨

---

## 🔄 Как работает обработка

```
┌─────────────────────────────────────────┐
│ Пользователь отправляет DWG в бот       │
│ (от Leica DISTO или любой другой)       │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ Cloud Run: telegram-bti-bot             │
│ • Загружает в GCS                       │
│ • Создает signed URLs                   │
│ • Отправляет WorkItem в APS             │
│   Activity: BTI_AUTO_PROCESS+v1         │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ Autodesk APS Design Automation          │
│ • Загружает AppBundle BtiAutoProcess+v1│
│ • Запускает AutoCAD Core Console       │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ AutoCAD accoreconsole.exe               │
│ • Открывает input.dwg                   │
│ • Загружает BTI_AUTO_APPLY.lsp          │
│ • 🤖 LISP АВТОМАТИЧЕСКИ ВЫПОЛНЯЕТСЯ:   │
│   1. Создает слои A-DOOR, A-WINDOW      │
│   2. Находит MARK_DOOR → BTI_DOOR       │
│   3. Находит MARK_WINDOW → BTI_WINDOW   │
│   4. QSAVE (сохранение)                 │
│ • Закрывает файл                        │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ Результат загружается в GCS             │
│ • Обработанный DWG                      │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ Telegram бот отправляет файл            │
│ пользователю                            │
└─────────────────────────────────────────┘
```

---

## 📊 Сравнение режимов

| Функция | simple | auto |
|---------|--------|------|
| Обработка | ❌ Копия | ✅ BTI обработка |
| MARK_DOOR → BTI_DOOR | ❌ | ✅ |
| MARK_WINDOW → BTI_WINDOW | ❌ | ✅ |
| Создание слоев БТИ | ❌ | ✅ |
| Автосохранение | ✅ | ✅ |
| Время | ~10-15 сек | ~20-30 сек |

---

## 🧪 Тестирование

### Через Telegram:
1. Отправь DWG файл в бота
2. Дождись обработки (~20-30 сек)
3. Получи обработанный файл

### Через API:
```bash
curl -X POST https://telegram-bti-bot-637190449180.us-central1.run.app/process-dwg \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "gs://btibot-processed/raw/test.dwg",
    "user_id": "test",
    "chat_id": "test",
    "job_id": "test_'$(date +%s)'"
  }'
```

### Проверка логов:
```bash
gcloud logging read "resource.labels.service_name=telegram-bti-bot" \
  --limit=20 --project=talkhint
```

Должны увидеть:
```
🤖 Режим AUTO: Автоматическая BTI обработка
   ✅ Слоевое распознавание (MARK_DOOR, MARK_WINDOW)
   ✅ Вставка блоков (BTI_DOOR, BTI_WINDOW)
   ✅ Автозапуск при загрузке LISP
```

---

## 📋 Что было сделано

### Созданы в APS (по официальной документации):
1. ✅ AppBundle `BtiAutoProcess` (id БЕЗ nickname prefix)
2. ✅ Alias `v1` для AppBundle
3. ✅ Activity `BTI_AUTO_PROCESS` (id БЕЗ nickname prefix)
4. ✅ Alias `v1` для Activity
5. ✅ ZIP файл загружен на S3

### Обновлено в коде:
1. ✅ `BTI_AUTO_APPLY.lsp` создан (автозапуск)
2. ✅ `forge_client.py` обновлен (константы v1)
3. ✅ `app.py` обновлен (режим auto)

### Задеплоено:
1. ✅ Cloud Run revision 00007-kl2
2. ✅ Environment: `BTI_PROCESSING_MODE=auto`
3. ✅ Изменения в GitHub (ветка forge-plugin-gold)

---

## 🎯 Готово к работе!

**Система полностью запущена** и обрабатывает DWG файлы:

- ✅ Слоевое распознавание MARK_DOOR, MARK_WINDOW
- ✅ Автоматическая вставка блоков БТИ
- ✅ Автосохранение результата
- ✅ Время обработки: ~20-30 секунд

---

**🚀 Отправь DWG файл с метками MARK_DOOR и MARK_WINDOW - они будут обработаны!**


