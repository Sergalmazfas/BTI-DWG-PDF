# 🤖 Задача для Gemini CLI - Создание AppBundle

**Платформа:** Windows VM (instance-20251013-185458)  
**Цель:** Скомпилировать .NET плагин, создать и загрузить AppBundle в Autodesk APS

---

## 🎯 Задача для Gemini

```
Создай PowerShell скрипт для автоматизации создания AppBundle для Autodesk APS.

Требования:
1. Скомпилировать C# проект BTI_InsertBasman.csproj
2. Создать структуру .bundle с PackageContents.xml
3. Заархивировать в .zip
4. Зарегистрировать AppBundle в Autodesk APS через REST API
5. Загрузить архив на S3
6. Создать alias v1

Параметры:
- Project: C:\BTI-DWG-PDF\BTI_TemplateAppBundle\BTI_InsertBasman.csproj
- Output: C:\out
- AppBundle Name: BtiPlugin
- APS Client ID: m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4
- APS Client Secret: tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW
- Engine: Autodesk.AutoCAD+25_1
- Nickname: BotBti (уже зарегистрирован)

Используй существующие скрипты если есть (build-fixed.ps1, setup-and-build.ps1).
```

---

## 📋 Детали для Gemini

### **1. Компиляция:**

```powershell
# Проект находится здесь
C:\BTI-DWG-PDF\BTI_TemplateAppBundle\BTI_InsertBasman.csproj

# Скомпилировать
dotnet build BTI_InsertBasman.csproj -c Release -o C:\out

# Результат: C:\out\BTI_InsertBasman.dll
```

### **2. Структура .bundle:**

```
C:\out\BtiPlugin.bundle\
├── PackageContents.xml
└── Contents\
    ├── BTI_InsertBasman.dll
    └── bti_basmanny_template.dwg (опционально)
```

### **3. PackageContents.xml (шаблон):**

```xml
<?xml version="1.0" encoding="utf-8"?>
<ApplicationPackage SchemaVersion="1.0" AutodeskProduct="AutoCAD" ProductType="Application">
  <Components>
    <RuntimeRequirements OS="Win64" Platform="AutoCAD" />
    <ComponentEntry AppName="BtiPlugin" ModuleName="./Contents/BTI_InsertBasman.dll">
      <Commands GroupName="BTI">
        <Command Global="BTI_INSERT_TEMPLATE" Local="BTI_INSERT_TEMPLATE" />
      </Commands>
    </ComponentEntry>
  </Components>
</ApplicationPackage>
```

### **4. Autodesk APS API:**

**Получить токен:**
```http
POST https://developer.api.autodesk.com/authentication/v2/token
Body: client_id, client_secret, grant_type=client_credentials, scope=code:all
```

**Зарегистрировать AppBundle:**
```http
POST https://developer.api.autodesk.com/da/us-east/v3/appbundles
Headers: Authorization: Bearer <token>
Body: {"id": "BotBti.BtiPlugin", "engine": "Autodesk.AutoCAD+25_1"}
```

**Загрузить на S3:**
```http
POST <uploadParameters.endpointURL>
(multipart/form-data с formData из предыдущего ответа)
```

**Создать alias:**
```http
POST https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin/aliases
Body: {"id": "v1", "version": 1}
```

---

## 🚀 Альтернатива: Используй существующие скрипты

### **На VM попробуй:**

```powershell
# Попробуй существующий скрипт
cd C:\BTI-DWG-PDF
pwsh .\build-fixed.ps1
```

Если этот скрипт не работает, попроси Gemini:

```
Проверь и исправь скрипт build-fixed.ps1:
1. Убедись что компилирует BTI_InsertBasman.csproj
2. Создает .bundle структуру
3. Создает PackageContents.xml
4. Архивирует в .zip

Затем загрузи AppBundle в Autodesk APS используя credentials:
- Client ID: m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4
- Client Secret: tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW
```

---

## 📝 Шаги для Gemini

**Дай Gemini эту последовательность:**

```
Task: Create and upload AppBundle to Autodesk APS

Steps:
1. Compile C# project at C:\BTI-DWG-PDF\BTI_TemplateAppBundle\BTI_InsertBasman.csproj
   Output: C:\out\BTI_InsertBasman.dll

2. Create .bundle structure:
   C:\out\BtiPlugin.bundle\
   └── Contents\
       └── BTI_InsertBasman.dll

3. Generate PackageContents.xml (see template above)

4. Create ZIP archive: C:\out\BtiPlugin.zip

5. Get APS token using credentials above

6. Register AppBundle via POST to:
   https://developer.api.autodesk.com/da/us-east/v3/appbundles

7. Upload ZIP to S3 (use uploadParameters from step 6)

8. Create alias v1

Check existing scripts: build-fixed.ps1, setup-and-build.ps1
Use them if they do the same, or create new one.
```

---

## ✅ Ожидаемый результат

После выполнения должно быть:

```
✅ C:\out\BTI_InsertBasman.dll (скомпилирован)
✅ C:\out\BtiPlugin.zip (архив для APS)
✅ AppBundle зарегистрирован: BotBti.BtiPlugin+v1
✅ Alias v1 создан
```

---

## 🔍 Проверка после выполнения

```powershell
# Проверить файлы
Get-ChildItem C:\out

# Проверить AppBundle в APS (через API или веб)
# AppBundle должен появиться: BotBti.BtiPlugin+v1
```

---

**💡 Gemini поймет эту задачу и выполнит автоматически!**


