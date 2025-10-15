"""
AutoDesk Design Automation for AutoCAD (DA4A) Controller
Интеграция с BTI Processor для автоматической обработки DWG в облаке AutoCAD
"""

import json
import os
import time
import requests
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from google.cloud import storage, secretmanager
from google.cloud import pubsub_v1
import logging

logger = logging.getLogger(__name__)

class ForgeController:
    """Контроллер для работы с AutoDesk Design Automation API"""
    
    def __init__(self, project_id: str = "talkhint"):
        self.project_id = project_id
        self.storage_client = storage.Client()
        self.secret_client = secretmanager.SecretManagerServiceClient()
        
        # AutoDesk API URLs
        self.auth_url = "https://developer.api.autodesk.com/authentication/v1/authenticate"
        self.workitems_url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
        self.workitem_status_url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
        
        # Кэш токена
        self._access_token = None
        self._token_expires = None
        
        # Pub/Sub для уведомлений
        self.publisher = pubsub_v1.PublisherClient()
        
        # Метрики
        self.metrics = ForgeMetrics()
        
        # Buckets and activity from env
        self.bucket_input = os.getenv("GCS_BUCKET_INPUT", "btibot-queue")
        self.bucket_output = os.getenv("GCS_BUCKET_OUTPUT", "btibot-processed")
        self.activity_name = os.getenv("ACTIVITY_NAME", "BotBti.BTI_AUTO_PROCESS_POINT+v1")
    
    def get_access_token(self) -> str:
        """Получает access token для AutoDesk API"""
        # Проверяем кэш
        if self._access_token and self._token_expires and datetime.now() < self._token_expires:
            return self._access_token
        
        try:
            # Получаем credentials из Secret Manager
            client_id = self._get_secret("FORGE_CLIENT_ID")
            client_secret = self._get_secret("FORGE_CLIENT_SECRET")
            
            # Запрос токена
            response = requests.post(
                self.auth_url,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'scope': 'data:read data:write data:create bucket:read bucket:create'
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Forge auth failed: {response.status_code} - {response.text}")
                raise Exception(f"Forge authentication failed: {response.status_code}")
            
            token_data = response.json()
            self._access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            self._token_expires = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info("✅ Forge access token получен")
            return self._access_token
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения Forge token: {e}")
            raise
    
    def _get_secret(self, secret_name: str) -> str:
        """Получает секрет из Secret Manager"""
        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"❌ Ошибка получения секрета {secret_name}: {e}")
            raise
    
    def create_signed_urls(self, input_bucket: str, input_blob_path: str, output_bucket: str, output_blob_path: str, 
                          template_bucket: str, template_blob_path: str) -> Dict[str, str]:
        """Создает signed URLs для GCS объектов"""
        try:
            # Signed URL для входного файла (read)
            in_bucket = self.storage_client.bucket(input_bucket)
            input_blob = in_bucket.blob(input_blob_path)
            input_url = input_blob.generate_signed_url(
                version="v4",
                expiration=datetime.now() + timedelta(hours=2),
                method="GET"
            )
            
            # Signed URL для выходного файла (write)
            out_bucket = self.storage_client.bucket(output_bucket)
            output_blob = out_bucket.blob(output_blob_path)
            output_url = output_blob.generate_signed_url(
                version="v4",
                expiration=datetime.now() + timedelta(hours=2),
                method="PUT"
            )
            
            # Signed URL для шаблона (read)
            tpl_bucket = self.storage_client.bucket(template_bucket)
            template_blob = tpl_bucket.blob(template_blob_path)
            template_url = template_blob.generate_signed_url(
                version="v4",
                expiration=datetime.now() + timedelta(hours=2),
                method="GET"
            )
            
            return {
                "input_url": input_url,
                "output_url": output_url,
                "template_url": template_url
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания signed URLs: {e}")
            raise
    
    def submit_forge_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Отправляет задачу в AutoDesk Design Automation"""
        start_time = time.time()
        
        try:
            # Получаем токен
            access_token = self.get_access_token()
            
            # Определяем пути и buckets
            input_uri = job_data['dwg']  # ожидается gs://bucket/path
            input_bucket_name = self.bucket_input
            input_blob_path = input_uri
            if input_uri.startswith("gs://"):
                # разбор gs://bucket/key
                parts = input_uri.replace("gs://", "").split("/", 1)
                if len(parts) == 2:
                    input_bucket_name, input_blob_path = parts[0], parts[1]
            output_bucket_name = self.bucket_output
            output_blob_path = f"ready/{job_data.get('chat_id','anon')}/{job_data['job_id']}/bti_ready.dwg"
            template_bucket_name = self.bucket_output
            template_blob_path = f"templates/{job_data['template']}/bti_template.dwt"
            
            signed_urls = self.create_signed_urls(
                input_bucket_name, input_blob_path,
                output_bucket_name, output_blob_path,
                template_bucket_name, template_blob_path
            )
            
            # Формируем payload для Forge API
            forge_payload = {
                "activityId": self.activity_name,
                "arguments": {
                    "inputFile": {
                        "verb": "get",
                        "url": signed_urls["input_url"],
                        "localName": "input.dwg"
                    },
                    "templateFile": {
                        "verb": "get", 
                        "url": signed_urls["template_url"],
                        "localName": "template.dwt"
                    },
                    "params": {
                        "verb": "get",
                        "url": self._create_params_url(job_data['meta']),
                        "localName": "params.json"
                    },
                    "result": {
                        "verb": "put",
                        "url": signed_urls["output_url"],
                        "localName": "bti_ready.dwg"
                    }
                }
            }
            
            # Отправляем запрос в Forge API
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.workitems_url,
                json=forge_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code not in [200, 201, 202]:
                logger.error(f"❌ Forge API error: {response.status_code} - {response.text}")
                raise Exception(f"Forge API error: {response.status_code}")
            
            workitem_data = response.json()
            workitem_id = workitem_data['id']
            
            # Сохраняем информацию о задаче
            job_info = {
                "job_id": job_data['job_id'],
                "workitem_id": workitem_id,
                "chat_id": job_data['chat_id'],
                "template": job_data['template'],
                "status": "submitted",
                "submitted_at": datetime.now().isoformat(),
                "input_blob": input_blob_path,
                "output_blob": output_blob_path,
                "meta": job_data['meta']
            }
            
            # Сохраняем в GCS для отслеживания
            self._save_job_info(job_info)
            
            # Записываем метрику
            self.metrics.record_job_submitted(job_data['template'])
            
            logger.info(f"✅ Forge job submitted: {workitem_id} for job {job_data['job_id']}")
            
            return {
                "status": "submitted",
                "workitem_id": workitem_id,
                "job_id": job_data['job_id'],
                "submitted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Записываем метрику ошибки
            self.metrics.record_job_failed(job_data['template'], str(e))
            
            logger.error(f"❌ Ошибка отправки Forge job: {e}")
            raise
    
    def _create_params_url(self, meta: Dict[str, Any]) -> str:
        """Создает временный URL для параметров задачи"""
        # Сохраняем параметры во временный blob
        bucket = self.storage_client.bucket("btibot-processed")
        params_blob = bucket.blob(f"temp/params_{int(time.time())}.json")
        params_blob.upload_from_string(
            json.dumps(meta, ensure_ascii=False, indent=2),
            content_type='application/json'
        )
        
        # Создаем signed URL
        return params_blob.generate_signed_url(
            version="v4",
            expiration=datetime.now() + timedelta(hours=2),
            method="GET"
        )
    
    def _save_job_info(self, job_info: Dict[str, Any]):
        """Сохраняет информацию о задаче в GCS"""
        bucket = self.storage_client.bucket("btibot-processed")
        job_blob = bucket.blob(f"jobs/{job_info['job_id']}.json")
        job_blob.upload_from_string(
            json.dumps(job_info, ensure_ascii=False, indent=2),
            content_type='application/json'
        )
    
    def get_job_status(self, workitem_id: str) -> Dict[str, Any]:
        """Получает статус задачи в Forge API"""
        try:
            access_token = self.get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.workitem_status_url}/{workitem_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 401:
                # Токен просрочен, обновляем и повторяем
                self._access_token = None
                access_token = self.get_access_token()
                headers['Authorization'] = f'Bearer {access_token}'
                
                response = requests.get(
                    f"{self.workitem_status_url}/{workitem_id}",
                    headers=headers,
                    timeout=30
                )
            
            if response.status_code != 200:
                logger.error(f"❌ Forge status API error: {response.status_code} - {response.text}")
                return {"status": "error", "error": f"API error: {response.status_code}"}
            
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса Forge job: {e}")
            return {"status": "error", "error": str(e)}
    
    def notify_bot_completion(self, job_info: Dict[str, Any], result: Dict[str, Any]):
        """Отправляет уведомление боту о завершении задачи"""
        try:
            topic_path = self.publisher.topic_path(self.project_id, "bti-jobs-done")
            
            message_data = {
                "chat_id": job_info['chat_id'],
                "job_id": job_info['job_id'],
                "status": result['status'],
                "workitem_id": job_info['workitem_id'],
                "processing_time": result.get('processing_time', 0),
                "template": job_info['template']
            }
            
            if result['status'] == 'success':
                message_data.update({
                    "file": f"gs://btibot-processed/{job_info['output_blob']}",
                    "report": f"gs://btibot-processed/reports/{job_info['job_id']}/report.json"
                })
            else:
                message_data['error'] = result.get('error', 'Unknown error')
            
            self.publisher.publish(topic_path, json.dumps(message_data).encode('utf-8'))
            logger.info(f"✅ Bot notification sent for job {job_info['job_id']}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления боту: {e}")


class ForgeMetrics:
    """Метрики для мониторинга Forge API"""
    
    def __init__(self):
        from google.cloud import monitoring_v3
        self.client = monitoring_v3.MetricServiceClient()
        self.project_id = "talkhint"
    
    def record_job_submitted(self, template: str):
        """Записывает отправку задачи"""
        self._write_metric('forge_jobs_total', 1, {'template': template, 'status': 'submitted'})
    
    def record_job_completed(self, template: str, status: str, duration_ms: float):
        """Записывает завершение задачи"""
        self._write_metric('forge_jobs_total', 1, {'template': template, 'status': status})
        self._write_metric('forge_avg_duration_ms', duration_ms, {'template': template, 'status': status})
    
    def record_job_failed(self, template: str, error: str):
        """Записывает ошибку задачи"""
        self._write_metric('forge_jobs_failed', 1, {'template': template, 'error_type': type(error).__name__})
    
    def _write_metric(self, metric_name: str, value: float, labels: Dict[str, str]):
        """Записывает метрику в Cloud Monitoring"""
        try:
            # Создаем метрику
            project_name = f"projects/{self.project_id}"
            metric_type = f"custom.googleapis.com/{metric_name}"
            
            # Здесь должна быть логика записи метрики
            # Упрощенная версия для демонстрации
            logger.info(f"📊 Metric: {metric_name}={value}, labels={labels}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи метрики {metric_name}: {e}")


class ForgeJobPoller:
    """Пуллер для отслеживания статуса Forge задач"""
    
    def __init__(self):
        self.forge_controller = ForgeController()
        self.storage_client = storage.Client()
    
    def poll_pending_jobs(self):
        """Опрашивает незавершенные задачи каждые 30 секунд"""
        try:
            bucket = self.storage_client.bucket("btibot-processed")
            blobs = bucket.list_blobs(prefix="jobs/")
            
            for blob in blobs:
                if not blob.name.endswith('.json'):
                    continue
                
                try:
                    job_info = json.loads(blob.download_as_text())
                    
                    # Пропускаем завершенные задачи
                    if job_info.get('status') in ['success', 'failed']:
                        continue
                    
                    # Проверяем статус в Forge API
                    status_result = self.forge_controller.get_job_status(job_info['workitem_id'])
                    
                    if status_result.get('status') == 'success':
                        self._handle_job_success(job_info, status_result)
                    elif status_result.get('status') == 'failed':
                        self._handle_job_failure(job_info, status_result)
                    elif status_result.get('status') in ['inprogress', 'pending']:
                        # Задача еще выполняется
                        continue
                    else:
                        logger.warning(f"⚠️ Unknown status for job {job_info['job_id']}: {status_result}")
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки job {blob.name}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка polling Forge jobs: {e}")
    
    def _handle_job_success(self, job_info: Dict[str, Any], status_result: Dict[str, Any]):
        """Обрабатывает успешное завершение задачи"""
        try:
            # Обновляем статус
            job_info['status'] = 'success'
            job_info['completed_at'] = datetime.now().isoformat()
            
            # Сохраняем обновленную информацию
            self.forge_controller._save_job_info(job_info)
            
            # Создаем отчет
            report = self._create_report(job_info, status_result)
            self._save_report(job_info['job_id'], report)
            
            # Отправляем уведомление боту
            result = {
                'status': 'success',
                'processing_time': self._calculate_processing_time(job_info)
            }
            self.forge_controller.notify_bot_completion(job_info, result)
            
            # Записываем метрику
            self.forge_controller.metrics.record_job_completed(
                job_info['template'], 'success', result['processing_time']
            )
            
            logger.info(f"✅ Job {job_info['job_id']} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки успешного завершения job {job_info['job_id']}: {e}")
    
    def _handle_job_failure(self, job_info: Dict[str, Any], status_result: Dict[str, Any]):
        """Обрабатывает ошибку задачи"""
        try:
            # Обновляем статус
            job_info['status'] = 'failed'
            job_info['failed_at'] = datetime.now().isoformat()
            job_info['error'] = status_result.get('error', 'Unknown error')
            
            # Сохраняем обновленную информацию
            self.forge_controller._save_job_info(job_info)
            
            # Отправляем уведомление боту
            result = {
                'status': 'failed',
                'error': job_info['error'],
                'processing_time': self._calculate_processing_time(job_info)
            }
            self.forge_controller.notify_bot_completion(job_info, result)
            
            # Записываем метрику
            self.forge_controller.metrics.record_job_failed(job_info['template'], job_info['error'])
            
            logger.error(f"❌ Job {job_info['job_id']} failed: {job_info['error']}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки ошибки job {job_info['job_id']}: {e}")
    
    def _calculate_processing_time(self, job_info: Dict[str, Any]) -> float:
        """Вычисляет время обработки в миллисекундах"""
        try:
            submitted_at = datetime.fromisoformat(job_info['submitted_at'])
            completed_at = datetime.now()
            duration = (completed_at - submitted_at).total_seconds()
            return duration * 1000  # в миллисекундах
        except:
            return 0.0
    
    def _create_report(self, job_info: Dict[str, Any], status_result: Dict[str, Any]) -> Dict[str, Any]:
        """Создает отчет о выполненной задаче"""
        return {
            "job_id": job_info['job_id'],
            "workitem_id": job_info['workitem_id'],
            "template": job_info['template'],
            "status": "success",
            "processing_time_ms": self._calculate_processing_time(job_info),
            "input_file": job_info['input_blob'],
            "output_file": job_info['output_blob'],
            "meta": job_info['meta'],
            "forge_result": status_result,
            "completed_at": datetime.now().isoformat()
        }
    
    def _save_report(self, job_id: str, report: Dict[str, Any]):
        """Сохраняет отчет в GCS"""
        bucket = self.storage_client.bucket("btibot-processed")
        report_blob = bucket.blob(f"reports/{job_id}/report.json")
        report_blob.upload_from_string(
            json.dumps(report, ensure_ascii=False, indent=2),
            content_type='application/json'
        )


# Flask приложение для Cloud Run
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/forge/process', methods=['POST'])
def forge_process():
    """Эндпоинт для отправки DWG в AutoDesk Design Automation"""
    try:
        job_data = request.get_json()
        
        # Валидация входных данных
        required_fields = ['dwg', 'template', 'meta']
        for field in required_fields:
            if field not in job_data:
                return jsonify({
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Создаем контроллер и отправляем задачу
        forge_controller = ForgeController()
        result = forge_controller.submit_forge_job(job_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки Forge request: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/forge/poll', methods=['POST'])
def forge_poll():
    """Эндпоинт для опроса статуса задач (вызывается по cron)"""
    try:
        poller = ForgeJobPoller()
        poller.poll_pending_jobs()
        
        return jsonify({'status': 'polling completed'}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка polling Forge jobs: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'forge-controller'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
