# 🔧 Необходимые сервисы Google Cloud для проекта BTI-DWG-PDF

## ✅ Активные сервисы в проекте

### 🎯 **Основные сервисы (критически важные):**

#### **1. Cloud Run (`run.googleapis.com`)**
- **Назначение:** Развертывание Telegram бота и веб-приложения
- **Использование:** 
  - Telegram bot API endpoints
  - Webhook обработка
  - Обработка файлов DWG
- **Статус:** ✅ Активен
- **Важность:** 🔴 Критически важный

#### **2. Cloud Storage (`storage.googleapis.com`)**
- **Назначение:** Хранение DWG и PDF файлов
- **Использование:**
  - Bucket `btibot-processed` - исходные DWG файлы
  - Bucket `btibot-queue` - очередь обработки
  - Signed URLs для Forge интеграции
- **Статус:** ✅ Активен
- **Важность:** 🔴 Критически важный

#### **3. Secret Manager (`secretmanager.googleapis.com`)**
- **Назначение:** Хранение секретных данных
- **Использование:**
  - `BOT_TOKEN` - токен Telegram бота
  - `FORGE_CLIENT_ID` - ID клиента Forge
  - `FORGE_CLIENT_SECRET` - секрет Forge
  - `telegram-bot-key` - приватный ключ Service Account
- **Статус:** ✅ Активен
- **Важность:** 🔴 Критически важный

#### **4. Container Registry (`containerregistry.googleapis.com`)**
- **Назначение:** Хранение Docker образов
- **Использование:**
  - Образ `gcr.io/talkhint/telegram-bot-commands:latest`
  - CI/CD pipeline
- **Статус:** ✅ Активен
- **Важность:** 🔴 Критически важный

#### **5. Cloud Build (`cloudbuild.googleapis.com`)**
- **Назначение:** Автоматическая сборка и деплой
- **Использование:**
  - Сборка Docker образов
  - Автоматический деплой при изменениях
- **Статус:** ✅ Активен
- **Важность:** 🟡 Важный для CI/CD

---

### 🎯 **Вспомогательные сервисы (важные):**

#### **6. IAM (`iam.googleapis.com`)**
- **Назначение:** Управление доступом и Service Accounts
- **Использование:**
  - Service Account `telegram-bot-sa@talkhint.iam.gserviceaccount.com`
  - Права доступа к Storage и Secret Manager
- **Статус:** ✅ Активен
- **Важность:** 🟡 Важный для безопасности

#### **7. Cloud Logging (`logging.googleapis.com`)**
- **Назначение:** Логирование и мониторинг
- **Использование:**
  - Логи Cloud Run сервиса
  - Мониторинг ошибок
  - Отладка приложения
- **Статус:** ✅ Активен
- **Важность:** 🟡 Важный для мониторинга

#### **8. IAM Service Account Credentials (`iamcredentials.googleapis.com`)**
- **Назначение:** Управление учетными данными Service Account
- **Использование:**
  - Генерация временных токенов доступа
  - Signed URLs для Storage
- **Статус:** ✅ Активен
- **Важность:** 🟡 Важный для подписи URL

---

### 🎯 **Дополнительные сервисы (полезные):**

#### **9. Cloud Monitoring (`monitoring.googleapis.com`)**
- **Назначение:** Мониторинг производительности
- **Использование:**
  - Метрики Cloud Run
  - Алерты при ошибках
- **Статус:** ✅ Активен
- **Важность:** 🟢 Полезный для мониторинга

#### **10. Cloud Trace (`cloudtrace.googleapis.com`)**
- **Назначение:** Трассировка запросов
- **Использование:**
  - Отслеживание производительности
  - Диагностика проблем
- **Статус:** ✅ Активен
- **Важность:** 🟢 Полезный для диагностики

---

## 🚫 **Неиспользуемые сервисы (можно отключить):**

### **Сервисы, которые НЕ используются в проекте:**

#### **1. BigQuery (`bigquery.googleapis.com`)**
- **Статус:** ❌ Не используется
- **Можно отключить:** ✅ Да

#### **2. Vertex AI (`aiplatform.googleapis.com`)**
- **Статус:** ❌ Не используется
- **Можно отключить:** ✅ Да

#### **3. App Engine (`appengine.googleapis.com`)**
- **Статус:** ❌ Не используется (используется Cloud Run)
- **Можно отключить:** ✅ Да

#### **4. Compute Engine (`compute.googleapis.com`)**
- **Статус:** ❌ Не используется (используется Cloud Run)
- **Можно отключить:** ✅ Да

#### **5. Cloud SQL (`sql-component.googleapis.com`)**
- **Статус:** ❌ Не используется
- **Можно отключить:** ✅ Да

#### **6. Cloud Datastore (`datastore.googleapis.com`)**
- **Статус:** ❌ Не используется
- **Можно отключить:** ✅ Да

#### **7. Pub/Sub (`pubsub.googleapis.com`)**
- **Статус:** ❌ Не используется (есть в проекте, но не в коде)
- **Можно отключить:** ✅ Да

#### **8. Cloud Translation (`translate.googleapis.com`)**
- **Статус:** ❌ Не используется
- **Можно отключить:** ✅ Да

#### **9. Speech-to-Text (`speech.googleapis.com`)**
- **Статус:** ❌ Не используется
- **Можно отключить:** ✅ Да

#### **10. Vision AI (`visionai.googleapis.com`)**
- **Статус:** ❌ Не используется
- **Можно отключить:** ✅ Да

---

## 📊 **Сводка по сервисам:**

### ✅ **Необходимые сервисы (5):**
1. **Cloud Run** - основное приложение
2. **Cloud Storage** - хранение файлов
3. **Secret Manager** - секреты
4. **Container Registry** - Docker образы
5. **Cloud Build** - CI/CD

### 🟡 **Важные сервисы (3):**
6. **IAM** - управление доступом
7. **Cloud Logging** - логирование
8. **IAM Credentials** - подпись URL

### 🟢 **Полезные сервисы (2):**
9. **Cloud Monitoring** - мониторинг
10. **Cloud Trace** - трассировка

### ❌ **Неиспользуемые сервисы (10+):**
- BigQuery, Vertex AI, App Engine, Compute Engine, Cloud SQL, Datastore, Pub/Sub, Translation, Speech, Vision AI и другие

---

## 💰 **Рекомендации по оптимизации:**

### **Для экономии средств можно отключить:**

```bash
# Отключение неиспользуемых сервисов
gcloud services disable \
  bigquery.googleapis.com \
  aiplatform.googleapis.com \
  appengine.googleapis.com \
  compute.googleapis.com \
  sql-component.googleapis.com \
  datastore.googleapis.com \
  translate.googleapis.com \
  speech.googleapis.com \
  visionai.googleapis.com
```

### **Минимальный набор для работы:**
- Cloud Run
- Cloud Storage
- Secret Manager
- Container Registry
- IAM
- Cloud Logging

**Это позволит сэкономить на неиспользуемых API вызовах и лицензиях.**

---

## 🎯 **Заключение:**

**Для проекта BTI-DWG-PDF критически важны только 5 сервисов:**
1. Cloud Run
2. Cloud Storage  
3. Secret Manager
4. Container Registry
5. Cloud Build

**Остальные 10+ сервисов можно отключить для экономии средств, не влияя на функциональность проекта.**
