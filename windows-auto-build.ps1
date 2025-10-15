# ========================================
# АВТОМАТИЧЕСКАЯ СБОРКА BTI PLUGIN
# Выполняется на Windows VM автоматически
# ========================================

$ErrorActionPreference = "Continue"
$LogFile = "C:\build-log.txt"

function Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage
}

Log "========================================="
Log "BTI AppBundle Auto-Build Script Started"
Log "========================================="

# 1. Установка Chocolatey
Log "Step 1: Installing Chocolatey..."
try {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    Log "✅ Chocolatey installed"
} catch {
    Log "❌ Chocolatey installation failed: $_"
}

# Обновить PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 2. Установка Git
Log "Step 2: Installing Git..."
try {
    choco install git -y --no-progress
    Log "✅ Git installed"
} catch {
    Log "⚠️ Git installation failed: $_"
}

# 3. Установка Python
Log "Step 3: Installing Python..."
try {
    choco install python -y --no-progress
    Log "✅ Python installed"
} catch {
    Log "⚠️ Python installation failed: $_"
}

# 4. Установка 7zip
Log "Step 4: Installing 7zip..."
try {
    choco install 7zip -y --no-progress
    Log "✅ 7zip installed"
} catch {
    Log "⚠️ 7zip installation failed: $_"
}

# 5. Установка .NET SDK
Log "Step 5: Installing .NET SDK..."
try {
    choco install dotnet-sdk -y --no-progress
    Log "✅ .NET SDK installed"
} catch {
    Log "⚠️ .NET SDK installation failed: $_"
}

# Обновить PATH снова после установки
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Подождать, чтобы все установилось
Start-Sleep -Seconds 30

# 6. Проверка установленных инструментов
Log "Step 6: Verifying installations..."
try {
    $gitVersion = & git --version 2>&1
    Log "Git: $gitVersion"
} catch {
    Log "❌ Git not found"
}

try {
    $pythonVersion = & python --version 2>&1
    Log "Python: $pythonVersion"
} catch {
    Log "❌ Python not found"
}

try {
    $dotnetVersion = & dotnet --version 2>&1
    Log "Dotnet: $dotnetVersion"
} catch {
    Log "❌ Dotnet not found"
}

# 7. Клонирование репозитория
Log "Step 7: Cloning repository..."
try {
    Set-Location C:\
    if (Test-Path "C:\BTI-DWG-PDF") {
        Log "Repository already exists, pulling latest..."
        Set-Location C:\BTI-DWG-PDF
        & git pull
    } else {
        & git clone https://github.com/Sergalmazfas/BTI-DWG-PDF.git
        Set-Location C:\BTI-DWG-PDF
    }
    & git checkout release/gold1
    Log "✅ Repository cloned/updated"
} catch {
    Log "❌ Repository clone failed: $_"
    exit 1
}

# 8. Сборка проекта
Log "Step 8: Building .NET project..."
try {
    $projPath = "C:\BTI-DWG-PDF\BTI_TemplateAppBundle\BTI_InsertBasman.csproj"
    $outDir = "C:\build-output"
    
    if (!(Test-Path $outDir)) {
        New-Item -ItemType Directory -Path $outDir -Force | Out-Null
    }
    
    & dotnet build $projPath -c Release -o $outDir
    
    if (Test-Path "$outDir\BTI_InsertBasman.dll") {
        Log "✅ Build successful! DLL created."
    } else {
        Log "❌ Build failed - DLL not found"
        exit 1
    }
} catch {
    Log "❌ Build failed: $_"
    exit 1
}

# 9. Создание bundle.zip
Log "Step 9: Creating bundle.zip..."
try {
    $bundlePath = "C:\BTI_InsertBasman.bundle.zip"
    $dllPath = "C:\build-output\BTI_InsertBasman.dll"
    $xmlPath = "C:\BTI-DWG-PDF\BTI_TemplateAppBundle\PackageContents_Basmann.xml"
    
    # Копировать файлы во временную директорию
    Copy-Item $dllPath -Destination "C:\BTI_InsertBasman.dll" -Force
    Copy-Item $xmlPath -Destination "C:\PackageContents_Basmann.xml" -Force
    
    # Создать ZIP
    if (Test-Path $bundlePath) {
        Remove-Item $bundlePath -Force
    }
    
    & "C:\Program Files\7-Zip\7z.exe" a -tzip $bundlePath "C:\BTI_InsertBasman.dll" "C:\PackageContents_Basmann.xml"
    
    if (Test-Path $bundlePath) {
        $size = (Get-Item $bundlePath).Length
        $hash = (Get-FileHash $bundlePath -Algorithm SHA256).Hash
        Log "✅ Bundle created: $bundlePath"
        Log "   Size: $size bytes"
        Log "   SHA256: $hash"
    } else {
        Log "❌ Bundle creation failed"
        exit 1
    }
    
    # Очистка временных файлов
    Remove-Item "C:\BTI_InsertBasman.dll" -Force -ErrorAction SilentlyContinue
    Remove-Item "C:\PackageContents_Basmann.xml" -Force -ErrorAction SilentlyContinue
} catch {
    Log "❌ Bundle creation failed: $_"
    exit 1
}

# 10. Загрузка в GCS
Log "Step 10: Uploading to Google Cloud Storage..."
try {
    # Проверка gsutil
    $gsutilPath = "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gsutil.cmd"
    
    if (Test-Path $gsutilPath) {
        & $gsutilPath cp "C:\BTI_InsertBasman.bundle.zip" "gs://btibot-processed/appbundles/BTI_InsertBasman.bundle.zip"
        Log "✅ Bundle uploaded to GCS"
    } else {
        Log "⚠️ gsutil not found, skipping upload to GCS"
        Log "   Bundle available locally at: C:\BTI_InsertBasman.bundle.zip"
    }
} catch {
    Log "⚠️ Upload to GCS failed: $_"
    Log "   Bundle available locally at: C:\BTI_InsertBasman.bundle.zip"
}

# 11. Сохранить метаданные
Log "Step 11: Saving build metadata..."
$metadata = @{
    BuildDate = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss UTC")
    BundlePath = "C:\BTI_InsertBasman.bundle.zip"
    SHA256 = (Get-FileHash "C:\BTI_InsertBasman.bundle.zip" -Algorithm SHA256).Hash
    Size = (Get-Item "C:\BTI_InsertBasman.bundle.zip").Length
    Status = "SUCCESS"
} | ConvertTo-Json

$metadata | Out-File "C:\build-metadata.json" -Encoding UTF8
Log "Metadata saved to C:\build-metadata.json"

Log "========================================="
Log "✅ BUILD COMPLETE!"
Log "========================================="
Log "Next steps:"
Log "1. Download bundle from GCS or VM"
Log "2. Upload to Autodesk APS"
Log "3. Update Activity"
Log "4. Test with 5 DWG files"

