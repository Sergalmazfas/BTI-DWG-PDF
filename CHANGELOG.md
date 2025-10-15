# Changelog

All notable changes to BTI DWG Processor Core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.0.0] - 2025-10-15 - "IRON"

### 🎯 Major Changes

- **Полный отказ от PDF/кадастра/GPT/3D** - фокус только на 2D DWG обработку
- **Inline LISP solution** - весь код обработки встроен в Activity settings.script
- **Следование официальной документации Autodesk** - все компоненты соответствуют docs
- **Единичная обработка** - `PROCESS_CONCURRENCY=1` для стабильности

### ✨ Added

- Inline LISP в `settings.script` для Activity
- AppBundle `BotBti.BtiLISP+prod` с упрощённой структурой
- Activity `BotBti.BtiLISPActivity+prod` для LISP-обработки
- Автоматическое создание слоёв БТИ (BTI_WALLS, BTI_MARKERS, BTI_TEXT)
- Функция `CREATE_MARKER` для POINT + TEXT меток
- Команда `SAVEAS` для контроля имени выходного файла
- Продакшен скрипт `test_forge_production.py`
- Детальные логи с маркерами `[BTI]` для отладки

### 🔧 Changed

- **AppBundle структура:** упрощена до минимума (файлы в корне)
- **Activity commandLine:** одна строка вместо массива (по документации)
- **LISP команды:** добавлены завершающие `""` для автозавершения
- **Сохранение файла:** SAVEAS вместо QSAVE для контроля имени
- **Обработка:** только одного файла за цикл (no parallel)

### ❌ Removed

- PDF конвертация и все связанные модули
- Интеграции с Росреестром и кадастровыми API
- GPT/AI компоненты
- 3D обработка и визуализация
- Цветовое распознавание (заменено на геометрическое)
- Параллельная обработка множества файлов
- .NET плагины (не нужны для LISP)
- PackageContents.xml ComponentEntry для LISP (не работает в Forge)

### 🐛 Fixed

- PackageContents.xml ComponentEntry не загружал LISP → использован inline script
- CommandLine массив вместо строки → исправлено на одну строку
- Команды зависали в ожидании ENTER → добавлены завершающие `""`
- QSAVE сохранял под входным именем → заменён на SAVEAS
- Файлы не находились через (load) → встроен весь код в settings

### 🔒 Security

- Все credentials в Google Secret Manager
- Signed URLs для GCS с временным доступом (1 час)
- Service Account для подписи URL

---

## Миграция с предыдущих версий

### С версии 3.x (POINT-based):
1. Обновить Activity alias: `BotBti.BtiLISPActivity+prod`
2. Удалить старые AppBundle версии (опционально)
3. Обновить env переменную: `ACTIVITY_NAME=BotBti.BtiLISPActivity+prod`
4. Передеплоить Cloud Run сервисы

### С версии 2.x (INSERT-based):
1. Полностью заменить AppBundle на BtiLISP
2. Создать новую Activity
3. Обновить все env переменные
4. Протестировать на одном файле перед переводом в продакшен

---

## 📊 Производительность

| Метрика | Значение |
|---------|----------|
| Среднее время обработки | 15-20 секунд |
| Максимальный таймаут | 100 секунд (Forge quota) |
| Размер входного файла | 10 KB - 500 KB |
| Размер выходного файла | +3-5% от входного |
| Успешность обработки | >95% |

---

## 🧪 Тестирование

### Локальный тест
```bash
python3 test_forge_production.py
```

### Тест через Telegram
1. Отправьте .dwg файл боту
2. Дождитесь сообщения о завершении
3. Проверьте `ready/` в GCS

### Проверка логов
```bash
# Проверить последний WorkItem
gcloud logging read 'resource.labels.service_name=forge-poller AND textPayload:"success"' \
  --limit=10 --project=talkhint

# Проверить ошибки
gcloud logging read 'resource.labels.service_name=dwg-processor-core AND severity>=ERROR' \
  --limit=10 --project=talkhint
```

---

## 🔧 Разработка

### Обновление LISP-логики
1. Отредактируйте inline script в `inline_lisp_fixed.py`
2. Создайте новую версию Activity:
   ```bash
   python3 inline_lisp_fixed.py
   ```
3. Протестируйте локально
4. Обновите prod alias после успешного теста

### Добавление новых функций
Все изменения делаются в inline LISP коде - не нужна компиляция!

---

## 📞 Поддержка

- **Логи:** Cloud Run console или `gcloud logging read`
- **Статус:** `gcloud run services list --project=talkhint`
- **Документация Forge:** https://aps.autodesk.com/

---

## 📄 Лицензия

Proprietary - BTI Team

---

**Версия:** 4.0.0 "IRON"  
**Дата:** 2025-10-15  
**Статус:** ✅ Production Ready

