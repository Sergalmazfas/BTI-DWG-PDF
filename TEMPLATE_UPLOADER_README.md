# 📁 Загрузчик эталонных шаблонов БТИ

## 🎯 **Назначение**

Скрипт для загрузки эталонного DWG файла `Басманное — новые обмерные планы.dwg` из Telegram и сохранения его как шаблон `basmanoe-bti.dwg` в GCS с проверкой доступности через AutoDesk Forge API.

## 📋 **Требования**

### **Переменные окружения:**
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export GOOGLE_CLOUD_PROJECT="talkhint"
```

### **Google Cloud сервисы:**
- Cloud Storage (bucket: `btibot-processed`)
- Secret Manager (секреты: `FORGE_CLIENT_ID`, `FORGE_CLIENT_SECRET`)
- IAM права для работы с GCS и Forge API

### **Python зависимости:**
```bash
pip install -r requirements.txt
```

## 🚀 **Использование**

### **Автоматический запуск:**
```bash
python3 run_template_uploader.py
```

### **Ручной запуск бота:**
```bash
python3 upload_template.py
```

### **Проверка существующего шаблона:**
```bash
python3 verify_template.py
```

## 📱 **Инструкция для пользователя**

1. **Запустите бота** командой `/start`
2. **Загрузите файл** с точным именем: `Басманное — новые обмерные планы.dwg`
3. **Дождитесь обработки** - бот покажет прогресс:
   - ✅ Загрузка из Telegram
   - ✅ Сохранение в GCS
   - ✅ Проверка через Forge API
4. **Получите подтверждение** о готовности шаблона

## 🏗️ **Архитектура**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   Google Cloud   │    │  AutoDesk Forge │
│                 │    │     Storage      │    │       API       │
│  File Upload    │───▶│                  │───▶│                 │
│  Validation     │    │ templates/       │    │  Accessibility  │
│  Processing     │    │ basmanoe-bti.dwg │    │     Check       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📊 **Метаданные шаблона**

После загрузки файлу назначаются следующие метаданные:

```json
{
  "x-type": "template",
  "x-name": "basmanoe-bti.dwg",
  "x-purpose": "BTI reference drawing",
  "x-uploaded-at": "2025-01-XX...",
  "x-source": "telegram-upload",
  "x-version": "1.0"
}
```

## 🔍 **Проверка шаблона**

### **Команды бота:**
- `/start` - Начало работы
- `/status` - Проверка статуса шаблона
- `/help` - Справка

### **Программная проверка:**
```python
from verify_template import TemplateVerifier

verifier = TemplateVerifier()
result = verifier.verify_template_complete()

if result['overall_success']:
    print("✅ Шаблон готов к использованию!")
else:
    print(f"❌ Ошибка: {result['error']}")
```

## 📁 **Структура файлов**

```
gs://btibot-processed/
└── templates/
    └── basmanoe-bti.dwg    # Эталонный шаблон БТИ
        ├── x-type: template
        ├── x-name: basmanoe-bti.dwg
        ├── x-purpose: BTI reference drawing
        ├── x-uploaded-at: timestamp
        ├── x-source: telegram-upload
        └── x-version: 1.0
```

## 🧪 **Тестирование**

### **Тест загрузки:**
1. Отправьте файл `Басманное — новые обмерные планы.dwg`
2. Проверьте сохранение в GCS
3. Убедитесь в назначении метаданных

### **Тест Forge API:**
1. Запустите `python3 verify_template.py`
2. Проверьте загрузку в Forge OSS
3. Убедитесь в корректной обработке

### **Тест интеграции:**
```bash
# Проверка доступности через Forge API
curl -X POST https://forge-controller-637190449180.europe-west1.run.app/forge/process \
  -H "Content-Type: application/json" \
  -d '{
    "dwg": "gs://btibot-processed/templates/basmanoe-bti.dwg",
    "template": "basmanoe",
    "meta": {"test": true}
  }'
```

## 🚨 **Обработка ошибок**

### **Частые ошибки:**

1. **Неправильное имя файла:**
   ```
   ❌ Неправильное имя файла
   Ожидается: Басманное — новые обмерные планы.dwg
   Получен: basmanoe.dwg
   ```

2. **Неправильный формат:**
   ```
   ❌ Неправильный формат файла
   Ожидается: .dwg
   Получен: .pdf
   ```

3. **Ошибка Forge API:**
   ```
   ⚠️ Шаблон загружен с предупреждением
   ❌ Forge API: Authentication failed
   ✅ GCS: Файл сохранен
   ```

### **Решение проблем:**

1. **Проверьте имя файла** - должно точно совпадать
2. **Убедитесь в формате DWG** - не PDF или другой формат
3. **Проверьте Forge API credentials** в Secret Manager
4. **Убедитесь в правах доступа** к GCS bucket

## 📊 **Логирование**

### **Уровни логов:**
- `INFO` - Обычная работа (загрузка, сохранение)
- `WARNING` - Предупреждения (файл загружен, но Forge недоступен)
- `ERROR` - Ошибки (неправильный файл, проблемы с API)

### **Примеры логов:**
```
2025-01-XX 10:30:00 - INFO - ✅ Template uploaded successfully: templates/basmanoe-bti.dwg
2025-01-XX 10:30:05 - INFO - ✅ Forge access token получен
2025-01-XX 10:30:10 - ERROR - ❌ Forge API error: 401 Unauthorized
```

## 🔧 **Конфигурация**

### **Настройка бота:**
```python
# В upload_template.py
class TemplateUploader:
    def __init__(self, project_id: str = "talkhint"):
        self.bucket_name = "btibot-processed"
        self.template_path = "templates/basmanoe-bti.dwg"
```

### **Настройка проверки:**
```python
# В verify_template.py
class TemplateVerifier:
    def __init__(self, project_id: str = "talkhint"):
        self.bucket_name = "btibot-processed"
        self.template_path = "templates/basmanoe-bti.dwg"
```

## 🎯 **Результат**

После успешной загрузки:

1. **Файл сохранен** в `gs://btibot-processed/templates/basmanoe-bti.dwg`
2. **Метаданные назначены** для идентификации как шаблон БТИ
3. **Forge API проверен** - файл корректно открывается
4. **Готов к использованию** в BTI Processor

### **Использование в BTI Processor:**
```python
# Теперь можно использовать шаблон
template_files = {
    "template": "gs://btibot-processed/templates/basmanoe-bti.dwg",
    "frame": "gs://btibot-processed/templates/basmanoe-frame.dwg",
    "stamp": "gs://btibot-processed/templates/basmanoe-stamp.dwg"
}
```

## 📞 **Поддержка**

При возникновении проблем:

1. Проверьте логи в консоли
2. Убедитесь в правильности переменных окружения
3. Проверьте доступность Google Cloud сервисов
4. Убедитесь в корректности Forge API credentials

---

**🎉 Шаблон готов к использованию в BTI Processor!**
