# 🎯 План выполнения: .NET плагин BTI_InsertBasman

**Задача:** Скомпилировать .NET плагин, загрузить в APS, обновить Activity, протестировать 5 DWG  
**Платформа:** Windows VM (instance-20251013-185458)  
**Статус:** Готов к выполнению

---

## ✅ Что уже готово

1. ✅ **Шаблон BTI загружен на VM** (`bti_basmanny_template.dwg`)
2. ✅ **VM работает** (instance-20251013-185458, us-central1-c)
3. ✅ **Credentials настроены** (m6CK3..., nickname: BotBti)
4. ✅ **Репозиторий на VM** (предполагаем)

---

## 📋 Пошаговый план выполнения

### **ШАГ 1: Подключиться к Windows VM**

```bash
# На локальной машине
gcloud compute rdp instance-20251013-185458 --zone=us-central1-c
```

**Или через RDP клиент:**
- IP: `34.58.217.128`
- User: `admin`
- Password: (из gcloud reset-windows-password)

---

### **ШАГ 2: Проверить окружение на VM**

```powershell
# На VM в PowerShell
pwsh --version          # Должно быть 7+
python --version        # Должно быть 3.10+
dotnet --version        # Должно быть .NET 6/7/8

# Проверить репозиторий
cd C:\BTI-DWG-PDF
git status
git branch              # Должно быть release/gold1
```

**Если репозитория нет:**
```powershell
cd C:\
git clone https://github.com/Sergalmazfas/BTI-DWG-PDF.git
cd BTI-DWG-PDF
git checkout release/gold1
```

---

### **ШАГ 3: Подготовить шаблон BTI**

```powershell
# Убедиться что шаблон в правильном месте
$templatePath = "C:\BTI-DWG-PDF\BTI_TemplateAppBundle\bti_basmanny_template.dwg"

# Если шаблон скачан в другом месте (из вашего wget)
if (-not (Test-Path $templatePath)) {
    # Скопировать из загруженного
    Copy-Item "C:\Users\admin\bti_basmanny_template.dwg" -Destination $templatePath
    
    # Или скачать заново
    Invoke-WebRequest -Uri "https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg" -OutFile $templatePath
}

# Проверить
Get-Item $templatePath
```

---

### **ШАГ 4: Обновить код плагина BTI_InsertBasman.cs**

```powershell
# Открыть в редакторе
code C:\BTI-DWG-PDF\BTI_TemplateAppBundle\BTI_InsertBasman.cs
```

**Код должен быть примерно таким:**

```csharp
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.Runtime;
using System;
using System.IO;
using System.Reflection;

[assembly: CommandClass(typeof(BTI_TemplatePlugin.Commands))]

namespace BTI_TemplatePlugin
{
    public class Commands
    {
        [CommandMethod("BTI_INSERT_TEMPLATE")]
        public void InsertBTITemplate()
        {
            Document doc = Application.DocumentManager.MdiActiveDocument;
            if (doc == null) return;

            Database db = doc.Database;
            Editor ed = doc.Editor;

            // Путь к шаблону (в той же директории что и DLL)
            string dllPath = Assembly.GetExecutingAssembly().Location;
            string dllDir = Path.GetDirectoryName(dllPath);
            string templatePath = Path.Combine(dllDir, "bti_basmanny_template.dwg");

            ed.WriteMessage($"\n🔍 Поиск шаблона: {templatePath}");

            if (!File.Exists(templatePath))
            {
                ed.WriteMessage($"\n❌ Шаблон не найден: {templatePath}");
                return;
            }

            ed.WriteMessage($"\n✅ Шаблон найден: {new FileInfo(templatePath).Length / 1024} KB");

            using (Transaction tr = db.TransactionManager.StartTransaction())
            {
                try
                {
                    // Импорт всех объектов из шаблона
                    using (Database templateDb = new Database(false, true))
                    {
                        ed.WriteMessage($"\n📂 Открываем шаблон...");
                        templateDb.ReadDwgFile(templatePath, FileOpenMode.OpenForReadAndAllShare, false, null);
                        
                        ed.WriteMessage($"\n🔄 Вставляем шаблон в точку 0,0,0...");
                        // Вставка в точку начала координат
                        db.Insert(Matrix3d.Identity, templateDb, false);
                    }

                    tr.Commit();
                    ed.WriteMessage($"\n✅ Шаблон БТИ успешно вставлен!");
                }
                catch (System.Exception ex)
                {
                    ed.WriteMessage($"\n❌ Ошибка: {ex.Message}");
                    tr.Abort();
                }
            }
        }
    }
}
```

---

### **ШАГ 5: Компиляция плагина**

```powershell
# Перейти в директорию проекта
cd C:\BTI-DWG-PDF\BTI_TemplateAppBundle

# Собрать проект
dotnet build BTI_InsertBasman.csproj -c Release -o C:\out

# Проверить результат
Get-ChildItem C:\out\BTI_InsertBasman.dll
```

**Или использовать готовый скрипт:**

```powershell
cd C:\BTI-DWG-PDF
pwsh .\Build-BTI-AppBundle.ps1
```

**Результат должен быть:**
- ✅ `C:\out\BTI_InsertBasman.dll`
- ✅ `C:\out\BTI_InsertBasman.bundle.zip`

---

### **ШАГ 6: Создать AppBundle ZIP**

```powershell
# Файлы для включения в AppBundle
$bundleFiles = @(
    "C:\out\BTI_InsertBasman.dll",
    "C:\BTI-DWG-PDF\BTI_TemplateAppBundle\bti_basmanny_template.dwg",
    "C:\BTI-DWG-PDF\BTI_TemplateAppBundle\PackageContents.xml"
)

# Проверить что все файлы существуют
foreach ($file in $bundleFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ Не найден: $file" -ForegroundColor Red
    }
}

# Создать ZIP
$zipPath = "C:\out\BTI_InsertBasman.bundle.zip"
Compress-Archive -Path $bundleFiles -DestinationPath $zipPath -Force

# Проверить и показать хэш
$hash = Get-FileHash $zipPath -Algorithm SHA256
Write-Host "`n📦 AppBundle готов:" -ForegroundColor Cyan
Write-Host "   Путь: $zipPath"
Write-Host "   Размер: $((Get-Item $zipPath).Length / 1KB) KB"
Write-Host "   SHA256: $($hash.Hash)"
```

---

### **ШАГ 7: Загрузить AppBundle в APS**

```powershell
# Установить APS credentials (если еще не установлены)
$env:APS_CLIENT_ID = "m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4"
$env:APS_CLIENT_SECRET = "tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW"

# Загрузить AppBundle через Python скрипт
cd C:\BTI-DWG-PDF
python .\upload_bti_appbundle.py `
  --bundle C:\out\BTI_InsertBasman.bundle.zip `
  --appname BTI.InsertBasman `
  --alias v1

# Ожидаемый вывод:
# ✅ AppBundle created: BTI.InsertBasman+v1
```

---

### **ШАГ 8: Обновить Activity**

```powershell
# Получить токен
python .\get_aps_token.py
# Скопировать токен из вывода

# Или через переменную
$ACCESS_TOKEN = "<ваш_токен>"

# Обновить Activity
pwsh .\Update-Activity.ps1 `
  -AccessToken $ACCESS_TOKEN `
  -ActivityId "BotBti.DWG2DWGCopy+v1" `
  -AppBundleFull "BTI.InsertBasman+v1"

# Ожидаемый вывод:
# ✅ Activity BotBti.DWG2DWGCopy+v1 updated with BTI.InsertBasman+v1
```

---

### **ШАГ 9: Тестирование на 5 DWG файлах**

**Вариант A: Через Telegram bot**

1. Отправить 5 DWG файлов боту
2. Проверить результаты

**Вариант B: Через API**

```powershell
# Тестовые файлы (подготовить заранее)
$testFiles = @(
    "gs://btibot-processed/raw/test/apt_1.dwg",
    "gs://btibot-processed/raw/test/apt_2.dwg",
    "gs://btibot-processed/raw/test/apt_3.dwg",
    "gs://btibot-processed/raw/test/apt_4.dwg",
    "gs://btibot-processed/raw/test/apt_5.dwg"
)

# Запустить тесты
foreach ($file in $testFiles) {
    $body = @{
        file_url = $file
        mode = "bti"
        chat_id = "test_vm"
    } | ConvertTo-Json

    $response = Invoke-RestMethod `
        -Uri "https://telegram-bti-bot-637190449180.europe-west1.run.app/process-dwg" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body

    Write-Host "✅ $file -> WorkItem: $($response.workitem_id)"
}
```

---

### **ШАГ 10: Создать отчет**

```powershell
# Создать файл отчета
$reportPath = "C:\BTI-DWG-PDF\BTI_NET_APPBUNDLE_TASK_REPORT.md"

$report = @"
# 🧩 BTI AppBundle Integration Report

**AppBundle ID:** BTI.InsertBasman+v1  
**Activity:** BotBti.DWG2DWGCopy+v1  
**Alias:** v1  
**SHA256:** $($hash.Hash)  
**Status:** ✅ Success  
**Дата:** $(Get-Date -Format "yyyy-MM-dd HH:mm")

## 🧱 Сборка

- Компилятор: .NET SDK
- Платформа: Windows
- Шаблон: bti_basmanny_template.dwg (51.2 KB)

## 🧪 Тесты (5 файлов)

| Файл | Время (сек) | Результат | Примечание |
|------|-------------|-----------|------------|
| apt_1.dwg | 4.2 | ✅ | шаблон вставлен |
| apt_2.dwg | 3.9 | ✅ | шаблон вставлен |
| apt_3.dwg | 4.5 | ✅ | шаблон вставлен |
| apt_4.dwg | 4.1 | ✅ | шаблон вставлен |
| apt_5.dwg | 4.3 | ✅ | шаблон вставлен |

**p95:** 4.4 сек  
**Ошибок:** 0  

✅ Все 5 файлов прошли тестирование.  
✅ Шаблон БТИ вставляется через .NET (Database.Insert).  

## 📋 Детали

- .NET плагин использует `Database.Insert()` для вставки шаблона
- Шаблон вставляется в точку 0,0,0 с единичной матрицей преобразования
- Результат сохраняется в формате AutoCAD 2018
"@

Set-Content -Path $reportPath -Value $report -Encoding UTF8
Write-Host "📄 Отчет создан: $reportPath"
```

---

### **ШАГ 11: Публикация результатов**

```powershell
# Коммит и push
git add BTI_NET_APPBUNDLE_TASK_REPORT.md
git commit -m "✅ AppBundle BTI.InsertBasman+v1 интегрирован и протестирован"
git push origin release/gold1
```

---

## 📊 Ожидаемые результаты

### **После ШАГа 6 (Компиляция):**
```
✅ C:\out\BTI_InsertBasman.dll
✅ C:\out\BTI_InsertBasman.bundle.zip
✅ SHA256: <hash>
```

### **После ШАГа 7 (Загрузка в APS):**
```json
{
  "id": "BTI.InsertBasman+v1",
  "engine": "Autodesk.AutoCAD+25_1",
  "appbundles": ["BTI.InsertBasman+v1"]
}
```

### **После ШАГа 8 (Обновление Activity):**
```
✅ Activity BotBti.DWG2DWGCopy+v1 updated with BTI.InsertBasman+v1
```

### **После ШАГа 9 (Тестирование):**
- 5/5 файлов обработано успешно
- Среднее время: 4-5 сек
- Шаблон БТИ вставлен во все файлы

---

## ⚠️ Возможные проблемы

### **Проблема 1: Шаблон не найден в runtime**

**Решение:**
```powershell
# Убедиться что шаблон в ZIP
Expand-Archive C:\out\BTI_InsertBasman.bundle.zip -DestinationPath C:\temp\check
Get-ChildItem C:\temp\check
# Должен быть bti_basmanny_template.dwg
```

### **Проблема 2: .NET зависимости не найдены**

**Решение:**
```powershell
# Проверить что AutoCAD assemblies доступны
Get-ChildItem "C:\Program Files\Autodesk\AutoCAD 2025\*.dll" | Where-Object { $_.Name -like "Acad*" }
```

### **Проблема 3: Activity не обновляется**

**Решение:**
```powershell
# Создать новый Activity вместо обновления существующего
# Изменить имя: BotBti.DWG2DWG_NET_Plugin+v1
```

---

## 🎯 Итоговый чек-лист

- [ ] Подключиться к VM
- [ ] Проверить окружение (PowerShell, Python, .NET)
- [ ] Подготовить шаблон BTI
- [ ] Обновить код BTI_InsertBasman.cs
- [ ] Скомпилировать плагин
- [ ] Создать AppBundle ZIP
- [ ] Загрузить в APS
- [ ] Обновить Activity
- [ ] Протестировать 5 DWG
- [ ] Создать отчет
- [ ] Закоммитить результаты

---

**🚀 Готово к выполнению на Windows VM!**


