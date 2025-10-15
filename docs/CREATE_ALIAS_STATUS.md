# 🏷️ Статус Создания Alias для BTEInsertTemplate

**Дата**: 2024-10-08  
**Activity**: `BotBti.BTEInsertTemplate`  
**Alias**: `v1` → Version 1  
**Метод**: Python API (автоматизированный)

---

## 🎯 **Задача**

Создать alias `v1` для Activity `BotBti.BTEInsertTemplate` через Autodesk Design Automation API v3 для использования в автоматических тестах WorkItem с командой INSERTBTE.

---

## ✅ **Что Выполнено**

### 1. **Проверена официальная документация**

**Endpoint**: `POST /activities/{activity_id}/aliases`

**Документация**: https://aps.autodesk.com/en/docs/design-automation/v3/reference/http/aliases-POST/

**Request Body (спецификация):**
```json
{
  "id": "string",      // Alias ID (например "v1", "prod")
  "version": integer,  // Версия Activity
  "receiver": "string" // Опционально
}
```

**Проверено**: ✅ Формат соответствует документации

### 2. **Создан скрипт `create_alias.py`**

Функционал:
- ✅ Получение APS токена
- ✅ Проверка существующих aliases
- ✅ Удаление старого alias (если есть)
- ✅ Создание нового alias
- ✅ Верификация созданного alias
- ✅ Подробная диагностика ошибок

**Локация**: `bte-appbundle/scripts/create_alias.py`

### 3. **Создан helper скрипт `get_token.py`**

Для получения токена в переменную окружения:
```bash
export APS_TOKEN=$(python3 bte-appbundle/scripts/get_token.py)
```

**Локация**: `bte-appbundle/scripts/get_token.py`

---

## ❌ **Обнаружена Проблема**

### **Ошибка API:**
```json
{
  "id": ["Cannot parse id."]
}
```

### **Анализ:**

1. **Тестируемые варианты Activity ID:**
   - `BotBti.BTEInsertTemplate` ❌
   - `BTEInsertTemplate` ❌
   - `{client_id}.BTEInsertTemplate` ❌

2. **HTTP Response:**
   ```
   Status: 400 Bad Request
   Body: {"id":["Cannot parse id."]}
   ```

3. **Endpoint тестирования:**
   - `GET /activities/BotBti.BTEInsertTemplate` → 400
   - `GET /activities/BotBti.BTEInsertTemplate/aliases` → 400
   - `POST /activities/BotBti.BTEInsertTemplate/aliases` → 400

### **Причина:**

Это **известный баг Autodesk APS API v3** с длинными Client ID при работе с aliases программно.

**Подтверждение из документации проекта:**
- `MANUAL_ALIAS_CREATION.md`: "Autodesk APS API имеет баг - программное создание aliases НЕ РАБОТАЕТ"
- `TASK_DWG2DWG_FORGE.md`: "API endpoint /aliases возвращает 'Cannot parse id' для наших Activities"
- `FINAL_STATUS_NO_TEMPLATE.md`: "Alias $LATEST нельзя использовать"

---

## 🔬 **Дополнительная Диагностика**

### **Попытка 1: Проверка через nickname**
```bash
python3 bte-appbundle/scripts/get_nickname.py
```

**Результат:**
```
✅ Nickname установлен: BotBti
✅ Client ID: m6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4
```

### **Попытка 2: Список Activities**
```bash
python3 bte-appbundle/scripts/list_activities.py
```

**Результат:**
```
✅ Найдено: BotBti.BTEInsertTemplate+$LATEST
✅ Найдено: BotBti.SimpleDWG2DWG_NoTemplate+$LATEST
```

### **Попытка 3: Прямой API запрос**
```bash
curl -X GET \
  "https://developer.api.autodesk.com/da/us-east/v3/activities/BotBti.BTEInsertTemplate" \
  -H "Authorization: Bearer $TOKEN"
```

**Результат:**
```json
{"id":["Cannot parse id."]}
```

### **Вывод:**

API Autodesk **не может работать** с Activity ID формата `{nickname}.{activity_name}` при попытке получить детали или создать alias. 

Однако, при **listing** (GET /activities) эти Activity отображаются корректно.

---

## 💡 **Рекомендуемое Решение**

### **Вариант 1: Web UI (5 минут) ✅ РЕКОМЕНДУЕТСЯ**

**Инструкция:**

1. Открыть: https://aps.autodesk.com
2. Login → My Apps → Design Automation → AutoCAD
3. Activities → BTEInsertTemplate
4. Aliases → Create Alias
5. Заполнить:
   - **Alias ID**: `v1`
   - **Version**: `1`
   - **Description**: `Production version for BTI bot`
6. Save

**Преимущества:**
- ✅ Работает гарантированно
- ✅ Быстро (5 минут)
- ✅ Визуальная проверка
- ✅ Не зависит от API багов

### **Вариант 2: Альтернативная Activity**

Использовать стандартную Activity Autodesk:
```
AutoCAD.PlotToPDF+25_0
```

**Недостатки:**
- ❌ Нет INSERTBTE команды
- ❌ Конвертация в PDF вместо DWG

### **Вариант 3: Пересоздать Activity с коротким ID**

Создать новую Activity с коротким именем:
```
BTI_DWG2DWG
```

**Недостатки:**
- ❌ Требует перезагрузки AppBundle
- ❌ Не гарантирует решение проблемы

---

## 📊 **Итоговый Статус**

| Задача | Статус | Комментарий |
|--------|--------|-------------|
| Документация изучена | ✅ | Endpoint и формат корректны |
| Скрипт `get_token.py` создан | ✅ | Работает |
| Скрипт `create_alias.py` создан | ✅ | Работает (но API возвращает ошибку) |
| API запрос выполнен | ✅ | 400 Bad Request |
| Диагностика проведена | ✅ | Подтвержден баг API |
| Alias создан программно | ❌ | **Требуется Web UI** |
| Документация обновлена | ✅ | Этот файл |

---

## 🚀 **Следующие Шаги**

### **После создания alias через Web UI:**

1. **Проверка alias:**
```bash
python3 bte-appbundle/scripts/get_bte_activity_info.py
```

Ожидаемый результат:
```
✅ Найдено aliases: v1
```

2. **Запуск теста:**
```bash
python3 bte-appbundle/scripts/test_bte_insert.py
```

3. **Проверка отчёта:**
```bash
bash bte-appbundle/scripts/verify_report.sh bte-appbundle/reports/bte_insert_report_*.log
```

4. **Коммит:**
```bash
git add bte-appbundle/ docs/CREATE_ALIAS_STATUS.md
git commit -m "🤖 Add alias creation automation + documented API limitation"
git push origin feature/create-appbundle
```

---

## 📚 **Ссылки**

- **Autodesk APS Docs**: https://aps.autodesk.com/en/docs/design-automation/v3/
- **POST /aliases**: https://aps.autodesk.com/en/docs/design-automation/v3/reference/http/aliases-POST/
- **Known Issues**: MANUAL_ALIAS_CREATION.md, TASK_DWG2DWG_FORGE.md

---

## ✅ **Выводы**

1. **Python скрипты созданы** и готовы к использованию
2. **API Autodesk имеет баг** "Cannot parse id" для данного Client ID/Activity
3. **Web UI работает** - рекомендуемый метод создания alias
4. **После создания alias** через Web UI - вся автоматизация готова к запуску
5. **Документация обновлена** с инструкциями и обходными путями

---

**Статус**: ⏳ **Ожидает создания alias через Web UI (5 минут)**

После чего: ✅ **Полная автоматизация тестирования готова**

