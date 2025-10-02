"""
Forge AppBundle Manager
Управление AppBundles и Activities для BTI и TZ конвертации
"""

import os
import json
import logging
import requests
import time
from typing import Optional, Dict, Any, Literal, List
from google.cloud import secretmanager
from collections import defaultdict
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AppBundleType = Literal["BTI2PDF", "TZ2PDF"]


class ForgeAppBundleManager:
    """
    Менеджер для управления Forge AppBundles и Activities
    
    Поддерживает два типа конвертации:
    - BTI2PDF: Техпаспорт БТИ с шаблоном
    - TZ2PDF: Техническое задание с ГОСТ таблицами
    """
    
    def __init__(self):
        self.base_url = "https://developer.api.autodesk.com/da/us-east/v3"
        self.client_id = self._get_secret("FORGE_CLIENT_ID")
        self.client_secret = self._get_secret("FORGE_CLIENT_SECRET")
        self.access_token = None
        self.token_expires_at = None  # Время истечения токена
        
        # Rate limiting counters
        self.post_requests = defaultdict(list)  # POST requests per minute
        self.get_requests = defaultdict(list)    # GET requests per minute
        self.auth_requests = defaultdict(list)   # Authentication requests per hour
        self.max_post_per_minute = 100
        self.max_get_per_minute = 150
        self.max_auth_per_hour = 200  # Authentication API limit: 200/hour
        self.min_polling_interval = 60  # Minimum 60 seconds between polls (согласно рекомендациям)
        
        logger.info("✅ Forge AppBundle Manager initialized")
    
    def _check_rate_limit(self, request_type: str) -> bool:
        """Проверяет, не превышен ли лимит запросов"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        if request_type == "POST":
            # Очищаем старые записи
            self.post_requests[request_type] = [
                req_time for req_time in self.post_requests[request_type] 
                if req_time > minute_ago
            ]
            
            if len(self.post_requests[request_type]) >= self.max_post_per_minute:
                logger.warning(f"⚠️ POST rate limit reached: {len(self.post_requests[request_type])}/{self.max_post_per_minute}")
                return False
                
        elif request_type == "GET":
            # Очищаем старые записи
            self.get_requests[request_type] = [
                req_time for req_time in self.get_requests[request_type] 
                if req_time > minute_ago
            ]
            
            if len(self.get_requests[request_type]) >= self.max_get_per_minute:
                logger.warning(f"⚠️ GET rate limit reached: {len(self.get_requests[request_type])}/{self.max_get_per_minute}")
                return False
                
        elif request_type == "AUTH":
            # Очищаем старые записи (час)
            self.auth_requests[request_type] = [
                req_time for req_time in self.auth_requests[request_type] 
                if req_time > hour_ago
            ]
            
            if len(self.auth_requests[request_type]) >= self.max_auth_per_hour:
                logger.warning(f"⚠️ AUTH rate limit reached: {len(self.auth_requests[request_type])}/{self.max_auth_per_hour}")
                return False
        
        return True
    
    def _record_request(self, request_type: str):
        """Записывает время запроса для rate limiting"""
        now = datetime.now()
        if request_type == "POST":
            self.post_requests[request_type].append(now)
        elif request_type == "GET":
            self.get_requests[request_type].append(now)
        elif request_type == "AUTH":
            self.auth_requests[request_type].append(now)
    
    def _wait_for_rate_limit(self, request_type: str) -> int:
        """Ждет, пока не освободится место в rate limit"""
        if request_type == "POST":
            current_count = len(self.post_requests[request_type])
            if current_count >= self.max_post_per_minute:
                # Ждем до следующей минуты
                wait_seconds = 60 - datetime.now().second
                logger.info(f"⏳ Waiting {wait_seconds}s for POST rate limit reset...")
                return wait_seconds
        elif request_type == "GET":
            current_count = len(self.get_requests[request_type])
            if current_count >= self.max_get_per_minute:
                # Ждем до следующей минуты
                wait_seconds = 60 - datetime.now().second
                logger.info(f"⏳ Waiting {wait_seconds}s for GET rate limit reset...")
                return wait_seconds
        
        return 0
    
    def _log_rate_limit_status(self):
        """Логирует текущий статус rate limiting"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Очищаем старые записи
        self.post_requests["POST"] = [
            req_time for req_time in self.post_requests["POST"] 
            if req_time > minute_ago
        ]
        self.get_requests["GET"] = [
            req_time for req_time in self.get_requests["GET"] 
            if req_time > minute_ago
        ]
        
        post_count = len(self.post_requests["POST"])
        get_count = len(self.get_requests["GET"])
        
        logger.info(f"📊 Rate Limit Status:")
        logger.info(f"   POST requests: {post_count}/{self.max_post_per_minute} per minute")
        logger.info(f"   GET requests: {get_count}/{self.max_get_per_minute} per minute")
        logger.info(f"   Min polling interval: {self.min_polling_interval}s")
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Возвращает текущий статус rate limiting для мониторинга"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Очищаем старые записи
        self.post_requests["POST"] = [
            req_time for req_time in self.post_requests["POST"] 
            if req_time > minute_ago
        ]
        self.get_requests["GET"] = [
            req_time for req_time in self.get_requests["GET"] 
            if req_time > minute_ago
        ]
        
        return {
            "post_requests": {
                "current": len(self.post_requests["POST"]),
                "limit": self.max_post_per_minute,
                "remaining": self.max_post_per_minute - len(self.post_requests["POST"])
            },
            "get_requests": {
                "current": len(self.get_requests["GET"]),
                "limit": self.max_get_per_minute,
                "remaining": self.max_get_per_minute - len(self.get_requests["GET"])
            },
            "min_polling_interval": self.min_polling_interval,
            "timestamp": now.isoformat()
        }
    
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
        """Получить Forge access token с кэшированием и rate limiting"""
        try:
            # Проверяем, есть ли валидный кэшированный токен
            now = datetime.now()
            if (self.access_token and self.token_expires_at and 
                now < self.token_expires_at):
                logger.info("✅ Using cached Forge token")
                return self.access_token
            
            # Проверяем rate limit для AUTH запросов
            if not self._check_rate_limit("AUTH"):
                wait_time = self._wait_for_rate_limit("AUTH")
                if wait_time > 0:
                    logger.warning(f"⏳ AUTH rate limit reached, waiting {wait_time}s...")
                    time.sleep(wait_time)
            
            url = "https://developer.api.autodesk.com/authentication/v2/token"
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": "code:all data:read data:write bucket:create bucket:read"
            }
            
            logger.info("🔄 Requesting new Forge token...")
            response = requests.post(url, data=data, timeout=30)
            
            # Записываем AUTH запрос в rate limiter
            self._record_request("AUTH")
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                
                # Устанавливаем время истечения токена (обычно 3600 секунд, но берем 3500 для безопасности)
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = now + timedelta(seconds=expires_in - 100)
                
                logger.info(f"✅ Forge token obtained (expires in {expires_in}s)")
                
                # Логируем Rate Limit заголовки
                rate_limit_headers = {
                    'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
                    'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
                    'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset')
                }
                logger.info(f"📊 Rate Limit Headers: {rate_limit_headers}")
                
                # Логируем текущие счетчики
                self._log_rate_limit_status()
                
                return self.access_token
            else:
                logger.error(f"❌ Failed to get token: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logger.error(f"❌ Token error: {e}")
            return ""
    
    def list_appbundles(self) -> list:
        """Получить список всех AppBundles"""
        try:
            token = self.get_token()
            if not token:
                return []
            
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{self.base_url}/appbundles", headers=headers, timeout=30)
            
            if response.status_code == 200:
                bundles = response.json().get("data", [])
                logger.info(f"📦 Found {len(bundles)} AppBundles")
                return bundles
            else:
                logger.error(f"❌ Failed to list AppBundles: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Error listing AppBundles: {e}")
            return []
    
    def list_activities(self) -> list:
        """Получить список всех Activities"""
        try:
            token = self.get_token()
            if not token:
                return []
            
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{self.base_url}/activities", headers=headers, timeout=30)
            
            if response.status_code == 200:
                activities = response.json().get("data", [])
                logger.info(f"🔧 Found {len(activities)} Activities")
                return activities
            else:
                logger.error(f"❌ Failed to list Activities: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Error listing Activities: {e}")
            return []
    
    def create_workitem(
        self, 
        activity_type: AppBundleType,
        input_dwg_url: str,
        output_pdf_signed_url: str
    ) -> Optional[str]:
        """
        Создать WorkItem для конвертации DWG → PDF
        
        Args:
            activity_type: Тип активности ("BTI2PDF" или "TZ2PDF")
            input_dwg_url: URL входного DWG файла (публичный)
            output_pdf_signed_url: Signed URL для записи PDF (PUT)
            
        Returns:
            WorkItem ID или None
        """
        try:
            # Проверяем rate limit для POST запросов
            if not self._check_rate_limit("POST"):
                wait_time = self._wait_for_rate_limit("POST")
                if wait_time > 0:
                    time.sleep(wait_time)
            
            token = self.get_token()
            if not token:
                return None
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Выбираем Activity в зависимости от типа (используем правильный engine)
            activity_id = f"{activity_type}Activity+prod"
            
            # URL для callback (APS будет вызывать этот endpoint при завершении)
            callback_url = "https://dwg-processor-metadata-637190449180.europe-west1.run.app/aps-callback"
            
            # Валидация URL перед отправкой
            logger.info("🔍 Validating URLs before WorkItem creation...")
            
            # Проверяем доступность входного URL
            try:
                input_response = requests.head(input_dwg_url, timeout=10)
                logger.info(f"📥 Input URL check: {input_response.status_code}")
                if input_response.status_code not in [200, 403, 405]:  # 403/405 могут быть нормальными для HEAD
                    logger.warning(f"⚠️ Input URL may not be accessible: {input_response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ Could not validate input URL: {e}")
            
            # Проверяем signed URL (должен быть PUT)
            try:
                # Для signed URL делаем простую проверку структуры
                if "X-Goog-Signature" not in output_pdf_signed_url and "Signature" not in output_pdf_signed_url:
                    logger.warning("⚠️ Output URL may not be a valid signed URL")
                logger.info("📤 Output signed URL structure validated")
            except Exception as e:
                logger.warning(f"⚠️ Could not validate output URL: {e}")
            
            workitem_data = {
                "activityId": activity_id,
                "arguments": {
                    "inputFile": {
                        "verb": "get",
                        "url": input_dwg_url
                    },
                    "resultPdf": {
                        "verb": "put", 
                        "url": output_pdf_signed_url
                    },
                    "onComplete": {
                        "verb": "post",
                        "url": callback_url
                    }
                }
            }
            
            logger.info(f"🚀 Creating {activity_type} WorkItem...")
            logger.info(f"📄 Input: {input_dwg_url}")
            logger.info(f"📄 Output: {output_pdf_signed_url}")
            logger.info(f"📞 Callback: {callback_url}")
            
            # Детальное логирование WorkItem payload
            logger.info(f"📋 WorkItem payload: {json.dumps(workitem_data, indent=2)}")
            
            response = requests.post(
                f"{self.base_url}/workitems",
                headers=headers,
                json=workitem_data,
                timeout=30
            )
            
            # Записываем POST запрос в rate limiter
            self._record_request("POST")
            
            if response.status_code in [200, 201]:
                result = response.json()
                workitem_id = result["id"]
                logger.info(f"✅ WorkItem created: {workitem_id}")
                
                # Детальное логирование созданного WorkItem
                logger.info(f"📋 Created WorkItem details:")
                logger.info(f"   - ID: {workitem_id}")
                logger.info(f"   - Activity: {activity_id}")
                logger.info(f"   - Input URL: {input_dwg_url}")
                logger.info(f"   - Output URL: {output_pdf_signed_url}")
                logger.info(f"   - Callback URL: {callback_url}")
                
                return workitem_id
            else:
                logger.error(f"❌ WorkItem creation failed: {response.status_code} - {response.text}")
                
                # Детальное логирование ошибки
                logger.error(f"📋 Failed WorkItem details:")
                logger.error(f"   - Status Code: {response.status_code}")
                logger.error(f"   - Response Headers: {dict(response.headers)}")
                logger.error(f"   - Response Text: {response.text}")
                logger.error(f"   - Activity ID: {activity_id}")
                logger.error(f"   - Input URL: {input_dwg_url}")
                logger.error(f"   - Output URL: {output_pdf_signed_url}")
                
                # Специальная обработка для failedUpload ошибок
                if "failedUpload" in response.text or "upload" in response.text.lower():
                    logger.error("🚨 FAILED UPLOAD DETECTED!")
                    logger.error("🔍 Possible causes:")
                    logger.error("   1. Invalid or expired signed URL")
                    logger.error("   2. Input URL not accessible from APS")
                    logger.error("   3. Incorrect URL format")
                    logger.error("   4. Missing required headers")
                    
                    # Дополнительная диагностика URL
                    logger.error("🔍 URL Diagnostics:")
                    logger.error(f"   - Input URL length: {len(input_dwg_url)}")
                    logger.error(f"   - Output URL length: {len(output_pdf_signed_url)}")
                    logger.error(f"   - Input URL starts with https: {input_dwg_url.startswith('https://')}")
                    logger.error(f"   - Output URL contains signature: {'X-Goog-Signature' in output_pdf_signed_url}")
                
                return None
                
        except Exception as e:
            logger.error(f"❌ WorkItem creation error: {e}")
            return None
    
    def poll_workitem(self, workitem_id: str, timeout: int = 600) -> Dict[str, Any]:
        """
        Poll WorkItem до завершения
        
        Args:
            workitem_id: ID WorkItem
            timeout: Максимальное время ожидания (секунды)
            
        Returns:
            Dict со статусом и результатами
        """
        try:
            token = self.get_token()
            if not token:
                return {"status": "error", "message": "No token"}
            
            headers = {"Authorization": f"Bearer {token}"}
            
            import time
            start_time = time.time()
            poll_interval = max(self.min_polling_interval, 60)  # Минимум 60 секунд между запросами
            
            logger.info(f"⏳ Polling WorkItem: {workitem_id}")
            
            while True:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    logger.error(f"❌ WorkItem timeout after {timeout}s")
                    return {"status": "timeout", "message": f"Timeout after {timeout}s"}
                
                # Проверяем rate limit для GET запросов
                if not self._check_rate_limit("GET"):
                    wait_time = self._wait_for_rate_limit("GET")
                    if wait_time > 0:
                        time.sleep(wait_time)
                
                response = requests.get(
                    f"{self.base_url}/workitems/{workitem_id}",
                    headers=headers,
                    timeout=30
                )
                
                # Записываем GET запрос в rate limiter
                self._record_request("GET")
                
                if response.status_code == 429:
                    # Обрабатываем 429 с Retry-After заголовком
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            wait_seconds = int(retry_after)
                            logger.warning(f"⚠️ Rate limited (429), Retry-After: {wait_seconds}s...")
                            time.sleep(wait_seconds)
                        except ValueError:
                            # Агрессивный backoff: 10s → 300s
                            backoff_delay = min(300, max(10, poll_interval * 5))
                            logger.warning(f"⚠️ Rate limited (429), Retry-After: {retry_after} (не число), используем {backoff_delay}s...")
                            time.sleep(backoff_delay)
                    else:
                        # Агрессивный backoff: 10s → 300s
                        backoff_delay = min(300, max(10, poll_interval * 5))
                        logger.warning(f"⚠️ Rate limited (429), Retry-After не указан, используем {backoff_delay}s...")
                        time.sleep(backoff_delay)
                    continue
                elif response.status_code != 200:
                    logger.error(f"❌ Failed to poll WorkItem: {response.status_code}")
                    return {"status": "error", "message": response.text}
                
                data = response.json()
                status = data.get("status", "unknown")
                
                logger.info(f"📊 WorkItem status: {status} (elapsed: {elapsed:.0f}s)")
                
                # Детальное логирование статуса WorkItem
                if status in ["failedUpload", "failedInstructions", "failed"]:
                    logger.error(f"📋 Failed WorkItem details:")
                    logger.error(f"   - Status: {status}")
                    logger.error(f"   - Full Response: {json.dumps(data, indent=2)}")
                    logger.error(f"   - Report URL: {data.get('reportUrl', 'N/A')}")
                    logger.error(f"   - Error: {data.get('error', 'N/A')}")
                    
                    # Специальная обработка для failedUpload
                    if status == "failedUpload":
                        logger.error("🚨 FAILED UPLOAD DETECTED IN WORKITEM STATUS!")
                        logger.error("🔍 Diagnostic information:")
                        
                        # Проверяем аргументы WorkItem
                        arguments = data.get('arguments', {})
                        if arguments:
                            logger.error("📋 WorkItem Arguments:")
                            for arg_name, arg_data in arguments.items():
                                if isinstance(arg_data, dict) and 'url' in arg_data:
                                    url = arg_data['url']
                                    logger.error(f"   - {arg_name}: {url}")
                                    
                                    # Проверяем URL на валидность
                                    if arg_name == 'inputFile':
                                        try:
                                            test_resp = requests.head(url, timeout=5)
                                            logger.error(f"     URL accessibility: {test_resp.status_code}")
                                        except Exception as e:
                                            logger.error(f"     URL accessibility: ERROR - {e}")
                                    elif arg_name == 'resultPdf':
                                        if 'X-Goog-Signature' not in url:
                                            logger.error("     ⚠️ URL may not be a valid signed URL")
                        
                        # Проверяем reportUrl если есть
                        report_url = data.get('reportUrl')
                        if report_url:
                            logger.error(f"📊 Report URL available: {report_url}")
                            try:
                                report_resp = requests.get(report_url, timeout=10)
                                if report_resp.status_code == 200:
                                    logger.error(f"📊 Report content: {report_resp.text[:500]}...")
                                else:
                                    logger.error(f"📊 Report URL status: {report_resp.status_code}")
                            except Exception as e:
                                logger.error(f"📊 Report URL error: {e}")
                    logger.error(f"   - Stats: {data.get('stats', {})}")
                
                if status == "success":
                    logger.info(f"✅ WorkItem succeeded!")
                    logger.info(f"📋 Success details:")
                    logger.info(f"   - Report URL: {data.get('reportUrl', 'N/A')}")
                    logger.info(f"   - Stats: {data.get('stats', {})}")
                    return {
                        "status": "success",
                        "data": data,
                        "report_url": data.get("reportUrl", ""),
                        "stats": data.get("stats", {})
                    }
                elif status in ["failed", "cancelled", "failedUpload", "failedInstructions"]:
                    logger.error(f"❌ WorkItem {status}: {data.get('reportUrl', '')}")
                    return {
                        "status": status,
                        "data": data,
                        "report_url": data.get("reportUrl", ""),
                        "error": data.get("error", "Unknown error")
                    }
                
                time.sleep(poll_interval)
                
        except Exception as e:
            logger.error(f"❌ Polling error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_workitems_status(self, workitem_ids: List[str]) -> Dict[str, Any]:
        """
        Групповой опрос статусов нескольких WorkItem
        
        Args:
            workitem_ids: Список ID WorkItem для проверки
            
        Returns:
            Dict со статусами всех WorkItem
        """
        try:
            token = self.get_token()
            if not token:
                return {"status": "error", "message": "No token"}
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Проверяем rate limit для POST запросов
            if not self._check_rate_limit("POST"):
                wait_time = self._wait_for_rate_limit("POST")
                if wait_time > 0:
                    time.sleep(wait_time)
            
            payload = {"workItemIds": workitem_ids}
            
            response = requests.post(
                f"{self.base_url}/workitems/status",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Записываем POST запрос в rate limiter
            self._record_request("POST")
            
            if response.status_code == 429:
                # Обрабатываем 429 с Retry-After заголовком
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    try:
                        wait_seconds = int(retry_after)
                        logger.warning(f"⚠️ Rate limited (429), Retry-After: {wait_seconds}s...")
                        time.sleep(wait_seconds)
                        # Повторяем запрос
                        response = requests.post(
                            f"{self.base_url}/workitems/status",
                            headers=headers,
                            json=payload,
                            timeout=30
                        )
                        self._record_request("POST")
                    except ValueError:
                        logger.warning(f"⚠️ Rate limited (429), Retry-After: {retry_after} (не число)")
                        return {"status": "error", "message": "Rate limited"}
                else:
                    logger.warning("⚠️ Rate limited (429), Retry-After не указан")
                    return {"status": "error", "message": "Rate limited"}
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Group status check completed for {len(workitem_ids)} WorkItems")
                return {"status": "success", "data": data}
            else:
                logger.error(f"❌ Group status check failed: {response.status_code} - {response.text}")
                return {"status": "error", "message": response.text}
                
        except Exception as e:
            logger.error(f"❌ Group status check error: {e}")
            return {"status": "error", "message": str(e)}
    
    def convert_dwg_to_pdf(
        self,
        activity_type: AppBundleType,
        input_dwg_url: str,
        output_pdf_signed_url: str
    ) -> Dict[str, Any]:
        """
        Полная цепочка конвертации DWG → PDF
        
        Args:
            activity_type: Тип конвертации ("BTI2PDF" или "TZ2PDF")
            input_dwg_url: URL входного DWG
            output_pdf_signed_url: Signed URL для PDF
            
        Returns:
            Dict с результатами
        """
        try:
            logger.info(f"🚀 Starting {activity_type} conversion")
            
            # Создать WorkItem
            workitem_id = self.create_workitem(
                activity_type=activity_type,
                input_dwg_url=input_dwg_url,
                output_pdf_signed_url=output_pdf_signed_url
            )
            
            if not workitem_id:
                return {"success": False, "error": "Failed to create WorkItem"}
            
            # Poll до завершения
            result = self.poll_workitem(workitem_id, timeout=600)
            
            if result["status"] != "success":
                return {
                    "success": False,
                    "error": result.get("error", "WorkItem failed"),
                    "workitem_id": workitem_id,
                    "report_url": result.get("report_url")
                }
            
            return {
                "success": True,
                "workitem_id": workitem_id,
                "report_url": result.get("report_url"),
                "stats": result.get("stats", {})
            }
            
        except Exception as e:
            logger.error(f"❌ Conversion error: {e}")
            return {"success": False, "error": str(e)}


# Helper function для использования в других модулях
def convert_dwg_to_pdf(
    activity_type: AppBundleType,
    input_dwg_url: str,
    output_pdf_signed_url: str
) -> Dict[str, Any]:
    """
    Convenience function для конвертации DWG → PDF
    
    Args:
        activity_type: "BTI2PDF" или "TZ2PDF"
        input_dwg_url: Публичный URL DWG файла
        output_pdf_signed_url: Signed PUT URL для PDF
        
    Returns:
        Dict с результатами конвертации
    """
    manager = ForgeAppBundleManager()
    return manager.convert_dwg_to_pdf(activity_type, input_dwg_url, output_pdf_signed_url)

