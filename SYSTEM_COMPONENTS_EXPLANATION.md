# 🔧 Объяснение компонентов системы

## 🎯 **Общая схема работы:**

```
Пользователь → Telegram Bot → GCS Upload → Queue → Forge API → PDF Generation → Уведомление
```

---

## 📱 **1. Telegram Bot (app.py)**

### **Что делает:**
- **Принимает команды** от пользователей в Telegram
- **Обрабатывает файлы** DWG, загруженные пользователями
- **Отправляет уведомления** о статусе обработки

### **Основные функции:**

#### **`/start` - Приветствие**
```python
async def start(update, context):
    # Показывает приветственное сообщение
    # Объясняет доступные команды: /bti и /tz
```

#### **`/bti` - Режим БТИ**
```python
async def bti_command(update, context):
    # Устанавливает режим "bti" для пользователя
    # Показывает что будет сделано:
    # - Вставка шаблона БТИ (BTI_Template.dwt)
    # - Конвертация в PDF (A4, Landscape)
    # - Штамп БТИ на чертеже
```

#### **`/tz` - Режим Техзадание**
```python
async def tz_command(update, context):
    # Устанавливает режим "tz" для пользователя
    # Показывает что будет сделано:
    # - ГОСТ таблицы и нумерация
    # - Спецификация элементов
    # - Конвертация в PDF (A3, Portrait)
```

#### **`handle_document()` - Обработка файлов**
```python
async def handle_document(update, context):
    # Проверяет что пользователь выбрал режим (/bti или /tz)
    # Валидирует файл (только .dwg, размер до 100MB)
    # Загружает файл в Google Cloud Storage
    # Добавляет метаданные (x-type: bti или tz)
    # Ставит задачу в очередь обработки
    # Уведомляет пользователя о принятии файла
```

---

## ☁️ **2. Google Cloud Storage (GCS)**

### **Что делает:**
- **Хранит файлы** DWG и PDF
- **Управляет очередью** задач через файловую систему
- **Предоставляет метаданные** для обработки

### **Структура папок:**
```
btibot-queue/
├── queue/           # Очередь задач (JSON файлы)
├── processing/      # Lock файлы для блокировки
├── done/           # Завершенные задачи
└── failed/         # Неудачные задачи

btibot-processed/
└── processed/      # Готовые PDF файлы
```

### **Как работает очередь:**
1. **Добавление задачи** - создается JSON файл в `queue/`
2. **Блокировка** - создается lock файл в `processing/`
3. **Обработка** - система берет задачу из очереди
4. **Завершение** - файл перемещается в `done/` или `failed/`

---

## 📋 **3. GCS Queue Manager (gcs_queue_manager.py)**

### **Что делает:**
- **Управляет очередью** задач в GCS
- **Предотвращает конфликты** через lock-файлы
- **Обрабатывает задачи** по одной

### **Основные методы:**

#### **`add_job()` - Добавление задачи**
```python
def add_job(self, job_data):
    # Создает уникальный ID задачи
    # Сохраняет данные в JSON файл
    # Помещает файл в очередь queue/
```

#### **`get_next_job()` - Получение следующей задачи**
```python
def get_next_job(self):
    # Проверяет lock (нет ли активной обработки)
    # Находит самый старый файл в очереди
    # Создает lock файл
    # Возвращает данные задачи
```

#### **`complete_job()` - Завершение задачи**
```python
def complete_job(self, job_id, result_data):
    # Сохраняет результат в done/
    # Удаляет задачу из queue/
    # Удаляет lock файл
```

#### **`fail_job()` - Ошибка задачи**
```python
def fail_job(self, job_id, error_message):
    # Сохраняет ошибку в failed/
    # Удаляет задачу из queue/
    # Удаляет lock файл
```

---

## 🔧 **4. Forge AppBundle Manager (forge_appbundle_manager.py)**

### **Что делает:**
- **Интегрируется с Autodesk Forge API**
- **Управляет токенами доступа**
- **Создает WorkItems** для конвертации DWG в PDF
- **Отслеживает статус** обработки

### **Основные компоненты:**

#### **Аутентификация**
```python
def get_access_token(self):
    # Получает токен доступа от Forge API
    # Кэширует токен до истечения
    # Обрабатывает rate limiting
```

#### **Создание WorkItem**
```python
def convert_dwg_to_pdf(self, dwg_url, pdf_url, activity_type):
    # Создает WorkItem для конвертации
    # Указывает входной DWG файл
    # Указывает выходной PDF файл
    # Выбирает Activity (BTI2PDFActivity или TZ2PDFActivity)
    # Отправляет запрос в Forge API
```

#### **Отслеживание статуса**
```python
def poll_workitem_status(self, workitem_id):
    # Проверяет статус WorkItem
    # Возвращает результат когда готово
    # Обрабатывает ошибки
```

---

## 🔄 **5. Процесс обработки (process_queue)**

### **Что происходит пошагово:**

#### **Шаг 1: Получение задачи**
```python
# Берет следующую задачу из очереди
job = queue_manager.get_next_job()
if not job:
    return  # Нет задач
```

#### **Шаг 2: Подготовка URL**
```python
# Создает signed URLs для файлов
dwg_url = create_signed_url(dwg_file_path)
pdf_url = create_signed_url(pdf_file_path)
```

#### **Шаг 3: Конвертация через Forge**
```python
# Отправляет задачу в Forge API
result = forge_manager.convert_dwg_to_pdf(
    dwg_url, 
    pdf_url, 
    activity_type
)
```

#### **Шаг 4: Обработка результата**
```python
if result['status'] == 'success':
    # Уведомляет пользователя об успехе
    # Отправляет ссылку на PDF
    queue_manager.complete_job(job_id, result)
else:
    # Уведомляет пользователя об ошибке
    queue_manager.fail_job(job_id, error_message)
```

---

## 📊 **6. Типы обработки**

### **BTI Режим:**
- **Activity:** `BTI2PDFActivity`
- **Шаблон:** BTI_Template.dwt
- **Формат PDF:** A4, Landscape
- **Особенности:** Штамп БТИ на чертеже

### **TZ Режим:**
- **Activity:** `TZ2PDFActivity`
- **Шаблон:** ГОСТ таблицы
- **Формат PDF:** A3, Portrait
- **Особенности:** Спецификация элементов

---

## 🔐 **7. Безопасность и секреты**

### **Secret Manager:**
- **FORGE_CLIENT_ID** - ID приложения Forge
- **FORGE_CLIENT_SECRET** - Секрет приложения Forge
- **BOT_TOKEN** - Токен Telegram бота
- **telegram-bot-key** - Service Account ключ

### **Service Account:**
- **telegram-bot-sa** - Учетная запись для работы с GCS
- **Права:** Storage Admin, Secret Manager Accessor

---

## 📈 **8. Мониторинг и логи**

### **Логи Cloud Run:**
```bash
# Проверка логов главного сервиса
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=telegram-bot-commands"

# Проверка логов dwg-processor
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=dwg-processor"
```

### **Метрики:**
- Количество обработанных файлов
- Время обработки
- Ошибки и их типы
- Статус очереди

---

## 🎯 **Итоговая схема работы:**

```
1. Пользователь → /bti или /tz → Telegram Bot
2. Пользователь → Загружает DWG → Telegram Bot
3. Telegram Bot → Загружает в GCS → Добавляет в очередь
4. Queue Manager → Берет задачу → Создает lock
5. Process Queue → Получает задачу → Создает signed URLs
6. Forge Manager → Отправляет в Forge API → WorkItem
7. Forge API → Обрабатывает DWG → Создает PDF
8. Process Queue → Получает результат → Уведомляет пользователя
9. Queue Manager → Завершает задачу → Удаляет lock
```

**🎉 Каждый компонент выполняет свою роль в цепочке обработки DWG → PDF!**
