"""
Скрипт для проверки загруженного эталонного шаблона через Forge API
"""

import json
import requests
import logging
from datetime import datetime, timedelta
from google.cloud import storage, secretmanager
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemplateVerifier:
    """Класс для проверки шаблона через Forge API"""
    
    def __init__(self, project_id: str = "talkhint"):
        self.project_id = project_id
        self.storage_client = storage.Client()
        self.secret_client = secretmanager.SecretManagerServiceClient()
        
        # Forge API URLs
        self.auth_url = "https://developer.api.autodesk.com/authentication/v1/authenticate"
        self.oss_url = "https://developer.api.autodesk.com/oss/v2"
        self.model_derivative_url = "https://developer.api.autodesk.com/modelderivative/v2"
        
        # Template info
        self.bucket_name = "btibot-processed"
        self.template_path = "templates/basmanoe-bti.dwg"
        
        # Cache
        self._access_token = None
        self._token_expires = None
    
    def get_access_token(self) -> str:
        """Получает access token для Forge API"""
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
    
    def check_template_exists(self) -> Dict[str, Any]:
        """Проверяет существование шаблона в GCS"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(self.template_path)
            
            if not blob.exists():
                return {
                    'exists': False,
                    'error': f'Template not found: gs://{self.bucket_name}/{self.template_path}'
                }
            
            # Получаем метаданные
            blob.reload()
            metadata = blob.metadata or {}
            
            return {
                'exists': True,
                'path': f"gs://{self.bucket_name}/{self.template_path}",
                'size_bytes': blob.size,
                'size_mb': blob.size / 1024 / 1024,
                'created': blob.time_created.isoformat(),
                'updated': blob.updated.isoformat(),
                'metadata': metadata,
                'content_type': blob.content_type
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки шаблона в GCS: {e}")
            return {'exists': False, 'error': str(e)}
    
    def create_signed_url(self, expiration_hours: int = 2) -> Optional[str]:
        """Создает signed URL для шаблона"""
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(self.template_path)
            
            if not blob.exists():
                logger.error(f"❌ Template not found: {self.template_path}")
                return None
            
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.now() + timedelta(hours=expiration_hours),
                method="GET"
            )
            
            logger.info(f"✅ Signed URL created for template")
            return signed_url
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания signed URL: {e}")
            return None
    
    def upload_to_forge_oss(self) -> Dict[str, Any]:
        """Загружает шаблон в Forge Object Storage Service"""
        try:
            access_token = self.get_access_token()
            
            # Создаем bucket в Forge OSS (если не существует)
            bucket_key = f"bti-templates-{self.project_id}".lower()
            self._create_forge_bucket(bucket_key)
            
            # Создаем signed URL для загрузки
            upload_url = self._create_upload_url(bucket_key, "basmanoe-bti.dwg")
            
            # Получаем содержимое файла из GCS
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(self.template_path)
            file_content = blob.download_as_bytes()
            
            # Загружаем в Forge OSS
            upload_response = requests.put(upload_url, data=file_content)
            
            if upload_response.status_code in [200, 201]:
                # Получаем URN для файла
                object_id = self._get_object_id(bucket_key, "basmanoe-bti.dwg")
                base64_urn = self._encode_urn(object_id)
                
                logger.info(f"✅ Template uploaded to Forge OSS: {object_id}")
                
                return {
                    'success': True,
                    'object_id': object_id,
                    'base64_urn': base64_urn,
                    'bucket_key': bucket_key,
                    'filename': 'basmanoe-bti.dwg'
                }
            else:
                logger.error(f"❌ Upload to Forge OSS failed: {upload_response.status_code} - {upload_response.text}")
                return {
                    'success': False,
                    'error': f'Upload failed: {upload_response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки в Forge OSS: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_forge_bucket(self, bucket_key: str):
        """Создает bucket в Forge OSS"""
        try:
            access_token = self.get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'bucketKey': bucket_key,
                'policyKey': 'transient'  # временное хранилище
            }
            
            response = requests.post(
                f"{self.oss_url}/buckets",
                json=data,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Forge bucket created/verified: {bucket_key}")
            elif response.status_code == 409:
                logger.info(f"ℹ️ Forge bucket already exists: {bucket_key}")
            else:
                logger.warning(f"⚠️ Unexpected response creating bucket: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания Forge bucket: {e}")
    
    def _create_upload_url(self, bucket_key: str, filename: str) -> str:
        """Создает URL для загрузки файла в Forge OSS"""
        try:
            access_token = self.get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'bucketKey': bucket_key,
                'objectName': filename,
                'access': 'full'
            }
            
            response = requests.post(
                f"{self.oss_url}/buckets/{bucket_key}/objects/{filename}/signed",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()['signedUrl']
            else:
                raise Exception(f"Failed to create upload URL: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания upload URL: {e}")
            raise
    
    def _get_object_id(self, bucket_key: str, filename: str) -> str:
        """Получает object ID файла в Forge OSS"""
        try:
            access_token = self.get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            response = requests.get(
                f"{self.oss_url}/buckets/{bucket_key}/objects/{filename}/details",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()['objectId']
            else:
                raise Exception(f"Failed to get object ID: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения object ID: {e}")
            raise
    
    def _encode_urn(self, object_id: str) -> str:
        """Кодирует object ID в base64 URN"""
        import base64
        urn = f"urn:adsk.objects:os.object:{object_id}"
        return base64.b64encode(urn.encode()).decode()
    
    def test_forge_processing(self, base64_urn: str) -> Dict[str, Any]:
        """Тестирует обработку файла через Forge API"""
        try:
            access_token = self.get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Запускаем job для получения информации о файле
            data = {
                'input': {
                    'urn': base64_urn
                },
                'output': {
                    'formats': [
                        {
                            'type': 'svf',
                            'views': ['2d', '3d']
                        }
                    ]
                }
            }
            
            response = requests.post(
                f"{self.model_derivative_url}/designdata/job",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                job_data = response.json()
                logger.info(f"✅ Forge processing job started: {job_data.get('result')}")
                
                return {
                    'success': True,
                    'job_id': job_data.get('result'),
                    'status': 'processing_started',
                    'message': 'File is being processed by Forge API'
                }
            else:
                logger.error(f"❌ Forge processing failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Processing failed: {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования Forge processing: {e}")
            return {'success': False, 'error': str(e)}
    
    def verify_template_complete(self) -> Dict[str, Any]:
        """Полная проверка шаблона"""
        logger.info("🔍 Начинаем полную проверку шаблона...")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'template_path': f"gs://{self.bucket_name}/{self.template_path}",
            'checks': {}
        }
        
        # 1. Проверка существования в GCS
        logger.info("1️⃣ Проверка существования в GCS...")
        gcs_check = self.check_template_exists()
        result['checks']['gcs_exists'] = gcs_check
        
        if not gcs_check['exists']:
            result['overall_success'] = False
            result['error'] = 'Template not found in GCS'
            return result
        
        # 2. Создание signed URL
        logger.info("2️⃣ Создание signed URL...")
        signed_url = self.create_signed_url()
        result['checks']['signed_url'] = {
            'success': signed_url is not None,
            'url': signed_url
        }
        
        if not signed_url:
            result['overall_success'] = False
            result['error'] = 'Failed to create signed URL'
            return result
        
        # 3. Загрузка в Forge OSS
        logger.info("3️⃣ Загрузка в Forge OSS...")
        oss_upload = self.upload_to_forge_oss()
        result['checks']['oss_upload'] = oss_upload
        
        if not oss_upload['success']:
            result['overall_success'] = False
            result['error'] = f"Failed to upload to Forge OSS: {oss_upload['error']}"
            return result
        
        # 4. Тестирование обработки
        logger.info("4️⃣ Тестирование обработки через Forge API...")
        processing_test = self.test_forge_processing(oss_upload['base64_urn'])
        result['checks']['forge_processing'] = processing_test
        
        if not processing_test['success']:
            result['overall_success'] = False
            result['error'] = f"Forge processing failed: {processing_test['error']}"
            return result
        
        # Все проверки пройдены
        result['overall_success'] = True
        result['message'] = 'Template is ready for use in BTI Processor'
        
        logger.info("✅ Все проверки пройдены успешно!")
        return result


def main():
    """Основная функция для проверки шаблона"""
    try:
        verifier = TemplateVerifier()
        
        print("🔍 Проверка эталонного шаблона БТИ...")
        print("=" * 50)
        
        result = verifier.verify_template_complete()
        
        print("\n📋 Результаты проверки:")
        print("=" * 50)
        
        if result['overall_success']:
            print("✅ Шаблон готов к использованию!")
            print(f"📍 Путь: {result['template_path']}")
            print(f"📊 Размер: {result['checks']['gcs_exists']['size_mb']:.2f} MB")
            print(f"🏷️ Метаданные: {result['checks']['gcs_exists']['metadata']}")
            print(f"🔗 Forge URN: {result['checks']['oss_upload']['base64_urn']}")
        else:
            print("❌ Обнаружены проблемы:")
            print(f"🚨 {result['error']}")
        
        print("\n📊 Детальные результаты:")
        for check_name, check_result in result['checks'].items():
            status = "✅" if check_result.get('success', False) else "❌"
            print(f"{status} {check_name}: {check_result}")
        
        # Сохраняем результаты в файл
        with open('template_verification_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Результаты сохранены в: template_verification_result.json")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        print(f"❌ Ошибка: {e}")


if __name__ == '__main__':
    main()
