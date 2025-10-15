#!/usr/bin/env python3
"""
AppBundle WorkItem Test Script
Автоматическое тестирование WorkItem на Autodesk APS
"""

import os
import sys
import time
import json
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from google.cloud import storage
from google.oauth2 import service_account

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# APS credentials
APS_CLIENT_ID = os.getenv('APS_CLIENT_ID', 'm6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4')
APS_CLIENT_SECRET = os.getenv('APS_CLIENT_SECRET', 'tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW')
APS_BASE_URL = "https://developer.api.autodesk.com"


class APSClient:
    """Клиент для работы с Autodesk APS API"""
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = 0
        
    def get_access_token(self):
        """Получить токен доступа"""
        # Проверяем, не истёк ли токен
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
            
        url = f"{APS_BASE_URL}/authentication/v2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "code:all data:write data:read bucket:create bucket:read"
        }
        
        print("🔑 Получение токена доступа APS...")
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code != 200:
            print(f"❌ Ошибка получения токена: {response.status_code}")
            print(response.text)
            sys.exit(1)
            
        token_data = response.json()
        self.access_token = token_data['access_token']
        # Сохраняем время истечения с запасом в 5 минут
        self.token_expires_at = time.time() + token_data['expires_in'] - 300
        
        print(f"✅ Токен получен (expires in {token_data['expires_in']}s)")
        return self.access_token
    
    def create_workitem(self, payload):
        """Создать WorkItem"""
        token = self.get_access_token()
        url = f"{APS_BASE_URL}/da/us-east/v3/workitems"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("🚀 Создание WorkItem...")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code not in [200, 201]:
            print(f"❌ Ошибка создания WorkItem: {response.status_code}")
            print(response.text)
            sys.exit(1)
            
        workitem = response.json()
        print(f"✅ WorkItem создан: {workitem['id']}")
        print(f"📊 Статус: {workitem['status']}")
        
        return workitem
    
    def get_workitem_status(self, workitem_id):
        """Получить статус WorkItem"""
        token = self.get_access_token()
        url = f"{APS_BASE_URL}/da/us-east/v3/workitems/{workitem_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Ошибка получения статуса: {response.status_code}")
            return None
            
        return response.json()
    
    def wait_for_completion(self, workitem_id, timeout=300, poll_interval=5):
        """Ожидание завершения WorkItem"""
        print(f"⏳ Ожидание завершения WorkItem (timeout: {timeout}s)...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            status_data = self.get_workitem_status(workitem_id)
            
            if not status_data:
                time.sleep(poll_interval)
                continue
                
            status = status_data['status']
            print(f"📊 Статус: {status} (прошло {int(time.time() - start_time)}s)")
            
            if status == 'success':
                print("✅ WorkItem успешно выполнен!")
                return status_data
            elif status == 'failedInstructions':
                print("❌ WorkItem завершился с ошибкой (failedInstructions)")
                return status_data
            elif status == 'failedDownload':
                print("❌ WorkItem завершился с ошибкой (failedDownload)")
                return status_data
            elif status == 'failedUpload':
                print("❌ WorkItem завершился с ошибкой (failedUpload)")
                return status_data
            elif status in ['cancelled', 'failed']:
                print(f"❌ WorkItem завершился с ошибкой: {status}")
                return status_data
                
            time.sleep(poll_interval)
        
        print(f"⏰ Timeout ({timeout}s) - WorkItem не завершился")
        return self.get_workitem_status(workitem_id)
    
    def download_report(self, report_url, output_path):
        """Скачать отчёт WorkItem"""
        print(f"📥 Скачивание отчёта...")
        
        response = requests.get(report_url)
        
        if response.status_code != 200:
            print(f"❌ Ошибка скачивания отчёта: {response.status_code}")
            return False
            
        # Создаём директорию, если не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        print(f"✅ Отчёт сохранён: {output_path}")
        return True


def generate_signed_urls(input_file, output_file):
    """Генерация signed URLs для входного и выходного файлов используя Python API"""
    print("🔗 Генерация signed URLs...")
    
    try:
        # Попробуем использовать service account key если есть
        service_account_key_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'dwg-processor-sa-key.json'
        )
        
        if os.path.exists(service_account_key_path):
            print(f"🔑 Использование service account key: {service_account_key_path}")
            credentials = service_account.Credentials.from_service_account_file(
                service_account_key_path
            )
            storage_client = storage.Client(credentials=credentials)
        else:
            # Инициализируем клиент GCS с Application Default Credentials
            storage_client = storage.Client()
        
        # Парсим GCS пути
        # Формат: gs://bucket-name/path/to/file
        input_bucket_name = input_file.replace('gs://', '').split('/')[0]
        input_blob_name = '/'.join(input_file.replace('gs://', '').split('/')[1:])
        
        output_bucket_name = output_file.replace('gs://', '').split('/')[0]
        output_blob_name = '/'.join(output_file.replace('gs://', '').split('/')[1:])
        
        # Получаем bucket и blob для входного файла
        input_bucket = storage_client.bucket(input_bucket_name)
        input_blob = input_bucket.blob(input_blob_name)
        
        # Получаем bucket и blob для выходного файла
        output_bucket = storage_client.bucket(output_bucket_name)
        output_blob = output_bucket.blob(output_blob_name)
        
        # Генерируем signed URL для входного файла (GET, 1 час)
        input_url = input_blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="GET"
        )
        
        # Генерируем signed URL для выходного файла (PUT, 1 час)
        output_url = output_blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="PUT",
            content_type="application/octet-stream"
        )
        
        print(f"✅ Input URL: {input_url[:80]}...")
        print(f"✅ Output URL: {output_url[:80]}...")
        
        return input_url, output_url
        
    except Exception as e:
        print(f"❌ Ошибка при генерации signed URLs: {e}")
        print("\n💡 Попытка использовать gcloud impersonate...")
        
        # Fallback: используем gcloud с impersonate
        service_account_email = "dwg-processor-sa@talkhint.iam.gserviceaccount.com"
        
        input_result = os.popen(
            f'gcloud storage sign-url "{input_file}" --duration=1h '
            f'--impersonate-service-account={service_account_email} 2>&1'
        ).read()
        
        output_result = os.popen(
            f'gcloud storage sign-url "{output_file}" --duration=1h --http-verb=PUT '
            f'--impersonate-service-account={service_account_email} 2>&1'
        ).read()
        
        # Извлекаем URL из результата
        input_url = None
        output_url = None
        
        for line in input_result.split('\n'):
            if 'https://storage.googleapis.com' in line:
                input_url = line.strip()
                break
        
        for line in output_result.split('\n'):
            if 'https://storage.googleapis.com' in line:
                output_url = line.strip()
                break
        
        if not input_url or not output_url:
            print("❌ Не удалось сгенерировать signed URLs")
            print("Input result:", input_result)
            print("Output result:", output_result)
            sys.exit(1)
        
        print(f"✅ Input URL (impersonate): {input_url[:80]}...")
        print(f"✅ Output URL (impersonate): {output_url[:80]}...")
        
        return input_url, output_url


def create_zip_archive(dwg_file, zip_file):
    """Создание ZIP архива с DWG файлом"""
    import zipfile
    
    print(f"📦 Создание ZIP архива: {zip_file}")
    
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Добавляем DWG файл
        zipf.write(dwg_file, os.path.basename(dwg_file))
        
        # Добавляем manifest
        manifest_content = f"Basmannyi DWG test package for AppBundle\nCreated: {datetime.now().isoformat()}\n"
        zipf.writestr("manifest.txt", manifest_content)
    
    print(f"✅ ZIP архив создан: {os.path.getsize(zip_file)} bytes")
    return zip_file


def upload_to_gcs(local_file, gcs_path):
    """Загрузка файла в GCS"""
    print(f"☁️  Загрузка в GCS: {gcs_path}")
    
    result = os.popen(f'gcloud storage cp "{local_file}" "{gcs_path}" 2>&1').read()
    
    if 'ERROR' in result or 'error' in result.lower():
        print(f"❌ Ошибка загрузки: {result}")
        return False
    
    print(f"✅ Файл загружен в GCS")
    return True


def main():
    parser = argparse.ArgumentParser(description='Test AppBundle WorkItem')
    parser.add_argument('--dwg', help='Path to DWG file', default='bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg')
    parser.add_argument('--activity', help='Activity ID', default='BotBti.BTEInsertActivity+1')
    parser.add_argument('--output-dir', help='Output directory', default='bte-appbundle/reports')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🧩 AppBundle WorkItem Test")
    print("=" * 80)
    
    # Проверяем наличие DWG файла
    if not os.path.exists(args.dwg):
        print(f"❌ DWG файл не найден: {args.dwg}")
        sys.exit(1)
    
    print(f"📂 DWG файл: {args.dwg} ({os.path.getsize(args.dwg)} bytes)")
    
    # Создаём ZIP архив
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_file = f"bte-appbundle/archives/basmannyi_test_{timestamp}.zip"
    create_zip_archive(args.dwg, zip_file)
    
    # Загружаем в GCS
    gcs_input_path = f"gs://btibot-queue/test_input/basmannyi_test_{timestamp}.zip"
    if not upload_to_gcs(zip_file, gcs_input_path):
        sys.exit(1)
    
    # Генерируем signed URLs
    gcs_output_path = f"gs://btibot-processed/test_output/basmannyi_result_{timestamp}.dwg"
    input_url, output_url = generate_signed_urls(gcs_input_path, gcs_output_path)
    
    # Создаём WorkItem payload с правильными параметрами для разных Activities
    if "AutoCAD.PlotToPDF" in args.activity:
        # Стандартная Activity использует HostDwg и Result
        arguments = {
            "HostDwg": {
                "url": input_url,
                "verb": "get"
            },
            "Result": {
                "url": output_url,
                "verb": "put"
            }
        }
    elif "SimpleDWG2DWG" in args.activity or "BTI_DWG2DWG" in args.activity:
        # Кастомные Activities используют inputFile и resultFile
        arguments = {
            "inputFile": {
                "url": input_url
            },
            "resultFile": {
                "url": output_url,
                "verb": "put"
            }
        }
    else:
        # Для других Activities используем HostDWG и ResultDWG (legacy)
        arguments = {
            "HostDWG": {
                "url": input_url,
                "verb": "get"
            },
            "ResultDWG": {
                "url": output_url,
                "verb": "put"
            }
        }
    
    payload = {
        "activityId": args.activity,
        "arguments": arguments
    }
    
    # Сохраняем payload в файл
    payload_file = f"bte-appbundle/workitems/workitem_basmannyi_{timestamp}.json"
    os.makedirs(os.path.dirname(payload_file), exist_ok=True)
    with open(payload_file, 'w') as f:
        json.dump(payload, f, indent=2)
    print(f"📝 WorkItem payload сохранён: {payload_file}")
    
    # Создаём APS клиент
    client = APSClient(APS_CLIENT_ID, APS_CLIENT_SECRET)
    
    # Создаём WorkItem
    workitem = client.create_workitem(payload)
    workitem_id = workitem['id']
    
    # Ждём завершения
    result = client.wait_for_completion(workitem_id, timeout=300, poll_interval=5)
    
    if not result:
        print("❌ Не удалось получить результат WorkItem")
        sys.exit(1)
    
    # Сохраняем полный результат
    result_file = f"{args.output_dir}/workitem_result_{timestamp}.json"
    os.makedirs(args.output_dir, exist_ok=True)
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"📝 Результат WorkItem сохранён: {result_file}")
    
    # Скачиваем отчёт, если есть
    if 'reportUrl' in result:
        report_file = f"{args.output_dir}/basmannyi_report_{timestamp}.log"
        client.download_report(result['reportUrl'], report_file)
        
        # Сохраняем путь к отчёту в переменную окружения
        os.environ['LATEST_REPORT'] = report_file
        
        print("\n" + "=" * 80)
        print("📋 Отчёт WorkItem:")
        print("=" * 80)
        with open(report_file, 'r') as f:
            print(f.read())
        print("=" * 80)
    
    # Итоговый статус
    print("\n" + "=" * 80)
    print(f"🎯 ИТОГОВЫЙ СТАТУС: {result['status']}")
    print("=" * 80)
    
    if result['status'] == 'success':
        print("✅ ТЕСТ УСПЕШНО ЗАВЕРШЁН!")
        print(f"📁 Результат: {gcs_output_path}")
        
        # Проверяем наличие результата в GCS
        check_result = os.popen(f'gcloud storage ls -l "{gcs_output_path}" 2>&1').read()
        if 'TOTAL' in check_result:
            print("✅ Файл результата найден в GCS")
            for line in check_result.split('\n'):
                if gcs_output_path.split('/')[-1] in line:
                    print(f"   {line.strip()}")
        
        sys.exit(0)
    else:
        print(f"❌ ТЕСТ ЗАВЕРШИЛСЯ С ОШИБКОЙ: {result['status']}")
        if 'stats' in result:
            print(f"📊 Stats: {json.dumps(result['stats'], indent=2)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

