# BTI DWG → PDF Converter

Telegram bot для конвертации DWG файлов в PDF формат.

## Возможности

- 📐 Конвертация DWG файлов в PDF
- ☁️ Облачное хранение в Google Cloud Storage
- 🔗 Публичные ссылки на результаты
- 📱 Telegram Bot интерфейс
- 🌐 REST API для интеграций

## Технологии

- **Python 3.11** - основной язык
- **Flask** - веб-фреймворк
- **python-telegram-bot** - Telegram Bot API
- **ezdxf + matplotlib** - конвертация DWG → PDF
- **Google Cloud Storage** - хранение файлов
- **Cloud Run** - деплой и масштабирование

## Ограничения

- Только DWG файлы (входной формат)
- Максимальный размер: 100 MB
- Время обработки: 2-5 минут
- Результаты хранятся 30 дней

## Установка

### Локальная разработка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Sergalmazfas/BTI-DWG-PDF.git
cd BTI-DWG-PDF
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения:
```bash
export BOT_TOKEN="your_telegram_bot_token"
export GOOGLE_CLOUD_PROJECT="your_project_id"
export GCS_BUCKET="your_bucket_name"
```

5. Запустите приложение:
```bash
python app.py
```

### Docker

```bash
# Сборка образа
docker build -t bti-dwg-pdf .

# Запуск контейнера
docker run -p 8080:8080 \
  -e BOT_TOKEN="your_token" \
  -e GOOGLE_CLOUD_PROJECT="your_project" \
  bti-dwg-pdf
```

## Деплой в Google Cloud

### Автоматический деплой через Cloud Build

1. Подключите репозиторий к Cloud Build
2. Настройте триггеры для автоматического деплоя
3. Убедитесь, что настроены секреты:
   - `BOT_TOKEN` - токен Telegram бота

### Ручной деплой

```bash
# Сборка и деплой через gcloud
gcloud builds submit --config cloudbuild.yaml

# Или через Cloud Build CLI
gcloud run deploy bti-dwg-pdf \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900
```

## API

### Endpoints

- `POST /upload` - загрузка DWG файла для конвертации
- `GET /health` - проверка состояния сервиса
- `GET /status` - подробная информация о сервисе
- `POST /` - webhook для Telegram Bot

### Пример использования API

```bash
# Загрузка DWG файла
curl -X POST \
  -F "file=@drawing.dwg" \
  https://your-service-url.run.app/upload

# Ответ
{
  "success": true,
  "message": "DWG → PDF conversion successful",
  "pdf_url": "https://storage.googleapis.com/bucket/processed/123/plan.pdf",
  "raw_url": "https://storage.googleapis.com/bucket/raw/123/drawing.dwg",
  "file_info": {
    "original_filename": "drawing.dwg",
    "file_size": 1048576,
    "format": "DWG → PDF"
  }
}
```

## Telegram Bot

Бот поддерживает следующие команды:

- `/start` - главное меню
- Загрузка DWG файлов через интерфейс бота
- Получение ссылок на PDF и исходные файлы

## Структура проекта

```
BTI-DWG-PDF/
├── app.py              # Основное приложение (Flask + Telegram Bot)
├── dwg_converter.py    # Модуль конвертации DWG → PDF
├── requirements.txt    # Python зависимости
├── Dockerfile         # Docker образ
├── cloudbuild.yaml    # Конфигурация Cloud Build
└── README.md          # Документация
```

## Мониторинг

- Логи доступны в Google Cloud Logging
- Метрики в Cloud Monitoring
- Health check endpoint: `/health`

## Поддержка

Для вопросов и предложений создавайте Issues в репозитории.

## Лицензия

MIT License
