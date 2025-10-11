# ✅ ФИНАЛЬНЫЙ ЧЕКЛИСТ - WINDOWS СБОРКА

**Цель:** Скомпилировать и загрузить .NET плагин для вставки шаблона БТИ  
**Требования:** Windows 10/11  
**Время:** 15-30 минут

---

## ☑️ ШАГ 0: Проверка окружения

```powershell
# Проверить установки
python --version        # Должно быть: Python 3.11.x
git --version          # Должно быть: git version 2.x
dotnet --version       # Должно быть: .NET SDK 6.0+
7z                     # Должно быть: 7-Zip

# Если чего-то нет - установите через winget (см. WINDOWS_QUICK_START.md)
```

**Критерий:** ✅ Все 4 команды работают

---

## ☑️ ШАГ 1: Клонирование репозитория

```powershell
git clone https://github.com/Sergalmazfas/BTI-DWG-PDF.git
cd BTI-DWG-PDF
git checkout release/gold1
git pull origin release/gold1
```

**Проверка файлов:**
```powershell
dir BTI_TemplateAppBundle\BTI_InsertBasman.cs
dir BTI_TemplateAppBundle\BTI_InsertBasman.csproj
dir BTI_TemplateAppBundle\PackageContents_Basmann.xml
dir Build-BTI-AppBundle.ps1
dir upload_bti_appbundle.py
```

**Критерий:** ✅ Все 5 файлов найдены

---

## ☑️ ШАГ 2: Настройка credentials

```powershell
# Установить переменные окружения
setx APS_CLIENT_ID "ваш_client_id"
setx APS_CLIENT_SECRET "ваш_client_secret"

# ОБЯЗАТЕЛЬНО перезапустить PowerShell!
exit
```

**Новый PowerShell:**
```powershell
cd BTI-DWG-PDF
echo $env:APS_CLIENT_ID      # Должно показать ваш ID
echo $env:APS_CLIENT_SECRET  # Должно показать ваш Secret
```

**Критерий:** ✅ Переменные отображаются

---

## ☑️ ШАГ 3: ONE-CLICK СБОРКА

```powershell
pwsh .\Build-BTI-AppBundle.ps1
```

**Проверка результата:**
```powershell
dir out\BTI_InsertBasman.bundle.zip
type build_report.txt
```

**Критерий:** 
- ✅ ZIP создан
- ✅ Размер 50-150 KB
- ✅ SHA256 в build_report.txt

---

## ☑️ ШАГ 4: ЗАГРУЗКА В APS

```powershell
python upload_bti_appbundle.py --bundle .\out\BTI_InsertBasman.bundle.zip
```

**Ожидаемый вывод:**
```
✅ AppBundle создан: BotBti.BTI_InsertBasman
✅ Alias v1 создан
✅ Activity создан: BotBti.DWG2DWG_InsertBasman
✅ УСПЕХ! APPBUNDLE ЗАГРУЖЕН!
```

**Критерий:** ✅ Сообщение "УСПЕХ"

---

## ☑️ ШАГ 5: ОБНОВЛЕНИЕ БОТА (на Mac)

**На Mac машине:**
```bash
cd /Users/seregaboss/BTI-DWG-PDF-1

# Редактировать forge_client.py строка ~121:
# Изменить: "activityId": "BotBti.DWG2DWGCopy+v1"
# На:       "activityId": "BotBti.DWG2DWG_InsertBasman+v1"

# Деплой
gcloud run deploy telegram-bti-bot \
  --source . \
  --region europe-west1 \
  --quiet
```

**Критерий:** ✅ Новая ревизия задеплоена

---

## ☑️ ШАГ 6: ТЕСТИРОВАНИЕ

### **Тест 1:**
```
Telegram → @ZamerProbot → /start → Загрузить test1.dwg
Дождаться → Скачать result.dwg → Открыть в AutoCAD
```

**Проверка:** ✅ Шаблон Басманная присутствует в чертеже

### **Тесты 2-5:**
Повторить с разными файлами (маленькие, большие, с кириллицей)

**Критерий:** ✅ 5/5 файлов обработаны со вставленным шаблоном

---

## ☑️ ШАГ 7: ПРОВЕРКА ЛОГОВ

```bash
gcloud logging read \
  "resource.labels.service_name=telegram-bti-bot AND \
   (textPayload:\"InsertBTIBasman\" OR textPayload:\"ШАБЛОН БАСМАННАЯ ВСТАВЛЕН\")" \
  --limit=20
```

**Ожидаемые строки:**
```
✅ BTI Insert Basmann Plugin v1.0 загружен
✅ Template найден: template.dwg
✅ Блок создан
🎉 УСПЕХ! ШАБЛОН БАСМАННАЯ ВСТАВЛЕН!
```

**Критерий:** ✅ Логи показывают успешную вставку

---

## 📊 ИТОГОВЫЙ ОТЧЁТ

После выполнения всех шагов:

```
✅ Шаг 0: Окружение готово
✅ Шаг 1: Репозиторий клонирован
✅ Шаг 2: Credentials настроены
✅ Шаг 3: AppBundle собран (SHA256: [хэш])
✅ Шаг 4: AppBundle загружен в APS
✅ Шаг 5: Бот обновлён
✅ Шаг 6: 5/5 тестов прошли
✅ Шаг 7: Логи подтверждают вставку шаблона

AppBundle ID: BotBti.BTI_InsertBasman+v1
Activity ID:  BotBti.DWG2DWG_InsertBasman+v1
Bundle SHA256: [хэш из build_report.txt]

p95 время обработки: XX секунд
Success Rate: 100%
```

---

## 🎯 ВЫВОД

**Шаблон БТИ применяется через .NET ✅**  
**Все тесты — PASS ✅**  
**Ошибок нет ✅**

---

**Следуйте этому чеклисту шаг за шагом!**

