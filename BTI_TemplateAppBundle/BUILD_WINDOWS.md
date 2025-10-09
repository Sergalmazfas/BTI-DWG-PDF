# 🏗️ Компиляция BTI_InsertBasman на Windows

## 📋 Требования

- ✅ Windows 10/11
- ✅ Visual Studio 2019+ или MSBuild Tools
- ✅ AutoCAD 2025 (для .NET API DLLs)
- ✅ .NET Framework 4.8 SDK

---

## 🔧 Шаг 1: Проверка AutoCAD DLLs

Убедитесь что файлы существуют:

```cmd
dir "C:\Program Files\Autodesk\AutoCAD 2025\acdbmgd.dll"
dir "C:\Program Files\Autodesk\AutoCAD 2025\acmgd.dll"
dir "C:\Program Files\Autodesk\AutoCAD 2025\AcCoreMgd.dll"
```

Если AutoCAD установлен в другую папку, обновите пути в `BTI_InsertBasman.csproj`.

---

## 📦 Шаг 2: Компиляция

### **Через Visual Studio:**

1. Откройте `BTI_InsertBasman.csproj` в Visual Studio
2. Build → Build Solution (Release | x64)
3. Результат: `bin\Release\BTI_InsertBasman.dll`

### **Через Command Line:**

```cmd
cd BTI_TemplateAppBundle

REM Убедитесь что MSBuild в PATH
where msbuild

REM Компиляция
msbuild BTI_InsertBasman.csproj /p:Configuration=Release /p:Platform=x64 /t:Build /v:minimal

REM Проверка результата
dir bin\Release\BTI_InsertBasman.dll
```

**Ожидаемый вывод:**
```
bin\Release\BTI_InsertBasman.dll
bin\Release\PackageContents_Basmann.xml
```

---

## 🗜️ Шаг 3: Создание bundle.zip

### **PowerShell команды:**

```powershell
cd bin\Release

# Создать структуру
New-Item -ItemType Directory -Path "BTI_InsertBasman.bundle\Contents" -Force

# Копировать файлы
Copy-Item "PackageContents_Basmann.xml" "BTI_InsertBasman.bundle\PackageContents.xml"
Copy-Item "BTI_InsertBasman.dll" "BTI_InsertBasman.bundle\Contents\"

# Проверка структуры
tree /F BTI_InsertBasman.bundle

# Создать ZIP
Compress-Archive -Path "BTI_InsertBasman.bundle" -DestinationPath "BTI_InsertBasman.bundle.zip" -Force

Write-Host "`n✅ BTI_InsertBasman.bundle.zip создан!"
```

### **CMD команды:**

```cmd
cd bin\Release

mkdir BTI_InsertBasman.bundle\Contents

copy PackageContents_Basmann.xml BTI_InsertBasman.bundle\PackageContents.xml
copy BTI_InsertBasman.dll BTI_InsertBasman.bundle\Contents\

REM Создать ZIP через tar (Windows 10+)
tar -a -c -f BTI_InsertBasman.bundle.zip BTI_InsertBasman.bundle

echo ✅ BTI_InsertBasman.bundle.zip создан!
```

---

## ✅ Шаг 4: Проверка ZIP

```cmd
tar -tf BTI_InsertBasman.bundle.zip
```

**Ожидаемый вывод:**
```
BTI_InsertBasman.bundle/PackageContents.xml
BTI_InsertBasman.bundle/Contents/BTI_InsertBasman.dll
```

**Размер ZIP:** должен быть ~50-100 KB

---

## ☁️ Шаг 5: Загрузка в APS

### **Вариант A: Автоматически (Python):**

```bash
# Скопировать ZIP на Mac/Linux
scp bin\Release\BTI_InsertBasman.bundle.zip user@mac:/path/to/BTI-DWG-PDF-1/BTI_TemplateAppBundle/bin/Release/net48/

# На Mac/Linux запустить
python3 upload_bti_appbundle.py
```

### **Вариант B: Через APS Web UI:**

1. Откройте: https://aps.autodesk.com
2. My Apps → [Ваше приложение]
3. Design Automation → AppBundles
4. Click **"Create AppBundle"**
5. Заполните:
   - **Name:** `BTI_InsertBasman`
   - **Engine:** `Autodesk.AutoCAD+25_1`
   - **Upload:** `BTI_InsertBasman.bundle.zip`
6. Click **"Create"**
7. Создайте Alias:
   - **ID:** `v1`
   - **Version:** `1`

---

## 🎯 Шаг 6: Создание Activity

### **Через Web UI:**

1. Design Automation → Activities
2. Click **"Create Activity"**
3. Заполните:
   - **ID:** `DWG2DWG_InsertBasman`
   - **Engine:** `Autodesk.AutoCAD+25_1`
   - **AppBundles:** Select `BTI_InsertBasman+v1`
   - **Command Line:**
     ```
     $(engine.path)\accoreconsole.exe /i "$(args[inputFile].path)" /al "$(appbundles[BTI_InsertBasman].path)" /s "InsertBTIBasman\n"
     ```
   - **Parameters:**
     - `inputFile`: verb=get, localName=input.dwg
     - `templateFile`: verb=get, localName=template.dwg, url=https://storage.googleapis.com/btibot-processed/templates/basmanny-template.dwg
     - `resultFile`: verb=put, localName=result.dwg
4. Click **"Create"**
5. Создайте Alias `v1`

---

## 🧪 Шаг 7: Тестирование

```bash
# Обновите forge_client.py
# В строке ~121 измените:
activityId = "BotBti.DWG2DWG_InsertBasman+v1"

# Задеплойте бота
gcloud run deploy telegram-bti-bot ...

# Отправьте файл в Telegram @ZamerProbot
# Проверьте логи:
gcloud logging read "resource.labels.service_name=telegram-bti-bot AND textPayload:\"InsertBTIBasman\"" --limit=20
```

**Ожидаемые логи:**
```
✅ BTI Insert Basmann Plugin v1.0 загружен
🔧 BTI INSERT BASMANN PLUGIN - START
✅ Template найден: template.dwg
✅ Template загружен в память
✅ Блок создан
✅ BlockReference добавлен в Model Space
✅ Transaction committed
💾 Сохранение result.dwg...
🎉 УСПЕХ! ШАБЛОН БАСМАННАЯ ВСТАВЛЕН!
```

---

## ✅ Acceptance Criteria

| № | Критерий | Проверка |
|---|----------|----------|
| 1 | DLL скомпилирован | `dir BTI_InsertBasman.dll` ✅ |
| 2 | ZIP создан | `tar -tf *.zip` показывает правильную структуру ✅ |
| 3 | AppBundle загружен | APS Web UI показывает `BTI_InsertBasman+v1` ✅ |
| 4 | Activity создан | APS Web UI показывает `DWG2DWG_InsertBasman+v1` ✅ |
| 5 | WorkItem успешен | Status: `success`, result.dwg создан ✅ |
| 6 | Шаблон вставлен | AutoCAD открывает result.dwg с шаблоном Басманная ✅ |

---

## 📁 Итоговая структура

```
BTI_TemplateAppBundle/
├── BTI_InsertBasman.cs                        ✅ Исходный код
├── BTI_InsertBasman.csproj                    ✅ Проект
├── PackageContents_Basmann.xml                ✅ Манифест
├── BUILD_WINDOWS.md                           ✅ Эта инструкция
└── bin/
    └── Release/
        ├── BTI_InsertBasman.dll               ← Результат компиляции
        ├── PackageContents_Basmann.xml
        └── BTI_InsertBasman.bundle.zip        ← Готовый AppBundle
```

---

## 🎉 После успешной загрузки

Бот будет:
1. Принимать DWG файл от пользователя
2. Нормализовать имя (кириллица → латиница)
3. Отправлять в Autodesk APS
4. **Вставлять шаблон Басманная** через .NET плагин
5. Возвращать result.dwg с BTI шаблоном

**Success Rate: ожидается 100%!** 🚀

