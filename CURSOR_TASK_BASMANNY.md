# CURSOR_TASK_BASMANNY.md

## 🎯 **Цель**

Автоматизировать тестирование AppBundle на реальном файле
**«басманный, новый, обмерный.dwg»** —
заархивировать, создать signed URLs, зарегистрировать в WorkItem и проверить выполнение INSERTBTE-команды на серверах Autodesk APS.

---

## ⚙️ **Исходные данные**

- **Репозиторий**: https://github.com/Sergalmazfas/dwg-processor-core
- **Ветка**: feature/create-appbundle
- **Файл**: Чертеж_Басманная_Новая_обмерный_план.dwg (уже в GCS)
- **Бакет входной**: `gs://btibot-processed/raw/1759861119/`
- **Целевой бакет для результата**: `gs://btibot-processed/test_output/`
- **WorkItem тестируемый**: BTEInsertActivity

---

## 🧩 **1️⃣ Найти и упаковать DWG**

Проверить наличие файла и создать ZIP:

```bash
# Скачать файл из GCS
gcloud storage cp "gs://btibot-processed/raw/1759861119/Чертеж_Басманная_Новая_обмерный_план.dwg" ./basmannyi_novyi_obmernyi.dwg

# Создать ZIP архив
zip -r basmannyi_test.zip basmannyi_novyi_obmernyi.dwg

# Загрузить в GCS
gcloud storage cp basmannyi_test.zip gs://btibot-queue/test_input/
```

Создать контрольный файл manifest.txt:

```bash
echo "Basmannyi DWG test package for AppBundle" > manifest.txt
zip -r basmannyi_test.zip manifest.txt
```

---

## 🧠 **2️⃣ Создать Signed URLs**

Получить временные ссылки (1 час) для загрузки и сохранения результата:

```bash
# Для входного файла
gcloud storage sign-url gs://btibot-queue/test_input/basmannyi_test.zip --duration=1h

# Для выходного файла (с методом PUT)
gcloud storage sign-url gs://btibot-processed/test_output/basmannyi_result.dwg --duration=1h --http-verb=PUT
```

Сохранить их в переменные окружения:

```bash
export INPUT_URL="https://storage.googleapis.com/btibot-queue/test_input/basmannyi_test.zip?..."
export OUTPUT_URL="https://storage.googleapis.com/btibot-processed/test_output/basmannyi_result.dwg?..."
```

---

## ⚙️ **3️⃣ Подготовить WorkItem JSON**

Создать файл `bte-appbundle/workitems/workitem_basmannyi.json`:

```json
{
  "activityId": "BotBti.BTEInsertActivity+1",
  "arguments": {
    "HostDWG": {
      "url": "${INPUT_URL}",
      "verb": "get"
    },
    "ResultDWG": {
      "url": "${OUTPUT_URL}",
      "verb": "put"
    }
  }
}
```

---

## 🚀 **4️⃣ Запустить тест через Python**

```bash
python bte-appbundle/scripts/test_workitem.py --payload bte-appbundle/workitems/workitem_basmannyi.json
```

Скрипт выполнит:

- ✅ Отправку WorkItem на APS
- ✅ Ожидание завершения (polling)
- ✅ Скачивание отчёта (report.log)
- ✅ Сохранение в bte-appbundle/reports/basmannyi_report.log

---

## 🔍 **5️⃣ Проверить результат**

Проверить, что команда вставки выполнилась:

```bash
bash bte-appbundle/scripts/verify_report.sh bte-appbundle/reports/basmannyi_report.log
```

✅ **Успешный результат:**

```
Command: INSERTBTE
Command: QSAVE
Command: QUIT
BytesDownloaded: > 10000
Duration: < 5s
```

---

## 📦 **6️⃣ Сохранить артефакты**

```bash
# Архив
gcloud storage cp basmannyi_test.zip gs://btibot-processed/archives/

# Отчёт
gcloud storage cp bte-appbundle/reports/basmannyi_report.log gs://btibot-processed/logs/

# Результат (уже сохранён через WorkItem)
# gs://btibot-processed/test_output/basmannyi_result.dwg
```

---

## 💾 **7️⃣ Коммит в GitHub**

```bash
git add bte-appbundle/workitems/workitem_basmannyi.json bte-appbundle/reports/basmannyi_report.log
git commit -m "🧩 Add Basmannyi DWG AppBundle test and report"
git push origin feature/create-appbundle
```

---

## ✅ **Ожидаемый результат**

| Этап | Результат |
|------|-----------|
| Найден DWG | ✅ |
| ZIP создан | ✅ |
| Signed URLs | ✅ |
| WorkItem отправлен | ✅ |
| INSERTBTE выполнен | ✅ |
| Result DWG сохранён | ✅ |
| Report.log содержит команды | ✅ |
| Коммит на GitHub | ✅ |

---

## 📋 **Структура проекта**

```
bte-appbundle/
├── workitems/
│   └── workitem_basmannyi.json
├── scripts/
│   ├── test_workitem.py
│   └── verify_report.sh
├── reports/
│   └── basmannyi_report.log
└── archives/
    └── basmannyi_test.zip
```

---

## 🔧 **Автоматизация (одна команда)**

Полный процесс можно выполнить одним скриптом:

```bash
bash bte-appbundle/scripts/run_full_test.sh
```

Этот скрипт автоматически:
1. Скачает DWG из GCS
2. Создаст ZIP архив
3. Сгенерирует signed URLs
4. Создаст WorkItem JSON
5. Запустит тест на APS
6. Проверит результат
7. Сохранит все артефакты

---

## 🚨 **Проверка статуса**

После запуска теста можно проверить статус:

```bash
# Проверить логи
cat bte-appbundle/reports/basmannyi_report.log

# Проверить результат в GCS
gcloud storage ls -l gs://btibot-processed/test_output/basmannyi_result.dwg

# Скачать результат для визуальной проверки
gcloud storage cp gs://btibot-processed/test_output/basmannyi_result.dwg ./basmannyi_result_FINAL.dwg
```

---

✨ **Готово к выполнению!**

