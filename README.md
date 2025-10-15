# BTI DWG Processor Core — LISP v4 (IRON)

## 🎯 Цель

Автоматическая обработка 2D DWG (Leica DISTO Plan) через Autodesk APS/Forge Design Automation: применяем BTI-шаблон, расставляем маркеры дверей/окон, размеры и надписи. **Без PDF, без кадастра, без GPT, без 3D.**

---

## 🧱 Архитектура

```
Telegram → GCS (btibot-queue) → Forge WorkItem → GCS (btibot-processed/ready/bti_ready_<ts>.dwg)
```

**Компоненты:**
- **Telegram Bot** - приём DWG-файлов от пользователей
- **GCS Queue** - временное хранилище входящих файлов
- **Forge Design Automation** - обработка DWG через AutoCAD Core Engine
- **GCS Storage** - хранение готовых файлов
- **Cloud Run Services** - управление процессом

---

## 🔧 Технологии

- **Autodesk Design Automation** (AutoCAD+25_1)
- **Inline LISP** в `settings.script` (без .NET компиляции)
- **GCP Cloud Run**: `dwg-processor-core`, `forge-controller`, `forge-poller`, `telegram-bti-bot`
- **GCS Buckets**: 
  - `btibot-queue` (входящие файлы)
  - `btibot-processed/ready` (готовые файлы)

---

## ⚙️ Конфигурация (Environment Variables)

| Переменная | Значение | Назначение |
|------------|----------|------------|
| `FORGE_CLIENT_ID` | Secret Manager | Autodesk Forge Client ID |
| `FORGE_CLIENT_SECRET` | Secret Manager | Autodesk Forge Client Secret |
| `ACTIVITY_NAME` | `BotBti.BtiLISPActivity+prod` | Forge Activity для обработки |
| `GCS_BUCKET_INPUT` | `btibot-queue` | Входящие DWG |
| `GCS_BUCKET_OUTPUT` | `btibot-processed` | Готовые DWG |
| `PROCESS_CONCURRENCY` | `1` | Обработка одного файла за цикл |

---

## 📦 AppBundle / Activity

### AppBundle: `BotBti.BtiLISP+prod`
**Структура:**
```
BtiLISP.bundle/
├── PackageContents.xml
└── Contents/
    ├── BTI_PROCESS.lsp
    ├── BTI_MARKERS.lsp
    └── BTI_Template.dwg
```

### Activity: `BotBti.BtiLISPActivity+prod`
**Тип:** Inline LISP в `settings.script`

**Пример LISP-кода:**
```lisp
; Создание слоёв БТИ
(command "_.LAYER" "M" "BTI_WALLS" "C" "8" "" "")
(command "_.LAYER" "M" "BTI_MARKERS" "C" "2" "" "")
(command "_.LAYER" "M" "BTI_TEXT" "C" "7" "" "")

; Функция создания меток
(defun CREATE_MARKER (pt label / textPt)
  (command "_.LAYER" "S" "BTI_MARKERS" "")
  (command "_.POINT" pt "")
  (setq textPt (list (+ (car pt) 200.0) (cadr pt)))
  (command "_.TEXT" "J" "L" textPt 150.0 0.0 label "")
  (princ (strcat "\\n[BTI] Метка: " label))
)

; Создание меток
(CREATE_MARKER (list 1000.0 1500.0) "DOOR")
(CREATE_MARKER (list 2000.0 1500.0) "WINDOW")

; Сохранение результата
(command "_.ZOOM" "E")
(command "_.SAVEAS" "2018" "bti_ready.dwg")
(princ "\\n[BTI] ✅ COMPLETE")
```

---

## 🚀 Деплой (GCP Cloud Run)

### Деплой DWG Processor Core
```bash
gcloud run deploy dwg-processor-core \
  --source . \
  --region=europe-west1 \
  --project=talkhint \
  --set-env-vars ACTIVITY_NAME=BotBti.BtiLISPActivity+prod,GCS_BUCKET_INPUT=btibot-queue,GCS_BUCKET_OUTPUT=btibot-processed,PROCESS_CONCURRENCY=1
```

### Деплой вспомогательных сервисов
```bash
gcloud run deploy forge-controller --source . --region=europe-west1 --project=talkhint
gcloud run deploy forge-poller --source . --region=europe-west1 --project=talkhint
gcloud run deploy telegram-bti-bot --source . --region=us-central1 --project=talkhint
```

### Проверка статуса
```bash
gcloud run services list --project=talkhint
```

---

## ✅ Критерии готовности

- ✅ WorkItem завершается со статусом `success` за ≤ 70 секунд
- ✅ В логе присутствует: `[BTI] ✅ COMPLETE` и `SAVEAS bti_ready.dwg`
- ✅ В `btibot-processed/ready/` появляется файл `bti_ready_*.dwg`
- ✅ Размер выходного файла > входного (добавлены метки и слои)

---

## 🧪 Тестирование

### 1. Отправить DWG через Telegram
Отправьте .dwg файл боту

### 2. Проверить логи
```bash
gcloud logging read 'resource.labels.service_name=forge-poller AND textPayload:"WorkItem"' \
  --limit=30 --project=talkhint --format="value(timestamp,textPayload)"
```

Ожидаемый результат:
```
[BTI] Создание меток...
[BTI] Метка: DOOR
[BTI] Метка: WINDOW
[BTI] ✅ COMPLETE
```

### 3. Проверить результат в GCS
```bash
gsutil ls -lh gs://btibot-processed/ready/**/bti_ready*.dwg | tail -3
```

### 4. Локальный тест
```bash
python3 test_forge_production.py
```

---

## 🧹 Что исключено (v4.0.0)

- ❌ PDF конвертация
- ❌ Кадастр/Росреестр
- ❌ GPT/AI интеграции
- ❌ 3D обработка
- ❌ Цветовое распознавание (заменено на геометрическое)

---

## 📚 Документация

- **Официальная документация Autodesk:**  
  https://aps.autodesk.com/en/docs/design-automation/v3/tutorials/autocad/
- **Структура AppBundle:**  
  https://aps.autodesk.com/en/docs/design-automation/v3/reference/http/appbundles-POST/
- **Activity создание:**  
  https://aps.autodesk.com/en/docs/design-automation/v3/reference/http/activities-POST/

---

## 📁 Файловая структура

```
BTI-DWG-PDF-1/
├── app.py                          # Telegram Bot entry point
├── forge_controller.py             # Forge WorkItem controller
├── forge_client.py                 # Forge API client
├── gcs_queue_manager.py            # GCS queue management
├── inline_lisp_fixed.py            # Финальный тестовый скрипт
├── test_forge_production.py        # Продакшен тест
├── BtiLISP.zip                     # AppBundle v4
├── scripts/
│   ├── BTI_PROCESS.lsp             # Основная логика LISP
│   └── BTI_MARKERS.lsp             # Библиотека меток
├── templates/
│   └── BTI_Template.dwg            # Шаблон БТИ
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 🔍 Мониторинг

### Cloud Run логи
```bash
gcloud logging read 'resource.labels.service_name=dwg-processor-core' \
  --limit=50 --project=talkhint
```

### Forge WorkItem статус
```bash
gcloud logging read 'resource.labels.service_name=forge-poller' \
  --limit=20 --project=talkhint
```

---

## 🎯 Версия

**v4.0.0 "IRON"**  
- LISP inline solution
- 2D only processing
- No PDF/cadastre/GPT
- Production-ready

**Дата релиза:** 2025-10-15  
**Статус:** ✅ Production Ready
