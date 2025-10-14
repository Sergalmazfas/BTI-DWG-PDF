"""
Forge Client для Design Automation API
Упрощенный клиент для интеграции с Autodesk Platform Services (APS)
"""

import os
import json
import logging
import requests
import time
import uuid
from typing import Optional, Dict, Any
from google.cloud import secretmanager
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForgeClient:
    """
    Клиент для работы с Autodesk Platform Services (APS) Design Automation API
    """
    
    def __init__(self):
        self.base_url = "https://developer.api.autodesk.com/da/us-east/v3"
        self.client_id = self._get_secret("FORGE_CLIENT_ID")
        self.client_secret = self._get_secret("FORGE_CLIENT_SECRET")
        self.access_token = None
        self.token_expires_at = None
        
        logger.info("✅ Forge Client initialized")
        logger.info(f"🔑 Using Client ID: {self.client_id[:8]}... (masked)")
    
    def _get_secret(self, secret_id: str) -> str:
        """Получить секрет из Google Secret Manager или env"""
        value = os.getenv(secret_id)
        if value:
            return value
        
        try:
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv("GCP_PROJECT_ID", "talkhint")
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"❌ Failed to get secret {secret_id}: {e}")
            return ""
    
    def get_token(self) -> str:
        """Получить Forge access token с кэшированием"""
        try:
            # Проверяем, есть ли валидный кэшированный токен
            now = datetime.now()
            if (self.access_token and self.token_expires_at and 
                now < self.token_expires_at):
                logger.debug("✅ Using cached Forge token")
                return self.access_token
            
            url = "https://developer.api.autodesk.com/authentication/v2/token"
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": "code:all data:read data:write bucket:create bucket:read"
            }
            
            logger.info(f"🔄 Requesting new Forge token for Client ID: {self.client_id[:8]}...")
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                
                # Устанавливаем время истечения токена
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = now + timedelta(seconds=expires_in - 100)
                
                logger.info(f"✅ Forge token obtained (expires in {expires_in}s)")
                return self.access_token
            else:
                error_text = response.text
                logger.error(f"❌ Failed to get token: {response.status_code} - {error_text}")
                
                # Проверяем специфичные ошибки доступа к API
                if "does not have access to the api product" in error_text:
                    logger.error("🚨 CLIENT ID ACCESS ERROR DETECTED!")
                    logger.error(f"   Client ID {self.client_id} не имеет доступа к Design Automation API")
                    logger.error("   Возможные решения:")
                    logger.error("   1. Дать доступ к Design Automation API в настройках приложения")
                    logger.error("   2. Использовать другой Client ID с нужными правами")
                
                return ""
        except Exception as e:
            logger.error(f"❌ Token error: {e}")
            return ""
    
    def submit_workitem(self, input_url: str, output_url: str) -> Dict[str, Any]:
        """
        Создать WorkItem для обработки DWG
        
        Args:
            input_url: URL входного DWG файла
            output_url: Signed URL для записи результата
            
        Returns:
            Dict с информацией о WorkItem или ошибке
        """
        try:
            token = self.get_token()
            if not token:
                return {"error": "No access token"}
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Используем BTI Activity по умолчанию
            activity_id = "BTI2PDFActivity+prod"
            
            # URL для callback
            callback_url = "https://dwg-processor-metadata-637190449180.europe-west1.run.app/aps-callback"
            
            workitem_data = {
                "activityId": activity_id,
                "arguments": {
                    "inputFile": {
                        "verb": "get",
                        "url": input_url
                    },
                    "resultPdf": {
                        "verb": "put", 
                        "url": output_url
                    },
                    "onComplete": {
                        "verb": "post",
                        "url": callback_url
                    }
                }
            }
            
            logger.info(f"🚀 Creating WorkItem...")
            logger.info(f"📄 Input: {input_url}")
            logger.info(f"📄 Output: {output_url[:80]}...")
            logger.info(f"📞 Callback: {callback_url}")
            
            response = requests.post(
                f"{self.base_url}/workitems",
                headers=headers,
                json=workitem_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                workitem_id = result["id"]
                logger.info(f"✅ WorkItem created: {workitem_id}")
                return {"id": workitem_id, **result}
            else:
                logger.error(f"❌ WorkItem creation failed: {response.status_code} - {response.text}")
                return {"error": f"WorkItem creation failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ WorkItem submission error: {e}")
            return {"error": str(e)}
    
    def wait_for_completion(self, workitem_id: str, timeout_minutes: int = 5) -> Dict[str, Any]:
        """
        Ожидать завершения WorkItem
        
        Args:
            workitem_id: ID WorkItem
            timeout_minutes: Максимальное время ожидания в минутах
            
        Returns:
            Dict со статусом и результатами
        """
        try:
            token = self.get_token()
            if not token:
                return {"status": "error", "message": "No token"}
            
            headers = {"Authorization": f"Bearer {token}"}
            timeout_seconds = timeout_minutes * 60
            start_time = time.time()
            poll_interval = 30  # 30 секунд между проверками
            
            logger.info(f"⏳ Waiting for WorkItem completion: {workitem_id}")
            
            while True:
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    logger.error(f"❌ WorkItem timeout after {timeout_minutes}m")
                    return {"status": "timeout", "message": f"Timeout after {timeout_minutes} minutes"}
                
                response = requests.get(
                    f"{self.base_url}/workitems/{workitem_id}",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Failed to poll WorkItem: {response.status_code}")
                    return {"status": "error", "message": response.text}
                
                data = response.json()
                status = data.get("status", "unknown")
                
                logger.info(f"📊 WorkItem status: {status} (elapsed: {elapsed:.0f}s)")
                
                if status == "success":
                    logger.info(f"✅ WorkItem succeeded!")
                    return {
                        "status": "success",
                        "data": data,
                        "reportUrl": data.get("reportUrl", ""),
                        "stats": data.get("stats", {})
                    }
                elif status in ["failed", "cancelled", "failedUpload", "failedInstructions"]:
                    logger.error(f"❌ WorkItem {status}: {data.get('reportUrl', '')}")
                    return {
                        "status": status,
                        "data": data,
                        "reportUrl": data.get("reportUrl", ""),
                        "error": data.get("error", f"WorkItem {status}")
                    }
                
                time.sleep(poll_interval)
                
        except Exception as e:
            logger.error(f"❌ Polling error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_client_info(self) -> Dict[str, str]:
        """Получить информацию о текущем клиенте"""
        return {
            "client_id": self.client_id,
            "client_id_masked": f"{self.client_id[:8]}..." if self.client_id else "Not set",
            "has_token": bool(self.access_token),
            "base_url": self.base_url
        }


# Создаем глобальный экземпляр для совместимости
forge_client = ForgeClient()