# 🏗️ Архитектура проекта автоматизации БТИ

## 🎯 **Цель проекта:**
Автоматическое преобразование обычных DWG файлов в чертежи, соответствующие требованиям БТИ (технический паспорт с оформлением по ГОСТ/СПДС).

---

## 📊 **Текущая архитектура (базовая):**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Telegram Bot   │    │  dwg-processor  │    │dwg-processor-   │
│                 │───▶│                 │───▶│metadata         │
│  (загрузка)     │    │  (Forge API)    │    │ (локальная)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🚀 **Будущая архитектура (с БТИ-автоматизацией):**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Telegram Bot   │    │  BTI Processor  │    │  Template       │
│                 │───▶│                 │───▶│  Manager        │
│  /bti /tz       │    │  (AI + Forge)   │    │  (GCS Storage)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  User Interface │    │  Layer Mapping  │    │  BTI Templates  │
│  (команды)      │    │  Engine         │    │  (DWT, Blocks)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🔧 **Компоненты системы:**

### **1. 🎨 Template Manager (Менеджер шаблонов)**
```
bti-templates/
├── templates/
│   ├── bti_moscow_template.dwt      # Шаблон для Москвы
│   ├── bti_mo_template.dwt          # Шаблон для МО
│   ├── bti_region_template.dwt      # Шаблон для регионов
│   └── bti_custom_template.dwt      # Пользовательский шаблон
├── blocks/
│   ├── bti_frame_moscow.dwg         # Рамка для Москвы
│   ├── bti_stamp_moscow.dwg         # Штамп для Москвы
│   ├── bti_frame_mo.dwg             # Рамка для МО
│   └── bti_stamp_mo.dwg             # Штамп для МО
├── examples/
│   ├── apt_1room_bti_ready.dwg      # Пример 1-комн. квартиры
│   ├── apt_2room_bti_ready.dwg      # Пример 2-комн. квартиры
│   ├── house_floorplan_bti.dwg      # Пример частного дома
│   └── commercial_space_bti.dwg     # Пример нежилого помещения
└── configs/
    ├── layer_mapping.yaml           # Маппинг слоев
    ├── style_mapping.yaml           # Маппинг стилей
    └── bti_rules.yaml               # Правила БТИ
```

### **2. 🧠 BTI Processor (Процессор БТИ)**
```python
class BTIProcessor:
    def __init__(self):
        self.template_manager = TemplateManager()
        self.layer_mapper = LayerMapper()
        self.style_applier = StyleApplier()
        self.forge_client = ForgeClient()
    
    def process_dwg_for_bti(self, input_dwg_url, bti_type="moscow"):
        # 1. Загружаем исходный DWG
        # 2. Анализируем структуру
        # 3. Применяем маппинг слоев
        # 4. Загружаем БТИ-шаблон
        # 5. Применяем стили и рамку
        # 6. Вставляем штамп
        # 7. Расставляем размеры
        # 8. Экспортируем результат
        pass
```

### **3. 📋 Layer Mapping Engine (Движок маппинга слоев)**
```yaml
# layer_mapping.yaml
bti_moscow:
  walls:
    - match: ["walls", "стены", "wall*", "WALL*"]
      to: "A-WALL"
      properties:
        color: 7
        lineweight: 0.5
        linetype: "CONTINUOUS"
  
  doors:
    - match: ["door*", "двери", "DOOR*", "дверь*"]
      to: "A-DOOR"
      properties:
        color: 2
        lineweight: 0.3
        linetype: "CONTINUOUS"
  
  windows:
    - match: ["okna", "windows", "win*", "окна", "WINDOW*"]
      to: "A-WIND"
      properties:
        color: 4
        lineweight: 0.25
        linetype: "CONTINUOUS"
  
  text:
    - match: ["text*", "текст*", "TEXT*", "labels*"]
      to: "A-TEXT"
      properties:
        color: 7
        text_style: "BTI-TXT"
        height: 2.5
  
  dimensions:
    - match: ["dim*", "размер*", "DIM*", "размеры*"]
      to: "A-DIMS"
      properties:
        color: 3
        dim_style: "BTI-DIM"
  
  default: "A-MISC"
```

### **4. ⚙️ Style Mapping Engine (Движок стилей)**
```yaml
# style_mapping.yaml
text_styles:
  BTI-TXT:
    font: "gosttypea.shx"
    height: 2.5
    width_factor: 0.8
    oblique_angle: 0
  
  BTI-TITLE:
    font: "gosttypea.shx"
    height: 5.0
    width_factor: 1.0
    oblique_angle: 0

dimension_styles:
  BTI-DIM:
    arrow_size: 2.5
    text_height: 2.5
    extension_line_offset: 1.0
    dimension_line_gap: 1.0
    arrow_type: "ARCHITECTURAL_TICK"

linetypes:
  BTI-WALL: "CONTINUOUS"
  BTI-HIDDEN: "HIDDEN"
  BTI-CENTER: "CENTER"
  BTI-DASHED: "DASHED"
```

### **5. 📏 BTI Rules Engine (Движок правил БТИ)**
```yaml
# bti_rules.yaml
moscow:
  scale: "1:100"
  units: "mm"
  paper_size: "A3"
  orientation: "Landscape"
  
  frame:
    position: "bottom_right"
    size: [297, 210]  # A3 в мм
    margin: [20, 20, 20, 20]
  
  stamp:
    template: "bti_stamp_moscow.dwg"
    fields:
      object_address: "auto_detect"
      floor: "auto_detect"
      executor: "Иванов И.И."
      date: "current_date"
      scale: "1:100"
  
  layers:
    required: ["A-WALL", "A-DOOR", "A-WIND", "A-TEXT", "A-DIMS"]
    colors:
      A-WALL: 7
      A-DOOR: 2
      A-WIND: 4
      A-TEXT: 7
      A-DIMS: 3
  
  text_requirements:
    min_height: 2.0
    max_height: 5.0
    font: "gosttypea.shx"
  
  dimension_requirements:
    precision: 0
    units: "mm"
    arrow_size: 2.5
```

---

## 🔄 **Процесс обработки:**

### **Этап 1: Анализ входного файла**
```python
def analyze_input_dwg(dwg_file):
    analysis = {
        "layers": extract_layers(dwg_file),
        "styles": extract_text_styles(dwg_file),
        "dimensions": extract_dimensions(dwg_file),
        "blocks": extract_blocks(dwg_file),
        "units": detect_units(dwg_file),
        "scale": detect_scale(dwg_file)
    }
    return analysis
```

### **Этап 2: Применение маппинга**
```python
def apply_layer_mapping(dwg_file, mapping_config):
    for layer in dwg_file.layers:
        new_name = map_layer_name(layer.name, mapping_config)
        if new_name != layer.name:
            layer.name = new_name
            apply_layer_properties(layer, mapping_config[new_name])
```

### **Этап 3: Применение БТИ-шаблона**
```python
def apply_bti_template(dwg_file, template_path):
    # Загружаем шаблон
    template = load_template(template_path)
    
    # Применяем стили
    apply_text_styles(dwg_file, template.text_styles)
    apply_dimension_styles(dwg_file, template.dim_styles)
    
    # Вставляем рамку и штамп
    insert_frame(dwg_file, template.frame_block)
    insert_stamp(dwg_file, template.stamp_block)
    
    # Настраиваем лист
    setup_layout(dwg_file, template.layout_config)
```

### **Этап 4: Автоматическое оформление**
```python
def auto_format_bti(dwg_file, bti_rules):
    # Расставляем размеры
    auto_dimension(dwg_file, bti_rules.dimension_rules)
    
    # Добавляем подписи помещений
    auto_label_rooms(dwg_file, bti_rules.text_rules)
    
    # Проверяем соответствие требованиям
    validate_bti_compliance(dwg_file, bti_rules)
    
    # Исправляем нарушения
    fix_compliance_issues(dwg_file, bti_rules)
```

---

## 📱 **Telegram Bot Commands:**

### **Новые команды:**
```
/bti_moscow    - БТИ для Москвы
/bti_mo        - БТИ для МО  
/bti_region    - БТИ для регионов
/bti_custom    - Пользовательский шаблон БТИ
/tz_gost       - Техзадание по ГОСТ
/template_list - Список доступных шаблонов
/rules         - Правила оформления БТИ
```

### **Расширенные команды:**
```
/bti_moscow --scale=1:100 --executor="Иванов И.И." --address="ул. Ленина, д. 10"
/bti_mo --template=custom_mo.dwt --stamp=mo_stamp_v2.dwg
/bti_region --region=spb --rules=spb_bti.yaml
```

---

## 🗄️ **База данных шаблонов:**

### **GCS Storage структура:**
```
bti-templates/
├── templates/
│   ├── moscow/
│   │   ├── bti_moscow_template.dwt
│   │   ├── bti_moscow_frame.dwg
│   │   └── bti_moscow_stamp.dwg
│   ├── mo/
│   │   ├── bti_mo_template.dwt
│   │   ├── bti_mo_frame.dwg
│   │   └── bti_mo_stamp.dwg
│   └── regions/
│       ├── spb/
│       ├── ekb/
│       └── nsk/
├── examples/
│   ├── apartments/
│   ├── houses/
│   └── commercial/
├── configs/
│   ├── layer_mappings/
│   ├── style_mappings/
│   └── bti_rules/
└── metadata/
    ├── template_info.json
    ├── version_history.json
    └── usage_stats.json
```

---

## 🔧 **Техническая реализация:**

### **1. BTI Template Manager Service:**
```python
class BTITemplateManager:
    def __init__(self):
        self.gcs_client = storage.Client()
        self.bucket = self.gcs_client.bucket("bti-templates")
    
    def get_template(self, region, template_type):
        template_path = f"templates/{region}/{template_type}.dwt"
        return self.bucket.blob(template_path)
    
    def get_frame_block(self, region):
        frame_path = f"templates/{region}/frame.dwg"
        return self.bucket.blob(frame_path)
    
    def get_stamp_block(self, region):
        stamp_path = f"templates/{region}/stamp.dwg"
        return self.bucket.blob(stamp_path)
    
    def get_mapping_config(self, region):
        mapping_path = f"configs/layer_mappings/{region}.yaml"
        return self.bucket.blob(mapping_path)
```

### **2. BTI Processor Service:**
```python
class BTIProcessor:
    def __init__(self):
        self.template_manager = BTITemplateManager()
        self.forge_client = ForgeClient()
        self.layer_mapper = LayerMapper()
    
    def process_for_bti(self, input_dwg_url, region="moscow"):
        # 1. Скачиваем исходный DWG
        input_dwg = self.download_dwg(input_dwg_url)
        
        # 2. Анализируем структуру
        analysis = self.analyze_dwg(input_dwg)
        
        # 3. Получаем БТИ-шаблон
        template = self.template_manager.get_template(region, "bti_template")
        mapping = self.template_manager.get_mapping_config(region)
        
        # 4. Создаем WorkItem для Forge
        workitem_data = {
            "activityId": f"BTI{region.upper()}Activity",
            "arguments": {
                "inputFile": {"url": input_dwg_url, "verb": "get"},
                "templateFile": {"url": template.public_url, "verb": "get"},
                "mappingConfig": {"url": mapping.public_url, "verb": "get"},
                "resultFile": {"url": output_url, "verb": "put"}
            }
        }
        
        # 5. Отправляем в Forge
        workitem_id = self.forge_client.create_workitem(workitem_data)
        
        # 6. Ждем результат
        result = self.forge_client.poll_workitem(workitem_id)
        
        return result
```

### **3. Forge Activity для БТИ:**
```json
{
  "id": "BTIMOSCOWActivity",
  "commandLine": [
    "$(engine.path)\\accoreconsole.exe",
    "/i", "\"$(args[inputFile].path)\"",
    "/s", "\"$(settings[bti_script].path)\"",
    "/t", "\"$(args[templateFile].path)\"",
    "/m", "\"$(args[mappingConfig].path)\""
  ],
  "parameters": {
    "inputFile": {
      "verb": "get",
      "localName": "input.dwg"
    },
    "templateFile": {
      "verb": "get", 
      "localName": "template.dwt"
    },
    "mappingConfig": {
      "verb": "get",
      "localName": "mapping.yaml"
    },
    "resultFile": {
      "verb": "put",
      "localName": "result.dwg"
    }
  },
  "settings": {
    "bti_script": {
      "value": "bti_processor.scr"
    }
  },
  "engine": "Autodesk.AutoCAD+25_1"
}
```

---

## 📋 **План развития:**

### **Фаза 1: Базовая БТИ-автоматизация (1-2 месяца)**
- ✅ Создание шаблонов для Москвы и МО
- ✅ Базовая система маппинга слоев
- ✅ Интеграция с Forge API
- ✅ Команды `/bti_moscow` и `/bti_mo`

### **Фаза 2: Расширенная функциональность (2-3 месяца)**
- 🔄 Поддержка региональных стандартов
- 🔄 Автоматическое определение типа помещения
- 🔄 Умная расстановка размеров
- 🔄 Валидация соответствия БТИ

### **Фаза 3: AI-улучшения (3-4 месяца)**
- 🔄 Машинное обучение для анализа чертежей
- 🔄 Автоматическое исправление ошибок
- 🔄 Предсказание требований БТИ
- 🔄 Оптимизация качества результата

### **Фаза 4: Интеграции (4-6 месяцев)**
- 🔄 API для внешних систем
- 🔄 Интеграция с CAD-системами
- 🔄 Автоматическая загрузка в БТИ-системы
- 🔄 Мобильное приложение

---

## 🎯 **Ожидаемые результаты:**

### **Для пользователей:**
- 🚀 **Скорость:** Обработка за 2-5 минут вместо часов
- 💰 **Экономия:** Снижение стоимости подготовки на 70%
- ✅ **Качество:** 95%+ соответствие требованиям БТИ
- 🎯 **Удобство:** Один клик для получения готового БТИ

### **Для бизнеса:**
- 📈 **Масштабируемость:** Обработка сотен файлов в день
- 🔄 **Автоматизация:** Минимум ручного труда
- 📊 **Аналитика:** Статистика использования и качества
- 💡 **Инновации:** Первая в России система БТИ-автоматизации

**🎉 Эта архитектура превратит обычные DWG в профессиональные БТИ-чертежи автоматически!**
