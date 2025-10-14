# 🔧 Использование существующих скриптов на VM

**Найденные скрипты на VM:**
- `setup-and-build.ps1`
- `build.ps1`
- `build-fixed.ps1`

---

## ⚡ Вариант 1: Использовать существующий скрипт

### **Попробуйте build-fixed.ps1:**

```powershell
# На VM в PowerShell
cd C:\BTI-DWG-PDF

# Установить credentials
$env:APS_CLIENT_ID = "m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4"
$env:APS_CLIENT_SECRET = "tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW"

# Запустить
pwsh .\build-fixed.ps1
```

**Или:**

```powershell
pwsh .\setup-and-build.ps1
```

---

## ⚡ Вариант 2: Скопировать новый скрипт вручную

### **Через RDP:**

1. **Подключиться к VM:**
   - IP: 34.58.217.128
   - Пользователь: admin
   
2. **На VM открыть браузер и скачать:**
   - Перейти на: https://raw.githubusercontent.com/Sergalmazfas/BTI-DWG-PDF/release/gold1/Create-And-Upload-AppBundle.ps1
   - Сохранить как: `C:\BTI-DWG-PDF\Create-And-Upload-AppBundle.ps1`

3. **Или создать файл вручную:**

```powershell
# На VM создать новый файл
notepad C:\BTI-DWG-PDF\Create-And-Upload-AppBundle.ps1

# Скопировать содержимое из локальной машины
```

---

## ⚡ Вариант 3: Скачать из облака

```powershell
# На VM в PowerShell
Invoke-WebRequest -Uri "https://storage.googleapis.com/btibot-processed/scripts/Create-And-Upload-AppBundle.ps1" -OutFile "C:\BTI-DWG-PDF\Create-And-Upload-AppBundle.ps1"
```

---

## 📋 Содержимое скрипта (для copy-paste)

Если хотите создать файл вручную, вот содержимое:

```powershell
# См. файл Create-And-Upload-AppBundle.ps1 на локальной машине
# Скопируйте всё содержимое через RDP
```

**Или используйте простую версию:**

```powershell
# === УПРОЩЕННАЯ ВЕРСИЯ ===
param(
    [string]$ApsClientId = $env:APS_CLIENT_ID,
    [string]$ApsClientSecret = $env:APS_CLIENT_SECRET
)

Write-Host "🚀 Быстрая сборка и загрузка AppBundle" -ForegroundColor Cyan

# 1. Компиляция
cd C:\BTI-DWG-PDF\BTI_TemplateAppBundle
dotnet build BTI_InsertBasman.csproj -c Release -o C:\out

# 2. Создать .bundle структуру
New-Item -Path "C:\out\BtiPlugin.bundle\Contents" -ItemType Directory -Force | Out-Null

# 3. Копировать файлы
Copy-Item "C:\out\BTI_InsertBasman.dll" -Destination "C:\out\BtiPlugin.bundle\Contents\"
Copy-Item "bti_basmanny_template.dwg" -Destination "C:\out\BtiPlugin.bundle\Contents\" -ErrorAction SilentlyContinue

# 4. Создать PackageContents.xml (упрощенный)
$xml = @"
<?xml version="1.0"?>
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
"@
Set-Content "C:\out\BtiPlugin.bundle\PackageContents.xml" -Value $xml

# 5. Создать ZIP
Compress-Archive -Path "C:\out\BtiPlugin.bundle" -DestinationPath "C:\out\BtiPlugin.zip" -Force

# 6. Показать результат
Get-Item C:\out\BtiPlugin.zip | Format-List Name, Length
Get-FileHash C:\out\BtiPlugin.zip | Format-List Hash

Write-Host "✅ AppBundle готов: C:\out\BtiPlugin.zip" -ForegroundColor Green
```

Сохраните это как `C:\BTI-DWG-PDF\Quick-Build-AppBundle.ps1`

---

## 🎯 Рекомендация

### **Используйте существующий скрипт:**

```powershell
cd C:\BTI-DWG-PDF
pwsh .\build-fixed.ps1
```

**Или попробуйте:**

```powershell
pwsh .\setup-and-build.ps1
```

Эти скрипты уже на VM и скорее всего делают то же самое!

---

## ✅ После успешной компиляции

Результат должен быть:

```
C:\out\
├── BTI_InsertBasman.dll
└── BtiPlugin.zip (или другое имя)
```

Затем:

1. **Загрузить в APS** (через Python скрипт):
```powershell
python .\upload_bti_appbundle.py --bundle C:\out\BtiPlugin.zip --appname BTI.InsertBasman --alias v1
```

2. **Обновить Activity:**
```powershell
pwsh .\Update-Activity.ps1 -ActivityId "BotBti.DWG2DWGCopy+v1" -AppBundleFull "BTI.InsertBasman+v1"
```

---

**💡 Используйте существующие скрипты на VM - они уже настроены!**


