# 🚀 Руководство по развертыванию BTI DWG → PDF Converter

## Быстрый старт

### 1. Подготовка окружения

```bash
# Клонируйте репозиторий
git clone https://github.com/Sergalmazfas/BTI-DWG-PDF.git
cd BTI-DWG-PDF

# Убедитесь, что у вас настроен gcloud CLI
gcloud auth login
gcloud config set project talkhint  # Замените на ваш проект
```

### 2. Настройка сервисного аккаунта

```bash
# Запустите скрипт настройки Cloud Build
./setup-cloud-build.sh
```

### 3. Настройка секретов

```bash
# Установите токен Telegram бота
echo "YOUR_BOT_TOKEN" | gcloud secrets versions add BOT_TOKEN --data-file=-
```

### 4. Деплой

#### Автоматический деплой (рекомендуется)
```bash
# Просто запушьте изменения в main ветку
git add .
git commit -m "Deploy to Cloud Run"
git push origin main
```

#### Ручной деплой
```bash
# Используйте готовый скрипт
./deploy.sh

# Или через gcloud напрямую
gcloud builds submit --config cloudbuild.yaml
```

### 5. Настройка Telegram Webhook

```bash
# Получите URL вашего сервиса
SERVICE_URL=$(gcloud run services describe bti-dwg-pdf --region=europe-west1 --format="value(status.url)")

# Установите webhook (замените YOUR_BOT_TOKEN)
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=${SERVICE_URL}/"
```

## Тестирование

### 1. Локальное тестирование

```bash
# Установите зависимости
pip install -r requirements.txt

# Запустите приложение
export BOT_TOKEN="your_bot_token"
export GOOGLE_CLOUD_PROJECT="talkhint"
export GCS_BUCKET="btibot-processed"
python app.py

# В другом терминале запустите тесты
python test_converter.py
```

### 2. Тестирование API

```bash
# Проверка здоровья сервиса
curl https://your-service-url.run.app/health

# Проверка статуса
curl https://your-service-url.run.app/status

# Тест загрузки файла
curl -X POST -F "file=@test.dwg" https://your-service-url.run.app/upload
```

### 3. Тестирование Telegram бота

1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Загрузите DWG файл
4. Проверьте, что получили ссылки на PDF и исходный файл

## Мониторинг

### 1. Логи Cloud Run

```bash
# Просмотр логов
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=bti-dwg-pdf' --limit=50

# Следить за логами в реальном времени
gcloud logging tail 'resource.type=cloud_run_revision AND resource.labels.service_name=bti-dwg-pdf'
```

### 2. Метрики

- **Cloud Console**: https://console.cloud.google.com/run
- **Мониторинг**: https://console.cloud.google.com/monitoring

### 3. Проверка здоровья

```bash
# Health check
curl -f https://your-service-url.run.app/health

# Подробный статус
curl https://your-service-url.run.app/status | jq
```

## Устранение неполадок

### 1. Проблемы с деплоем

```bash
# Проверьте статус сборки
gcloud builds list --limit=5

# Просмотрите логи сборки
gcloud builds log [BUILD_ID]
```

### 2. Проблемы с конвертацией

- Убедитесь, что файл имеет расширение `.dwg`
- Проверьте размер файла (максимум 100MB)
- Проверьте логи на предмет ошибок ezdxf

### 3. Проблемы с Telegram ботом

```bash
# Проверьте webhook
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo"

# Сбросьте webhook при необходимости
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/deleteWebhook"
```

## Конфигурация

### Переменные окружения

- `BOT_TOKEN` - токен Telegram бота (секрет)
- `GOOGLE_CLOUD_PROJECT` - ID проекта Google Cloud
- `GCS_BUCKET` - имя bucket для хранения файлов
- `PORT` - порт приложения (по умолчанию 8080)

### Ресурсы Cloud Run

- **Memory**: 2Gi
- **CPU**: 2
- **Timeout**: 900 секунд (15 минут)
- **Max instances**: 10
- **Min instances**: 0
- **Concurrency**: 1

## Обслуживание

### 1. Обновление

```bash
# Обновление кода
git pull origin main
git push origin main  # Автоматический деплой

# Обновление зависимостей
# Отредактируйте requirements.txt и запушьте изменения
```

### 2. Масштабирование

```bash
# Увеличить количество экземпляров
gcloud run services update bti-dwg-pdf \
  --region=europe-west1 \
  --max-instances=20
```

### 3. Резервное копирование

- Файлы автоматически сохраняются в Google Cloud Storage
- Bucket `btibot-processed` содержит все обработанные файлы
- Ссылки действуют 30 дней

## Безопасность

### 1. Сервисный аккаунт

Сервис использует минимальные необходимые права:
- `roles/run.admin` - управление Cloud Run
- `roles/storage.admin` - доступ к GCS
- `roles/secretmanager.secretAccessor` - доступ к секретам

### 2. Сетевой доступ

- Сервис доступен публично (для Telegram webhook)
- Можно ограничить доступ через Cloud Armor при необходимости

### 3. Секреты

- Токен бота хранится в Secret Manager
- Автоматическая ротация не настроена (требует ручного обновления)

## Стоимость

Примерная стоимость (на 2024 год):
- **Cloud Run**: ~$0.40 за миллион запросов + $0.024 за vCPU-час
- **Cloud Storage**: ~$0.020 за GB в месяц
- **Cloud Build**: ~$0.003 за минуту сборки

При умеренном использовании (1000 конвертаций в месяц):
- **Общая стоимость**: ~$5-10 в месяц
