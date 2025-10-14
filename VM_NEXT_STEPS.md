# ✅ Шаблон скачан! Что дальше?

**Файл:** `bti_basmanny_template.dwg` (52420 bytes = 51.2 KB)  
**Статус:** ✅ Успешно скачан на VM

---

## 🎯 Следующие шаги

### **1. Переместить шаблон в проект**

```powershell
# Создать директорию templates в проекте
New-Item -Path "C:\BTI-DWG-PDF\templates" -ItemType Directory -Force

# Переместить скачанный шаблон
Move-Item -Path "bti_basmanny_template.dwg" -Destination "C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg"

# Проверить
Get-Item "C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg"
```

---

### **2. Использовать шаблон в .NET плагине**

В файле `BTI_InsertBasman.cs` можно использовать шаблон:

```csharp
// Путь к шаблону
string templatePath = @"C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg";

// Или относительный путь
string templatePath = Path.Combine(
    Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location),
    "templates",
    "bti_basmanny_template.dwg"
);

// Вставить блок из шаблона в текущий чертеж
public void InsertTemplate()
{
    Document doc = Application.DocumentManager.MdiActiveDocument;
    Database db = doc.Database;
    
    using (Transaction tr = db.TransactionManager.StartTransaction())
    {
        // Импорт всех объектов из шаблона
        using (Database templateDb = new Database(false, true))
        {
            templateDb.ReadDwgFile(templatePath, FileOpenMode.OpenForReadAndAllShare, false, null);
            db.Insert(Matrix3d.Identity, templateDb, false);
        }
        
        tr.Commit();
    }
}
```

---

### **3. Создать Activity с шаблоном**

**Вариант A: Упаковать шаблон в AppBundle**

```powershell
# Скопировать шаблон в директорию AppBundle
Copy-Item "C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg" `
  -Destination "C:\BTI-DWG-PDF\BTI_TemplateAppBundle\bti_basmanny_template.dwg"

# Создать ZIP с плагином и шаблоном
Compress-Archive -Path "C:\BTI-DWG-PDF\BTI_TemplateAppBundle\*" `
  -DestinationPath "C:\BTI-DWG-PDF\BTI_InsertBasman.zip" -Force
```

**Вариант B: Использовать публичный URL шаблона**

Activity уже настроен использовать URL:
```
https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
```

Это уже работает через `BotBti.BTI_INSERT_Basman+v1`!

---

### **4. Тестировать локально (на VM)**

```powershell
# Открыть AutoCAD на VM
& "C:\Program Files\Autodesk\AutoCAD 2025\acad.exe"

# Загрузить .NET плагин
NETLOAD → Выбрать BTI_InsertBasman.dll

# Запустить команду вставки шаблона
BTI_INSERT_TEMPLATE
```

---

## 🚀 Рекомендуемый путь

### **Самый простой вариант:**

**Использовать уже настроенный Activity с публичным URL шаблона!**

Не нужно ничего компилировать на VM - просто используйте:

```python
# В forge_client.py
workitem = forge_client.submit_workitem(
    input_url, 
    output_url, 
    use_template=True  # ← Включить типовой шаблон BTI
)
```

Это автоматически:
1. Загружает шаблон из GCS
2. Вставляет в DWG через Activity `BotBti.BTI_INSERT_Basman+v1`
3. Сохраняет результат

**Никакой работы на VM не требуется!** ✨

---

## 🔧 Альтернативный путь (для .NET разработки)

Если хотите создать собственный .NET плагин:

### **1. Обновить код плагина:**

```powershell
# Перейти в директорию проекта
cd C:\BTI-DWG-PDF\BTI_TemplateAppBundle

# Убедиться что шаблон в проекте
Copy-Item "C:\BTI-DWG-PDF\templates\bti_basmanny_template.dwg" `
  -Destination ".\bti_basmanny_template.dwg"
```

### **2. Обновить BTI_InsertBasman.cs:**

```csharp
namespace BTI_TemplatePlugin
{
    public class Commands
    {
        [CommandMethod("BTI_INSERT_TEMPLATE")]
        public void InsertBTITemplate()
        {
            // Путь к шаблону (в той же директории что и DLL)
            string templatePath = Path.Combine(
                Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location),
                "bti_basmanny_template.dwg"
            );

            // Проверка существования файла
            if (!File.Exists(templatePath))
            {
                Application.DocumentManager.MdiActiveDocument.Editor
                    .WriteMessage($"\nШаблон не найден: {templatePath}");
                return;
            }

            Document doc = Application.DocumentManager.MdiActiveDocument;
            Database db = doc.Database;

            using (Transaction tr = db.TransactionManager.StartTransaction())
            {
                try
                {
                    // Импорт шаблона
                    using (Database templateDb = new Database(false, true))
                    {
                        templateDb.ReadDwgFile(templatePath, 
                            FileOpenMode.OpenForReadAndAllShare, false, null);
                        
                        // Вставка в точку 0,0,0
                        db.Insert(Matrix3d.Identity, templateDb, false);
                    }

                    tr.Commit();
                    
                    doc.Editor.WriteMessage("\n✅ Шаблон BTI успешно вставлен!");
                }
                catch (Exception ex)
                {
                    doc.Editor.WriteMessage($"\n❌ Ошибка: {ex.Message}");
                    tr.Abort();
                }
            }
        }
    }
}
```

### **3. Скомпилировать:**

```powershell
# Собрать проект
dotnet build BTI_InsertBasman.csproj -c Release

# Создать ZIP для AppBundle
$files = @(
    "bin\Release\net48\BTI_InsertBasman.dll",
    "bti_basmanny_template.dwg",
    "PackageContents.xml"
)

Compress-Archive -Path $files -DestinationPath "BTI_InsertBasman.zip" -Force
```

### **4. Загрузить в APS:**

```powershell
# Загрузить AppBundle (используйте существующие скрипты)
python ..\upload_bti_appbundle.py BTI_InsertBasman.zip
```

---

## 📊 Сравнение вариантов

| Вариант | Сложность | Время | Результат |
|---------|-----------|-------|-----------|
| **Использовать готовый Activity** | ⭐ Легко | 0 мин | ✅ Работает сразу |
| **Создать .NET плагин** | ⭐⭐⭐ Средне | 30-60 мин | ✅ Кастомизация |
| **Локальный тест на VM** | ⭐⭐ Легко | 10 мин | ✅ Для отладки |

---

## ✅ Рекомендация

**Используйте готовый Activity с публичным URL шаблона:**

```bash
# На локальной машине (не на VM!)
# В app.py уже настроено:

USE_BTI_TEMPLATE=true

# Деплой
gcloud run deploy telegram-bti-bot \
  --source . \
  --region europe-west1 \
  --set-env-vars="USE_BTI_TEMPLATE=true"
```

**Готово!** Шаблон будет автоматически использоваться при обработке DWG файлов! 🎉

---

## 🎯 Итог

Шаблон `bti_basmanny_template.dwg` на VM:
- ✅ Скачан
- ✅ Доступен по URL в GCS
- ✅ Настроен в Activity `BotBti.BTI_INSERT_Basman+v1`
- ✅ Готов к использованию через `USE_BTI_TEMPLATE=true`

**Никаких дополнительных действий на VM не требуется!** 🚀


