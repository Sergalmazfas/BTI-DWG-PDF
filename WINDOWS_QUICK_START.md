# ⚡ БЫСТРЫЙ СТАРТ НА WINDOWS

**Время выполнения:** 15-30 минут  
**Требования:** Windows 10/11, PowerShell

---

## 🚀 Шаг 1: Установка окружения (один раз)

### **Запустите PowerShell от администратора:**

```powershell
# Python 3.11
winget install --id Python.Python.3.11 -e --source winget

# Git
winget install --id Git.Git -e --source winget

# 7zip
winget install --id 7zip.7zip -e --source winget

# Visual Studio Build Tools
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --source winget `
  --override "--quiet --wait --norestart --nocache --installPath C:\BuildTools `
  --add Microsoft.VisualStudio.Workload.ManagedDesktopBuildTools `
  --add Microsoft.Net.Component.4.8.TargetingPack `
  --add Microsoft.Net.ComponentGroup.DevelopmentPrerequisites"
```

**Перезапустите PowerShell после установки!**

---

## 📦 Шаг 2: Клонирование репозитория

```powershell
git clone https://github.com/Sergalmazfas/BTI-DWG-PDF.git
cd BTI-DWG-PDF
git checkout release/gold1
```

---

## 🔐 Шаг 3: Настройка credentials

```powershell
# Установить APS креды (получить из Google Secret Manager)
setx APS_CLIENT_ID "your_client_id_here"
setx APS_CLIENT_SECRET "your_client_secret_here"

# Перезапустить PowerShell для применения
exit
```

**Откройте новый PowerShell и проверьте:**
```powershell
cd BTI-DWG-PDF
echo $env:APS_CLIENT_ID
echo $env:APS_CLIENT_SECRET
```

---

## 🏗️ Шаг 4: Сборка AppBundle (ONE-CLICK!)

```powershell
pwsh .\Build-BTI-AppBundle.ps1
```

**Ожидаемый вывод:**
```
✅ Компиляция успешна!
✅ DLL создан: XXXXX bytes
✅ Bundle создан: XXXXX bytes
✅ SHA256: [хэш]
```

**Результат:** `out/BTI_InsertBasman.bundle.zip` готов к загрузке!

---

## ☁️ Шаг 5: Загрузка в APS

```powershell
# Установить зависимости
pip install requests

# Загрузить AppBundle
python upload_bti_appbundle.py --bundle .\out\BTI_InsertBasman.bundle.zip
```

**Ожидаемый вывод:**
```
✅ OAuth2 токен получен
✅ AppBundle создан: BTI_InsertBasman
✅ ZIP загружен успешно
✅ Alias v1 создан
✅ Activity создан: BotBti.DWG2DWG_InsertBasman
✅ Alias v1 создан для Activity

╔══════════════════════════════════════════════════════════╗
║              ✅ УСПЕХ! APPBUNDLE ЗАГРУЖЕН!              ║
╚══════════════════════════════════════════════════════════╝
```

---

## 🧪 Шаг 6: Обновление бота (на Mac/Linux)

```bash
# На вашей Mac машине
cd /Users/seregaboss/BTI-DWG-PDF-1

# Обновить forge_client.py (строка ~121):
# "activityId": "BotBti.DWG2DWG_InsertBasman+v1"

# Деплой
gcloud run deploy telegram-bti-bot \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=talkhint,GCS_BUCKET=btibot-processed,AUTO_PDF=false,JOB_TIMEOUT_SEC=900" \
  --set-secrets="FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,BOT_TOKEN=BOT_TOKEN:latest,FORGE_SERVICE_KEY=FORGE_SERVICE_KEY:latest" \
  --cpu=1 \
  --memory=2Gi \
  --timeout=300
```

---

## 📝 Шаг 7: Тестирование

### **Telegram бот:**
1. Откройте @ZamerProbot
2. /start
3. Загрузите DWG файл
4. Дождитесь обработки (~15-20 сек)
5. Скачайте result.dwg
6. Откройте в AutoCAD
7. ✅ Проверьте: шаблон Басманная вставлен!

### **Проверка логов:**
```bash
gcloud logging read \
  "resource.labels.service_name=telegram-bti-bot AND \
   textPayload:\"InsertBTIBasman\"" \
  --limit=20
```

**Ожидаемые логи:**
```
✅ BTI Insert Basmann Plugin v1.0 загружен
🔧 BTI INSERT BASMANN PLUGIN - START
✅ Template найден: template.dwg (52420 bytes)
✅ Template загружен в память
✅ Блок создан
✅ BlockReference добавлен в Model Space
✅ Transaction committed
💾 Сохранение result.dwg...
🎉 УСПЕХ! ШАБЛОН БАСМАННАЯ ВСТАВЛЕН!
📁 result.dwg создан (формат: AC1032)
```

---

## 🎯 Итого

**Шаги 1-5:** Выполняются на Windows (~15 минут)  
**Шаг 6:** Выполняется на Mac/Linux (~3 минуты)  
**Шаг 7:** Тестирование через Telegram

**Общее время:** ~20-30 минут

---

## 🚨 Если что-то не работает

### **Компиляция не удалась:**
- Проверьте что AutoCAD 2025 установлен
- Проверьте пути к DLLs в `.csproj`
- Запустите из "Developer PowerShell for VS 2022"

### **Загрузка AppBundle не удалась:**
- Проверьте `$env:APS_CLIENT_ID` и `$env:APS_CLIENT_SECRET`
- Проверьте что bundle.zip корректный
- Попробуйте загрузить через APS Web UI: https://aps.autodesk.com

### **Тесты провалились:**
- Проверьте логи Cloud Run
- Получите Report URL из WorkItem
- Убедитесь что Activity использует правильный AppBundle

---

**🎉 СЛЕДУЙТЕ ЭТИМ ШАГАМ И ШАБЛОН БТИ ЗАРАБОТАЕТ!**

