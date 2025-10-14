# 🔧 Исправление доступа к Design Automation API

## 🚨 Проблема
```
❌ The client_id specified does not have access to the api product
```

Текущий Client ID (ECc0J...) не имеет доступа к **Design Automation API**.

## 💡 Решения

### Вариант 1: Дать доступ текущему Client ID (Рекомендуется)

1. **Зайти в APS Portal:**
   - Открыть https://aps.autodesk.com/myapps/
   - Войти в аккаунт Autodesk

2. **Найти приложение:**
   - Найти приложение с Client ID начинающимся на `ECc0J...`
   - Кликнуть на название приложения

3. **Добавить API доступ:**
   - В разделе "API Access" найти **Design Automation API**
   - Поставить галочку напротив **Design Automation API**
   - Нажать **Save**

4. **Проверить изменения:**
   ```bash
   python3 check_forge_access.py
   ```

### Вариант 2: Использовать другой Client ID

Если у вас уже есть Client ID с доступом к Design Automation API (например, `m6CK3...`):

#### 2.1 Через Google Cloud Console (Production)

1. **Обновить секреты:**
   ```bash
   # Обновить Client ID
   echo "YOUR_NEW_CLIENT_ID" | gcloud secrets versions add FORGE_CLIENT_ID --data-file=-

   # Обновить Client Secret (если нужно)
   echo "YOUR_NEW_CLIENT_SECRET" | gcloud secrets versions add FORGE_CLIENT_SECRET --data-file=-
   ```

2. **Проверить изменения:**
   ```bash
   # Перезапустить сервис в Cloud Run
   gcloud run deploy dwg-processor-metadata --region europe-west1
   ```

#### 2.2 Через переменные окружения (Локальная разработка)

1. **Установить переменные:**
   ```bash
   export FORGE_CLIENT_ID="m6CK3YOUR_CLIENT_ID_WITH_DA_ACCESS"
   export FORGE_CLIENT_SECRET="YOUR_CORRESPONDING_SECRET"
   ```

2. **Проверить:**
   ```bash
   python3 check_forge_access.py
   ```

## 🔍 Диагностика

### Проверка текущего статуса
```bash
python3 check_forge_access.py
```

### Проверка секретов в GCP
```bash
# Проверить список версий
gcloud secrets versions list FORGE_CLIENT_ID

# Получить текущее значение (осторожно - выводится в plain text!)
gcloud secrets versions access latest --secret="FORGE_CLIENT_ID"
```

### Проверка переменных окружения
```bash
echo "Client ID: ${FORGE_CLIENT_ID:0:8}..."
echo "Client Secret: ${FORGE_CLIENT_SECRET:0:8}..."
```

## 📋 Сравнение вариантов

| Критерий | Вариант 1 (Дать доступ) | Вариант 2 (Сменить ID) |
|----------|-------------------------|------------------------|
| Простота | ⭐⭐⭐ | ⭐⭐ |
| Время | 5 минут | 10-15 минут |
| Риски | Минимальные | Средние (нужно менять секреты) |
| Откат | Легко | Сложнее |

## 🎯 Рекомендация

**Выберите Вариант 1** - дать доступ к Design Automation API текущему Client ID.

Это:
- ✅ Быстрее всего
- ✅ Не требует изменения секретов
- ✅ Минимальный риск сломать что-то другое
- ✅ Легко откатить при необходимости

## 🚀 После исправления

1. **Проверить работу API:**
   ```bash
   python3 check_forge_access.py
   ```

2. **Перезапустить бота:**
   ```bash
   # Локально
   python3 app.py

   # В Cloud Run
   gcloud run deploy dwg-processor-metadata --region europe-west1
   ```

3. **Проверить работу через Telegram бота:**
   - Отправить DWG файл боту
   - Убедиться, что обработка проходит без ошибок

## 🔐 Безопасность

- 🚨 **Никогда** не публикуйте Client ID и Client Secret в открытых репозиториях
- 🔒 Используйте Google Secret Manager для production
- 🔄 Регулярно ротируйте секреты (раз в 6-12 месяцев)
- 📝 Ведите журнал изменений секретов

## 📞 Поддержка

Если проблема не решается:

1. **Проверьте APS Status:** https://health.autodesk.com/
2. **Проверьте квоты:** В APS Portal → Usage & Quotas
3. **Обратитесь в поддержку Autodesk:** https://aps.autodesk.com/support

## 📊 Мониторинг

После исправления рекомендуется настроить мониторинг:

1. **Логи успешных WorkItem:**
   ```
   ✅ WorkItem created: [ID]
   ✅ WorkItem succeeded!
   ```

2. **Алерты на ошибки доступа:**
   ```
   ❌ does not have access to the api product
   ❌ Invalid client credentials
   ```

3. **Метрики использования API:**
   - Количество WorkItem в день
   - Время обработки
   - Процент успешных конверсий