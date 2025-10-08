# BTI Template AppBundle для Autodesk Design Automation

## 🎯 Назначение

.NET плагин для AutoCAD Design Automation API, который применяет BTI Template к DWG файлам.

---

## 📁 Структура

```
BTI_TemplateAppBundle/
├── BTI_TemplatePlugin.cs       # .NET код плагина
├── BTI_TemplatePlugin.csproj   # Файл проекта
├── PackageContents.xml         # Манифест AppBundle
├── BTI_Template.dwt            # Шаблон BTI (нужно добавить)
└── README.md                   # Эта инструкция
```

---

## 🔧 Компиляция

### **Требования:**
- .NET Framework 4.8 SDK
- Visual Studio 2019+ или MSBuild
- AutoCAD .NET API NuGet packages

### **Команды:**

**Windows:**
```cmd
cd BTI_TemplateAppBundle
dotnet restore
dotnet build -c Release
```

**После компиляции:**
```
bin/Release/net48/
├── BTI_TemplatePlugin.dll
├── BTI_Template.dwt
└── PackageContents.xml
```

---

## 📦 Создание AppBundle.zip

### **Структура zip:**
```
BTI_TemplateAppBundle.bundle/
├── PackageContents.xml
└── Contents/
    ├── BTI_TemplatePlugin.dll
    └── BTI_Template.dwt
```

### **Команда:**
```bash
cd bin/Release/net48
mkdir -p BTI_TemplateAppBundle.bundle/Contents
cp PackageContents.xml BTI_TemplateAppBundle.bundle/
cp BTI_TemplatePlugin.dll BTI_TemplateAppBundle.bundle/Contents/
cp BTI_Template.dwt BTI_TemplateAppBundle.bundle/Contents/
zip -r BTI_TemplateAppBundle.zip BTI_TemplateAppBundle.bundle/
```

---

## 🚀 Загрузка в Autodesk APS

### **Вариант 1: Через Python скрипт**
```bash
python3 ../create_and_upload_appbundle.py
```

### **Вариант 2: Через curl**
```bash
# 1. Создать AppBundle
curl -X POST https://developer.api.autodesk.com/da/us-east/v3/appbundles \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "<client_id>.BTI_TemplateAppBundle",
    "engine": "Autodesk.AutoCAD+25_1",
    "description": "BTI Template plugin"
  }'

# 2. Загрузить ZIP (используя uploadParameters из ответа)
curl -X POST "<upload_url>" \
  -F "file=@BTI_TemplateAppBundle.zip"

# 3. Создать alias
curl -X POST https://developer.api.autodesk.com/da/us-east/v3/appbundles/<client_id>.BTI_TemplateAppBundle/aliases \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "v1", "version": 1}'
```

### **Вариант 3: Через Forge Web UI** (РЕКОМЕНДУЕТСЯ)
1. Зайти на https://aps.autodesk.com
2. Design Automation → AppBundles → Create
3. Загрузить `BTI_TemplateAppBundle.zip`
4. Создать alias `v1` или `prod`

---

## 🧪 Тестирование

### **После загрузки AppBundle:**

```python
# Создать Activity использующую AppBundle
activity_data = {
    "id": f"{client_id}.BTI_DWG2DWG",
    "appbundles": [f"{client_id}.BTI_TemplateAppBundle+v1"],
    "commandLine": [
        "$(engine.path)\\accoreconsole.exe /al \"$(appbundles[BTI_TemplateAppBundle].path)\" /i \"$(args[inputFile].path)\" /s \"APPLYBTITEMPLATE\n\""
    ],
    "engine": "Autodesk.AutoCAD+25_1",
    "parameters": {
        "inputFile": {"verb": "get", "localName": "input.dwg"},
        "resultFile": {"verb": "put", "localName": "output.dwg"}
    }
}

# Создать WorkItem
workitem_data = {
    "activityId": f"{client_id}.BTI_DWG2DWG+v1",
    "arguments": {
        "inputFile": {"url": "https://storage.googleapis.com/.../input.dwg"},
        "resultFile": {"url": "https://storage.googleapis.com/.../output.dwg", "verb": "put"}
    }
}
```

---

## ⚠️ ВАЖНЫЕ ЗАМЕЧАНИЯ

### **1. Компиляция на Windows:**
Этот проект требует компиляции на Windows с установленным AutoCAD .NET API.

### **2. BTI_Template.dwt:**
Нужно добавить реальный файл шаблона в директорию проекта.

### **3. API Limitations:**
- ❌ Autodesk API `/aliases` endpoint может не работать с длинными Client IDs
- ✅ Решение: Создавать aliases через Forge Web UI

### **4. Альтернативное решение:**
Если компиляция .NET невозможна, использовать:
- **AutoCAD Script (.scr)** вместо .NET
- **LISP скрипт (.lsp)** для простых операций
- **Стандартную Activity** `AutoCAD.PlotToPDF+25_0`

---

## 🔄 Fallback стратегия

Если AppBundle не работает, система автоматически использует:
- **Локальную обработку** через `ezdxf` (Python)
- **Стандартную Activity** для PDF конвертации

---

## 📊 Статус

- ✅ Код .NET создан
- ⚠️ Требуется компиляция на Windows
- ⚠️ Требуется BTI_Template.dwt
- ⚠️ Требуется загрузка через Web UI (API ограничения)

**Для немедленного использования: используйте `AutoCAD.PlotToPDF+25_0`**

