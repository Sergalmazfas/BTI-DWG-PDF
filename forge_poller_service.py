"""
Forge Job Poller Service
Облачный сервис для отслеживания статуса задач AutoDesk Design Automation
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from google.cloud import storage, pubsub_v1
from forge_controller import ForgeController, ForgeJobPoller

logger = logging.getLogger(__name__)

class ForgePollerService:
    """Сервис для опроса статуса Forge задач"""
    
    def __init__(self, project_id: str = "talkhint"):
        self.project_id = project_id
        self.storage_client = storage.Client()
        self.forge_controller = ForgeController(project_id)
        self.publisher = pubsub_v1.PublisherClient()
        
        # Настройки polling
        self.poll_interval = 30  # секунд
        self.max_poll_duration = 1800  # 30 минут
        self.cleanup_threshold = 24 * 3600  # 24 часа
        
        # Статистика
        self.stats = {
            'jobs_processed': 0,
            'jobs_success': 0,
            'jobs_failed': 0,
            'last_poll': None
        }
    
    def poll_all_pending_jobs(self) -> Dict[str, Any]:
        """Опрашивает все незавершенные задачи"""
        start_time = time.time()
        poll_results = {
            'started_at': datetime.now().isoformat(),
            'jobs_checked': 0,
            'jobs_updated': 0,
            'jobs_cleaned': 0,
            'errors': []
        }
        
        try:
            # Получаем список всех задач
            bucket = self.storage_client.bucket("btibot-processed")
            job_blobs = list(bucket.list_blobs(prefix="jobs/"))
            
            logger.info(f"🔍 Found {len(job_blobs)} job files to check")
            
            for blob in job_blobs:
                if not blob.name.endswith('.json'):
                    continue
                
                try:
                    job_info = json.loads(blob.download_as_text())
                    poll_results['jobs_checked'] += 1
                    
                    # Обрабатываем задачу
                    result = self._process_job(job_info)
                    if result['updated']:
                        poll_results['jobs_updated'] += 1
                    if result['cleaned']:
                        poll_results['jobs_cleaned'] += 1
                        
                except Exception as e:
                    error_msg = f"Error processing job {blob.name}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    poll_results['errors'].append(error_msg)
            
            # Очистка старых задач
            cleaned_count = self._cleanup_old_jobs()
            poll_results['jobs_cleaned'] += cleaned_count
            
            # Обновляем статистику
            poll_results['duration_seconds'] = time.time() - start_time
            poll_results['stats'] = self.stats.copy()
            poll_results['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"✅ Polling completed: {poll_results['jobs_updated']} jobs updated, {poll_results['jobs_cleaned']} cleaned")
            
            return poll_results
            
        except Exception as e:
            logger.error(f"❌ Critical error in polling: {e}")
            poll_results['critical_error'] = str(e)
            return poll_results
    
    def _process_job(self, job_info: Dict[str, Any]) -> Dict[str, bool]:
        """Обрабатывает одну задачу"""
        result = {'updated': False, 'cleaned': False}
        
        try:
            job_id = job_info.get('job_id')
            workitem_id = job_info.get('workitem_id')
            current_status = job_info.get('status')
            
            # Пропускаем завершенные задачи
            if current_status in ['success', 'failed']:
                # Проверяем, не пора ли удалить старую задачу
                if self._should_cleanup_job(job_info):
                    self._cleanup_job(job_info)
                    result['cleaned'] = True
                return result
            
            # Проверяем таймаут
            if self._is_job_timeout(job_info):
                self._handle_job_timeout(job_info)
                result['updated'] = True
                return result
            
            # Получаем статус из Forge API
            status_result = self.forge_controller.get_job_status(workitem_id)
            
            if status_result.get('status') == 'success':
                self._handle_job_success(job_info, status_result)
                result['updated'] = True
                self.stats['jobs_success'] += 1
                
            elif status_result.get('status') == 'failed':
                self._handle_job_failure(job_info, status_result)
                result['updated'] = True
                self.stats['jobs_failed'] += 1
                
            elif status_result.get('status') in ['inprogress', 'pending']:
                # Задача еще выполняется, обновляем время последней проверки
                job_info['last_polled'] = datetime.now().isoformat()
                self._save_job_info(job_info)
                
            else:
                logger.warning(f"⚠️ Unknown status for job {job_id}: {status_result}")
            
            self.stats['jobs_processed'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error processing job {job_info.get('job_id', 'unknown')}: {e}")
        
        return result
    
    def _handle_job_success(self, job_info: Dict[str, Any], status_result: Dict[str, Any]):
        """Обрабатывает успешное завершение задачи"""
        try:
            # Обновляем статус
            job_info['status'] = 'success'
            job_info['completed_at'] = datetime.now().isoformat()
            job_info['forge_result'] = status_result
            
            # Сохраняем обновленную информацию
            self._save_job_info(job_info)
            
            # Создаем отчет
            report = self._create_success_report(job_info, status_result)
            self._save_report(job_info['job_id'], report)
            
            # Отправляем уведомление боту
            notification_data = {
                "chat_id": job_info['chat_id'],
                "job_id": job_info['job_id'],
                "status": "success",
                "workitem_id": job_info['workitem_id'],
                "processing_time_ms": self._calculate_processing_time(job_info),
                "template": job_info['template'],
                "file": f"gs://btibot-processed/{job_info['output_blob']}",
                "report": f"gs://btibot-processed/reports/{job_info['job_id']}/report.json"
            }
            
            self._send_bot_notification(notification_data)
            
            # Записываем метрику
            self.forge_controller.metrics.record_job_completed(
                job_info['template'], 'success', notification_data['processing_time_ms']
            )
            
            logger.info(f"✅ Job {job_info['job_id']} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error handling job success {job_info['job_id']}: {e}")
    
    def _handle_job_failure(self, job_info: Dict[str, Any], status_result: Dict[str, Any]):
        """Обрабатывает ошибку задачи"""
        try:
            # Обновляем статус
            job_info['status'] = 'failed'
            job_info['failed_at'] = datetime.now().isoformat()
            job_info['error'] = status_result.get('error', 'Unknown error')
            job_info['forge_result'] = status_result
            
            # Сохраняем обновленную информацию
            self._save_job_info(job_info)
            
            # Создаем отчет об ошибке
            report = self._create_error_report(job_info, status_result)
            self._save_report(job_info['job_id'], report)
            
            # Отправляем уведомление боту
            notification_data = {
                "chat_id": job_info['chat_id'],
                "job_id": job_info['job_id'],
                "status": "failed",
                "workitem_id": job_info['workitem_id'],
                "processing_time_ms": self._calculate_processing_time(job_info),
                "template": job_info['template'],
                "error": job_info['error'],
                "report": f"gs://btibot-processed/reports/{job_info['job_id']}/report.json"
            }
            
            self._send_bot_notification(notification_data)
            
            # Записываем метрику
            self.forge_controller.metrics.record_job_failed(job_info['template'], job_info['error'])
            
            logger.error(f"❌ Job {job_info['job_id']} failed: {job_info['error']}")
            
        except Exception as e:
            logger.error(f"❌ Error handling job failure {job_info['job_id']}: {e}")
    
    def _handle_job_timeout(self, job_info: Dict[str, Any]):
        """Обрабатывает таймаут задачи"""
        try:
            job_info['status'] = 'timeout'
            job_info['timeout_at'] = datetime.now().isoformat()
            job_info['error'] = f"Job timeout after {self.max_poll_duration} seconds"
            
            # Сохраняем обновленную информацию
            self._save_job_info(job_info)
            
            # Отправляем уведомление боту
            notification_data = {
                "chat_id": job_info['chat_id'],
                "job_id": job_info['job_id'],
                "status": "timeout",
                "error": job_info['error'],
                "template": job_info['template']
            }
            
            self._send_bot_notification(notification_data)
            
            logger.warning(f"⏰ Job {job_info['job_id']} timed out")
            
        except Exception as e:
            logger.error(f"❌ Error handling job timeout {job_info['job_id']}: {e}")
    
    def _is_job_timeout(self, job_info: Dict[str, Any]) -> bool:
        """Проверяет, не превышено ли время ожидания задачи"""
        try:
            submitted_at = datetime.fromisoformat(job_info['submitted_at'])
            elapsed = (datetime.now() - submitted_at).total_seconds()
            return elapsed > self.max_poll_duration
        except:
            return False
    
    def _should_cleanup_job(self, job_info: Dict[str, Any]) -> bool:
        """Определяет, нужно ли удалить старую задачу"""
        try:
            completed_at = job_info.get('completed_at') or job_info.get('failed_at') or job_info.get('timeout_at')
            if not completed_at:
                return False
            
            completed = datetime.fromisoformat(completed_at)
            elapsed = (datetime.now() - completed).total_seconds()
            return elapsed > self.cleanup_threshold
        except:
            return False
    
    def _cleanup_job(self, job_info: Dict[str, Any]):
        """Удаляет старую задачу и связанные файлы"""
        try:
            job_id = job_info['job_id']
            
            # Удаляем файл задачи
            bucket = self.storage_client.bucket("btibot-processed")
            job_blob = bucket.blob(f"jobs/{job_id}.json")
            if job_blob.exists():
                job_blob.delete()
            
            # Удаляем отчет
            report_blob = bucket.blob(f"reports/{job_id}/report.json")
            if report_blob.exists():
                report_blob.delete()
            
            # Удаляем выходной файл (если есть)
            if 'output_blob' in job_info:
                output_blob = bucket.blob(job_info['output_blob'])
                if output_blob.exists():
                    output_blob.delete()
            
            logger.info(f"🗑️ Cleaned up old job {job_id}")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up job {job_info.get('job_id', 'unknown')}: {e}")
    
    def _cleanup_old_jobs(self) -> int:
        """Очищает старые завершенные задачи"""
        cleaned_count = 0
        
        try:
            bucket = self.storage_client.bucket("btibot-processed")
            job_blobs = list(bucket.list_blobs(prefix="jobs/"))
            
            for blob in job_blobs:
                if not blob.name.endswith('.json'):
                    continue
                
                try:
                    job_info = json.loads(blob.download_as_text())
                    
                    if self._should_cleanup_job(job_info):
                        self._cleanup_job(job_info)
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Error processing job for cleanup {blob.name}: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
        
        return cleaned_count
    
    def _calculate_processing_time(self, job_info: Dict[str, Any]) -> float:
        """Вычисляет время обработки в миллисекундах"""
        try:
            submitted_at = datetime.fromisoformat(job_info['submitted_at'])
            completed_at = datetime.now()
            duration = (completed_at - submitted_at).total_seconds()
            return duration * 1000  # в миллисекундах
        except:
            return 0.0
    
    def _create_success_report(self, job_info: Dict[str, Any], status_result: Dict[str, Any]) -> Dict[str, Any]:
        """Создает отчет об успешном выполнении"""
        return {
            "job_id": job_info['job_id'],
            "workitem_id": job_info['workitem_id'],
            "template": job_info['template'],
            "status": "success",
            "processing_time_ms": self._calculate_processing_time(job_info),
            "input_file": job_info.get('input_blob'),
            "output_file": job_info.get('output_blob'),
            "meta": job_info.get('meta', {}),
            "forge_result": status_result,
            "completed_at": datetime.now().isoformat(),
            "chat_id": job_info.get('chat_id')
        }
    
    def _create_error_report(self, job_info: Dict[str, Any], status_result: Dict[str, Any]) -> Dict[str, Any]:
        """Создает отчет об ошибке"""
        return {
            "job_id": job_info['job_id'],
            "workitem_id": job_info['workitem_id'],
            "template": job_info['template'],
            "status": "failed",
            "processing_time_ms": self._calculate_processing_time(job_info),
            "error": job_info.get('error'),
            "input_file": job_info.get('input_blob'),
            "meta": job_info.get('meta', {}),
            "forge_result": status_result,
            "failed_at": datetime.now().isoformat(),
            "chat_id": job_info.get('chat_id')
        }
    
    def _save_report(self, job_id: str, report: Dict[str, Any]):
        """Сохраняет отчет в GCS"""
        try:
            bucket = self.storage_client.bucket("btibot-processed")
            report_blob = bucket.blob(f"reports/{job_id}/report.json")
            report_blob.upload_from_string(
                json.dumps(report, ensure_ascii=False, indent=2),
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"❌ Error saving report for job {job_id}: {e}")
    
    def _save_job_info(self, job_info: Dict[str, Any]):
        """Сохраняет информацию о задаче в GCS"""
        try:
            bucket = self.storage_client.bucket("btibot-processed")
            job_blob = bucket.blob(f"jobs/{job_info['job_id']}.json")
            job_blob.upload_from_string(
                json.dumps(job_info, ensure_ascii=False, indent=2),
                content_type='application/json'
            )
        except Exception as e:
            logger.error(f"❌ Error saving job info {job_info.get('job_id', 'unknown')}: {e}")
    
    def _send_bot_notification(self, notification_data: Dict[str, Any]):
        """Отправляет уведомление боту через Pub/Sub"""
        try:
            topic_path = self.publisher.topic_path(self.project_id, "bti-jobs-done")
            self.publisher.publish(
                topic_path, 
                json.dumps(notification_data).encode('utf-8')
            )
            logger.info(f"✅ Bot notification sent for job {notification_data['job_id']}")
        except Exception as e:
            logger.error(f"❌ Error sending bot notification: {e}")


# Flask приложение для Cloud Run
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Глобальный экземпляр сервиса
poller_service = ForgePollerService()

@app.route('/forge/poll', methods=['POST'])
def poll_jobs():
    """Эндпоинт для опроса статуса задач (вызывается по cron)"""
    try:
        result = poller_service.poll_all_pending_jobs()
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка polling Forge jobs: {e}")
        return jsonify({
            'error': str(e),
            'status': 'failed'
        }), 500

@app.route('/forge/stats', methods=['GET'])
def get_stats():
    """Возвращает статистику polling сервиса"""
    try:
        return jsonify({
            'stats': poller_service.stats,
            'config': {
                'poll_interval': poller_service.poll_interval,
                'max_poll_duration': poller_service.max_poll_duration,
                'cleanup_threshold': poller_service.cleanup_threshold
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/forge/cleanup', methods=['POST'])
def cleanup_old_jobs():
    """Принудительная очистка старых задач"""
    try:
        cleaned_count = poller_service._cleanup_old_jobs()
        return jsonify({
            'cleaned_jobs': cleaned_count,
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка очистки задач: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'forge-poller',
        'stats': poller_service.stats
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
