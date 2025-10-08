# 🧩 BTE AppBundle Test Suite

Автоматизированное тестирование AppBundle для BTI проекта на реальных файлах через Autodesk APS.

## 📁 Структура проекта

```
bte-appbundle/
├── archives/          # DWG файлы и ZIP архивы
├── workitems/         # JSON файлы с WorkItem payload
├── scripts/           # Скрипты автоматизации
│   ├── test_workitem.py       # Python скрипт для запуска теста
│   ├── verify_report.sh       # Bash скрипт для проверки отчёта
│   └── run_full_test.sh       # Полный автоматизированный тест
└── reports/           # Отчёты и результаты тестов
```

## 🚀 Быстрый старт

### 1. Полный автоматический тест

Запустить весь процесс одной командой:

```bash
bash bte-appbundle/scripts/run_full_test.sh
```

Этот скрипт автоматически:
- ✅ Проверяет наличие DWG файла
- ✅ Создаёт ZIP архив
- ✅ Генерирует signed URLs
- ✅ Создаёт и отправляет WorkItem
- ✅ Ждёт завершения и скачивает отчёт
- ✅ Проверяет результат
- ✅ Сохраняет артефакты в GCS

### 2. Запуск отдельного теста

Если нужен больший контроль:

```bash
python3 bte-appbundle/scripts/test_workitem.py \
  --dwg bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg \
  --activity BotBti.BTEInsertActivity+1 \
  --output-dir bte-appbundle/reports
```

### 3. Проверка отчёта

Проверить отчёт после выполнения:

```bash
bash bte-appbundle/scripts/verify_report.sh bte-appbundle/reports/basmannyi_report_*.log
```

## 📋 Процесс тестирования

### Шаг 1: Подготовка DWG файла

Файл `basmannyi_novyi_obmernyi.dwg` (51KB) уже скачан из GCS:

```
gs://btibot-processed/raw/1759861119/Чертеж_Басманная_Новая_обмерный_план.dwg
```

### Шаг 2: Создание ZIP архива

Скрипт автоматически создаёт ZIP архив с:
- DWG файлом
- Файлом manifest.txt с метаданными

### Шаг 3: Генерация Signed URLs

Используется `gcloud storage sign-url` для создания временных URL (1 час):
- **Input URL** (GET): для загрузки ZIP архива
- **Output URL** (PUT): для сохранения результата

### Шаг 4: Создание WorkItem

Payload для APS:

```json
{
  "activityId": "BotBti.BTEInsertActivity+1",
  "arguments": {
    "HostDWG": {
      "url": "<input_signed_url>",
      "verb": "get"
    },
    "ResultDWG": {
      "url": "<output_signed_url>",
      "verb": "put"
    }
  }
}
```

### Шаг 5: Мониторинг выполнения

Скрипт проверяет статус каждые 5 секунд (timeout: 300s) и выводит:
- Текущий статус (pending → inprogress → success/failed)
- Время выполнения
- Прогресс выполнения

### Шаг 6: Проверка результата

Автоматическая проверка отчёта на наличие:
- ✅ Команда `INSERTBTE` выполнена
- ✅ Команда `QSAVE` выполнена
- ✅ Команда `QUIT` выполнена
- ✅ BytesDownloaded > 10000
- ✅ Duration < 5s

### Шаг 7: Сохранение артефактов

Все результаты сохраняются в GCS:
- `gs://btibot-queue/test_input/basmannyi_test_*.zip` - входной архив
- `gs://btibot-processed/test_output/basmannyi_result_*.dwg` - результат
- `gs://btibot-processed/logs/basmannyi_report_*.log` - отчёт
- `gs://btibot-processed/archives/basmannyi_test_*.zip` - архив результатов

## 🔧 Конфигурация

### Переменные окружения

```bash
# APS credentials (необязательно, есть defaults)
export APS_CLIENT_ID="dFqYmq4IKNf1p5xRzY31rKF1Ib9RzWRV"
export APS_CLIENT_SECRET="nD2QojaPdYwNFv1Q"
```

### Activity ID

По умолчанию используется:
```
BotBti.BTEInsertActivity+1
```

Можно изменить через параметр `--activity`.

## 📊 Формат отчёта

Успешный отчёт содержит:

```
Command: INSERTBTE
Result: Success
Command: QSAVE
Command: QUIT
BytesDownloaded: 52480
TimeElapsed: 3.2s
```

## 🧪 Примеры использования

### Тест на другом DWG файле

```bash
python3 bte-appbundle/scripts/test_workitem.py \
  --dwg /path/to/your/file.dwg \
  --activity BotBti.BTEInsertActivity+1
```

### Проверка конкретного отчёта

```bash
bash bte-appbundle/scripts/verify_report.sh reports/basmannyi_report_20241008_123456.log
```

### Скачивание результата из GCS

```bash
# Найти последний результат
gcloud storage ls gs://btibot-processed/test_output/basmannyi_result_*.dwg

# Скачать
gcloud storage cp gs://btibot-processed/test_output/basmannyi_result_TIMESTAMP.dwg ./result.dwg
```

## ✅ Критерии успеха

| Критерий | Описание |
|----------|----------|
| WorkItem создан | Status code 200/201 от APS |
| WorkItem выполнен | Status = "success" |
| INSERTBTE выполнена | Команда найдена в отчёте |
| Файл сохранён | ResultDWG найден в GCS |
| Размер > 10KB | Результат не пустой |
| Время < 5s | Быстрое выполнение |

## 🚨 Устранение неполадок

### Ошибка: "Failed to create signed URL"

Проверьте, что у вас настроен gcloud:

```bash
gcloud auth login
gcloud config set project swiftchair
```

### Ошибка: "WorkItem failed"

Проверьте логи:

```bash
cat bte-appbundle/reports/workitem_result_*.json
```

Частые причины:
- Неправильный Activity ID
- Истекший signed URL
- Недоступен входной файл
- Ошибка в AppBundle

### Ошибка: "DWG file not found"

Скачайте файл вручную:

```bash
gcloud storage cp "gs://btibot-processed/raw/1759861119/*" bte-appbundle/archives/
```

## 📚 Дополнительная документация

- [CURSOR_TASK_BASMANNY.md](../CURSOR_TASK_BASMANNY.md) - Подробное описание задачи
- [Autodesk APS Documentation](https://aps.autodesk.com/developer/documentation)
- [Design Automation API](https://aps.autodesk.com/en/docs/design-automation/v3/)

## 🎯 Следующие шаги

После успешного теста:

1. ✅ Проверить результат визуально в AutoCAD
2. ✅ Сделать коммит артефактов в GitHub
3. ✅ Обновить документацию с результатами
4. ✅ Интегрировать в CI/CD pipeline

---

**Статус**: ✅ Готово к использованию  
**Версия**: 1.0  
**Дата**: 2024-10-08

