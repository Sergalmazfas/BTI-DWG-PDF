# 🤖 Деплой AUTO режима с обработкой

## ✅ Что уже сделано:

1. ✅ Создан `BTI_AUTO_APPLY.lsp` - LISP скрипт с автозапуском
2. ✅ Создана конфигурация Activity `BTI_AUTO_PROCESS`
3. ✅ Обновлен `forge_client.py` с режимом "auto"
4. ✅ Обновлен `app.py` - режим по умолчанию: "auto"
5. ✅ Код закоммичен в ветку `forge-plugin-gold`

---

## 📋 Что нужно сделать:

### 1️⃣ Обновить AppBundle (добавить BTI_AUTO_APPLY.lsp)

```bash
# Создать bundle
mkdir -p /tmp/bti_auto/BtiPlugin.bundle/Contents
cp scripts/*.lsp /tmp/bti_auto/BtiPlugin.bundle/Contents/
cp templates/BTI_Template.dwg /tmp/bti_auto/BtiPlugin.bundle/Contents/bti_basmanny_template.dwg
cp forge/PackageContents.xml /tmp/bti_auto/BtiPlugin.bundle/

# Создать ZIP
cd /tmp/bti_auto
zip -r BtiPlugin_auto.zip BtiPlugin.bundle/

# Загрузить в APS (требует рабочие credentials)
# Используй upload_appbundle_v2.py или сделай через Postman
```

### 2️⃣ Создать Activity BTI_AUTO_PROCESS

Используй конфигурацию из `forge/activity_bti_auto.json`:

```json
{
  "id": "BotBti.BTI_AUTO_PROCESS",
  "engine": "Autodesk.AutoCAD+25_1",
  "appbundles": ["BotBti.BtiPlugin+$LATEST"],
  "commandLine": [
    "$(engine.path)\\accoreconsole.exe",
    "/i", "\"$(args[inputFile].path)\"",
    "/s", "\"$(appbundles[BtiPlugin].path)/Contents/BTI_AUTO_APPLY.lsp\"",
    "/o", "\"$(args[outputFile].path)\""
  ],
  ...
}
```

**Создание через API:**
```bash
cd /Users/seregaboss/BTI-DWG-PDF-1
python3 create_simple_activity.py
# (нужно адаптировать для BTI_AUTO_PROCESS)
```

### 3️⃣ Задеплоить Cloud Run с режимом AUTO

```bash
gcloud run deploy telegram-bti-bot \
  --source . \
  --region us-central1 \
  --set-env-vars='BTI_PROCESSING_MODE=auto' \
  --allow-unauthenticated
```

---

## 🔧 Что делает BTI_AUTO_APPLY.lsp:

```lisp
1. Загружается в AutoCAD при открытии файла
2. Автоматически выполняет BTI-AUTO-PROCESS:
   - Создает слои A-DOOR, A-WINDOW
   - Находит MARK_DOOR → вставляет BTI_DOOR
   - Находит MARK_WINDOW → вставляет BTI_WINDOW
   - Сохраняет файл (QSAVE)
3. Возвращает обработанный DWG
```

---

## ⚡ Быстрый деплой (только код, без APS)

Если хочешь сначала задеплоить код:

```bash
gcloud run deploy telegram-bti-bot \
  --source . \
  --region us-central1 \
  --allow-unauthenticated

# После этого обновить env var:
gcloud run services update telegram-bti-bot \
  --region us-central1 \
  --update-env-vars BTI_PROCESSING_MODE=auto
```

⚠️ **Но это не будет работать** пока не обновишь AppBundle и не создашь Activity!

---

## 🎯 Альтернатива: Вручную через Postman/Web UI

1. **AppBundle:**
   - Открыть https://aps.autodesk.com
   - Design Automation → AppBundles
   - Обновить `BotBti.BtiPlugin`
   - Загрузить `BtiPlugin_auto.zip`

2. **Activity:**
   - Design Automation → Activities
   - Create New: `BotBti.BTI_AUTO_PROCESS`
   - Использовать конфигурацию из `forge/activity_bti_auto.json`

3. **Деплой:**
   - Cloud Console → Cloud Run → telegram-bti-bot
   - Edit & Deploy New Revision
   - Environment: `BTI_PROCESSING_MODE=auto`
   - Deploy

---

## ✅ Проверка работы:

После деплоя отправь DWG файл в бота. Если есть слои `MARK_DOOR` и `MARK_WINDOW`, они должны быть обработаны!

Логи покажут:
```
🤖 Режим AUTO: Автоматическая BTI обработка
   ✅ Слоевое распознавание (MARK_DOOR, MARK_WINDOW)
   ✅ Вставка блоков (BTI_DOOR, BTI_WINDOW)
   ✅ Автозапуск при загрузке LISP
```

