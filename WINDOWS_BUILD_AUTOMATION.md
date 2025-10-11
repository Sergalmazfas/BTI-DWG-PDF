# 🏗️ АВТОМАТИЗАЦИЯ СБОРКИ .NET ПЛАГИНА - ПОЛНАЯ ИНСТРУКЦИЯ

**Task ID:** TASK-2025-10-09-NET-BUILD  
**Status:** Ready for Windows Execution  
**Branch:** release/gold1  
**Commit:** f810bca

---

## ⚠️ КРИТИЧЕСКОЕ: Выполняется ТОЛЬКО на Windows

Эта инструкция требует:
- ✅ Windows 10/11
- ✅ Visual Studio 2019+ с .NET Framework 4.8
- ✅ AutoCAD 2025 (для .NET API DLLs)
- ✅ Git для клонирования репозитория

---

## 📋 ФАЗА 0: Предварительные условия

### **Проверка файлов:**

```cmd
git clone https://github.com/Sergalmazfas/BTI-DWG-PDF.git
cd BTI-DWG-PDF
git checkout release/gold1
git pull origin release/gold1

REM Проверка наличия файлов
dir BTI_TemplateAppBundle\BTI_InsertBasman.cs
dir BTI_TemplateAppBundle\BTI_InsertBasman.csproj
dir BTI_TemplateAppBundle\PackageContents_Basmann.xml
dir BTI_TemplateAppBundle\BUILD_WINDOWS.md
dir upload_bti_appbundle.py
```

**Ожидаемый результат:**
```
✅ Все 5 файлов найдены
```

### **Настройка переменных окружения:**

```cmd
REM Установить креды APS (из Google Secret Manager)
setx APS_CLIENT_ID "ваш_client_id"
setx APS_CLIENT_SECRET "ваш_client_secret"

REM Перезапустить CMD для применения
exit
REM Открыть новый CMD и проверить:
echo %APS_CLIENT_ID%
echo %APS_CLIENT_SECRET%
```

**Критерий приёмки:**
- ✅ Файлы на месте
- ✅ Переменные окружения установлены

---

## 📋 ФАЗА 1: Сборка .NET-плагина

### **Шаг 1.1: Проверка Visual Studio**

```cmd
REM Найти MSBuild
where msbuild

REM Если не найден, добавить в PATH:
set PATH=%PATH%;C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin
```

### **Шаг 1.2: Проверка AutoCAD DLLs**

```cmd
dir "C:\Program Files\Autodesk\AutoCAD 2025\acdbmgd.dll"
dir "C:\Program Files\Autodesk\AutoCAD 2025\acmgd.dll"
dir "C:\Program Files\Autodesk\AutoCAD 2025\AcCoreMgd.dll"
```

**Если AutoCAD в другой папке:**
1. Откройте `BTI_InsertBasman.csproj`
2. Измените пути к DLL на правильные

### **Шаг 1.3: Компиляция**

```cmd
cd BTI_TemplateAppBundle

REM Очистка предыдущих сборок
rmdir /s /q bin
rmdir /s /q obj

REM Компиляция Release x64
msbuild BTI_InsertBasman.csproj /p:Configuration=Release /p:Platform=x64 /t:Build /v:minimal

REM Проверка результата
dir bin\Release\BTI_InsertBasman.dll
```

**Ожидаемый вывод:**
```
Build succeeded.
    0 Warning(s)
    0 Error(s)

✅ bin\Release\BTI_InsertBasman.dll создан
✅ Размер: ~50-100 KB
```

**Критерий приёмки:**
- ✅ `BTI_InsertBasman.dll` создан
- ✅ Без ошибок компиляции
- ✅ Размер > 0 bytes

---

## 📋 ФАЗА 2: Упаковка AppBundle

### **Шаг 2.1: Создание структуры bundle**

```powershell
cd bin\Release

# Создать папку bundle
New-Item -ItemType Directory -Path "BTI_InsertBasman.bundle\Contents" -Force

# Копировать файлы
Copy-Item "..\..\PackageContents_Basmann.xml" "BTI_InsertBasman.bundle\PackageContents.xml"
Copy-Item "BTI_InsertBasman.dll" "BTI_InsertBasman.bundle\Contents\"

# Проверка структуры
tree /F BTI_InsertBasman.bundle
```

**Ожидаемая структура:**
```
BTI_InsertBasman.bundle
├── PackageContents.xml
└── Contents
    └── BTI_InsertBasman.dll
```

### **Шаг 2.2: Создание ZIP**

```powershell
# PowerShell (рекомендуется)
Compress-Archive -Path "BTI_InsertBasman.bundle" -DestinationPath "BTI_InsertBasman.bundle.zip" -Force

# Проверка
Get-FileHash -Algorithm SHA256 BTI_InsertBasman.bundle.zip
(Get-Item BTI_InsertBasman.bundle.zip).Length
```

**Или через tar (Windows 10+):**
```cmd
tar -a -c -f BTI_InsertBasman.bundle.zip BTI_InsertBasman.bundle
```

### **Шаг 2.3: Проверка ZIP**

```cmd
tar -tf BTI_InsertBasman.bundle.zip
```

**Ожидаемый вывод:**
```
BTI_InsertBasman.bundle/PackageContents.xml
BTI_InsertBasman.bundle/Contents/BTI_InsertBasman.dll
```

**Критерий приёмки:**
- ✅ `BTI_InsertBasman.bundle.zip` создан
- ✅ Размер: 50-150 KB
- ✅ Структура корректна (2 файла внутри)
- ✅ SHA256 хэш зафиксирован

---

## 📋 ФАЗА 3: Публикация в APS

### **Шаг 3.1: Подготовка**

```cmd
REM Переместить ZIP в корень проекта
copy BTI_InsertBasman.bundle.zip ..\..\BTI_TemplateAppBundle\bin\Release\net48\

cd ..\..\..\

REM Установить Python зависимости
pip install requests google-cloud-secret-manager
```

### **Шаг 3.2: Загрузка через скрипт**

```cmd
python upload_bti_appbundle.py
```

**Скрипт автоматически:**
1. Получит токен OAuth2 от Autodesk
2. Создаст AppBundle `BTI_InsertBasman`
3. Загрузит ZIP через signed URL
4. Создаст alias `v1`
5. Создаст Activity `DWG2DWG_InsertBasman`
6. Создаст alias `v1` для Activity

**Ожидаемый вывод:**
```
✅ OAuth2 токен получен
🗑️  Старый AppBundle удалён (если был)
📦 Создание AppBundle: BTI_InsertBasman
✅ AppBundle создан: BTI_InsertBasman
   Version: 1
📤 Загрузка ZIP: BTI_TemplateAppBundle/bin/Release/net48/BTI_InsertBasman.bundle.zip
✅ ZIP загружен успешно
🏷️  Создание alias v1...
✅ Alias v1 создан
🎯 Создание Activity: DWG2DWG_InsertBasman
✅ Activity создан: BotBti.DWG2DWG_InsertBasman
   Version: 1
   AppBundles: ['BotBti.BTI_InsertBasman+v1']
✅ Alias v1 создан для Activity

╔══════════════════════════════════════════════════════════╗
║              ✅ УСПЕХ! APPBUNDLE ЗАГРУЖЕН!              ║
╚══════════════════════════════════════════════════════════╝

📋 СЛЕДУЮЩИЕ ШАГИ:

1. Обновите forge_client.py:
   activityId = "BotBti.DWG2DWG_InsertBasman+v1"

2. Задеплойте бота:
   gcloud run deploy telegram-bti-bot ...

3. Протестируйте через Telegram
```

### **Шаг 3.3: Сохранить артефакты**

```cmd
REM Сохранить SHA256 хэш ZIP
certutil -hashfile BTI_TemplateAppBundle\bin\Release\net48\BTI_InsertBasman.bundle.zip SHA256 > appbundle_sha256.txt

REM Скопировать для отчёта
copy appbundle_sha256.txt artifacts\
```

**Критерий приёмки:**
- ✅ AppBundle создан в APS
- ✅ Alias `BotBti.BTI_InsertBasman+v1` доступен
- ✅ Activity `BotBti.DWG2DWG_InsertBasman+v1` создан
- ✅ SHA256 хэш сохранён

---

## 📋 ФАЗА 4: Обновление бота

### **На Mac/Linux (после успешной загрузки AppBundle):**

```bash
cd /Users/seregaboss/BTI-DWG-PDF-1

# Обновить forge_client.py
# В строке ~121 изменить:
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
  --timeout=300 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=80
```

**Критерий приёмки:**
- ✅ Новая ревизия задеплоена
- ✅ Activity указан правильно
- ✅ Webhook активен

---

## 📋 ФАЗА 5: Тестирование (5 файлов)

### **Тест 1: Маленький файл**
```bash
# План ~17 KB
Telegram → @ZamerProbot → загрузить Plan_2025-10-03_155019_export_2D.dwg
```

### **Тест 2: Файл с кириллицей**
```bash
# Чертёж с русским именем
Telegram → @ZamerProbot → загрузить "Чертеж Басманная.dwg"
# Проверить: имя нормализовано → Chertezh_Basmannaia.dwg
```

### **Тест 3: Средний файл**
```bash
# Visualization ~974 KB
Telegram → @ZamerProbot → загрузить visualization_-_conference_room.dwg
```

### **Тест 4: Файл с пробелами**
```bash
# Имя с множественными пробелами
Telegram → @ZamerProbot → загрузить "Plan 2025 10 03.dwg"
# Проверить: Plan_2025_10_03.dwg
```

### **Тест 5: Крупный файл**
```bash
# > 1 MB если есть
```

### **Проверка каждого теста:**

```bash
# Логи
gcloud logging read \
  "resource.labels.service_name=telegram-bti-bot AND \
   textPayload:\"InsertBTIBasman\"" \
  --limit=30

# Ожидаемые логи:
# ✅ BTI Insert Basmann Plugin v1.0 загружен
# 🔧 BTI INSERT BASMANN PLUGIN - START
# ✅ Template найден: template.dwg
# ✅ Template загружен в память
# ✅ Блок создан
# ✅ BlockReference добавлен в Model Space
# 🎉 УСПЕХ! ШАБЛОН БАСМАННАЯ ВСТАВЛЕН!
# 📁 result.dwg создан (формат: AC1032)

# WorkItem статус
gcloud logging read \
  "resource.labels.service_name=telegram-bti-bot AND \
   textPayload:\"WorkItem\" AND \
   textPayload:\"success\"" \
  --limit=10
```

**Критерий приёмки:**
- ✅ 5/5 тестов прошли успешно
- ✅ Все файлы содержат шаблон БТИ
- ✅ Время обработки: 4-10 сек (p95)
- ✅ Нормализация работает
- ✅ БЕЗ ошибок в логах

---

## 📋 ФАЗА 6: Роллбэк и безопасность

### **Создание безопасного alias:**

```python
# В upload_bti_appbundle.py уже реализовано:
# 1. Создаётся version 1
# 2. Создаётся alias v1
# 3. Старый AppBundle НЕ удаляется (только если существует с тем же ID)
```

### **Быстрый откат:**

```bash
# Если новая версия не работает, откатываемся:
cd /Users/seregaboss/BTI-DWG-PDF-1

# В forge_client.py вернуть:
# "activityId": "BotBti.DWG2DWGCopy+v1"

gcloud run deploy telegram-bti-bot \
  --source . \
  --region europe-west1 \
  --quiet
```

**Время отката:** < 3 минуты

**Критерий приёмки:**
- ✅ Старый alias доступен для отката
- ✅ Откат занимает < 3 минут

---

## 📋 ФАЗА 7: Отчётность

### **Создать отчёт:**

```markdown
# ОТЧЁТ: Сборка и загрузка BTI .NET AppBundle

## Выполненные шаги:

1. ✅ Фаза 0: Файлы проверены
2. ✅ Фаза 1: BTI_InsertBasman.dll скомпилирован
   - Размер: XXX KB
   - SHA256: [хэш]
3. ✅ Фаза 2: BTI_InsertBasman.bundle.zip создан
   - Размер: XXX KB
   - SHA256: [хэш]
4. ✅ Фаза 3: AppBundle загружен в APS
   - AppBundle ID: BotBti.BTI_InsertBasman+v1
   - Activity ID: BotBti.DWG2DWG_InsertBasman+v1
5. ✅ Фаза 4: Бот обновлён
   - Ревизия: telegram-bti-bot-000XX-xxx
6. ✅ Фаза 5: Тесты пройдены
   - Success: 5/5
   - p95 время: XX сек
7. ✅ Фаза 6: Откат настроен

## Метрики:

| Тест | Файл | Размер вход | Размер выход | Время | Статус |
|------|------|-------------|--------------|-------|--------|
| 1    | Plan_...dwg | 16 KB | XX KB | X.X сек | ✅ |
| 2    | Chertezh_...dwg | XX KB | XX KB | X.X сек | ✅ |
| 3    | visualization...dwg | 974 KB | XX KB | X.X сек | ✅ |
| 4    | Plan_2025...dwg | XX KB | XX KB | X.X сек | ✅ |
| 5    | ...dwg | XX KB | XX KB | X.X сек | ✅ |

p95: XX секунд

## Артефакты:

SHA256 (bundle.zip): [хэш]
AppBundle ID: BotBti.BTI_InsertBasman+v1
Activity ID: BotBti.DWG2DWG_InsertBasman+v1

CommandLine:
$(engine.path)\\accoreconsole.exe /i "$(args[inputFile].path)" /al "$(appbundles[BTI_InsertBasman].path)" /s "InsertBTIBasman\n"

## Логи:

[Вставить ссылки на Cloud Run logs]

## Вывод:

✅ Шаблон БТИ применяется через .NET
✅ Все 5 тестов — PASS
✅ Время — XX сек p95
✅ Ошибок в логах нет
```

---

## 🎯 КОНТРОЛЬ КАЧЕСТВА

### **Требования Главного инженера:**

- ✅ Чистая интеграция (только боевой Autodesk APS)
- ✅ Ошибки API → в лог
- ✅ Время ответа ≤ 4 сек (цель)
- ✅ Только реальные результаты Activity

### **Проверка:**

```bash
# 1. Нет моков
grep -r "mock\|fake\|stub" forge_client.py
# Должно быть пусто

# 2. Реальные WorkItem IDs
gcloud logging read \
  "resource.labels.service_name=telegram-bti-bot AND \
   textPayload:\"WorkItem запущен\"" \
  --limit=5

# 3. Время обработки
gcloud logging read \
  "resource.labels.service_name=telegram-bti-bot AND \
   textPayload:\"завершен успешно\"" \
  --limit=5
```

---

## 📦 ИТОГОВЫЕ АРТЕФАКТЫ

После выполнения всех фаз:

1. ✅ `BTI_InsertBasman.dll` (скомпилированный плагин)
2. ✅ `BTI_InsertBasman.bundle.zip` (готовый AppBundle)
3. ✅ `appbundle_sha256.txt` (хэш для верификации)
4. ✅ AppBundle `BotBti.BTI_InsertBasman+v1` в APS
5. ✅ Activity `BotBti.DWG2DWG_InsertBasman+v1` в APS
6. ✅ Обновлённый `forge_client.py`
7. ✅ Задеплоенный `telegram-bti-bot`
8. ✅ Отчёт с метриками

---

## 🚨 ВАЖНЫЕ ПРИМЕЧАНИЯ

### **Если компиляция не удалась:**

1. Проверьте пути к AutoCAD DLLs в `.csproj`
2. Убедитесь что .NET Framework 4.8 SDK установлен
3. Запустите Visual Studio Developer Command Prompt

### **Если загрузка AppBundle не удалась:**

1. Проверьте переменные окружения `APS_CLIENT_ID`, `APS_CLIENT_SECRET`
2. Проверьте что ZIP корректный: `tar -tf *.zip`
3. Попробуйте загрузить через APS Web UI вручную

### **Если тесты провалились:**

1. Проверьте логи Cloud Run
2. Получите Report URL из WorkItem
3. Проверьте что Activity использует правильный AppBundle

---

## 🎯 СЛЕДУЮЩИЙ ШАГ

**НА WINDOWS ВЫПОЛНИТЕ:**

```cmd
cd C:\BTI-DWG-PDF\BTI_TemplateAppBundle
msbuild BTI_InsertBasman.csproj /p:Configuration=Release /p:Platform=x64
```

Затем следуйте этой инструкции шаг за шагом.

---

**Время выполнения всех фаз:** ~30-60 минут  
**Требуется:** Windows машина с Visual Studio и AutoCAD 2025

