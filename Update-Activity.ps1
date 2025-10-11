# Update-Activity.ps1
# Обновление Activity для подключения AppBundle
# Использование: pwsh .\Update-Activity.ps1 -AccessToken "..." -ActivityId "..." -AppBundleFull "..."

param(
  [Parameter(Mandatory=$true)]
  [string]$AccessToken,   # OAuth 2-legged token
  
  [Parameter(Mandatory=$true)]
  [string]$ActivityId,    # например: "BotBti.DWG2DWGCopy" (БЕЗ +v1)
  
  [Parameter(Mandatory=$true)]
  [string]$AppBundleFull  # например: "BotBti.BTI_InsertBasman+v1"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          🔄 ОБНОВЛЕНИЕ ACTIVITY В AUTODESK APS          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Параметры:" -ForegroundColor Yellow
Write-Host "   Activity ID:  $ActivityId" -ForegroundColor White
Write-Host "   AppBundle:    $AppBundleFull" -ForegroundColor White
Write-Host ""

# URL шаблона БТИ
$templateUrl = "https://storage.googleapis.com/btibot-processed/templates/basmanny-template.dwg"

# Тело запроса для обновления Activity
$body = @{
    commandLine = @(
        # Команда загружает плагин через /al и вызывает InsertBTIBasman
        '$(engine.path)\\accoreconsole.exe /i "$(args[inputFile].path)" /al "$(appbundles[BTI_InsertBasman].path)" /s "InsertBTIBasman\n"'
    )
    parameters = @{
        inputFile = @{
            verb = "get"
            description = "Input DWG file"
            required = $true
            localName = "input.dwg"
        }
        templateFile = @{
            verb = "get"
            description = "BTI Basmann template"
            required = $true
            localName = "template.dwg"
            url = $templateUrl
        }
        resultFile = @{
            verb = "put"
            description = "Output DWG with BTI template"
            required = $true
            localName = "result.dwg"
        }
    }
    engine = "Autodesk.AutoCAD+25_1"
    appbundles = @($AppBundleFull)
    description = "Insert BTI Basmann template using .NET plugin"
} | ConvertTo-Json -Depth 10

$headers = @{
    "Authorization" = "Bearer $AccessToken"
    "Content-Type"  = "application/json"
}

$uri = "https://developer.api.autodesk.com/da/us-east/v3/activities/$ActivityId"

try {
    Write-Host "🔄 Отправка PATCH запроса..." -ForegroundColor Yellow
    
    $response = Invoke-RestMethod -Method Patch -Uri $uri -Headers $headers -Body $body
    
    Write-Host ""
    Write-Host "✅ Activity обновлён успешно!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Результат:" -ForegroundColor Cyan
    Write-Host "   ID:          $($response.id)" -ForegroundColor White
    Write-Host "   Version:     $($response.version)" -ForegroundColor White
    Write-Host "   Engine:      $($response.engine)" -ForegroundColor White
    Write-Host "   AppBundles:  $($response.appbundles -join ', ')" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 Activity готов к использованию: $ActivityId+v1" -ForegroundColor Green
    
} catch {
    Write-Host ""
    Write-Host "❌ Ошибка обновления Activity!" -ForegroundColor Red
    Write-Host "   Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "   Message: $($_.Exception.Message)" -ForegroundColor Red
    
    # Пытаемся получить детали ошибки
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $errorBody = $reader.ReadToEnd()
        Write-Host "   Details: $errorBody" -ForegroundColor Red
    }
    
    exit 1
}

Write-Host ""
Write-Host "🎉 ГОТОВО! Теперь обновите forge_client.py:" -ForegroundColor Yellow
Write-Host "   activityId = `"$ActivityId+v1`"" -ForegroundColor White
Write-Host ""

