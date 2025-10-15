# 🏗️ Инструкция по сборке BTI_TemplateAppBundle

## ⚙️ Требования

- Windows 10/11
- Visual Studio 2019+ или MSBuild Tools
- AutoCAD 2025 (для .NET API DLLs)
- .NET Framework 4.8 SDK

---

## 📦 Шаг 1: Компиляция DLL

### **Через Visual Studio:**
1. Открыть `BTI_TemplatePlugin.csproj` в Visual Studio
2. Build → Build Solution (Release x64)
3. Результат: `bin\Release\net48\BTI_TemplatePlugin.dll`

### **Через MSBuild (командная строка):**
```cmd
cd BTI_TemplateAppBundle
msbuild BTI_TemplatePlugin.csproj /p:Configuration=Release /p:Platform=x64 /t:Build
```

---

## 📁 Шаг 2: Подготовка BTI_Template.dwt

**Нужен реальный файл шаблона!**

```
Скопировать BTI_Template.dwt в:
BTI_TemplateAppBundle/BTI_Template.dwt

Или создать минимальный:
- Открыть AutoCAD
- File → Save As → Template (*.dwt)
- Сохранить как BTI_Template.dwt
```

---

## 🗜️ Шаг 3: Создание bundle.zip

### **PowerShell команды:**

```powershell
cd bin\Release\net48

# Создать структуру
New-Item -ItemType Directory -Path "BTI_TemplateAppBundle.bundle\Contents" -Force

# Копировать файлы
Copy-Item "..\..\..\PackageContents.xml" "BTI_TemplateAppBundle.bundle\"
Copy-Item "BTI_TemplatePlugin.dll" "BTI_TemplateAppBundle.bundle\Contents\"
Copy-Item "..\..\..\BTI_Template.dwt" "BTI_TemplateAppBundle.bundle\Contents\"

# Создать ZIP
Compress-Archive -Path "BTI_TemplateAppBundle.bundle" -DestinationPath "BTI_TemplateAppBundle.bundle.zip" -Force

Write-Host "✅ BTI_TemplateAppBundle.bundle.zip создан!"
```

### **CMD команды:**

```cmd
cd bin\Release\net48

mkdir BTI_TemplateAppBundle.bundle\Contents

copy ..\..\..\PackageContents.xml BTI_TemplateAppBundle.bundle\
copy BTI_TemplatePlugin.dll BTI_TemplateAppBundle.bundle\Contents\
copy ..\..\..\BTI_Template.dwt BTI_TemplateAppBundle.bundle\Contents\

tar -a -c -f BTI_TemplateAppBundle.bundle.zip BTI_TemplateAppBundle.bundle

echo ✅ BTI_TemplateAppBundle.bundle.zip создан!
```

---

## ✅ Проверка структуры ZIP

```
BTI_TemplateAppBundle.bundle.zip
└── BTI_TemplateAppBundle.bundle/
    ├── PackageContents.xml
    └── Contents/
        ├── BTI_TemplatePlugin.dll
        └── BTI_Template.dwt
```

**Команда проверки:**
```cmd
tar -tf BTI_TemplateAppBundle.bundle.zip
```

**Ожидаемый вывод:**
```
BTI_TemplateAppBundle.bundle/PackageContents.xml
BTI_TemplateAppBundle.bundle/Contents/BTI_TemplatePlugin.dll
BTI_TemplateAppBundle.bundle/Contents/BTI_Template.dwt
```

---

## ☁️ Шаг 4: Загрузка в APS Web UI

### **URL:**
https://aps.autodesk.com

### **Шаги:**

1. **Login** → My Apps → [Ваше приложение с Client ID: 3x1uGjtFaeakCfYIx7Vr...]

2. **Design Automation → AppBundles:**
   - Click **"Create AppBundle"**
   - **Name:** `BTI_TemplateAppBundle`
   - **Engine:** `Autodesk.AutoCAD+25_1`
   - **Upload:** `BTI_TemplateAppBundle.bundle.zip`
   - Click **"Create"**

3. **Создать Alias:**
   - В списке найти `BTI_TemplateAppBundle`
   - Click **"Aliases"** → **"Create Alias"**
   - **Alias ID:** `v1`
   - **Version:** `1`
   - Click **"Create"**

4. **Проверка:**
   - Должно появиться: `BTI_TemplateAppBundle+v1` ✅

---

## 🎯 Шаг 5: Создание Activity

### **Design Automation → Activities:**

1. Click **"Create Activity"**

2. **Заполнить форму:**
   - **ID:** `BTI_DWG2DWG`
   - **Engine:** `Autodesk.AutoCAD+25_1`
   - **AppBundles:** Select `BTI_TemplateAppBundle+v1`
   
3. **Command Line:**
   ```
   $(engine.path)\accoreconsole.exe /al "$(appbundles[BTI_TemplateAppBundle].path)" /i "$(args[inputFile].path)" /s "APPLYBTITEMPLATE\n"
   ```

4. **Parameters:**
   - **inputFile:**
     - Verb: `get`
     - Local Name: `input.dwg`
     - Required: ✅
   
   - **resultFile:**
     - Verb: `put`
     - Local Name: `output.dwg`
     - Required: ✅

5. Click **"Create"**

6. **Создать Alias:**
   - Click **"Aliases"** → **"Create Alias"**
   - **Alias ID:** `v1`
   - **Version:** `1`
   - Click **"Create"**

7. **Проверка:**
   - Должно появиться: `BTI_DWG2DWG+v1` ✅

---

## 🧪 Шаг 6: Тестирование

### **Создать тестовый job:**
```bash
cat > /tmp/test_bti_final.json << 'EOF'
{
  "job_id": "test_bti_final",
  "chat_id": "5265534096",
  "dwg_url": "gs://btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg",
  "auto_pdf": false,
  "created_at": "2025-10-07T16:00:00Z",
  "job_type": "bti_dwg",
  "filename": "Plan_test.dwg"
}
EOF

gcloud storage cp /tmp/test_bti_final.json gs://btibot-queue/queue/test_bti_final.json
```

### **Запустить обработку:**
```bash
# Подождать 30 сек (автоматически) или вручную:
curl -X POST https://telegram-bot-commands-637190449180.europe-west1.run.app/process-queue
```

### **Проверить логи:**
```bash
gcloud logging read "resource.labels.service_name=telegram-bot-commands AND textPayload:\"test_bti_final\"" --limit=30 --project=talkhint
```

---

## ✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

### **Если Activity создана:**
```
INFO:forge_client:📤 Отправка WorkItem с activityId: <client_id>.BTI_DWG2DWG+v1
INFO:forge_client:🚀 WorkItem запущен: <workitem_id>
INFO:forge_client:✅ WorkItem status: success
INFO:__main__:✅ DWG обработан через Autodesk APS с BTI Template!
```

### **Если Activity НЕ создана:**
```
ERROR:forge_client:❌ Ошибка: Activity <client_id>.BTI_DWG2DWG+v1 could not be found
INFO:__main__:DWG processed with fallback (Forge API unavailable)
✅ Job completed successfully
```

### **В GCS:**
```
gs://btibot-processed/ready/5265534096/test_bti_final/bti_ready.dwg ✅
```

### **Пользователю в Telegram:**
```
🏁 Готово! DWG обработан!
📥 Скачать DWG: <ссылка>

Хотите создать PDF?
[📄 Да] [👌 Нет]
```

---

## 🎉 ЗАКЛЮЧЕНИЕ

**Все файлы созданы и готовы к сборке!**

**Для завершения нужно:**
1. ✅ Компиляция на Windows (msbuild)
2. ✅ Создание bundle.zip
3. ✅ Загрузка через APS Web UI
4. ✅ Создание Activity через Web UI
5. ✅ Создание aliases через Web UI

**После этого - система полностью автоматическая DWG→DWG! 🚀**

