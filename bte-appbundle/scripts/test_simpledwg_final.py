#!/usr/bin/env python3
"""
Финальный тест SimpleDWG2DWG_NoTemplate+v1 на файле Басманной
С правильными параметрами из документации
"""

import os
import sys
import time
import json
import requests
from datetime import datetime, timedelta
from google.cloud import storage
from google.oauth2 import service_account

# APS Configuration
APS_CLIENT_ID = os.getenv('APS_CLIENT_ID', 'm6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4')
APS_CLIENT_SECRET = os.getenv('APS_CLIENT_SECRET', 'tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW')
APS_BASE_URL = "https://developer.api.autodesk.com"

DWG_FILE = "bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg"
SERVICE_ACCOUNT_KEY = "bte-appbundle/dwg-processor-sa-key.json"

def get_token():
    url = f"{APS_BASE_URL}/authentication/v2/token"
    data = {
        "client_id": APS_CLIENT_ID,
        "client_secret": APS_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return response.json()['access_token']

def generate_signed_url(gcs_path, method="GET"):
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY)
    storage_client = storage.Client(credentials=credentials)
    
    bucket_name = gcs_path.replace('gs://', '').split('/')[0]
    blob_name = '/'.join(gcs_path.replace('gs://', '').split('/')[1:])
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method=method,
        content_type="application/octet-stream" if method == "PUT" else None
    )

def main():
    print("=" * 80)
    print("🎯 ФИНАЛЬНЫЙ ТЕСТ: SimpleDWG2DWG_NoTemplate+v1")
    print("=" * 80)
    print()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    gcs_input = f"gs://btibot-queue/test_input/basmannyi_final_{timestamp}.dwg"
    gcs_output = f"gs://btibot-processed/test_output/basmannyi_result_final_{timestamp}.dwg"
    
    # Загрузка
    print(f"📂 Загрузка DWG в GCS...")
    os.system(f'gcloud storage cp "{DWG_FILE}" "{gcs_input}"')
    
    # Signed URLs
    print(f"\n🔗 Генерация signed URLs...")
    input_url = generate_signed_url(gcs_input, "GET")
    output_url = generate_signed_url(gcs_output, "PUT")
    print(f"✅ URLs готовы\n")
    
    # Токен
    print(f"🔑 Получение токена...")
    token = get_token()
    print(f"✅ Токен получен\n")
    
    # WorkItem с правильными параметрами
    # Используем verb: "post" из документации для выходного файла
    payload = {
        "activityId": "BotBti.SimpleDWG2DWG_NoTemplate+v1",
        "arguments": {
            "inputFile": {
                "url": input_url
            },
            "resultFile": {
                "url": output_url,
                "verb": "post"  # Согласно официальной документации!
            }
        }
    }
    
    print(f"🚀 Создание WorkItem...")
    print(f"Activity: BotBti.SimpleDWG2DWG_NoTemplate+v1")
    print(f"Parameters: inputFile, resultFile")
    print(f"Output verb: post ← Из документации\n")
    print(f"Payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{APS_BASE_URL}/da/us-east/v3/workitems", headers=headers, json=payload)
    
    if response.status_code not in [200, 201]:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    workitem = response.json()
    workitem_id = workitem['id']
    
    print(f"✅ WorkItem создан: {workitem_id}")
    print(f"   Статус: {workitem.get('status')}\n")
    
    # Ожидание завершения
    print(f"⏳ Ожидание завершения (max 5 минут)...")
    
    start_time = time.time()
    while time.time() - start_time < 300:
        resp = requests.get(f"{APS_BASE_URL}/da/us-east/v3/workitems/{workitem_id}", headers=headers)
        
        if resp.status_code != 200:
            time.sleep(5)
            continue
        
        data = resp.json()
        status = data.get('status')
        elapsed = int(time.time() - start_time)
        
        print(f"   [{elapsed}s] Статус: {status}")
        
        if status == 'success':
            print(f"\n🎉 УСПЕХ!")
            
            # Сохранить результат
            result_file = f"bte-appbundle/reports/simpledwg_success_{timestamp}.json"
            with open(result_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Скачать отчёт
            if 'reportUrl' in data:
                report_resp = requests.get(data['reportUrl'])
                if report_resp.status_code == 200:
                    report_file = f"bte-appbundle/reports/simpledwg_report_{timestamp}.log"
                    with open(report_file, 'w') as f:
                        f.write(report_resp.text)
                    
                    print(f"\n📋 Отчёт:")
                    print("=" * 80)
                    print(report_resp.text)
                    print("=" * 80)
            
            print(f"\n📁 Результат сохранён в GCS:")
            print(f"   {gcs_output}")
            
            # Проверка файла
            check = os.popen(f'gcloud storage ls -l "{gcs_output}" 2>&1').read()
            if 'TOTAL' in check:
                print(f"\n✅ Файл найден в GCS!")
                for line in check.split('\n'):
                    if '.dwg' in line:
                        print(f"   {line.strip()}")
            
            sys.exit(0)
        
        elif status in ['failedInstructions', 'failedDownload', 'failedUpload', 'failed', 'cancelled']:
            print(f"\n❌ WorkItem завершился с ошибкой: {status}")
            
            if 'reportUrl' in data:
                report_resp = requests.get(data['reportUrl'])
                if report_resp.status_code == 200:
                    print(f"\n📋 Отчёт ошибки:")
                    print(report_resp.text[:1000])
            
            sys.exit(1)
        
        time.sleep(5)
    
    print(f"\n⏰ Timeout")
    sys.exit(1)

if __name__ == "__main__":
    main()

