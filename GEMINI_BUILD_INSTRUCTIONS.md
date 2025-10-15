# ✅ Инструкция по выполнению build-windows.ps1 от Gemini

**Скрипт:** build-windows.ps1 (создан Gemini CLI)  
**Платформа:** Windows VM  
**Статус:** Готов к выполнению

---

## 🚀 Быстрое выполнение

### **На Windows VM в PowerShell:**

```powershell
# 1. Перейти в директорию проекта
cd C:\BTI-DWG-PDF

# 2. Запустить скрипт Gemini
pwsh .\build-windows.ps1
```

---

## ⚙️ Требования (проверить перед запуском)

### **1. .NET 8.0 SDK:**

```powershell
dotnet --version
# Должно быть: 8.0.x или выше
```

**Если не установлено:**
```powershell
# Скачать и установить .NET 8.0 SDK
# https://dotnet.microsoft.com/download/dotnet/8.0
```

### **2. gsutil (Google Cloud SDK):**

```powershell
gsutil --version
# Должно быть: gsutil version 5.x
```

**Если не установлено:**
```powershell
# Скачать Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Или через PowerShell
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe
```

### **3. 7-Zip:**

```powershell
# Проверить
Test-Path "C:\Program Files\7-Zip\7z.exe"
# Должно вернуть: True
```

**Если не установлено:**
```powershell
# Скачать 7-Zip
# https://www.7-zip.org/download.html

# Или через winget
winget install 7zip.7zip
```

---

## 📋 Что делает скрипт build-windows.ps1

1. ✅ Скачивает исходный код проекта
2. ✅ Компилирует BTI_InsertBasman.csproj
3. ✅ Создает AppBundle структуру
4. ✅ Загружает AppBundle в Google Cloud Storage

---

## 🔍 Ожидаемый результат

После выполнения скрипта должно быть:

```
C:\out\
├── BTI_InsertBasman.dll (скомпилированный плагин)
└── BtiPlugin.zip (или AppBundle.zip)

GCS:
gs://btibot-processed/appbundles/BtiPlugin.zip
```

---

## ⏭️ Следующие шаги после успешной сборки

### **ШАГ 1: Проверить созданные файлы**

```powershell
# На VM проверить
Get-ChildItem C:\out

# Проверить размер ZIP
Get-Item C:\out\*.zip | Format-Table Name, Length

# Проверить что загружено в GCS
gsutil ls gs://btibot-processed/appbundles/
```

---

### **ШАГ 2: Загрузить AppBundle в Autodesk APS**

**Вариант A: Через Python скрипт (если есть)**

```powershell
# Установить credentials
$env:APS_CLIENT_ID = "m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4"
$env:APS_CLIENT_SECRET = "tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW"

# Загрузить в APS
python .\upload_bti_appbundle.py `
  --bundle C:\out\BtiPlugin.zip `
  --appname BTI.InsertBasman `
  --alias v1
```

**Вариант B: Через curl / Invoke-RestMethod**

```powershell
# Получить токен
$tokenUrl = "https://developer.api.autodesk.com/authentication/v2/token"
$tokenBody = @{
    client_id = $env:APS_CLIENT_ID
    client_secret = $env:APS_CLIENT_SECRET
    grant_type = "client_credentials"
    scope = "code:all"
}

$tokenResponse = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $tokenBody -ContentType "application/x-www-form-urlencoded"
$token = $tokenResponse.access_token

Write-Host "✅ Токен получен"

# Зарегистрировать AppBundle
$appBundleUrl = "https://developer.api.autodesk.com/da/us-east/v3/appbundles"
$appBundleData = @{
    id = "BotBti.BtiPlugin"
    engine = "Autodesk.AutoCAD+25_1"
    description = "BTI Plugin with template"
} | ConvertTo-Json

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$response = Invoke-RestMethod -Uri $appBundleUrl -Method Post -Headers $headers -Body $appBundleData

Write-Host "✅ AppBundle зарегистрирован"
Write-Host "   Upload URL: $($response.uploadParameters.endpointURL)"

# Далее - загрузка ZIP на S3 (используя uploadParameters)
```

---

### **ШАГ 3: Создать Alias v1**

```powershell
# После успешной загрузки на S3
$aliasUrl = "https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin/aliases"
$aliasData = @{
    id = "v1"
    version = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri $aliasUrl -Method Post -Headers $headers -Body $aliasData

Write-Host "✅ Alias v1 создан"
Write-Host "   Full ID: BotBti.BtiPlugin+v1"
```

---

### **ШАГ 4: Обновить Activity**

```powershell
# Обновить Activity для использования нового AppBundle
pwsh .\Update-Activity.ps1 `
  -AccessToken $token `
  -ActivityId "BotBti.DWG2DWGCopy+v1" `
  -AppBundleFull "BotBti.BtiPlugin+v1"
```

---

### **ШАГ 5: Задеплоить с типовым шаблоном**

**На локальной машине:**

```bash
gcloud run deploy telegram-bti-bot \
  --source . \
  --region europe-west1 \
  --set-env-vars="USE_BTI_TEMPLATE=true"
```

---

## ⚠️ Возможные проблемы

### **Проблема 1: .NET SDK не найден**

```powershell
# Установить .NET 8.0
winget install Microsoft.DotNet.SDK.8
```

### **Проблема 2: gsutil не найден**

```powershell
# Установить Google Cloud SDK
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\gcloud.exe")
& $env:Temp\gcloud.exe
```

### **Проблема 3: 7-Zip не найден**

```powershell
# Установить 7-Zip
winget install 7zip.7zip

# Или использовать встроенный Compress-Archive
Compress-Archive -Path "C:\out\BtiPlugin.bundle" -DestinationPath "C:\out\BtiPlugin.zip"
```

### **Проблема 4: AutoCAD DLL не найдены**

```powershell
# Проверить установку AutoCAD
Get-ChildItem "C:\Program Files\Autodesk" -Directory

# Если AutoCAD НЕ установлен:
Write-Host "⚠️ AutoCAD не найден"
Write-Host "Используйте готовый рабочий Activity: BotBti.DWG2DWGCopy+v1"
Write-Host "Деплой уже сделан и работает!"
```

---

## ✅ Итоговая проверка

После выполнения всех шагов проверьте:

```powershell
# 1. Файлы на VM
Get-ChildItem C:\out\*.dll, C:\out\*.zip

# 2. AppBundle в APS
# Проверить через Postman или API что BotBti.BtiPlugin+v1 существует

# 3. Тест Activity
# Отправить DWG файл через Telegram bot
```

---

## 📚 Документация

- `FOR_GEMINI_CLI.txt` - задача для Gemini (copy-paste)
- `GEMINI_BUILD_INSTRUCTIONS.md` - эта инструкция
- `VM_USE_EXISTING_SCRIPTS.md` - использование существующих скриптов
- `APPBUNDLE_AUTOMATION_GUIDE.md` - детальное руководство

---

**🤖 Gemini выполнит задачу автоматически! Просто скопируйте содержимое FOR_GEMINI_CLI.txt в чат с Gemini на VM!**


