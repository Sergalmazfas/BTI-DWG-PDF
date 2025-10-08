# 🚀 План реализации архитектуры БТИ v2

## 🎯 **SLO и цели:**
- **Скорость:** p95 ≤ 3 сек на типовой план
- **Достоверность:** ≥ 95% совпадения оформления
- **Надёжность:** ≥ 99% успешных прогонов

---

## 📋 **Чек-лист подготовки (Фаза 0):**

### **1. Сбор эталонных БТИ-DWG:**
```bash
# Структура для подготовки шаблонов
mkdir -p bti-templates-prep/{moscow,mo,default}
mkdir -p bti-templates-prep/{moscow,mo,default}/{examples,blocks,templates,configs}

# Нужно собрать:
# - 3-5 эталонных БТИ-DWG (прошедших приёмку)
# - Выделить рамку и штамп в блоки
# - Создать DWT шаблоны
# - Описать конфигурации
```

### **2. Создание GCS структуры:**
```bash
# Создать бакеты
gsutil mb gs://bti-templates
gsutil mb gs://bti-inbox  
gsutil mb gs://bti-out

# Настроить права доступа
gsutil iam ch serviceAccount:bti-processor@talkhint.iam.gserviceaccount.com:objectAdmin gs://bti-templates
gsutil iam ch serviceAccount:bti-processor@talkhint.iam.gserviceaccount.com:objectAdmin gs://bti-inbox
gsutil iam ch serviceAccount:bti-processor@talkhint.iam.gserviceaccount.com:objectAdmin gs://bti-out
```

---

## 🏗️ **Фаза 1: MVP (1-2 спринта)**

### **Спринт 1: Базовая инфраструктура**

#### **1.1 Template Manager Service:**
```python
# bti_template_manager.py
class BTITemplateManager:
    def __init__(self):
        self.storage_client = storage.Client()
        self.templates_bucket = self.storage_client.bucket("bti-templates")
        self.manifest = self._load_manifest()
    
    def _load_manifest(self):
        manifest_blob = self.templates_bucket.blob("templates.json")
        if manifest_blob.exists():
            return json.loads(manifest_blob.download_as_text())
        return {
            "moscow": "gs://bti-templates/moscow",
            "mo": "gs://bti-templates/mo", 
            "default": "gs://bti-templates/default"
        }
    
    def get_template_path(self, region):
        return self.manifest.get(region, self.manifest["default"])
    
    def get_template_files(self, region):
        base_path = self.get_template_path(region)
        return {
            "template": f"{base_path}/bti_template.dwt",
            "frame": f"{base_path}/frame.dwg",
            "stamp": f"{base_path}/stamp.dwg",
            "layer_map": f"{base_path}/layer_map.yaml",
            "style": f"{base_path}/style.json"
        }
```

#### **1.2 Обновленный Telegram Bot:**
```python
# app.py - новые команды
async def bti_moscow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /bti_moscow - БТИ для Москвы"""
    user_id = update.effective_user.id
    user_data[user_id] = {
        'step': 'waiting_dwg_file', 
        'mode': 'bti_moscow',
        'template': 'moscow'
    }
    
    message = (
        "🏢 <b>Режим: БТИ для Москвы</b>\n\n"
        "📋 <b>Что будет сделано:</b>\n"
        "• Применение московского шаблона БТИ\n"
        "• Нормализация слоев и стилей\n"
        "• Вставка рамки и штампа БТИ\n"
        "• Автоматическая расстановка размеров\n"
        "• Время обработки: 2-3 минуты\n\n"
        "📐 <b>Отправьте DWG файл для обработки</b>"
    )
    
    await update.message.reply_text(message, parse_mode='HTML')

async def bti_mo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /bti_mo - БТИ для МО"""
    user_id = update.effective_user.id
    user_data[user_id] = {
        'step': 'waiting_dwg_file', 
        'mode': 'bti_mo',
        'template': 'mo'
    }
    
    message = (
        "🏘️ <b>Режим: БТИ для Московской области</b>\n\n"
        "📋 <b>Что будет сделано:</b>\n"
        "• Применение шаблона БТИ для МО\n"
        "• Нормализация слоев и стилей\n"
        "• Вставка рамки и штампа БТИ\n"
        "• Автоматическая расстановка размеров\n"
        "• Время обработки: 2-3 минуты\n\n"
        "📐 <b>Отправьте DWG файл для обработки</b>"
    )
    
    await update.message.reply_text(message, parse_mode='HTML')

async def template_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /template_list - список шаблонов"""
    message = (
        "📋 <b>Доступные шаблоны БТИ:</b>\n\n"
        "🏢 <code>/bti_moscow</code> - БТИ для Москвы\n"
        "🏘️ <code>/bti_mo</code> - БТИ для МО\n"
        "🌍 <code>/bti_region</code> - БТИ для регионов\n\n"
        "💡 <b>Как использовать:</b>\n"
        "1. Выберите нужный шаблон\n"
        "2. Загрузите DWG файл\n"
        "3. Получите готовый БТИ-чертеж"
    )
    
    await update.message.reply_text(message, parse_mode='HTML')
```

#### **1.3 Обработка файлов с Pub/Sub:**
```python
async def handle_document_bti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка DWG файлов для БТИ"""
    document = update.message.document
    user_id = update.effective_user.id
    user_data_item = user_data.get(user_id, {})
    
    # Проверяем что выбран режим БТИ
    if not user_data_item.get('template'):
        await update.message.reply_text(
            "❌ <b>Сначала выберите шаблон БТИ</b>\n\n"
            "Используйте команды:\n"
            "🏢 <code>/bti_moscow</code>\n"
            "🏘️ <code>/bti_mo</code>\n"
            "🌍 <code>/bti_region</code>",
            parse_mode='HTML'
        )
        return
    
    # Валидация DWG файла
    if not document.file_name.endswith('.dwg'):
        await update.message.reply_text(
            "❌ <b>Поддерживается только DWG</b>\n\n"
            f"Ваш файл: <code>{document.file_name}</code>\n"
            "Формат: <code>{os.path.splitext(document.file_name)[1]}</code>\n\n"
            "💡 Экспортируйте чертёж как DWG и попробуйте снова",
            parse_mode='HTML'
        )
        return
    
    # Создаем уникальный ID задачи
    job_id = str(uuid.uuid4())
    chat_id = str(user_id)
    
    # Загружаем файл в GCS
    file_obj = await context.bot.get_file(document.file_id)
    file_content = await file_obj.download_as_bytearray()
    
    # Сохраняем в bti-inbox
    storage_client = storage.Client()
    bucket = storage_client.bucket("bti-inbox")
    blob_path = f"{chat_id}/{job_id}.dwg"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(file_content, content_type='application/octet-stream')
    
    # Публикуем событие в Pub/Sub
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path("talkhint", "bti-jobs-create")
    
    message_data = {
        "chat_id": chat_id,
        "job_id": job_id,
        "dwg": f"gs://bti-inbox/{blob_path}",
        "template": user_data_item['template'],
        "meta": {
            "address": "Автоопределение",
            "scale": "1:100",
            "executor": "BTI Bot",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    }
    
    publisher.publish(topic_path, json.dumps(message_data).encode('utf-8'))
    
    # Уведомляем пользователя
    await update.message.reply_text(
        f"✅ <b>Файл принят для обработки</b>\n\n"
        f"🆔 ID задачи: <code>{job_id}</code>\n"
        f"🏢 Шаблон: {user_data_item['template']}\n"
        f"⏱️ Ожидаемое время: 2-3 минуты\n\n"
        "📊 Статус обработки будет отправлен автоматически",
        parse_mode='HTML'
    )
```

### **Спринт 2: BTI Processor**

#### **2.1 Основной процессор:**
```python
# bti_processor.py
class BTIProcessor:
    def __init__(self):
        self.storage_client = storage.Client()
        self.template_manager = BTITemplateManager()
        self.layer_mapper = LayerMapper()
        self.style_applier = StyleApplier()
        
    def process_bti_job(self, job_data):
        """Основной пайплайн обработки БТИ"""
        start_time = time.time()
        
        try:
            # 1. Loader: скачать DWG + шаблон + конфиги
            input_dwg = self._download_dwg(job_data['dwg'])
            template_files = self.template_manager.get_template_files(job_data['template'])
            
            # 2. Units: проверить/пересчитать единицы
            self._normalize_units(input_dwg)
            
            # 3. Layer Mapping Engine
            self.layer_mapper.apply_mapping(input_dwg, template_files['layer_map'])
            
            # 4. Style Mapping Engine
            self.style_applier.apply_styles(input_dwg, template_files['style'])
            
            # 5. Layout: применить DWT, создать листы
            self._apply_layout(input_dwg, template_files, job_data['meta'])
            
            # 6. Dims: авто-минимум размеров
            self._add_dimensions(input_dwg)
            
            # 7. Cleanup: удалить мусор
            self._cleanup_dwg(input_dwg)
            
            # 8. Export: сохранить результат
            output_path = f"gs://bti-out/{job_data['chat_id']}/{job_data['job_id']}/bti_ready.dwg"
            self._save_result(input_dwg, output_path)
            
            # 9. Report: создать отчёт
            report = self._generate_report(input_dwg, time.time() - start_time)
            
            return {
                "status": "success",
                "output_dwg": output_path,
                "report": report,
                "processing_time": time.time() - start_time
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "processing_time": time.time() - start_time
            }
```

#### **2.2 Layer Mapping Engine:**
```python
# layer_mapper.py
class LayerMapper:
    def __init__(self):
        self.storage_client = storage.Client()
    
    def apply_mapping(self, dwg_doc, layer_map_url):
        """Применяет маппинг слоев"""
        # Загружаем конфигурацию маппинга
        layer_map = self._load_layer_map(layer_map_url)
        
        # Проходим по всем слоям в документе
        for layer in dwg_doc.layers:
            new_name = self._map_layer_name(layer.name, layer_map)
            if new_name != layer.name:
                layer.name = new_name
                self._apply_layer_properties(layer, layer_map[new_name])
    
    def _map_layer_name(self, layer_name, layer_map):
        """Определяет новое имя слоя по маппингу"""
        layer_name_lower = layer_name.lower()
        
        for mapping in layer_map.get('layers_map', []):
            for pattern in mapping['match']:
                if fnmatch.fnmatch(layer_name_lower, pattern.lower()):
                    return mapping['to']
        
        return layer_map.get('default', 'A-MISC')
    
    def _apply_layer_properties(self, layer, properties):
        """Применяет свойства слоя"""
        if 'color' in properties:
            layer.color = properties['color']
        if 'lineweight' in properties:
            layer.lineweight = properties['lineweight']
        if 'linetype' in properties:
            layer.linetype = properties['linetype']
```

#### **2.3 Style Mapping Engine:**
```python
# style_applier.py
class StyleApplier:
    def __init__(self):
        self.storage_client = storage.Client()
    
    def apply_styles(self, dwg_doc, style_url):
        """Применяет стили оформления"""
        # Загружаем конфигурацию стилей
        styles = self._load_style_config(style_url)
        
        # Применяем текстовые стили
        self._apply_text_styles(dwg_doc, styles.get('text_style', {}))
        
        # Применяем размерные стили
        self._apply_dimension_styles(dwg_doc, styles.get('dim_style', {}))
        
        # Применяем типы линий
        self._apply_line_types(dwg_doc, styles.get('line_types', {}))
    
    def _apply_text_styles(self, dwg_doc, text_style):
        """Создает и применяет текстовые стили"""
        if 'name' in text_style:
            style = dwg_doc.styles.new(text_style['name'])
            if 'font' in text_style:
                style.font = text_style['font']
            if 'height_mm' in text_style:
                style.height = text_style['height_mm']
```

#### **2.4 Layout Manager:**
```python
# layout_manager.py
class LayoutManager:
    def __init__(self):
        self.storage_client = storage.Client()
    
    def apply_layout(self, dwg_doc, template_files, meta):
        """Применяет макет и вставляет рамку/штамп"""
        # Загружаем DWT шаблон
        template_dwg = self._load_template(template_files['template'])
        
        # Копируем настройки из шаблона
        self._copy_layout_settings(dwg_doc, template_dwg)
        
        # Вставляем рамку
        self._insert_frame(dwg_doc, template_files['frame'])
        
        # Вставляем штамп с автозаполнением
        self._insert_stamp(dwg_doc, template_files['stamp'], meta)
        
        # Настраиваем viewport
        self._setup_viewport(dwg_doc)
    
    def _insert_stamp(self, dwg_doc, stamp_url, meta):
        """Вставляет штамп с автозаполнением полей"""
        # Загружаем блок штампа
        stamp_block = self._load_block(stamp_url)
        
        # Вставляем блок
        insert = dwg_doc.modelspace().add_blockref(
            stamp_block.name, 
            (0, 0)
        )
        
        # Заполняем поля из метаданных
        self._fill_stamp_fields(insert, meta)
```

#### **2.5 Dimension Engine:**
```python
# dimension_engine.py
class DimensionEngine:
    def __init__(self):
        pass
    
    def add_dimensions(self, dwg_doc):
        """Автоматически добавляет минимальный набор размеров"""
        # Анализируем геометрию
        walls = self._find_walls(dwg_doc)
        rooms = self._find_rooms(dwg_doc)
        
        # Добавляем размеры стен
        self._dimension_walls(dwg_doc, walls)
        
        # Добавляем размеры комнат
        self._dimension_rooms(dwg_doc, rooms)
    
    def _find_walls(self, dwg_doc):
        """Находит стены в чертеже"""
        walls = []
        for entity in dwg_doc.modelspace():
            if entity.dxftype() == 'LINE' and entity.layer == 'A-WALL':
                walls.append(entity)
        return walls
    
    def _dimension_walls(self, dwg_doc, walls):
        """Добавляет размеры стен"""
        for wall in walls:
            # Создаем линейный размер
            dimension = dwg_doc.modelspace().add_linear_dimension(
                base=(wall.start.x, wall.start.y),
                p1=(wall.start.x, wall.start.y),
                p2=(wall.end.x, wall.end.y),
                dimstyle='BTI-DIM'
            )
```

### **Спринт 3: Validator и интеграция**

#### **3.1 BTI Validator:**
```python
# bti_validator.py
class BTIValidator:
    def __init__(self):
        self.storage_client = storage.Client()
    
    def validate_bti_dwg(self, dwg_url, template):
        """Валидирует БТИ-чертеж"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "score": 0
        }
        
        try:
            # Загружаем DWG
            dwg_doc = self._load_dwg(dwg_url)
            
            # Проверяем слои
            self._validate_layers(dwg_doc, validation_result)
            
            # Проверяем стили
            self._validate_styles(dwg_doc, validation_result)
            
            # Проверяем рамку и штамп
            self._validate_frame_stamp(dwg_doc, validation_result)
            
            # Проверяем размеры
            self._validate_dimensions(dwg_doc, validation_result)
            
            # Проверяем единицы
            self._validate_units(dwg_doc, validation_result)
            
            # Вычисляем общий балл
            validation_result["score"] = self._calculate_score(validation_result)
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Ошибка валидации: {str(e)}")
        
        return validation_result
```

#### **3.2 Pub/Sub интеграция:**
```python
# main.py - Cloud Run endpoint для BTI Processor
@app.route('/bti-process', methods=['POST'])
def bti_process():
    """Обработчик Pub/Sub событий"""
    try:
        # Получаем сообщение из Pub/Sub
        envelope = request.get_json()
        if not envelope:
            return 'Bad Request: no Pub/Sub message received', 400
        
        pubsub_message = envelope.get('message', {})
        job_data = json.loads(base64.b64decode(pubsub_message['data']).decode('utf-8'))
        
        # Обрабатываем задачу
        processor = BTIProcessor()
        result = processor.process_bti_job(job_data)
        
        # Отправляем результат в бот
        if result['status'] == 'success':
            self._notify_bot_success(job_data, result)
        else:
            self._notify_bot_error(job_data, result)
        
        return 'OK', 200
        
    except Exception as e:
        logger.error(f"❌ BTI Processing error: {e}")
        return 'Internal Server Error', 500

def _notify_bot_success(self, job_data, result):
    """Уведомляет бота об успешной обработке"""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path("talkhint", "bti-jobs-done")
    
    message_data = {
        "chat_id": job_data['chat_id'],
        "job_id": job_data['job_id'],
        "status": "ok",
        "out_dwg": result['output_dwg'],
        "report": result['report'],
        "processing_time": result['processing_time']
    }
    
    publisher.publish(topic_path, json.dumps(message_data).encode('utf-8'))

def _notify_bot_error(self, job_data, result):
    """Уведомляет бота об ошибке обработки"""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path("talkhint", "bti-jobs-done")
    
    message_data = {
        "chat_id": job_data['chat_id'],
        "job_id": job_data['job_id'],
        "status": "error",
        "error": result['error'],
        "processing_time": result['processing_time']
    }
    
    publisher.publish(topic_path, json.dumps(message_data).encode('utf-8'))
```

---

## 🧪 **Тест-план (7 кейсов):**

### **Тест 1: Валидный план квартиры**
```python
def test_valid_apartment_plan():
    """Валидный план квартиры (мм) → OK ≤ 3 c; корректные слои/штамп"""
    input_dwg = "test_data/valid_apartment.dwg"
    result = process_bti_job({
        "dwg": input_dwg,
        "template": "moscow"
    })
    
    assert result['status'] == 'success'
    assert result['processing_time'] <= 3.0
    assert validate_layers(result['output_dwg'])
    assert validate_stamp(result['output_dwg'])
```

### **Тест 2: Смешанные языки слоев**
```python
def test_mixed_language_layers():
    """Смешанные рус/англ слои → корректный mapping"""
    input_dwg = "test_data/mixed_layers.dwg"
    result = process_bti_job({
        "dwg": input_dwg,
        "template": "moscow"
    })
    
    assert result['status'] == 'success'
    assert check_layer_mapping(result['output_dwg'])
```

### **Тест 3: Единицы в метрах**
```python
def test_meter_units():
    """Единицы в метрах → авто-scale в мм"""
    input_dwg = "test_data/meter_units.dwg"
    result = process_bti_job({
        "dwg": input_dwg,
        "template": "moscow"
    })
    
    assert result['status'] == 'success'
    assert validate_units(result['output_dwg'], 'mm')
```

### **Тест 4: Нет размеров**
```python
def test_no_dimensions():
    """Нет размеров → авто-минимум размеров ≤ N/лист"""
    input_dwg = "test_data/no_dimensions.dwg"
    result = process_bti_job({
        "dwg": input_dwg,
        "template": "moscow"
    })
    
    assert result['status'] == 'success'
    assert count_dimensions(result['output_dwg']) >= 5
```

### **Тест 5: Старый DWG**
```python
def test_old_dwg_format():
    """Несовместимый старый DWG → автоконверт в поддерживаемую версию"""
    input_dwg = "test_data/old_r2000.dwg"
    result = process_bti_job({
        "dwg": input_dwg,
        "template": "moscow"
    })
    
    assert result['status'] == 'success'
    assert validate_dwg_version(result['output_dwg'])
```

### **Тест 6: Битый файл**
```python
def test_corrupted_file():
    """Битый файл → аккуратная ошибка + report.json"""
    input_dwg = "test_data/corrupted.dwg"
    result = process_bti_job({
        "dwg": input_dwg,
        "template": "moscow"
    })
    
    assert result['status'] == 'error'
    assert 'report' in result
    assert 'corrupted' in result['error'].lower()
```

### **Тест 7: Большой файл**
```python
def test_large_file():
    """Большой файл (stress) → не падает, но может вернуть timeout по SLO"""
    input_dwg = "test_data/large_complex.dwg"
    result = process_bti_job({
        "dwg": input_dwg,
        "template": "moscow"
    })
    
    # Может быть timeout, но не crash
    assert result['status'] in ['success', 'timeout']
    if result['status'] == 'timeout':
        assert result['processing_time'] > 3.0
```

---

## 📊 **Мониторинг и метрики:**

### **Cloud Monitoring метрики:**
```python
# metrics.py
from google.cloud import monitoring_v3

class BTIMetrics:
    def __init__(self):
        self.client = monitoring_v3.MetricServiceClient()
        self.project_id = "talkhint"
    
    def record_job_started(self, template):
        """Записывает начало обработки"""
        self._write_metric('bti_jobs_total', 1, {'template': template})
    
    def record_job_completed(self, template, processing_time, success=True):
        """Записывает завершение обработки"""
        status = 'success' if success else 'failed'
        self._write_metric('bti_jobs_failed' if not success else 'bti_jobs_success', 1, {
            'template': template,
            'status': status
        })
        self._write_metric('bti_processing_duration_ms', processing_time * 1000, {
            'template': template,
            'status': status
        })
    
    def record_auto_dims_count(self, count):
        """Записывает количество автоматических размеров"""
        self._write_metric('auto_dims_count', count)
    
    def record_fallback_layers(self, count):
        """Записывает количество fallback слоев"""
        self._write_metric('fallback_layers_count', count)
```

### **Алерты:**
```yaml
# alerts.yaml
alert_policies:
  - name: "BTI High Error Rate"
    condition:
      filter: 'metric.type="custom.googleapis.com/bti_jobs_failed"'
      comparison: COMPARISON_GREATER_THAN
      threshold_value: 5
      duration: 900s  # 15 минут
    notification_channels: ["email:admin@example.com"]
  
  - name: "BTI Slow Processing"
    condition:
      filter: 'metric.type="custom.googleapis.com/bti_processing_duration_ms"'
      comparison: COMPARISON_GREATER_THAN
      threshold_value: 3000  # 3 секунды
      duration: 900s
    notification_channels: ["email:admin@example.com"]
```

---

## 🚀 **Дорожная карта:**

### **MVP (v1) - 2-3 недели:**
- ✅ Бот с командами `/bti_*`
- ✅ Template Manager
- ✅ BTI Processor с локальной нормализацией
- ✅ Layer/Style Mapping Engines
- ✅ Validator (базовый)
- ✅ Тесты на 7 кейсов

### **V2 - 4-6 недель:**
- 🔄 Autodesk Design Automation интеграция
- 🔄 PDF Renderer
- 🔄 Расширенная авто-семантика
- 🔄 Геометрические эвристики
- 🔄 Региональные шаблоны

### **V3 - 8-12 недель:**
- 🔄 AI-анализ чертежей
- 🔄 Автоисправление ошибок
- 🔄 Предсказание требований
- 🔄 API для внешних систем

**🎯 Эта архитектура обеспечит p95 ≤ 3 сек и ≥ 95% качество БТИ-чертежей!** 🚀
