# 🧩 BTI AppBundle Integration Report

**Дата:** `<ДАТА ВЫПОЛНЕНИЯ>`  
**Исполнитель:** `<ИМЯ>`  
**Платформа:** Windows 10/11 + PowerShell 7+  

---

## 📦 AppBundle Details

| Параметр | Значение |
|----------|----------|
| **AppBundle ID** | `BTI.InsertBasman+v1` |
| **Activity ID** | `BotBti.DWG2DWGCopy+v1` |
| **Alias** | `v1` |
| **Engine** | `Autodesk.AutoCAD+25_1` |
| **SHA256 (bundle.zip)** | `<SHA256_HASH>` |
| **Размер bundle** | `<SIZE> KB` |
| **Статус загрузки** | ✅ Success / ❌ Failed |

---

## 🧱 Compilation Details

**Команда сборки:**
```powershell
pwsh .\Build-BTI-AppBundle.ps1
```

**Output:**
```
<ВСТАВИТЬ ВЫВОД СБОРКИ>
```

**Проверка DLL:**
```
<ВСТАВИТЬ РЕЗУЛЬТАТ ПРОВЕРКИ>
```

---

## 🔁 Activity Update

**Команда:**
```powershell
pwsh .\Update-Activity.ps1 `
  -AccessToken $ACCESS_TOKEN `
  -ActivityId "BotBti.DWG2DWGCopy+v1" `
  -AppBundleFull "BTI.InsertBasman+v1"
```

**Результат:**
```json
<ВСТАВИТЬ JSON ОТВЕТ ОТ APS>
```

---

## 🧪 Тестирование (5 файлов)

| # | Файл | Размер | Время (сек) | Результат | Шаблон вставлен? | Примечание |
|---|------|--------|-------------|-----------|------------------|------------|
| 1 | `test_1.dwg` | `<SIZE>` | `<TIME>` | ✅ / ❌ | ✅ / ❌ | |
| 2 | `test_2.dwg` | `<SIZE>` | `<TIME>` | ✅ / ❌ | ✅ / ❌ | |
| 3 | `test_3.dwg` | `<SIZE>` | `<TIME>` | ✅ / ❌ | ✅ / ❌ | |
| 4 | `test_4.dwg` | `<SIZE>` | `<TIME>` | ✅ / ❌ | ✅ / ❌ | |
| 5 | `test_5.dwg` | `<SIZE>` | `<TIME>` | ✅ / ❌ | ✅ / ❌ | |

### Статистика:
- **Успешных:** `<N>/5`
- **Провалов:** `<N>/5`
- **Среднее время:** `<AVG>` сек
- **p95:** `<P95>` сек
- **Ошибок в логах:** `<N>`

---

## 📊 WorkItem Logs

### Пример успешного WorkItem:
```json
{
  "id": "<WORKITEM_ID>",
  "status": "success",
  "stats": {
    "timeQueued": "...",
    "timeDownloadStarted": "...",
    "timeInstructionsStarted": "...",
    "timeInstructionsEnded": "...",
    "timeUploadEnded": "..."
  }
}
```

### Скриншот/фрагмент лога accoreconsole:
```
<ВСТАВИТЬ ЛОГ С ЗАГРУЗКОЙ ПЛАГИНА И ВСТАВКОЙ ШАБЛОНА>
```

---

## ✅ Acceptance Criteria

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| AppBundle загружен в APS | ✅ / ❌ | |
| Activity обновлён | ✅ / ❌ | |
| Плагин .NET компилируется без ошибок | ✅ / ❌ | |
| 5/5 тестовых файлов обработаны | ✅ / ❌ | |
| Шаблон БТИ вставляется корректно | ✅ / ❌ | |
| Время обработки ≤ 5 сек | ✅ / ❌ | |
| Нет `failedInstructions` / `failedDownload` | ✅ / ❌ | |
| Логи без критических ошибок | ✅ / ❌ | |

---

## 🔍 Issues / Notes

<ОПИСАТЬ ЛЮБЫЕ ПРОБЛЕМЫ ИЛИ ОСОБЕННОСТИ>

---

## 🎯 Итоговый вывод

✅ **Все 5 тестов успешны. Шаблон БТИ вставляется через .NET (Database.Insert). AppBundle готов к продакшену.**

или

❌ **Обнаружены проблемы: <описание>. Требуется доработка.**

---

## 📚 Ссылки

- Официальная документация: https://aps.autodesk.com/en/docs/design-automation/v3/
- Репозиторий: https://github.com/Sergalmazfas/BTI-DWG-PDF
- Коммит: `<HASH>`

---

**Дата завершения:** `<ДАТА>`  
**Подпись:** `<ИМЯ>`

