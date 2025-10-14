# ===============================================
# 🚀 Автоматическое создание и загрузка AppBundle в Autodesk APS
# ===============================================
# 
# Этот скрипт выполняет полный цикл:
# 1. Компиляция .NET плагина
# 2. Создание структуры .bundle
# 3. Создание PackageContents.xml
# 4. Архивирование в .zip
# 5. Регистрация AppBundle в Forge API
# 6. Загрузка архива на S3
# 7. Создание alias (v1)
#
# Требования:
# - Windows с установленным AutoCAD 2024/2025
# - .NET SDK
# - PowerShell 7+
# ===============================================

param(
    [string]$ProjectPath = "C:\BTI-DWG-PDF\BTI_TemplateAppBundle",
    [string]$OutputPath = "C:\out",
    [string]$AppBundleName = "BtiPlugin",
    [string]$PluginDllName = "BTI_InsertBasman.dll",
    [string]$CommandName = "BTI_INSERT_TEMPLATE",
    [string]$ApsClientId = $env:APS_CLIENT_ID,
    [string]$ApsClientSecret = $env:APS_CLIENT_SECRET
)

# Цвета для вывода
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     🚀 Создание и загрузка AppBundle в Autodesk APS         ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ===============================================
# ШАГ 1: Проверка окружения
# ===============================================
Write-Info "ШАГ 1: Проверка окружения"

# Проверка APS credentials
if (-not $ApsClientId) {
    Write-Error "APS_CLIENT_ID не установлен!"
    Write-Info "Установите: `$env:APS_CLIENT_ID = 'ваш_client_id'"
    exit 1
}
if (-not $ApsClientSecret) {
    Write-Error "APS_CLIENT_SECRET не установлен!"
    Write-Info "Установите: `$env:APS_CLIENT_SECRET = 'ваш_client_secret'"
    exit 1
}

Write-Success "Credentials найдены"
Write-Info "   Client ID: $($ApsClientId.Substring(0, 20))..."

# Проверка .NET SDK
$dotnetVersion = dotnet --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Success ".NET SDK установлен: $dotnetVersion"
} else {
    Write-Error ".NET SDK не найден!"
    exit 1
}

# ===============================================
# ШАГ 2: Компиляция плагина
# ===============================================
Write-Host ""
Write-Info "ШАГ 2: Компиляция .NET плагина"

$csprojPath = Join-Path $ProjectPath "BTI_InsertBasman.csproj"
if (-not (Test-Path $csprojPath)) {
    Write-Error "Проект не найден: $csprojPath"
    exit 1
}

Write-Info "   Проект: $csprojPath"
Write-Info "   Компиляция..."

# Создаем выходную директорию
New-Item -Path $OutputPath -ItemType Directory -Force | Out-Null

# Компиляция
dotnet build $csprojPath -c Release -o $OutputPath 2>&1 | Out-Null

if (Test-Path (Join-Path $OutputPath $PluginDllName)) {
    $dllSize = (Get-Item (Join-Path $OutputPath $PluginDllName)).Length / 1KB
    Write-Success "Плагин скомпилирован: $PluginDllName ($([math]::Round($dllSize, 2)) KB)"
} else {
    Write-Error "Компиляция не удалась! DLL не создан."
    exit 1
}

# ===============================================
# ШАГ 3: Создание структуры .bundle
# ===============================================
Write-Host ""
Write-Info "ШАГ 3: Создание структуры .bundle"

$bundlePath = Join-Path $OutputPath "$AppBundleName.bundle"
$contentsPath = Join-Path $bundlePath "Contents"

# Создаем директории
New-Item -Path $bundlePath -ItemType Directory -Force | Out-Null
New-Item -Path $contentsPath -ItemType Directory -Force | Out-Null

Write-Success "Структура .bundle создана"

# ===============================================
# ШАГ 4: Создание PackageContents.xml
# ===============================================
Write-Host ""
Write-Info "ШАГ 4: Создание PackageContents.xml"

$packageXml = @"
<?xml version="1.0" encoding="utf-8"?>
<ApplicationPackage
  SchemaVersion="1.0"
  AutodeskProduct="AutoCAD"
  ProductType="Application"
  Name="$AppBundleName"
  Description="BTI AutoCAD Plugin для вставки типового шаблона БТИ"
  Author="BTI Team"
  AppVersion="1.0.0"
  OnlineDocumentation="https://github.com/Sergalmazfas/BTI-DWG-PDF"
  HelpFile="./Contents/Help.htm">
  
  <CompanyDetails
    Name="BTI"
    Email="info@bti.ru"
    Url="https://bti.ru" />
    
  <Components Description="$AppBundleName Components">
    <RuntimeRequirements
      OS="Win64"
      Platform="AutoCAD"
      SeriesMin="R24.0"
      SeriesMax="R25.2" />
      
    <ComponentEntry
      AppName="$AppBundleName"
      Version="1.0.0"
      ModuleName="./Contents/$PluginDllName"
      AppDescription="BTI Plugin для вставки типового шаблона БТИ Басманный"
      LoadOnCommandInvocation="True"
      LoadOnAutoCADStartup="False">
      
      <Commands GroupName="BTI_COMMANDS">
        <Command Global="$CommandName" Local="$CommandName" />
      </Commands>
    </ComponentEntry>
  </Components>
</ApplicationPackage>
"@

$packageXmlPath = Join-Path $bundlePath "PackageContents.xml"
Set-Content -Path $packageXmlPath -Value $packageXml -Encoding UTF8

Write-Success "PackageContents.xml создан"

# ===============================================
# ШАГ 5: Копирование DLL в bundle
# ===============================================
Write-Host ""
Write-Info "ШАГ 5: Копирование файлов в .bundle"

# Копируем DLL
$sourceDll = Join-Path $OutputPath $PluginDllName
$destDll = Join-Path $contentsPath $PluginDllName

if (Test-Path $sourceDll) {
    Copy-Item $sourceDll -Destination $destDll -Force
    Write-Success "DLL скопирован: $PluginDllName"
} else {
    Write-Error "DLL не найден: $sourceDll"
    exit 1
}

# Копируем шаблон BTI (если есть)
$templatePath = Join-Path $ProjectPath "bti_basmanny_template.dwg"
if (Test-Path $templatePath) {
    $destTemplate = Join-Path $contentsPath "bti_basmanny_template.dwg"
    Copy-Item $templatePath -Destination $destTemplate -Force
    Write-Success "Шаблон BTI скопирован"
}

# ===============================================
# ШАГ 6: Создание .zip архива
# ===============================================
Write-Host ""
Write-Info "ШАГ 6: Создание .zip архива"

$zipPath = Join-Path $OutputPath "$AppBundleName.zip"

# Удаляем старый архив если есть
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

# Архивируем .bundle директорию
Compress-Archive -Path $bundlePath -DestinationPath $zipPath -Force

if (Test-Path $zipPath) {
    $zipSize = (Get-Item $zipPath).Length / 1KB
    $zipHash = (Get-FileHash $zipPath -Algorithm SHA256).Hash
    Write-Success "Архив создан: $AppBundleName.zip ($([math]::Round($zipSize, 2)) KB)"
    Write-Info "   SHA256: $zipHash"
} else {
    Write-Error "Не удалось создать архив!"
    exit 1
}

# ===============================================
# ШАГ 7: Получение APS токена
# ===============================================
Write-Host ""
Write-Info "ШАГ 7: Получение APS токена"

$tokenUrl = "https://developer.api.autodesk.com/authentication/v2/token"
$tokenBody = @{
    client_id = $ApsClientId
    client_secret = $ApsClientSecret
    grant_type = "client_credentials"
    scope = "code:all"
}

try {
    $tokenResponse = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $tokenBody -ContentType "application/x-www-form-urlencoded"
    $accessToken = $tokenResponse.access_token
    Write-Success "APS токен получен"
} catch {
    Write-Error "Не удалось получить токен: $_"
    exit 1
}

# ===============================================
# ШАГ 8: Получение nickname
# ===============================================
Write-Host ""
Write-Info "ШАГ 8: Получение nickname (ForgeAppName)"

$nicknameUrl = "https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me"
$headers = @{
    "Authorization" = "Bearer $accessToken"
}

try {
    $nicknameResponse = Invoke-RestMethod -Uri $nicknameUrl -Method Get -Headers $headers
    $nickname = $nicknameResponse
    if ($nickname -is [string]) {
        Write-Success "Nickname: $nickname"
    } else {
        $nickname = $nicknameResponse.id
        Write-Success "Nickname: $nickname"
    }
} catch {
    Write-Error "Не удалось получить nickname: $_"
    exit 1
}

# ===============================================
# ШАГ 9: Регистрация AppBundle в APS
# ===============================================
Write-Host ""
Write-Info "ШАГ 9: Регистрация AppBundle в APS"

$appBundleId = "$nickname.$AppBundleName"
$appBundleUrl = "https://developer.api.autodesk.com/da/us-east/v3/appbundles"

$appBundleData = @{
    id = $appBundleId
    engine = "Autodesk.AutoCAD+25_1"
    description = "BTI Plugin для вставки типового шаблона БТИ Басманный"
} | ConvertTo-Json

$headers = @{
    "Authorization" = "Bearer $accessToken"
    "Content-Type" = "application/json"
}

try {
    Write-Info "   Создание AppBundle: $appBundleId"
    $appBundleResponse = Invoke-RestMethod -Uri $appBundleUrl -Method Post -Headers $headers -Body $appBundleData
    
    $uploadUrl = $appBundleResponse.uploadParameters.endpointURL
    $formData = $appBundleResponse.uploadParameters.formData
    
    Write-Success "AppBundle зарегистрирован"
    Write-Info "   Upload URL: $($uploadUrl.Substring(0, 50))..."
    
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 409) {
        Write-Warning "AppBundle уже существует, обновляем версию..."
        
        # Обновляем версию
        $updateUrl = "https://developer.api.autodesk.com/da/us-east/v3/appbundles/$appBundleId/versions"
        try {
            $appBundleResponse = Invoke-RestMethod -Uri $updateUrl -Method Post -Headers $headers -Body $appBundleData
            $uploadUrl = $appBundleResponse.uploadParameters.endpointURL
            $formData = $appBundleResponse.uploadParameters.formData
            Write-Success "Новая версия AppBundle создана"
        } catch {
            Write-Error "Не удалось обновить AppBundle: $_"
            exit 1
        }
    } else {
        Write-Error "Ошибка регистрации AppBundle: $_"
        exit 1
    }
}

# ===============================================
# ШАГ 10: Загрузка архива на S3
# ===============================================
Write-Host ""
Write-Info "ШАГ 10: Загрузка архива на S3"

# Подготовка multipart/form-data
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

# Создаем тело запроса
$bodyLines = @()

# Добавляем formData поля
foreach ($key in $formData.PSObject.Properties.Name) {
    $value = $formData.$key
    $bodyLines += "--$boundary"
    $bodyLines += "Content-Disposition: form-data; name=`"$key`""
    $bodyLines += ""
    $bodyLines += $value
}

# Добавляем файл
$bodyLines += "--$boundary"
$bodyLines += "Content-Disposition: form-data; name=`"file`"; filename=`"$AppBundleName.zip`""
$bodyLines += "Content-Type: application/octet-stream"
$bodyLines += ""

$bodyStart = ($bodyLines -join $LF) + $LF

$bodyEnd = $LF + "--$boundary--" + $LF

# Читаем ZIP файл как байты
$zipBytes = [System.IO.File]::ReadAllBytes($zipPath)

# Собираем полное тело запроса
$bodyStartBytes = [System.Text.Encoding]::UTF8.GetBytes($bodyStart)
$bodyEndBytes = [System.Text.Encoding]::UTF8.GetBytes($bodyEnd)

$totalBytes = $bodyStartBytes + $zipBytes + $bodyEndBytes

try {
    Write-Info "   Загрузка $AppBundleName.zip на S3..."
    
    $uploadResponse = Invoke-RestMethod -Uri $uploadUrl -Method Post -Body $totalBytes -ContentType "multipart/form-data; boundary=$boundary"
    
    Write-Success "Архив загружен на S3"
    
} catch {
    Write-Error "Ошибка загрузки на S3: $_"
    # Продолжаем, возможно уже загружен
}

# ===============================================
# ШАГ 11: Создание Alias
# ===============================================
Write-Host ""
Write-Info "ШАГ 11: Создание alias 'v1'"

$version = $appBundleResponse.version
$aliasUrl = "https://developer.api.autodesk.com/da/us-east/v3/appbundles/$appBundleId/aliases"

$aliasData = @{
    id = "v1"
    version = $version
} | ConvertTo-Json

$headers = @{
    "Authorization" = "Bearer $accessToken"
    "Content-Type" = "application/json"
}

try {
    $aliasResponse = Invoke-RestMethod -Uri $aliasUrl -Method Post -Headers $headers -Body $aliasData
    Write-Success "Alias 'v1' создан"
    Write-Info "   Full ID: $appBundleId+v1"
    
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 409) {
        Write-Warning "Alias 'v1' уже существует"
        
        # Обновляем существующий alias
        $updateAliasUrl = "$aliasUrl/v1"
        $aliasData = @{
            version = $version
        } | ConvertTo-Json
        
        try {
            Invoke-RestMethod -Uri $updateAliasUrl -Method Patch -Headers $headers -Body $aliasData | Out-Null
            Write-Success "Alias 'v1' обновлен на версию $version"
        } catch {
            Write-Warning "Не удалось обновить alias: $_"
        }
    } else {
        Write-Warning "Ошибка создания alias: $_"
    }
}

# ===============================================
# ШАГ 12: Проверка созданного AppBundle
# ===============================================
Write-Host ""
Write-Info "ШАГ 12: Проверка AppBundle"

$checkUrl = "https://developer.api.autodesk.com/da/us-east/v3/appbundles/$appBundleId+v1"

try {
    $checkResponse = Invoke-RestMethod -Uri $checkUrl -Method Get -Headers $headers
    
    Write-Success "AppBundle проверен и работает"
    Write-Host ""
    Write-Host "   📋 Детали:" -ForegroundColor Cyan
    Write-Host "      ID: $($checkResponse.id)"
    Write-Host "      Engine: $($checkResponse.engine)"
    Write-Host "      Version: $($checkResponse.version)"
    Write-Host "      Description: $($checkResponse.description)"
    
} catch {
    Write-Warning "Не удалось проверить AppBundle: $_"
}

# ===============================================
# ИТОГ
# ===============================================
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                  ✅ УСПЕХ! AppBundle готов!                  ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📦 AppBundle ID: $appBundleId+v1" -ForegroundColor Cyan
Write-Host "📁 Архив: $zipPath" -ForegroundColor Cyan
Write-Host "🔑 SHA256: $zipHash" -ForegroundColor Cyan
Write-Host ""

Write-Host "🎯 Следующий шаг: Обновить Activity" -ForegroundColor Yellow
Write-Host ""
Write-Host "   Используйте этот AppBundle в Activity:" -ForegroundColor Yellow
Write-Host "   `"appbundles`": [ `"$appBundleId+v1`" ]" -ForegroundColor White
Write-Host ""
Write-Host "   Или запустите:" -ForegroundColor Yellow
Write-Host "   pwsh .\Update-Activity.ps1 -ActivityId `"BotBti.DWG2DWGCopy+v1`" -AppBundleFull `"$appBundleId+v1`"" -ForegroundColor White
Write-Host ""

# Сохраняем информацию в файл
$reportPath = Join-Path $OutputPath "appbundle_report.json"
$report = @{
    appBundleId = "$appBundleId+v1"
    zipPath = $zipPath
    sha256 = $zipHash
    createdAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    version = $version
} | ConvertTo-Json

Set-Content -Path $reportPath -Value $report
Write-Info "Отчет сохранен: $reportPath"

