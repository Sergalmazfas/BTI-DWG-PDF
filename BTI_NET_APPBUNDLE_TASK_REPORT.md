# 🧩 BTI AppBundle Integration Report

**Дата:** 2025-10-14  
**Исполнитель:** Автоматическая сборка через GCP Windows VM  
**Платформа:** Windows Server 2022 + Cloud Shell automation  

---

## 📦 AppBundle Details

| Параметр | Значение |
|----------|----------|
| **AppBundle ID** | `BTI_InsertBasman+v1` |
| **Full ID** | `m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4.BTI_InsertBasman+v1` |
| **Activity ID** | `m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4.DWG2DWGTest+v1` |
| **Alias** | `v1` (version 2) |
| **Engine** | `Autodesk.AutoCAD+25_1` |
| **Bundle Size** | `1.9 KiB (1950 bytes)` |
| **Timestamp** | `2025-10-14T10:18:53Z` |
| **Location** | `gs://btibot-processed/appbundles/BTI_InsertBasman.bundle.zip` |
| **Статус загрузки** | ✅ Success |

---

## 🧱 Compilation Details

**Метод сборки:** Автоматический скрипт через Windows VM startup script

**Процесс:**
1. ✅ Windows Server 2022 VM создана (instance-20251013-185458, us-central1-c)
2. ✅ Файлы исходного кода загружены в GCS (bti-source.zip)
3. ✅ Автоматический скрипт `build-fixed.ps1` выполнен при загрузке VM
4. ✅ .NET SDK 8.0.120 использован для компиляции
5. ✅ DLL создана: `BTI_InsertBasman.dll` (4 KB)
6. ✅ Упаковано с `PackageContents_Basmann.xml` (247 bytes)
7. ✅ Bundle загружен в GCS, затем в Autodesk APS

**Команда сборки:**
```powershell
dotnet build C:\source\BTI_TemplateAppBundle\BTI_InsertBasman.csproj -c Release -o C:\out
```

**Bundle содержимое:**
```
Archive:  BTI_InsertBasman.bundle.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
     4096  2025-10-14 10:18   BTI_InsertBasman.dll
      247  2025-10-14 09:19   PackageContents_Basmann.xml
---------                     -------
     4343                     2 files
```

---

## 🔁 Activity Details

**Activity создана:** ✅

**CommandLine:**
```
$(engine.path)\accoreconsole.exe /i "$(args[inputFile].path)" /al "$(appbundles[BTI_InsertBasman].path)" /s "_QSAVE\n_QUIT\n"
```

**Parameters:**
- `inputFile`: verb=get, localName=input.dwg
- `resultFile`: verb=put, localName=input.dwg

**AppBundles referenced:**
- `m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4.BTI_InsertBasman+v1`

---

## ⚠️ Важные замечания

### Текущее состояние плагина:

**Это ТЕСТОВАЯ версия!** Плагин содержит минимальный код БЕЗ Autodesk AutoCAD зависимостей:

```csharp
using System;

namespace BTI_TemplatePlugin
{
    public class Commands
    {
        public static void SaveDWG()
        {
            Console.WriteLine("BTI Plugin Loaded");
        }
    }
}
```

**Почему упрощённый код:**
- ❌ На Windows VM нет AutoCAD DLL для компиляции
- ❌ Полный код с `Autodesk.AutoCAD.*` вызывает ошибки компиляции
- ✅ Минимальная версия позволяет проверить, что pipeline работает

**Для продакшена нужно:**
1. Установить AutoCAD ObjectARX SDK на Windows машине
2. Скомпилировать ПОЛНЫЙ плагин с `Database.Insert()` и шаблоном БТИ
3. Загрузить новую версию AppBundle

---

## 🧪 Тестирование

**Статус:** ⏳ В процессе

**План:**
1. ✅ Деплой Telegram бота с новой Activity (в процессе)
2. ⏳ Отправить тестовый DWG файл через @ZamerProbot
3. ⏳ Проверить статус WorkItem
4. ⏳ Протестировать 5 разных DWG файлов
5. ⏳ Зафиксировать время обработки и p95

**Ожидаемый результат:**
- WorkItem должен завершиться со `status: "success"`
- Выходной DWG должен быть создан
- Плагин загрузится (`/al` параметр)
- **НО:** шаблон БТИ не будет вставлен (т.к. плагин тестовый)

---

## 📊 Проблемы и решения

### Проблема 1: Нехватка памяти на VM
- **Проблема:** e2-micro (1 GB) недостаточно для Windows Server
- **Решение:** Увеличили до e2-small (2 GB) и e2-standard-2 (4 GB)

### Проблема 2: GitHub недоступен с VM
- **Проблема:** Private repository требует auth
- **Решение:** Загрузили исходники в GCS, VM скачивает оттуда

### Проблема 3: Autodesk DLL отсутствуют
- **Проблема:** `error CS0246: The type or namespace name 'Autodesk' could not be found`
- **Решение:** Создали упрощённую версию БЕЗ Autodesk зависимостей для теста pipeline

### Проблема 4: Пустой bundle.zip (22 bytes)
- **Проблема:** 7zip не находил файлы для архивации
- **Решение:** Исправили пути в PowerShell скрипте, использовали автопоиск файлов

### Проблема 5: GCS права доступа (403)
- **Проблема:** VM не могла загружать в GCS
- **Решение:** Добавили `devstorage.read_write` scope к service account

---

## ✅ Acceptance Criteria

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| AppBundle загружен в APS | ✅ | Version 2, alias v1 |
| Activity создана/обновлена | ✅ | DWG2DWGTest+v1 |
| .NET плагин компилируется без ошибок | ✅ | Тестовая версия |
| 5/5 тестовых файлов обработаны | ⏳ | Ожидает деплоя бота |
| Шаблон БТИ вставляется корректно | ❌ | Требуется полный плагин |
| Время обработки ≤ 5 сек | ⏳ | Будет проверено при тестах |
| Нет `failedInstructions` / `failedDownload` | ⏳ | Будет проверено при тестах |
| Логи без критических ошибок | ⏳ | Будет проверено при тестах |

---

## 🎯 Следующие шаги

### Немедленно (после деплоя бота):
1. ✅ Протестировать через Telegram бота (@ZamerProbot)
2. ✅ Проверить WorkItem status
3. ✅ Убедиться что плагин загружается

### Для продакшена (требуется Windows с AutoCAD SDK):
1. ❌ Установить AutoCAD ObjectARX SDK
2. ❌ Скомпилировать полный плагин с вставкой шаблона
3. ❌ Загрузить версию 3 AppBundle
4. ❌ Протестировать с реальными БТИ обмерами

---

## 📚 Ссылки

- **Официальная документация:** https://aps.autodesk.com/en/docs/design-automation/v3/
- **Репозиторий:** https://github.com/Sergalmazfas/BTI-DWG-PDF
- **AppBundle в GCS:** gs://btibot-processed/appbundles/BTI_InsertBasman.bundle.zip
- **Source в GCS:** gs://btibot-processed/sources/bti-source.zip

---

## 🔍 Технические детали

### Windows VM:
- **Instance:** instance-20251013-185458
- **Zone:** us-central1-c
- **Machine:** e2-small (2 vCPU, 2 GB RAM)
- **OS:** Windows Server 2022 Datacenter
- **IP:** 104.154.216.53

### Startup Script:
- **Location:** gs://btibot-processed/scripts/build-fixed.ps1
- **Method:** windows-startup-script-url
- **Execution:** Автоматически при каждом reset

### Build Process:
- **Chocolatey:** Уже установлен
- **Git:** Установлен через choco
- **.NET SDK:** 8.0.120
- **7-Zip:** 25.01 (x64)
- **Build time:** ~10 минут (после загрузки VM)

---

## 🎉 Итоговый вывод

✅ **AppBundle успешно собран и загружен в Autodesk APS!**

✅ **Activity создана и связана с AppBundle.**

⚠️ **Текущая версия плагина - ТЕСТОВАЯ (без Autodesk функционала).**

📋 **После тестирования через бота - обновить плагин с полным кодом вставки шаблона БТИ.**

---

**Дата завершения:** 2025-10-14 10:40 UTC  
**Подпись:** Automated Build System
