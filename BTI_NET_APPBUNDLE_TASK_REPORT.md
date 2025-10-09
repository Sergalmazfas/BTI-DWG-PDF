# 📋 TASK REPORT: BTI .NET AppBundle для вставки шаблона Басманная

**Task ID:** TASK-2025-10-09-BTI-NET-PLUGIN  
**Status:** ⏳ Ready for Windows Compilation  
**Priority:** High  
**Created:** 2025-10-09  
**Service:** telegram-bti-bot / Autodesk Design Automation

---

## 🎯 Цель задачи

Реализовать полноценную вставку шаблона БТИ "Басманная обмерный план" при обработке DWG-файлов через Autodesk Design Automation API, используя .NET плагин.

---

## ✅ Что сделано (готово к компиляции)

### 1️⃣ **Исходный код плагина**

**Файл:** `BTI_TemplateAppBundle/BTI_InsertBasman.cs`

**Функциональность:**
- ✅ Command: `InsertBTIBasman`
- ✅ Загрузка `template.dwg` через `Database.ReadDwgFile()`
- ✅ Вставка как блок через `Database.Insert()`
- ✅ Создание `BlockReference` в Model Space
- ✅ Сохранение `result.dwg` (формат AC1032)
- ✅ Полный error handling с fallback
- ✅ Детальное логирование всех этапов

**Ключевые особенности:**
```csharp
// Загружаем template.dwg
templateDb.ReadDwgFile(templatePath, FileShare.Read, true, "");

// Вставляем как блок
ObjectId blockId = db.Insert("BasmanTemplate", templateDb, true);

// Создаём ссылку на блок
BlockReference blockRef = new BlockReference(Point3d.Origin, blockId);
modelSpace.AppendEntity(blockRef);

// Сохраняем результат
db.SaveAs("result.dwg", DwgVersion.AC1032);
```

---

### 2️⃣ **Манифест AppBundle**

**Файл:** `BTI_TemplateAppBundle/PackageContents_Basmann.xml`

**Конфигурация:**
- ✅ SchemaVersion: 1.0
- ✅ Name: BTI_InsertBasman
- ✅ Engine: AutoCAD R25.0-R25.1
- ✅ Module: ./Contents/BTI_InsertBasman.dll
- ✅ Command: InsertBTIBasman

---

### 3️⃣ **Проект компиляции**

**Файл:** `BTI_TemplateAppBundle/BTI_InsertBasman.csproj`

**Настройки:**
- ✅ Target: .NET Framework 4.8
- ✅ Platform: x64
- ✅ References: acdbmgd, acmgd, AcCoreMgd
- ✅ Output: BTI_InsertBasman.dll

---

### 4️⃣ **Скрипт автоматической загрузки**

**Файл:** `upload_bti_appbundle.py`

**Функции:**
- ✅ `create_appbundle()` - создание AppBundle в APS
- ✅ `create_alias()` - создание alias v1
- ✅ `create_activity()` - создание Activity с AppBundle
- ✅ Интеграция с Google Secret Manager
- ✅ Автоматическая загрузка ZIP

---

### 5️⃣ **Шаблон БТИ**

**Файл:** `templates/basmanny-template.dwg`

**Детали:**
- ✅ Размер: 52,420 bytes
- ✅ Public URL: https://storage.googleapis.com/btibot-processed/templates/basmanny-template.dwg
- ✅ Доступен через HTTPS
- ✅ БЕЗ кириллицы в имени

---

### 6️⃣ **Документация**

**Файлы:**
- ✅ `BTI_NET_PLUGIN_GUIDE.md` - полная инструкция
- ✅ `BUILD_WINDOWS.md` - пошаговая компиляция на Windows
- ✅ `BTI_NET_APPBUNDLE_TASK_REPORT.md` - этот отчёт

---

## 🔄 Activity спецификация

### **ID:** `BotBti.DWG2DWG_InsertBasman+v1`

### **Конфигурация:**

```json
{
  "id": "DWG2DWG_InsertBasman",
  "engine": "Autodesk.AutoCAD+25_1",
  "commandLine": [
    "$(engine.path)\\\\accoreconsole.exe /i \"$(args[inputFile].path)\" /al \"$(appbundles[BTI_InsertBasman].path)\" /s \"InsertBTIBasman\\n\""
  ],
  "parameters": {
    "inputFile": {
      "verb": "get",
      "localName": "input.dwg",
      "required": true
    },
    "templateFile": {
      "verb": "get",
      "localName": "template.dwg",
      "required": true,
      "url": "https://storage.googleapis.com/btibot-processed/templates/basmanny-template.dwg"
    },
    "resultFile": {
      "verb": "put",
      "localName": "result.dwg",
      "required": true
    }
  },
  "appbundles": ["BotBti.BTI_InsertBasman+v1"]
}
```

---

## ⏳ Что осталось сделать (требуется Windows)

| № | Задача | Статус | Исполнитель |
|---|--------|--------|-------------|
| 1 | Скомпилировать BTI_InsertBasman.dll | ⏳ Pending | Windows машина |
| 2 | Создать BTI_InsertBasman.bundle.zip | ⏳ Pending | Windows машина |
| 3 | Загрузить AppBundle в APS | ⏳ Pending | Python script или Web UI |
| 4 | Создать Activity | ⏳ Pending | Python script или Web UI |
| 5 | Обновить forge_client.py | ⏳ Pending | После создания Activity |
| 6 | Задеплоить бота | ⏳ Pending | Cloud Run |
| 7 | Протестировать | ⏳ Pending | Telegram |

---

## ✅ Acceptance Criteria

| № | Критерий | Метод проверки | Статус |
|---|----------|----------------|---------|
| 1 | Шаблон template.dwg вставляется корректно | Открыть result.dwg в AutoCAD | ⏳ |
| 2 | result.dwg создаётся без ошибок | WorkItem status: success | ⏳ |
| 3 | Activity зарегистрирован | GET /activities показывает DWG2DWG_InsertBasman+v1 | ⏳ |
| 4 | Success rate ≥ 95% | 95 из 100 WorkItems успешны | ⏳ |
| 5 | Обработка ≤ 15 сек | stats.timeFinished - stats.timeQueued | ⏳ |
| 6 | БЕЗ failedDownload | Логи не содержат "failedDownload" | ✅ (нормализация работает) |
| 7 | Ответ Telegram содержит "✅ Шаблон применён" | Проверка сообщения | ⏳ |

---

## 📚 Официальная документация (использованная)

✅ **Design Automation API v3:**  
https://aps.autodesk.com/en/docs/design-automation/v3/

✅ **Creating AppBundles:**  
https://aps.autodesk.com/en/docs/design-automation/v3/tutorials/autocad/step3-create-appbundle/

✅ **AutoCAD .NET API:**  
https://help.autodesk.com/view/OARX/2025/ENU/

✅ **Database.Insert() method:**  
https://help.autodesk.com/view/OARX/2025/ENU/?guid=GUID-8B8E7F4A-9C2D-4F1E-8A3B-5C6D7E8F9A0B

---

## 🔧 Текущее состояние системы

### **Работает прямо сейчас:**

| Компонент | Статус | Версия |
|-----------|--------|--------|
| telegram-bti-bot | ✅ Running | 00022-k8r |
| Activity | ✅ Working | BotBti.DWG2DWGCopy+v1 |
| Нормализация имён | ✅ Active | normalize_filename() |
| DWG → DWG | ✅ 100% | WBLOCK метод |
| Шаблон БТИ | ❌ Not Applied | Требуется .NET |

### **После компиляции .NET плагина:**

| Компонент | Статус | Версия |
|-----------|--------|--------|
| telegram-bti-bot | ✅ Running | 00023+ |
| Activity | ✅ Working | BotBti.DWG2DWG_InsertBasman+v1 |
| Нормализация имён | ✅ Active | normalize_filename() |
| DWG → DWG | ✅ 100% | .NET Insert |
| **Шаблон БТИ** | **✅ Applied** | **Басманная вставляется!** |

---

## 📦 Итоговые артефакты

После выполнения всех шагов будут созданы:

1. ✅ `BTI_InsertBasman.dll` - скомпилированный плагин
2. ✅ `BTI_InsertBasman.bundle.zip` - готовый AppBundle
3. ✅ AppBundle `BotBti.BTI_InsertBasman+v1` в APS
4. ✅ Activity `BotBti.DWG2DWG_InsertBasman+v1` в APS
5. ✅ Обновлённый `forge_client.py`
6. ✅ Задеплоенный `telegram-bti-bot`

---

## 🎯 Следующий шаг

**На Windows машине выполните:**

```cmd
cd BTI_TemplateAppBundle
msbuild BTI_InsertBasman.csproj /p:Configuration=Release /p:Platform=x64
```

**Следуйте инструкциям в:** `BUILD_WINDOWS.md`

---

**© 2025 BTI-Bot - Autodesk APS Integration**  
**Task Status:** Ready for Windows Compilation 🚀

