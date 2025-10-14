# 📊 BTI AUTO Mode - Текущий статус

**Дата:** 2025-10-14  
**Ветка:** forge-plugin-gold  
**Статус:** ⏳ Частично готово

---

## ✅ Что готово:

### 1. Код
- ✅ `BTI_AUTO_APPLY.lsp` создан (84 строки)
- ✅ `forge_client.py` обновлен (режим "auto")
- ✅ `app.py` обновлен (режим по умолчанию "auto")
- ✅ Конфигурация Activity: `forge/activity_bti_auto.json`
- ✅ Все закоммичено в `forge-plugin-gold`

### 2. Cloud Run
- ✅ Сервис задеплоен: `telegram-bti-bot-00005-5wv`
- ✅ URL: https://telegram-bti-bot-637190449180.us-central1.run.app
- ✅ Режим: `simple` (работает)

### 3. AppBundle
- ✅ `BtiPlugin_auto.zip` создан (54 KB)
- ✅ Содержит `BTI_AUTO_APPLY.lsp`
- ✅ Готов к загрузке в APS
- ⏳ Ожидает загрузки (проблема с APS API)

---

## ⏳ Что нужно доделать:

### 1. Загрузить AppBundle в APS

**Проблема:** APS API возвращает `"Cannot parse id"` для всех операций с AppBundles.

**Решения:**

#### Вариант A: Через Postman (рекомендуется)
```
Инструкция: UPDATE_APPBUNDLE_POSTMAN.md
Файл: /tmp/bti_auto/BtiPlugin_auto.zip (54 KB)
```

#### Вариант B: Через Web UI
```
1. Зайти на https://aps.autodesk.com
2. Design Automation → AppBundles  
3. Создать новый или обновить BotBti.BtiAuto
4. Загрузить /tmp/bti_auto/BtiPlugin_auto.zip
```

### 2. Создать Activity BTI_AUTO_PROCESS

После загрузки AppBundle создай Activity через Postman:

```http
POST https://developer.api.autodesk.com/da/us-east/v3/activities
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "id": "BotBti.BTI_AUTO_PROCESS",
  "engine": "Autodesk.AutoCAD+25_1",
  "appbundles": ["BotBti.BtiAuto+$LATEST"],
  "commandLine": [
    "$(engine.path)\\accoreconsole.exe",
    "/i", "\"$(args[inputFile].path)\"",
    "/s", "\"$(appbundles[BtiAuto].path)/Contents/BTI_AUTO_APPLY.lsp\"",
    "/o", "\"$(args[outputFile].path)\""
  ],
  "parameters": {
    "inputFile": {...},
    "outputFile": {...}
  }
}
```

Затем создай alias:
```http
POST .../activities/BotBti.BTI_AUTO_PROCESS/aliases
{"id": "$LATEST", "version": 1}
```

### 3. Обновить константу в коде

```python
# В forge_client.py:
BTI_AUTO_PROCESS = "BotBti.BTI_AUTO_PROCESS+$LATEST"
```

### 4. Задеплоить с режимом AUTO

```bash
gcloud run deploy telegram-bti-bot \
  --source . \
  --region us-central1 \
  --update-env-vars BTI_PROCESSING_MODE=auto
```

---

## 🔄 Текущая работа (simple режим):

**Режим:** `simple`  
**Activity:** `BotBti.DWG2DWGCopy+v1`  
**Что делает:** Просто копирует DWG через WBLOCK  
**Статус:** ✅ Работает  

**Пример:**
```
Файл → Bot → Cloud Run → APS (WBLOCK) → Файл (копия) → Bot
```

---

## 🎯 Планируемая работа (auto режим):

**Режим:** `auto`  
**Activity:** `BotBti.BTI_AUTO_PROCESS+$LATEST`  
**AppBundle:** `BotBti.BtiAuto+$LATEST`  
**Что делает:**  
1. Находит слои MARK_DOOR и MARK_WINDOW
2. Вставляет блоки BTI_DOOR и BTI_WINDOW  
3. Автоматически сохраняет  

**Пример:**
```
Leica DWG → Bot → Cloud Run → APS (BTI_AUTO_APPLY.lsp) → BTI-чертеж → Bot
```

---

## 📋 Checklist

- [x] BTI_AUTO_APPLY.lsp создан
- [x] BtiPlugin_auto.zip создан (54 KB)
- [x] forge_client.py обновлен
- [x] app.py обновлен
- [x] Cloud Run задеплоен
- [ ] AppBundle загружен в APS
- [ ] Activity BTI_AUTO_PROCESS создана
- [ ] Режим переключен на 'auto'
- [ ] Протестирован с Leica DWG

---

## 🚀 После завершения:

Бот будет автоматически обрабатывать DWG файлы от Leica:
- Распознавать метки на слоях  
- Вставлять блоки БТИ
- Возвращать готовый чертеж

**Время обработки:** ~20-30 секунд

