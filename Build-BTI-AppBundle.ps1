# Build-BTI-AppBundle.ps1
# Автоматическая сборка .NET плагина BTI для Autodesk APS
# Использование: pwsh .\Build-BTI-AppBundle.ps1

param(
  [string]$ProjPath = ".\BTI_TemplateAppBundle\BTI_InsertBasman.csproj",
  [string]$OutDir   = ".\out\win-release",
  [string]$Bundle   = ".\out\BTI_InsertBasman.bundle.zip",
  [string]$Manifest = ".\BTI_TemplateAppBundle\PackageContents_Basmann.xml"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      🏗️  СБОРКА BTI APPBUNDLE ДЛЯ AUTODESK APS        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Проверка наличия проекта
if (!(Test-Path $ProjPath)) {
    Write-Host "❌ Проект не найден: $ProjPath" -ForegroundColor Red
    exit 1
}

Write-Host "📁 Проект: $ProjPath" -ForegroundColor Green
Write-Host ""

# 1) Очистка старых сборок
Write-Host "🧹 Очистка старых сборок..." -ForegroundColor Yellow
if (Test-Path $OutDir) {
    Remove-Item $OutDir -Recurse -Force
}
New-Item -Force -ItemType Directory $OutDir | Out-Null

# 2) Сборка через dotnet build
Write-Host "🔨 Компиляция проекта..." -ForegroundColor Yellow
$buildOutput = & dotnet build $ProjPath -c Release -o $OutDir 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка компиляции!" -ForegroundColor Red
    Write-Host $buildOutput
    exit 1
}

Write-Host "✅ Компиляция успешна!" -ForegroundColor Green

# 3) Проверка DLL
$dll = Join-Path $OutDir "BTI_InsertBasman.dll"
if (!(Test-Path $dll)) {
    Write-Host "❌ DLL не найден: $dll" -ForegroundColor Red
    exit 1
}

$dllSize = (Get-Item $dll).Length
Write-Host "✅ DLL создан: $dllSize bytes" -ForegroundColor Green

# 4) Упаковка bundle.zip
Write-Host ""
Write-Host "📦 Создание bundle.zip..." -ForegroundColor Yellow

# Удаляем старый ZIP если есть
if (Test-Path $Bundle) {
    Remove-Item $Bundle -Force
}

# Создаём временную папку для упаковки
$tempBundle = ".\temp_bundle"
if (Test-Path $tempBundle) {
    Remove-Item $tempBundle -Recurse -Force
}
New-Item -ItemType Directory $tempBundle | Out-Null

# Копируем файлы во временную папку (БЕЗ вложенной структуры!)
Copy-Item $dll -Destination "$tempBundle\BTI_InsertBasman.dll" -Force
Copy-Item $Manifest -Destination "$tempBundle\PackageContents_Basmann.xml" -Force

# Создаём ZIP (плоская структура - файлы в корне)
Write-Host "   Упаковка файлов..." -ForegroundColor Gray
if (Get-Command "7z" -ErrorAction SilentlyContinue) {
    # Используем 7zip если есть
    & 7z a -tzip $Bundle "$tempBundle\*" | Out-Null
} else {
    # Fallback на Compress-Archive
    Compress-Archive -Path "$tempBundle\*" -DestinationPath $Bundle -Force
}

# Очищаем временную папку
Remove-Item $tempBundle -Recurse -Force

if (!(Test-Path $Bundle)) {
    Write-Host "❌ Bundle.zip не создан!" -ForegroundColor Red
    exit 1
}

$bundleSize = (Get-Item $Bundle).Length
Write-Host "✅ Bundle создан: $bundleSize bytes" -ForegroundColor Green

# 5) Вычисление SHA256
Write-Host ""
Write-Host "🔐 Вычисление SHA256..." -ForegroundColor Yellow
$sha256 = (Get-FileHash $Bundle -Algorithm SHA256).Hash
Write-Host "✅ SHA256: $sha256" -ForegroundColor Green

# 6) Проверка содержимого ZIP
Write-Host ""
Write-Host "📋 Проверка содержимого ZIP:" -ForegroundColor Yellow
if (Get-Command "7z" -ErrorAction SilentlyContinue) {
    & 7z l $Bundle
} else {
    Write-Host "   (установите 7zip для детальной проверки)" -ForegroundColor Gray
    Write-Host "   Файлов в архиве: 2 (BTI_InsertBasman.dll + PackageContents_Basmann.xml)" -ForegroundColor Gray
}

# 7) Итоговый отчёт
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║              ✅ СБОРКА ЗАВЕРШЕНА УСПЕШНО!               ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "📁 Файлы:" -ForegroundColor Cyan
Write-Host "   DLL:    $dll" -ForegroundColor White
Write-Host "   Bundle: $Bundle" -ForegroundColor White
Write-Host ""
Write-Host "📊 Метрики:" -ForegroundColor Cyan
Write-Host "   DLL размер:    $dllSize bytes" -ForegroundColor White
Write-Host "   Bundle размер: $bundleSize bytes" -ForegroundColor White
Write-Host "   SHA256:        $sha256" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Следующий шаг:" -ForegroundColor Yellow
Write-Host "   python upload_bti_appbundle.py" -ForegroundColor White
Write-Host ""

# Сохраняем метрики в файл
$report = @"
BTI AppBundle Build Report
==========================
Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
DLL: $dll ($dllSize bytes)
Bundle: $Bundle ($bundleSize bytes)
SHA256: $sha256
"@

$report | Out-File "build_report.txt" -Encoding UTF8
Write-Host "📄 Отчёт сохранён: build_report.txt" -ForegroundColor Green

