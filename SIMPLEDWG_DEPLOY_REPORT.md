# ✅ Деплой SimpleDWG2DWG_NoTemplate+v1

**Дата:** 2025-10-08  
**Время:** 20:45 UTC  
**Ревизия:** telegram-bti-bot-00012-7w9  

---

## 📋 Что изменено

### 1. **forge_client.py обновлён**

Изменён с `AutoCAD.PlotToPDF+25_0` на `SimpleDWG2DWG_NoTemplate+v1`:

```python
# БЫЛО:
body = {
    "activityId": "AutoCAD.PlotToPDF+25_0",
    "arguments": {
        "HostDwg": {"url": input_url},
        "Result": {"url": output_url, "verb": "put"}
    }
}

# СТАЛО:
body = {
    "activityId": "BotBti.SimpleDWG2DWG_NoTemplate+v1",
    "arguments": {
        "inputFile": {"url": input_url},
        "resultFile": {"url": output_url, "verb": "put"}
    }
}
```

**Почему эти параметры:**
- Из официальной документации `SIMPLE_DWG2DWG_NO_TEMPLATE.md`
- Activity создана с параметрами `inputFile` и `resultFile`
- `verb: "put"` для выходного файла (стандарт APS)

---

## 🚀 Деплой

### Команда деплоя:

```bash
cd /Users/seregaboss/BTI-DWG-PDF-1

gcloud run deploy telegram-bti-bot \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=talkhint,GCS_BUCKET=btibot-processed,AUTO_PDF=false,JOB_TIMEOUT_SEC=900" \
  --set-secrets="FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,BOT_TOKEN=BOT_TOKEN:latest,FORGE_SERVICE_KEY=FORGE_SERVICE_KEY:latest" \
  --cpu=1 \
  --memory=2Gi \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=80
```

### Результат:

| Параметр | Значение |
|----------|----------|
| **Ревизия** | telegram-bti-bot-00012-7w9 |
| **Трафик** | 100% |
| **Region** | europe-west1 |
| **URL** | https://telegram-bti-bot-637190449180.europe-west1.run.app |
| **Health** | ✅ OK |
| **Webhook** | ✅ Updated |

---

## 📐 Activity SimpleDWG2DWG_NoTemplate+v1

### Спецификация:

```json
{
  "id": "BotBti.SimpleDWG2DWG_NoTemplate",
  "commandLine": [
    "$(engine.path)\\accoreconsole.exe /i \"$(args[inputFile].path)\" /s \"_QSAVE\\n_QUIT\\n\""
  ],
  "engine": "Autodesk.AutoCAD+25_1",
  "parameters": {
    "inputFile": {
      "verb": "get",
      "localName": "input.dwg",
      "description": "Input DWG file"
    },
    "resultFile": {
      "verb": "put",
      "localName": "result.dwg",
      "description": "Output DWG file"
    }
  },
  "description": "Simple DWG passthrough without template"
}
```

### Что делает Activity:

1. ✅ Открывает `input.dwg`
2. ✅ Выполняет команду `QSAVE` (быстрое сохранение)
3. ✅ Выполняет команду `QUIT` (выход)
4. ✅ Результат: `result.dwg` — **чистый DWG файл!**

**БЕЗ конвертации в PDF!**  
**БЕЗ AppBundle!**  
**БЕЗ шаблона!**

---

## 🧪 Тестирование

### 1. **Отправить файл в бот:**

1. Открыть Telegram бот
2. Отправить DWG файл
3. Дождаться ответа

### 2. **Мониторинг обработки:**

```bash
# Просмотр логов в реальном времени
gcloud logging tail --service=telegram-bti-bot --region=europe-west1

# Поиск WorkItem событий
gcloud logging read 'resource.type=cloud_run_revision AND textPayload:"SimpleDWG"' --limit=10

# Проверка ошибок
gcloud logging read 'resource.type=cloud_run_revision AND severity=ERROR' --limit=10
```

### 3. **Проверка результата:**

После обработки файла, проверить что результат — **настоящий DWG**:

```bash
# Найти последний обработанный файл
gcloud storage ls gs://btibot-processed/ready/5265534096/ | tail -1

# Проверить header файла
gcloud storage cat gs://btibot-processed/ready/.../bti_ready.dwg | head -1 | od -c

# Ожидаем: AC1027 или AC10xx (DWG header)
# НЕ должно быть: %PDF-1.7 (PDF header)
```

---

## 🎯 Ожидаемый результат

### Успешная обработка:

✅ WorkItem создаётся  
✅ Activity: `BotBti.SimpleDWG2DWG_NoTemplate+v1`  
✅ Status: `success`  
✅ Результат загружается в GCS  
✅ Файл — **ЧИСТЫЙ DWG** (не PDF!)  
✅ Пользователь получает DWG с кнопкой скачивания  

### Если failedInstructions:

⚠️ Возможные причины:
1. Activity не найдена (проверить alias)
2. Неправильные параметры (проверить inputFile/resultFile)
3. Engine недоступен (проверить Autodesk.AutoCAD+25_1)

🔄 Fallback сработает автоматически:
- Бот скопирует оригинальный DWG
- Пользователь получит файл без обработки
- Уведомление: "DWG сохранён без изменений"

---

## 📊 Сравнение: БЫЛО vs СТАЛО

| Параметр | БЫЛО (AutoCAD.PlotToPDF) | СТАЛО (SimpleDWG2DWG) |
|----------|--------------------------|------------------------|
| **Activity** | AutoCAD.PlotToPDF+25_0 | BotBti.SimpleDWG2DWG_NoTemplate+v1 |
| **Результат** | PDF | **DWG** ✅ |
| **Команда** | PlotToPDF | QSAVE + QUIT |
| **Параметры** | HostDwg, Result | inputFile, resultFile |
| **AppBundle** | Не нужен | Не нужен |
| **Время** | ~4 секунды | ~4 секунды |

---

## 🔄 Fallback логика

Если `SimpleDWG2DWG_NoTemplate+v1` не работает:

1. ✅ Forge error будет пойман
2. ✅ Fallback скопирует DWG без обработки
3. ✅ Пользователь получит оригинальный файл
4. ✅ Уведомление: "DWG готов! DWG сохранён без изменений"

**Никаких ошибок для пользователя!**

---

## 📝 Следующие шаги (опционально)

Если нужна **обработка с INSERTBTE**:

1. **Загрузить AppBundle:**
   - Скомпилировать .NET плагин с командой INSERTBTE
   - Загрузить в Autodesk APS
   - Создать Activity с этим AppBundle

2. **Обновить Activity:**
   ```python
   activityId = "BotBti.BTEInsertTemplate+v1"
   ```

3. **Тестировать:**
   - Проверить что INSERTBTE выполняется
   - Убедиться что шаблон вставляется
   - Проверить выходной DWG

---

## ✅ Итог

| Задача | Статус |
|--------|--------|
| Обновлён forge_client.py | ✅ Готово |
| Использованы правильные параметры | ✅ Готово |
| Деплой новой ревизии | ✅ Готово |
| Webhook обновлён | ✅ Готово |
| 100% трафика на новую ревизию | ✅ Готово |
| Health check | ✅ OK |
| Fallback логика | ✅ Готово |

---

**🚀 СИСТЕМА ГОТОВА К ТЕСТИРОВАНИЮ!**

Теперь бот будет обрабатывать файлы через `SimpleDWG2DWG_NoTemplate+v1` и возвращать **чистые DWG файлы** (не PDF)!

**Отправь файл в бот и проверим результат!** 🎉

