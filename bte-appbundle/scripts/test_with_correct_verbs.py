#!/usr/bin/env python3
"""
Тест BTEInsertTemplate с правильными verb из официальной документации
verb: "post" для выходных файлов (не "put"!)
"""

import os
import sys
import time
import json
import requests
from datetime import datetime, timedelta
from google.cloud import storage
from google.oauth2 import service_account

# APS credentials
APS_CLIENT_ID = os.getenv('APS_CLIENT_ID', 'm6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4')
APS_CLIENT_SECRET = os.getenv('APS_CLIENT_SECRET', 'tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW')
APS_BASE_URL = "https://developer.api.autodesk.com"

DWG_FILE = "bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg"
SERVICE_ACCOUNT_KEY = "bte-appbundle/dwg-processor-sa-key.json"

def get_access_token():
    """Получить APS токен"""
    url = f"{APS_BASE_URL}/authentication/v2/token"
    data = {
        "client_id": APS_CLIENT_ID,
        "client_secret": APS_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all data:write data:read"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return response.json()['access_token']

def generate_signed_url(gcs_path, method="GET"):
    """Генерация signed URL"""
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY)
    storage_client = storage.Client(credentials=credentials)
    
    bucket_name = gcs_path.replace('gs://', '').split('/')[0]
    blob_name = '/'.join(gcs_path.replace('gs://', '').split('/')[1:])
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method=method,
        content_type="application/octet-stream" if method == "PUT" else None
    )
    
    return url

def create_workitem_with_post_verb(token, activity_id, input_url, output_url):
    """Создать WorkItem с правильным verb: "post" """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # ПРАВИЛЬНЫЙ формат согласно документации:
    # verb: "post" для выходных файлов, а не "put"!
    payload = {
        "activityId": activity_id,
        "arguments": {
            "inputFile": {
                "url": input_url,
                "verb": "get"
            },
            "result": {
                "url": output_url,
                "verb": "post"  # ← КЛЮЧЕВОЕ ИЗМЕНЕНИЕ!
            }
        }
    }
    
    print(f"📋 Payload (с verb: post):")
    print(json.dumps(payload, indent=2))
    print()
    
    response = requests.post(f"{APS_BASE_URL}/da/us-east/v3/workitems", headers=headers, json=payload)
    
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)
        return None

def wait_for_completion(token, workitem_id, timeout=300):
    """Ожидание завершения"""
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(f"{APS_BASE_URL}/da/us-east/v3/workitems/{workitem_id}", headers=headers)
        
        if response.status_code != 200:
            time.sleep(5)
            continue
        
        data = response.json()
        status = data.get('status')
        elapsed = int(time.time() - start_time)
        
        print(f"📊 [{elapsed}s] Статус: {status}")
        
        if status in ['success', 'failedInstructions', 'failedDownload', 'failedUpload', 'failed', 'cancelled']:
            return data
        
        time.sleep(5)
    
    return None

def download_report(report_url, output_file):
    """Скачать отчёт"""
    response = requests.get(report_url)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        return True
    return False

def main():
    print("=" * 80)
    print("🧪 Тест с правильным verb: 'post' (из документации)")
    print("=" * 80)
    
    # Подготовка
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    gcs_input_path = f"gs://btibot-queue/test_input/basmannyi_{timestamp}.dwg"
    gcs_output_path = f"gs://btibot-processed/test_output/basmannyi_result_{timestamp}.dwg"
    
    print(f"\n📂 Загрузка DWG...")
    os.system(f'gcloud storage cp "{DWG_FILE}" "{gcs_input_path}"')
    
    print(f"\n🔗 Генерация signed URLs...")
    input_url = generate_signed_url(gcs_input_path, "GET")
    output_url = generate_signed_url(gcs_output_path, "PUT")
    print(f"✅ URLs готовы")
    
    print(f"\n🔑 Получение токена...")
    token = get_access_token()
    print(f"✅ Токен получен")
    
    # Тест с разными вариантами Activity ID и параметров
    test_variants = [
        {
            "activity": "BotBti.BTEInsertTemplate+v1",
            "args": {"inputFile": {"url": input_url, "verb": "get"}, "result": {"url": output_url, "verb": "post"}}
        },
        {
            "activity": "BotBti.BTEInsertTemplate+v1",
            "args": {"HostDwg": {"url": input_url, "verb": "get"}, "Result": {"url": output_url, "verb": "post"}}
        },
        {
            "activity": "BotBti.BTEInsertTemplate+v1",
            "args": {"inputFile": {"url": input_url}, "resultFile": {"url": output_url, "verb": "post"}}
        }
    ]
    
    print(f"\n🚀 Тестирование вариантов...")
    
    for i, variant in enumerate(test_variants, 1):
        print(f"\n━━━ Вариант {i}/{len(test_variants)} ━━━")
        print(f"Activity: {variant['activity']}")
        print(f"Arguments: {list(variant['args'].keys())}")
        
        payload = {
            "activityId": variant['activity'],
            "arguments": variant['args']
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(f"{APS_BASE_URL}/da/us-east/v3/workitems", headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            workitem = response.json()
            print(f"✅ WorkItem создан: {workitem['id']}")
            
            # Ожидание завершения
            result = wait_for_completion(token, workitem['id'], timeout=300)
            
            if result:
                # Сохранение результата
                result_file = f"bte-appbundle/reports/test_variant_{i}_{timestamp}.json"
                with open(result_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                # Скачивание отчёта
                if 'reportUrl' in result:
                    report_file = f"bte-appbundle/reports/report_variant_{i}_{timestamp}.log"
                    if download_report(result['reportUrl'], report_file):
                        print(f"\n📥 Отчёт сохранён: {report_file}")
                        
                        # Показать отчёт
                        with open(report_file, 'r') as f:
                            report = f.read()
                            if 'INSERTBTE' in report or 'Success' in report:
                                print(f"\n🎉 УСПЕХ! Найдена команда INSERTBTE!")
                                print(f"\n📋 Отчёт:")
                                print(report[:500])
                                
                                print(f"\n✅ РАБОЧАЯ КОМБИНАЦИЯ:")
                                print(f"   Activity: {variant['activity']}")
                                print(f"   Arguments: {list(variant['args'].keys())}")
                                
                                sys.exit(0)
                
                print(f"\n📊 Статус: {result.get('status')}")
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
    
    print(f"\n⚠️  Ни один вариант не сработал")
    sys.exit(1)

if __name__ == "__main__":
    main()

