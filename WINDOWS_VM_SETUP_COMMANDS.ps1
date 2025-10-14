# ========================================
# WINDOWS VM SETUP - BTI AppBundle Build
# ========================================
# Выполнить в PowerShell на Windows VM
# IP: 35.237.157.220
# User: sergalmazfas
# ========================================

Write-Host "🪟 BTI Windows VM Setup Script" -ForegroundColor Cyan

# 1. Проверка PowerShell версии
Write-Host "`n1️⃣ Проверка PowerShell..." -ForegroundColor Yellow
$PSVersionTable.PSVersion

# 2. Установка Chocolatey (package manager)
Write-Host "`n2️⃣ Установка Chocolatey..." -ForegroundColor Yellow
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 3. Установка инструментов через Chocolatey
Write-Host "`n3️⃣ Установка Git, Python, 7zip..." -ForegroundColor Yellow
choco install git python 7zip -y

# 4. Установка .NET SDK
Write-Host "`n4️⃣ Установка .NET SDK 8.0..." -ForegroundColor Yellow
choco install dotnet-sdk -y

# 5. Перезагрузить переменные окружения
Write-Host "`n5️⃣ Обновление PATH..." -ForegroundColor Yellow
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 6. Проверка установленных инструментов
Write-Host "`n6️⃣ Проверка установленных инструментов..." -ForegroundColor Yellow
Write-Host "Git:" -NoNewline
git --version
Write-Host "Python:" -NoNewline
python --version
Write-Host ".NET SDK:" -NoNewline
dotnet --version

# 7. Клонирование репозитория
Write-Host "`n7️⃣ Клонирование репозитория..." -ForegroundColor Yellow
cd C:\
git clone https://github.com/Sergalmazfas/BTI-DWG-PDF.git
cd BTI-DWG-PDF
git checkout release/gold1

# 8. Установка Python зависимостей
Write-Host "`n8️⃣ Установка Python зависимостей..." -ForegroundColor Yellow
pip install requests

# 9. Настройка APS переменных окружения
Write-Host "`n9️⃣ Настройка APS переменных..." -ForegroundColor Yellow
Write-Host "⚠️ НУЖНО УКАЗАТЬ APS_CLIENT_ID и APS_CLIENT_SECRET!" -ForegroundColor Red
Write-Host "Выполните в Cloud Shell:" -ForegroundColor Cyan
Write-Host 'gcloud secrets versions access latest --secret="FORGE_CLIENT_ID" --project="talkhint"' -ForegroundColor Green
Write-Host 'gcloud secrets versions access latest --secret="FORGE_CLIENT_SECRET" --project="talkhint"' -ForegroundColor Green
Write-Host ""
Write-Host "Затем выполните здесь (заменить значения):" -ForegroundColor Cyan
Write-Host '[System.Environment]::SetEnvironmentVariable("APS_CLIENT_ID", "YOUR_CLIENT_ID", "User")' -ForegroundColor Green
Write-Host '[System.Environment]::SetEnvironmentVariable("APS_CLIENT_SECRET", "YOUR_CLIENT_SECRET", "User")' -ForegroundColor Green

# 10. Готово к сборке
Write-Host "`n✅ Установка завершена!" -ForegroundColor Green
Write-Host "`n📋 Следующие шаги:" -ForegroundColor Cyan
Write-Host "1. Получить APS креды из Secret Manager (см. выше)" -ForegroundColor White
Write-Host "2. Установить переменные окружения APS_CLIENT_ID и APS_CLIENT_SECRET" -ForegroundColor White
Write-Host "3. Перезапустить PowerShell" -ForegroundColor White
Write-Host "4. cd C:\BTI-DWG-PDF" -ForegroundColor White
Write-Host "5. pwsh .\Build-BTI-AppBundle.ps1" -ForegroundColor White
Write-Host "6. python .\upload_bti_appbundle.py --bundle .\out\BTI_InsertBasman.bundle.zip --appname BTI.InsertBasman --alias v1" -ForegroundColor White

