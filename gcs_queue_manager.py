"""
GCS Queue Manager
Надежная очередь на базе Google Cloud Storage для обработки DWG файлов
"""

import json
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from google.cloud import storage
from google.cloud.exceptions import NotFound

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GCSQueueManager:
    """
    Менеджер очереди на базе GCS
    Обеспечивает строгую последовательность обработки файлов
    """
    
    def __init__(self, bucket_name: str = "btibot-queue"):
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        
        # Пути в GCS
        self.queue_path = "queue/"
        self.processing_path = "processing/"
        self.done_path = "done/"
        self.lock_file = "processing/lock.json"
        
        logger.info(f"✅ GCS Queue Manager initialized for bucket: {bucket_name}")
    
    def _ensure_bucket_structure(self):
        """Создает структуру папок в bucket если её нет"""
        try:
            # Проверяем существование bucket
            if not self.bucket.exists():
                logger.info(f"📦 Creating bucket: {self.bucket_name}")
                self.bucket = self.client.create_bucket(self.bucket_name)
            
            # Создаем placeholder файлы для папок
            placeholder_files = [
                f"{self.queue_path}.placeholder",
                f"{self.processing_path}.placeholder", 
                f"{self.done_path}.placeholder"
            ]
            
            for file_path in placeholder_files:
                try:
                    blob = self.bucket.blob(file_path)
                    blob.upload_from_string("")
                except Exception as e:
                    logger.warning(f"⚠️ Could not create placeholder {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error ensuring bucket structure: {e}")
    
    def add_job_to_queue(self, job_data: Dict[str, Any]) -> str:
        """
        Добавляет задание в очередь
        
        Args:
            job_data: Данные задания (dwg_path, user_id, job_type, etc.)
            
        Returns:
            job_id: ID созданного задания
        """
        try:
            # Генерируем уникальный ID задания
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
            job_id = f"{timestamp}_job{int(time.time() * 1000)}"
            
            # Создаем JSON с метаданными задания
            job_json = {
                "job_id": job_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "queued",
                "data": job_data
            }
            
            # Сохраняем в /queue/
            queue_file = f"{self.queue_path}{job_id}.json"
            blob = self.bucket.blob(queue_file)
            blob.upload_from_string(json.dumps(job_json, indent=2))
            
            logger.info(f"📝 Job {job_id} added to queue: {queue_file}")
            return job_id
            
        except Exception as e:
            logger.error(f"❌ Error adding job to queue: {e}")
            raise
    
    def get_next_job(self) -> Optional[Dict[str, Any]]:
        """
        Получает следующее задание из очереди
        
        Returns:
            Job data или None если очередь пуста или заблокирована
        """
        try:
            logger.info("🔍 get_next_job() called")
            logger.info("🔍 Checking lock status...")
            # Проверяем lock-файл
            if self._is_processing_locked():
                logger.info("🔒 Processing is locked, skipping queue")
                return None
            
            # Получаем список файлов в очереди
            queue_files = self._list_queue_files()
            if not queue_files:
                logger.info("📭 Queue is empty")
                return None
            
            # Берем самый ранний файл (по имени, которое содержит timestamp)
            queue_files.sort()
            oldest_file = queue_files[0]
            
            # Читаем данные задания
            logger.info(f"📄 Reading job file: {oldest_file}")
            blob = self.bucket.blob(f"{self.queue_path}{oldest_file}")
            job_data = json.loads(blob.download_as_text())
            logger.info(f"📋 Job data loaded: {job_data}")
            
            # Создаем lock-файл
            logger.info(f"🔒 Creating lock for job: {job_data['job_id']}")
            self._create_processing_lock(job_data["job_id"])
            logger.info(f"✅ Lock created successfully")
            
            logger.info(f"🚀 Processing job: {job_data['job_id']}")
            return job_data
            
        except Exception as e:
            logger.error(f"❌ Error getting next job: {e}")
            return None
    
    def finish_job(self, job_id: str, result_data: Optional[Dict[str, Any]] = None):
        """
        Завершает обработку задания
        
        Args:
            job_id: ID завершаемого задания
            result_data: Дополнительные данные результата
        """
        try:
            # Переносим файл из /queue/ в /done/
            queue_file = f"{self.queue_path}{job_id}.json"
            done_file = f"{self.done_path}{job_id}.json"
            
            # Читаем данные задания
            source_blob = self.bucket.blob(queue_file)
            job_data = json.loads(source_blob.download_as_text())
            
            # Обновляем статус
            job_data["status"] = "completed"
            job_data["completed_at"] = datetime.now(timezone.utc).isoformat()
            if result_data:
                job_data["result"] = result_data
            
            # Сохраняем в /done/
            done_blob = self.bucket.blob(done_file)
            done_blob.upload_from_string(json.dumps(job_data, indent=2))
            
            # Безопасно удаляем из /queue/
            self._safe_delete_blob(source_blob)
            
            # Удаляем lock-файл
            self._remove_processing_lock()
            
            logger.info(f"✅ Job {job_id} completed and moved to /done/")
            
        except Exception as e:
            logger.error(f"❌ Error finishing job {job_id}: {e}")
            # В случае ошибки все равно удаляем lock
            self._remove_processing_lock()
    
    def fail_job(self, job_id: str, error_message: str):
        """
        Помечает задание как неудачное
        
        Args:
            job_id: ID неудачного задания
            error_message: Сообщение об ошибке
        """
        try:
            # Переносим файл из /queue/ в /done/ с ошибкой
            queue_file = f"{self.queue_path}{job_id}.json"
            done_file = f"{self.done_path}{job_id}_failed.json"
            
            # Читаем данные задания
            source_blob = self.bucket.blob(queue_file)
            job_data = json.loads(source_blob.download_as_text())
            
            # Обновляем статус
            job_data["status"] = "failed"
            job_data["failed_at"] = datetime.now(timezone.utc).isoformat()
            job_data["error"] = error_message
            
            # Сохраняем в /done/
            done_blob = self.bucket.blob(done_file)
            done_blob.upload_from_string(json.dumps(job_data, indent=2))
            
            # Безопасно удаляем из /queue/
            self._safe_delete_blob(source_blob)
            
            # Удаляем lock-файл
            self._remove_processing_lock()
            
            logger.error(f"❌ Job {job_id} failed: {error_message}")
            
        except Exception as e:
            logger.error(f"❌ Error failing job {job_id}: {e}")
            # В случае ошибки все равно удаляем lock
            self._remove_processing_lock()
    
    def _is_processing_locked(self) -> bool:
        """Проверяет, заблокирована ли обработка"""
        try:
            logger.info(f"🔍 Checking lock file: {self.lock_file}")
            blob = self.bucket.blob(self.lock_file)
            exists = blob.exists()
            logger.info(f"🔍 Lock file exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"❌ Error checking lock: {e}")
            return False
    
    def _create_processing_lock(self, job_id: str):
        """Создает lock-файл"""
        try:
            lock_data = {
                "locked_at": datetime.now(timezone.utc).isoformat(),
                "job_id": job_id,
                "locked_by": "dwg-processor"
            }
            
            blob = self.bucket.blob(self.lock_file)
            blob.upload_from_string(json.dumps(lock_data, indent=2))
            logger.info(f"🔒 Processing locked for job: {job_id}")
            
        except Exception as e:
            logger.error(f"❌ Error creating lock: {e}")
            raise
    
    def _remove_processing_lock(self):
        """Удаляет lock-файл"""
        try:
            blob = self.bucket.blob(self.lock_file)
            if blob.exists():
                blob.delete()
                logger.info("🔓 Processing lock removed")
        except Exception as e:
            logger.error(f"❌ Error removing lock: {e}")
    
    def _safe_delete_blob(self, blob):
        """Безопасно удаляет blob с проверкой существования"""
        try:
            if blob.exists():
                blob.delete()
                logger.info(f"✅ Deleted blob: {blob.name}")
            else:
                logger.warning(f"⚠️ Blob does not exist, skipping deletion: {blob.name}")
        except Exception as e:
            logger.error(f"❌ Error deleting blob {blob.name}: {e}")
    
    def _list_queue_files(self) -> List[str]:
        """Получает список файлов в очереди"""
        try:
            blobs = self.bucket.list_blobs(prefix=self.queue_path)
            files = []
            for blob in blobs:
                if blob.name.endswith('.json') and not blob.name.endswith('.placeholder'):
                    # Извлекаем имя файла без пути
                    filename = blob.name.replace(self.queue_path, '')
                    files.append(filename)
            return files
        except Exception as e:
            logger.error(f"❌ Error listing queue files: {e}")
            return []
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Возвращает статус очереди"""
        try:
            queue_files = self._list_queue_files()
            is_locked = self._is_processing_locked()
            
            return {
                "queue_size": len(queue_files),
                "is_processing": is_locked,
                "queue_files": queue_files[:10],  # Первые 10 файлов
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Error getting queue status: {e}")
            return {
                "queue_size": 0,
                "is_processing": False,
                "error": str(e)
            }
