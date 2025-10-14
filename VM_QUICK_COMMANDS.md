# ⚡ Быстрые команды для Windows VM

**VM:** instance-20251013-185458  
**IP:** 34.58.217.128

---

## 🚀 Быстрое выполнение (copy-paste в PowerShell на VM)

### **1. Подготовка шаблона:**

```powershell
# Создать директорию
New-Item -Path "C:\BTI-DWG-PDF\BTI_TemplateAppBundle" -ItemType Directory -Force

# Скопировать или скачать шаблон
Copy-Item "C:\Users\admin\bti_basmanny_template.dwg" `
  -Destination "C:\BTI-DWG-PDF\BTI_TemplateAppBundle\bti_basmanny_template.dwg"

# Проверить
Get-Item "C:\BTI-DWG-PDF\BTI_TemplateAppBundle\bti_basmanny_template.dwg"
```

---

### **2. Компиляция плагина:**

```powershell
# Перейти в директорию
cd C:\BTI-DWG-PDF\BTI_TemplateAppBundle

# Собрать
dotnet build BTI_InsertBasman.csproj -c Release -o C:\out

# Проверить
Get-Item C:\out\BTI_InsertBasman.dll
```

---

### **3. Создать AppBundle ZIP:**

```powershell
# Файлы для ZIP
$files = @(
    "C:\out\BTI_InsertBasman.dll",
    "C:\BTI-DWG-PDF\BTI_TemplateAppBundle\bti_basmanny_template.dwg",
    "C:\BTI-DWG-PDF\BTI_TemplateAppBundle\PackageContents.xml"
)

# Создать ZIP
Compress-Archive -Path $files -DestinationPath "C:\out\BTI_InsertBasman.bundle.zip" -Force

# Показать хэш
Get-FileHash "C:\out\BTI_InsertBasman.bundle.zip" -Algorithm SHA256 | Format-List
```

---

### **4. Загрузить в APS:**

```powershell
# Установить credentials
$env:APS_CLIENT_ID = "m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4"
$env:APS_CLIENT_SECRET = "tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW"

# Загрузить
cd C:\BTI-DWG-PDF
python .\upload_bti_appbundle.py `
  --bundle C:\out\BTI_InsertBasman.bundle.zip `
  --appname BTI.InsertBasman `
  --alias v1
```

---

### **5. Обновить Activity:**

```powershell
# Получить токен
python .\get_aps_token.py
# Скопировать токен из вывода

# Обновить Activity
$token = "<вставить_токен>"
pwsh .\Update-Activity.ps1 `
  -AccessToken $token `
  -ActivityId "BotBti.DWG2DWGCopy+v1" `
  -AppBundleFull "BTI.InsertBasman+v1"
```

---

## 📋 Проверка после выполнения

```powershell
# 1. Проверить файлы
Get-ChildItem C:\out

# 2. Проверить ZIP содержимое
Expand-Archive C:\out\BTI_InsertBasman.bundle.zip -DestinationPath C:\temp\check -Force
Get-ChildItem C:\temp\check

# 3. Проверить размеры
Get-Item C:\out\BTI_InsertBasman.dll, C:\out\BTI_InsertBasman.bundle.zip | Format-Table Name, Length
```

---

## 🎯 Ожидаемые результаты

✅ `BTI_InsertBasman.dll` создан  
✅ `BTI_InsertBasman.bundle.zip` создан  
✅ AppBundle загружен: `BTI.InsertBasman+v1`  
✅ Activity обновлен: `BotBti.DWG2DWGCopy+v1`

---

📄 **Полный план:** BTI_NET_PLUGIN_EXECUTION_PLAN.md


