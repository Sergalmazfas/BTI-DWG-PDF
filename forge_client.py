"""
Autodesk APS (Design Automation API for AutoCAD) Client
Официальная интеграция с Autodesk APS для BTI Processor
"""

import os
import json
import requests
import time
import logging
from google.cloud import storage

logger = logging.getLogger(__name__)

# Конфигурация типового шаблона BTI
BTI_TEMPLATE_URL = "https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg"
BTI_TEMPLATE_ACTIVITY = "BotBti.BTI_INSERT_Basman+v1"  # С шаблоном (требует .NET плагин)
BTI_SIMPLE_ACTIVITY = "BotBti.DWG2DWGCopy+v1"  # Простой режим (WBLOCK - проверено работает!)

# 🆕 Activity V2 - Полный процесс обработки (LISP-based, 6 скриптов)
BTI_FULL_ROOM_V2 = "BotBti.BTI_FULL_ROOM_V2+$LATEST"  # Выравнивание, двери, окна, размеры, площадь

# ⚠️ ВРЕМЕННО: Цветовое распознавание не работает с Leica, используем простой режим
BTI_DEFAULT_MODE = "simple"  # simple = DWG2DWGCopy (WBLOCK, без обработки)

# 🆕 Activity с автоматической обработкой (LISP автозапуск)
BTI_AUTO_PROCESS = "BotBti.BTI_AUTO_PROCESS+$LATEST"  # Слоевая обработка с автозапуском

# Конфигурация Autodesk APS
FORGE_CLIENT_ID = os.getenv("FORGE_CLIENT_ID")
FORGE_CLIENT_SECRET = os.getenv("FORGE_CLIENT_SECRET")
FORGE_BASE_URL = "https://developer.api.autodesk.com/da/us-east/v3"
FORGE_ENGINE = "Autodesk.AutoCAD+24_2"  # AutoCAD 2025

class ForgeClient:
    """Клиент для работы с Autodesk APS Design Automation API"""
    
    def __init__(self):
        self.client_id = FORGE_CLIENT_ID
        self.client_secret = FORGE_CLIENT_SECRET
        self.base_url = FORGE_BASE_URL
        self.engine = FORGE_ENGINE
        self._access_token = None
        self._token_expires = None
        
        if not self.client_id or not self.client_secret:
            raise ValueError("FORGE_CLIENT_ID and FORGE_CLIENT_SECRET must be set")
    
    def get_access_token(self):
        """Получает access token для Autodesk APS API"""
        # Проверяем кэш токена
        if self._access_token and self._token_expires and time.time() < self._token_expires:
            return self._access_token
        
        url = "https://developer.api.autodesk.com/authentication/v2/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "data:read data:write data:create bucket:create bucket:read code:all"
        }
        
        try:
            resp = requests.post(url, data=payload, timeout=30)
            resp.raise_for_status()
            
            token_data = resp.json()
            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires = time.time() + expires_in - 60  # Обновляем за минуту до истечения
            
            logger.info("✅ Autodesk APS access token получен")
            return self._access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка получения токена Autodesk APS: {e}")
            raise
    
    def create_activity(self):
        """Создает Activity BTIProcessor.GenerateDWG (один раз)"""
        token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "id": f"{self.client_id}.GenerateDWG",
            "commandLine": [
                "$(engine.path)\\accoreconsole.exe /i \"$(args[inputFile].path)\" /s \"$(settings[script].path)\""
            ],
            "engine": self.engine,
            "parameters": {
                "inputFile": {"verb": "get", "description": "DWG input", "localName": "input.dwg"},
                "resultFile": {"verb": "put", "description": "DWG output", "localName": "output.dwg"}
            },
            "settings": {
                "script": {
                    "value": "(command \"_.open\" \"$(args[inputFile].path)\")(command \"_.qsave\")(command \"_.close\")"
                }
            },
            "description": "BTIProcessor basic DWG passthrough activity"
        }
        
        try:
            r = requests.post(f"{self.base_url}/activities", headers=headers, json=data, timeout=30)
            
            if r.status_code == 409:
                logger.info("ℹ️ Activity BTIProcessor.GenerateDWG уже существует")
                return {"status": "exists", "message": "Activity already exists"}
            elif r.status_code in [200, 201]:
                logger.info("✅ Activity BTIProcessor.GenerateDWG создан")
                return r.json()
            else:
                logger.error(f"❌ Ошибка создания Activity: {r.status_code} - {r.text}")
                r.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка создания Activity: {e}")
            raise
    
    def submit_workitem(self, input_url, output_url, use_template=False, mode="v2"):
        """
        Запускает WorkItem для обработки DWG
        
        Args:
            input_url: URL входного DWG файла
            output_url: URL для сохранения результата
            use_template: Использовать ли типовой шаблон BTI (default: False) - DEPRECATED
            mode: Режим обработки - "v2" (полный процесс), "simple" (без обработки), "template" (со вставкой шаблона)
        """
        token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Определяем режим обработки
        if mode == "auto":
            # 🆕 AUTO - Автоматическая обработка (LISP автозапуск)
            logger.info(f"🤖 Режим AUTO: Автоматическая BTI обработка")
            logger.info(f"   ✅ Слоевое распознавание (MARK_DOOR, MARK_WINDOW)")
            logger.info(f"   ✅ Вставка блоков (BTI_DOOR, BTI_WINDOW)")
            logger.info(f"   ✅ Автозапуск при загрузке LISP")
            
            body = {
                "activityId": BTI_AUTO_PROCESS,
                "arguments": {
                    "inputFile": {"url": input_url},
                    "outputFile": {"url": output_url, "verb": "put"}
                }
            }
        elif mode == "v2":
            # 🆕 V2 - Полный процесс обработки (выравнивание, двери, окна, размеры, площадь)
            logger.info(f"🏠 Режим V2: Полный процесс обработки BTI")
            logger.info(f"   ✅ Выравнивание углов")
            logger.info(f"   ✅ Цветовое распознавание")
            logger.info(f"   ✅ Двери и окна")
            logger.info(f"   ✅ Размеры и площадь")
            
            body = {
                "activityId": BTI_FULL_ROOM_V2,
                "arguments": {
                    "inputFile": {"url": input_url},
                    "outputFile": {"url": output_url, "verb": "put"}
                }
            }
        elif mode == "template" or use_template:
            # Режим с типовым шаблоном BTI (legacy)
            logger.info(f"🏛️ Режим: с типовым шаблоном BTI Basmanny")
            logger.info(f"📄 Шаблон: {BTI_TEMPLATE_URL}")
            
            body = {
                "activityId": BTI_TEMPLATE_ACTIVITY,
                "arguments": {
                    "inputFile": {"url": input_url},
                    "templateFile": {"url": BTI_TEMPLATE_URL},
                    "resultFile": {"url": output_url, "verb": "put"}
                }
            }
        else:
            # Простой режим (без обработки)
            logger.info(f"📐 Режим: простая обработка DWG (без шаблона)")
            
            body = {
                "activityId": BTI_SIMPLE_ACTIVITY,
                "arguments": {
                    "inputFile": {"url": input_url},
                    "resultFile": {"url": output_url, "verb": "put"}
                }
            }
        
        try:
            logger.info(f"📤 Отправка WorkItem с activityId: {body['activityId']}")
            logger.info(f"📋 Request body: {json.dumps(body, indent=2)}")
            
            r = requests.post(f"{self.base_url}/workitems", headers=headers, json=body, timeout=30)
            r.raise_for_status()
            
            result = r.json()
            logger.info(f"🚀 WorkItem запущен: {result['id']}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка запуска WorkItem: {e}")
            if hasattr(e, 'response') and e.response is not None and e.response.text:
                logger.error(f"📋 Response error: {e.response.text}")
            raise
    
    def check_status(self, workitem_id):
        """Проверяет статус WorkItem"""
        token = self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            r = requests.get(f"{self.base_url}/workitems/{workitem_id}", headers=headers, timeout=30)
            r.raise_for_status()
            return r.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка проверки статуса WorkItem {workitem_id}: {e}")
            raise
    
    def wait_for_completion(self, workitem_id, timeout_minutes=5):
        """Ожидает завершения WorkItem с таймаутом"""
        logger.info(f"⏳ Ожидание завершения WorkItem {workitem_id}...")
        
        max_attempts = timeout_minutes * 6  # Проверяем каждые 10 секунд
        for attempt in range(max_attempts):
            try:
                status = self.check_status(workitem_id)
                
                if status["status"] == "success":
                    logger.info(f"✅ WorkItem {workitem_id} завершен успешно")
                    return status
                elif status["status"] in ("failed", "error", "failedInstructions", "failedDownload", "failedUpload"):
                    # Любые failed* статусы - возвращаем результат для fallback
                    error_msg = status.get("reportUrl", "Unknown error")
                    logger.error(f"❌ WorkItem {workitem_id} failed: {status['status']}")
                    return status  # Возвращаем статус для обработки fallback в app.py
                elif status["status"] in ("pending", "inprogress"):
                    logger.info(f"🔄 WorkItem {workitem_id} в процессе... (попытка {attempt + 1}/{max_attempts})")
                    time.sleep(10)
                else:
                    logger.warning(f"⚠️ Неизвестный статус WorkItem {workitem_id}: {status['status']}")
                    time.sleep(10)
                    
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise
                logger.warning(f"⚠️ Ошибка проверки статуса (попытка {attempt + 1}): {e}")
                time.sleep(10)
        
        raise TimeoutError(f"⏳ WorkItem {workitem_id} превысил лимит времени ({timeout_minutes} минут)")
    
    def download_result(self, bucket_name, blob_name, local_path):
        """Скачивает результат из GCS"""
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.download_to_filename(local_path)
            logger.info(f"✅ Файл сохранен локально: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка скачивания файла {blob_name}: {e}")
            raise

# Глобальный экземпляр клиента
forge_client = ForgeClient()

# Функции для обратной совместимости
def get_access_token():
    """Получает access token для Autodesk APS API"""
    return forge_client.get_access_token()

def create_activity():
    """Создает Activity BTIProcessor.GenerateDWG (один раз)"""
    return forge_client.create_activity()

def submit_workitem(input_url, output_url):
    """Запускает WorkItem для обработки DWG"""
    return forge_client.submit_workitem(input_url, output_url)

def check_status(workitem_id):
    """Проверяет статус WorkItem"""
    return forge_client.check_status(workitem_id)

def wait_for_completion(workitem_id, timeout_minutes=5):
    """Ожидает завершения WorkItem с таймаутом"""
    return forge_client.wait_for_completion(workitem_id, timeout_minutes)

def download_result(bucket_name, blob_name, local_path):
    """Скачивает результат из GCS"""
    return forge_client.download_result(bucket_name, blob_name, local_path)
