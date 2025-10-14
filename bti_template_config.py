"""
Конфигурация типового шаблона BTI
"""

# URL типового шаблона BTI Basmanny в GCS (публичный)
BTI_TEMPLATE_URL = "https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg"

# Activity ID для вставки шаблона
BTI_TEMPLATE_ACTIVITY = "BotBti.BTI_INSERT_Basman+v1"

# Activity ID для простой обработки (без шаблона)
BTI_SIMPLE_ACTIVITY = "BotBti.SimpleDWG2DWG+v1"

# Режим работы
# "template" - с вставкой шаблона BTI
# "simple" - простая обработка DWG без шаблона
BTI_MODE = "simple"  # По умолчанию простой режим

# Описание Activities
ACTIVITY_INFO = {
    BTI_TEMPLATE_ACTIVITY: {
        "description": "DWG с вставкой типового шаблона БТИ Басманный",
        "params": ["inputFile", "templateFile", "resultFile"],
        "template_required": True,
        "command": "_INSERT template at 0,0,0"
    },
    BTI_SIMPLE_ACTIVITY: {
        "description": "Простая обработка DWG (SAVEAS в AutoCAD 2018)",
        "params": ["inputFile", "resultFile"],
        "template_required": False,
        "command": "_SAVEAS 2018 format"
    }
}

def get_activity_config(use_template=False):
    """
    Получить конфигурацию Activity в зависимости от режима
    
    Args:
        use_template: Использовать ли типовой шаблон BTI
        
    Returns:
        dict: Конфигурация Activity
    """
    if use_template:
        return {
            "activityId": BTI_TEMPLATE_ACTIVITY,
            "template_url": BTI_TEMPLATE_URL,
            "mode": "template"
        }
    else:
        return {
            "activityId": BTI_SIMPLE_ACTIVITY,
            "template_url": None,
            "mode": "simple"
        }

def get_workitem_arguments(activity_id, input_url, output_url, template_url=None):
    """
    Сформировать arguments для WorkItem
    
    Args:
        activity_id: ID Activity
        input_url: URL входного DWG файла
        output_url: URL для сохранения результата
        template_url: URL шаблона (если используется)
        
    Returns:
        dict: Arguments для WorkItem
    """
    if activity_id == BTI_TEMPLATE_ACTIVITY:
        # Режим с шаблоном
        if not template_url:
            template_url = BTI_TEMPLATE_URL
            
        return {
            "inputFile": {"url": input_url},
            "templateFile": {"url": template_url},
            "resultFile": {"url": output_url, "verb": "put"}
        }
    else:
        # Простой режим
        return {
            "inputFile": {"url": input_url},
            "resultFile": {"url": output_url, "verb": "put"}
        }

