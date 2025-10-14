# 🪟 Windows Execution Guide — Компиляция и публикация BTI_InsertBasman

> **Платформа:** Windows 10/11  
> **Требования:** PowerShell 7+, Python 3.10+, Visual Studio Build Tools, Git

---

## 🎯 Цель

Скомпилировать .NET плагин `BTI_InsertBasman`, загрузить AppBundle в Autodesk APS, обновить Activity и протестировать 5 DWG-файлов.

---

## ⚙️ ШАГ 1 — Подготовка среды

### 1.1 Проверка установленных инструментов

```powershell
# Проверка PowerShell (требуется 7+)
pwsh --version

# Проверка Python (требуется 3.10+)
python --version

# Проверка Git
git --version

# Проверка MSBuild (.NET компилятор)
dotnet --version
```

**Ожидаемый результат:**
```
PowerShell 7.x.x
Python 3.10+ / 3.11 / 3.12
Git 2.x.x
.NET SDK 8.x.x или 7.x.x
```

### 1.2 Клонирование репозитория

```powershell
# Перейти в рабочую директорию
cd C:\Projects  # или любая другая

# Клонировать репозиторий
git clone https://github.com/Sergalmazfas/BTI-DWG-PDF.git
cd BTI-DWG-PDF

# Переключиться на ветку release/gold1
git checkout release/gold1

# Проверить наличие файлов
ls Build-BTI-AppBundle.ps1
ls BTI_TemplateAppBundle\BTI_InsertBasman.cs
```

**✅ Критерий успеха:** Все файлы найдены.

---

## 🧰 ШАГ 2 — Сборка .NET-плагина

### 2.1 Запуск автоматической сборки

```powershell
# ONE-CLICK сборка
pwsh .\Build-BTI-AppBundle.ps1
```

### 2.2 Проверка результата

**Ожидаемый вывод:**
```
==> Build
Microsoft (R) Build Engine version X.X.X
...
Build succeeded.

==> Pack bundle
...

==> Bundle ready: .\out\BTI_InsertBasman.bundle.zip (SHA256=abc123...)
```

**✅ Критерий успеха:**
- Создан файл: `out\BTI_InsertBasman.bundle.zip`
- Отображается SHA256-хэш
- Размер bundle > 0 KB

### 2.3 Сохранить SHA256

```powershell
# Скопировать хэш в буфер обмена (для отчёта)
(Get-FileHash .\out\BTI_InsertBasman.bundle.zip -Algorithm SHA256).Hash | Set-Clipboard
Write-Host "SHA256 скопирован в буфер обмена"
```

---

## 📦 ШАГ 3 — Загрузка AppBundle в Autodesk APS

### 3.1 Настройка переменных окружения

```powershell
# Указать APS креды (ОДИН РАЗ)
setx APS_CLIENT_ID "<твой_CLIENT_ID>"
setx APS_CLIENT_SECRET "<твой_CLIENT_SECRET>"

# ⚠️ ВАЖНО: Закрыть и заново открыть PowerShell!
exit
```

### 3.2 Проверка переменных

```powershell
# Проверить, что переменные установлены
echo $env:APS_CLIENT_ID
echo $env:APS_CLIENT_SECRET
```

**✅ Критерий успеха:** Обе переменные отображаются корректно.

### 3.3 Установка Python зависимостей

```powershell
# Установить requests (если ещё не установлен)
pip install requests
```

### 3.4 Загрузка AppBundle

```powershell
# Запустить скрипт загрузки
python .\upload_bti_appbundle.py `
  --bundle .\out\BTI_InsertBasman.bundle.zip `
  --appname BTI.InsertBasman `
  --alias v1
```

**Ожидаемый вывод:**
```
✅ OAuth2 токен получен
🗑️  Старый AppBundle удалён (или не существовал)
📦 Создание AppBundle: BTI_InsertBasman
✅ AppBundle создан! ID: BTI.InsertBasman, Version: 1
📤 Загрузка bundle.zip в APS...
✅ AppBundle загружен успешно!
🔖 Создание alias v1...
✅ Alias v1 создан для AppBundle BTI.InsertBasman

📋 РЕЗУЛЬТАТ:
AppBundle ID: BTI.InsertBasman+v1
Upload status: 200
```

**✅ Критерий успеха:**
- В ответе есть `"id": "BTI.InsertBasman+v1"`
- Upload status: 200

### 3.5 Сохранить вывод

```powershell
# Повторить команду с сохранением в файл
python .\upload_bti_appbundle.py `
  --bundle .\out\BTI_InsertBasman.bundle.zip `
  --appname BTI.InsertBasman `
  --alias v1 > appbundle_upload_result.txt
```

---

## 🔁 ШАГ 4 — Обновление Activity в Autodesk APS

### 4.1 Получить OAuth токен

```powershell
# Запустить скрипт получения токена
python .\get_aps_token.py
```

**Ожидаемый вывод:**
```
✅ Токен получен (действует 60 минут)

ACCESS_TOKEN=eyJhbGc...

💡 Для использования в PowerShell:
$ACCESS_TOKEN = "eyJhbGc..."
```

### 4.2 Скопировать токен в переменную

```powershell
# Скопировать из вывода и вставить:
$ACCESS_TOKEN = "eyJhbGc..."
```

### 4.3 Обновить Activity

```powershell
# Обновить Activity (связать с новым AppBundle)
pwsh .\Update-Activity.ps1 `
  -AccessToken $ACCESS_TOKEN `
  -ActivityId "BotBti.DWG2DWGCopy+v1" `
  -AppBundleFull "BTI.InsertBasman+v1"
```

**Ожидаемый вывод:**
```
Activity BotBti.DWG2DWGCopy+v1 updated with BTI.InsertBasman+v1
```

**✅ Критерий успеха:** Нет ошибок, Activity обновлена.

---

## 🧪 ШАГ 5 — Тестирование WorkItem (5 файлов DWG)

### 5.1 Подготовка тестовых файлов

Подготовить 5 разных DWG файлов:
- Малый (< 100 KB)
- Средний (100-500 KB)
- Большой (> 500 KB)
- С внешними ссылками (если есть)
- С кириллицей в имени (будет нормализовано)

### 5.2 Отправка через Telegram бота

```powershell
# Открыть бот: @ZamerProbot
# Отправить 5 DWG файлов по очереди
```

### 5.3 Мониторинг логов

```powershell
# На Mac/Linux (через gcloud CLI):
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=telegram-bti-bot" --limit=50 --format=json
```

### 5.4 Проверка результатов

Для каждого файла проверить:
- ✅ Статус WorkItem: `success`
- ✅ Время обработки: ≤ 5 секунд
- ✅ Шаблон БТИ вставлен (открыть DWG в AutoCAD)
- ✅ Нет `failedInstructions` или `failedDownload`

### 5.5 Заполнить таблицу результатов

Открыть `BTI_NET_APPBUNDLE_TASK_REPORT_TEMPLATE.md` и заполнить:

| # | Файл | Размер | Время (сек) | Результат | Шаблон вставлен? |
|---|------|--------|-------------|-----------|------------------|
| 1 | test_1.dwg | 50 KB | 3.8 | ✅ | ✅ |
| 2 | test_2.dwg | 200 KB | 4.1 | ✅ | ✅ |
| ... | ... | ... | ... | ... | ... |

---

## 🧾 ШАГ 6 — Отчётность

### 6.1 Создать отчёт

```powershell
# Скопировать шаблон
cp BTI_NET_APPBUNDLE_TASK_REPORT_TEMPLATE.md BTI_NET_APPBUNDLE_TASK_REPORT.md

# Открыть в редакторе
notepad BTI_NET_APPBUNDLE_TASK_REPORT.md
```

### 6.2 Заполнить отчёт

Заполнить все секции:
- ✅ AppBundle ID и SHA256
- ✅ Результаты компиляции
- ✅ Результаты тестирования (5 файлов)
- ✅ Логи WorkItem
- ✅ Скриншоты/фрагменты (опционально)

### 6.3 Проверить Acceptance Criteria

| Критерий | Статус |
|----------|--------|
| AppBundle загружен в APS | ✅ |
| Activity обновлён | ✅ |
| .NET плагин компилируется | ✅ |
| 5/5 тестов успешны | ✅ |
| Шаблон БТИ вставляется | ✅ |
| Время ≤ 5 сек | ✅ |
| Нет `failedInstructions` | ✅ |
| Логи чистые | ✅ |

---

## 🔁 ШАГ 7 — Публикация итогов

### 7.1 Коммит в Git

```powershell
# Добавить отчёт
git add BTI_NET_APPBUNDLE_TASK_REPORT.md
git add appbundle_upload_result.txt

# Создать коммит
git commit -m "✅ AppBundle BTI.InsertBasman интегрирован и протестирован"

# Отправить в GitHub
git push origin release/gold1
```

### 7.2 Создать тег (опционально)

```powershell
# Создать тег релиза
git tag -a v1.0.0-bti-appbundle -m "BTI AppBundle v1.0.0 - First stable release"
git push origin v1.0.0-bti-appbundle
```

---

## 📚 Контрольные требования

- ✅ Только боевой Autodesk APS (никаких моков)
- ✅ Все токены и ключи из переменных окружения
- ✅ Время обработки ≤ 5 секунд
- ✅ Все 5 тестов успешны
- ✅ Шаблон БТИ вставляется через .NET (`Database.Insert()`)
- ✅ После успеха можно создать prod alias: `BTI.InsertBasman+prod`

---

## 🧯 Частые проблемы и решения

### Проблема: "DLL not found" при сборке

**Решение:**
```powershell
# Установить .NET SDK
winget install Microsoft.DotNet.SDK.8

# Проверить установку
dotnet --version
```

### Проблема: "ModuleNotFoundError: No module named 'requests'"

**Решение:**
```powershell
pip install requests
```

### Проблема: "APS_CLIENT_ID is not set"

**Решение:**
```powershell
# Установить переменные и ПЕРЕЗАПУСТИТЬ PowerShell
setx APS_CLIENT_ID "your_id"
setx APS_CLIENT_SECRET "your_secret"
exit
# Открыть новый PowerShell
```

### Проблема: "Activity update failed: 401 Unauthorized"

**Решение:**
```powershell
# Получить новый токен (старый истёк через 60 минут)
python .\get_aps_token.py
$ACCESS_TOKEN = "новый_токен"
```

### Проблема: "failedInstructions" в WorkItem

**Решение:**
1. Проверить логи accoreconsole в APS Report URL
2. Убедиться, что плагин загружается через `/al`
3. Проверить, что `Database.Insert()` выполняется без ошибок

---

## 🎉 Итого

После выполнения всех шагов:
- ✅ Плагин скомпилирован
- ✅ AppBundle загружен в APS
- ✅ Activity обновлена
- ✅ 5 тестов пройдены
- ✅ Отчёт создан и опубликован

**🚀 Система готова к продакшену!**

---

**Дата создания:** 2025-10-11  
**Версия:** 1.0.0

