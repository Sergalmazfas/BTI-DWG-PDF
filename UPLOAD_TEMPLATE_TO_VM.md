# 📤 Загрузка шаблона BTI на Windows VM

**VM Instance:** instance-20251013-185458  
**Zone:** us-central1-c  
**External IP:** 34.58.217.128  
**Статус:** RUNNING ✅

---

## 🎯 Что нужно загрузить

```
Файл: bti_basmanny_template.dwg
Размер: 51.2 KB
Локальный путь: bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg
```

---

## 📋 Способы загрузки

### **Способ 1: Через gcloud compute scp (рекомендуется)**

```bash
# Загрузить шаблон на VM
gcloud compute scp \
  bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg \
  instance-20251013-185458:C:/BTI-DWG-PDF/templates/bti_basmanny_template.dwg \
  --zone=us-central1-c
```

**Или сразу в рабочую директорию:**

```bash
# В корень проекта на VM
gcloud compute scp \
  bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg \
  instance-20251013-185458:C:/BTI-DWG-PDF/bti_basmanny_template.dwg \
  --zone=us-central1-c

# В директорию AppBundle
gcloud compute scp \
  bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg \
  instance-20251013-185458:C:/BTI-DWG-PDF/BTI_TemplateAppBundle/bti_basmanny_template.dwg \
  --zone=us-central1-c
```

---

### **Способ 2: Через RDP + скачивание из GCS**

1. **Подключиться к VM через RDP:**

```bash
# Получить Windows пароль (если еще не получали)
gcloud compute reset-windows-password instance-20251013-185458 \
  --zone=us-central1-c \
  --user=admin

# Запомните пароль!
```

2. **RDP подключение:**
   - IP: `34.58.217.128`
   - User: `admin`
   - Password: (из предыдущей команды)

3. **На VM откройте PowerShell и скачайте шаблон:**

```powershell
# Создать директорию для шаблонов
New-Item -Path "C:\BTI-DWG-PDF\templates" -ItemType Directory -Force

# Скачать шаблон из GCS
gsutil cp gs://btibot-processed/templates/bti_basmanny_template.dwg C:\BTI-DWG-PDF\templates\

# Или из локального архива (если уже есть)
Copy-Item "C:\BTI-DWG-PDF\bte-appbundle\archives\basmannyi_novyi_obmernyi.dwg" `
  -Destination "C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg"
```

---

### **Способ 3: Через Google Cloud Console**

1. Открыть: https://console.cloud.google.com/compute/instances
2. Найти VM: `instance-20251013-185458`
3. Нажать **Upload file** в меню
4. Выбрать файл: `bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg`
5. Указать путь на VM: `C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg`

---

### **Способ 4: Через браузер на VM**

1. **Подключиться через RDP** (см. Способ 2)

2. **На VM открыть браузер и скачать:**

```
URL: https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg

Сохранить в: C:\BTI-DWG-PDF\templates\
```

---

## 🔧 Проверка после загрузки

### **Вариант 1: Через gcloud (с локальной машины)**

```bash
# Проверить, что файл существует на VM
gcloud compute ssh instance-20251013-185458 \
  --zone=us-central1-c \
  --command="powershell -Command 'Test-Path C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg'"

# Проверить размер файла
gcloud compute ssh instance-20251013-185458 \
  --zone=us-central1-c \
  --command="powershell -Command 'Get-Item C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg | Select-Object Length'"
```

### **Вариант 2: На самой VM (через RDP)**

```powershell
# Проверить существование файла
Test-Path "C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg"
# Должно вернуть: True

# Проверить размер
Get-Item "C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg" | Select-Object Length, Name
# Должно быть: Length около 52428 bytes (51.2 KB)

# Список всех файлов в templates
Get-ChildItem "C:\BTI-DWG-PDF\templates"
```

---

## 📁 Структура директорий на VM

После загрузки структура должна быть:

```
C:\BTI-DWG-PDF\
├── BTI_TemplateAppBundle\
│   ├── BTI_InsertBasman.cs
│   ├── BTI_InsertBasman.csproj
│   └── ...
├── templates\
│   └── bti_basmanny_template.dwg  ← Сюда загружаем
├── bte-appbundle\
│   └── archives\
│       └── basmannyi_novyi_obmernyi.dwg  ← Исходный файл
└── ...
```

---

## 🚀 Использование шаблона в AppBundle

После загрузки можно использовать шаблон в .NET плагине:

```csharp
// В BTI_InsertBasman.cs
string templatePath = @"C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg";

// Вставить блок из шаблона
using (Transaction tr = db.TransactionManager.StartTransaction())
{
    BlockTable bt = tr.GetObject(db.BlockTableId, OpenMode.ForRead) as BlockTable;
    
    // Импорт шаблона
    using (Database templateDb = new Database(false, true))
    {
        templateDb.ReadDwgFile(templatePath, FileOpenMode.OpenForReadAndAllShare, false, null);
        db.Insert(Matrix3d.Identity, templateDb, false);
    }
    
    tr.Commit();
}
```

---

## 🧪 Быстрый тест

```bash
# 1. Загрузить шаблон
gcloud compute scp \
  bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg \
  instance-20251013-185458:C:/BTI-DWG-PDF/templates/bti_basmanny_template.dwg \
  --zone=us-central1-c

# 2. Проверить
gcloud compute ssh instance-20251013-185458 \
  --zone=us-central1-c \
  --command="powershell -Command 'Get-Item C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg'"
```

---

## ⚠️ Частые проблемы

### **Проблема 1: Директория не существует**

```powershell
# На VM создать директорию
New-Item -Path "C:\BTI-DWG-PDF\templates" -ItemType Directory -Force
```

### **Проблема 2: Нет прав доступа**

```powershell
# На VM дать права
icacls "C:\BTI-DWG-PDF\templates" /grant Everyone:F /T
```

### **Проблема 3: Файл не скопировался полностью**

```bash
# Проверить размер локально
ls -lh bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg

# Проверить размер на VM
gcloud compute ssh instance-20251013-185458 \
  --zone=us-central1-c \
  --command="powershell -Command 'Get-Item C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg | Select-Object Length'"

# Размеры должны совпадать!
```

---

## 📊 Альтернативный способ (через Postman на VM)

Если на VM установлен Postman, можно скачать через API:

```
Method: GET
URL: https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg

Save Response → Save to File
→ C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg
```

---

## ✅ Итоговая команда (рекомендуется)

```bash
# Полная последовательность
# 1. Создать директорию на VM
gcloud compute ssh instance-20251013-185458 \
  --zone=us-central1-c \
  --command="powershell -Command 'New-Item -Path C:\BTI-DWG-PDF\templates -ItemType Directory -Force'"

# 2. Загрузить шаблон
gcloud compute scp \
  bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg \
  instance-20251013-185458:C:/BTI-DWG-PDF/templates/bti_basmanny_template.dwg \
  --zone=us-central1-c

# 3. Проверить
gcloud compute ssh instance-20251013-185458 \
  --zone=us-central1-c \
  --command="powershell -Command 'Get-Item C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg | Format-List Name,Length'"
```

---

**🎯 После загрузки шаблон будет готов к использованию в .NET AppBundle!**


