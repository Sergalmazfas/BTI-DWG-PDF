# 🤖 Финальная задача для Gemini CLI - AppBundle с LISP

**Платформа:** Windows VM  
**Gemini скрипт:** build-windows.ps1  
**Цель:** Создать AppBundle с LISP скриптами для BTI обработки

---

## 📋 Задача для Gemini (copy-paste в CLI)

```
Задача: Создать AppBundle с LISP скриптами для Autodesk APS

Контекст:
- У меня есть build-windows.ps1 который компилирует проект
- Нужно создать AppBundle с LISP скриптами BTI_APPLY.lsp и BTI_CLEANUP.lsp
- LISP скрипты для автоматической вставки блоков по меткам от Leica DISTO

Что нужно сделать:

1. Проверь и запусти build-windows.ps1:
   - Должен создать BTI_InsertBasman.dll
   - Должен создать .zip архив

2. Создай AppBundle структуру:
   C:\out\BtiPlugin.bundle\
   ├── PackageContents.xml
   └── Contents\
       ├── BTI_InsertBasman.dll (если скомпилировано)
       ├── BTI_APPLY.lsp
       ├── BTI_CLEANUP.lsp
       └── bti_basmanny_template.dwg

3. PackageContents.xml должен содержать:
   - ComponentEntry для DLL (если есть)
   - Ссылку на LISP скрипты
   - Команду BTI_INSERT_TEMPLATE

4. Создай ZIP архив C:\out\BtiPlugin.zip

5. Загрузи в Google Cloud Storage:
   gsutil cp C:\out\BtiPlugin.zip gs://btibot-processed/appbundles/

6. Зарегистрируй в Autodesk APS:
   - Client ID: m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4
   - Client Secret: tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW
   - AppBundle ID: BotBti.BtiPlugin
   - Engine: Autodesk.AutoCAD+25_1
   - Alias: v1

LISP скрипты находятся в репозитории:
- https://raw.githubusercontent.com/Sergalmazfas/BTI-DWG-PDF/release/gold1/scripts/BTI_APPLY.lsp
- https://raw.githubusercontent.com/Sergalmazfas/BTI-DWG-PDF/release/gold1/scripts/BTI_CLEANUP.lsp

Или скачай их из GCS (когда я загружу):
- gs://btibot-processed/scripts/BTI_APPLY.lsp
- gs://btibot-processed/scripts/BTI_CLEANUP.lsp

Результат:
✅ AppBundle BotBti.BtiPlugin+v1 создан
✅ Содержит LISP скрипты для обработки
✅ Зарегистрирован в Autodesk APS
✅ Готов к использованию в Activity
```

---

## ⚙️ Детали для Gemini

### **PackageContents.xml (с LISP):**

```xml
<?xml version="1.0" encoding="utf-8"?>
<ApplicationPackage SchemaVersion="1.0">
  <Components>
    <RuntimeRequirements OS="Win64" Platform="AutoCAD" />
    <ComponentEntry AppName="BtiPlugin" ModuleName="./Contents/BTI_InsertBasman.dll">
      <Commands GroupName="BTI">
        <Command Global="BTI_INSERT_TEMPLATE" />
      </Commands>
    </ComponentEntry>
  </Components>
</ApplicationPackage>
```

### **Файлы для включения в AppBundle:**

```
Contents/
├── BTI_InsertBasman.dll (если скомпилировано, иначе пропустить)
├── BTI_APPLY.lsp (обязательно!)
├── BTI_CLEANUP.lsp (обязательно!)
└── bti_basmanny_template.dwg (уже есть на VM)
```

---

## 📝 Последовательность действий на VM

```powershell
# 1. Запустить build-windows.ps1
cd C:\BTI-DWG-PDF
.\build-windows.ps1

# 2. Скачать LISP скрипты (если их нет)
Invoke-WebRequest -Uri "https://storage.googleapis.com/btibot-processed/scripts/BTI_APPLY.lsp" -OutFile "C:\BTI-DWG-PDF\scripts\BTI_APPLY.lsp"
Invoke-WebRequest -Uri "https://storage.googleapis.com/btibot-processed/scripts/BTI_CLEANUP.lsp" -OutFile "C:\BTI-DWG-PDF\scripts\BTI_CLEANUP.lsp"

# 3. Добавить LISP в bundle
Copy-Item "C:\BTI-DWG-PDF\scripts\*.lsp" -Destination "C:\out\BtiPlugin.bundle\Contents\"

# 4. Пересоздать ZIP
Compress-Archive -Path "C:\out\BtiPlugin.bundle" -DestinationPath "C:\out\BtiPlugin.zip" -Force

# 5. Загрузить в GCS
gsutil cp C:\out\BtiPlugin.zip gs://btibot-processed/appbundles/

# 6. Зарегистрировать в APS (через скрипт или вручную)
```

---

**🎯 Gemini выполнит эти шаги автоматически!**


