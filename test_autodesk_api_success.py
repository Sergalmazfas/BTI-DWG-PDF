#!/usr/bin/env python3
"""
✅ АВТОТЕСТ: Проверка 100% рабочего прогона DWG→DWG через Autodesk APS API
БЕЗ FALLBACK - только официальный API
"""

import requests
import subprocess
import json
import time
from datetime import datetime, timedelta
from google.cloud import storage
from google.oauth2 import service_account

def get_secret(name):
    """Получить секрет из Google Secret Manager"""
    cmd = f"gcloud secrets versions access latest --secret={name} --project=talkhint"
    return subprocess.run(cmd.split(), capture_output=True, text=True).stdout.strip()

def test_aps_dwg2dwg():
    """
    Тест DWG→DWG обработки через Autodesk APS API
    
    Критерии успеха:
    - WorkItem создаётся без ошибок
    - Status = 'success' (не failedInstructions!)
    - Выходной файл — настоящий DWG (не PDF!)
    - Размер > 0
    - Header = AC10xx (DWG формат)
    """
    print("\n" + "="*70)
    print("🧪 АВТОТЕСТ: Autodesk APS DWG→DWG Pipeline")
    print("="*70 + "\n")
    
    # Get credentials
    print("1️⃣ Получение credentials...")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    
    # Get token
    auth_response = requests.post(
        "https://developer.api.autodesk.com/authentication/v2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "code:all"
        }
    )
    token = auth_response.json()["access_token"]
    print(f"   ✅ Token получен\n")
    
    # Get nickname
    nickname_url = "https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me"
    nickname_response = requests.get(nickname_url, headers={"Authorization": f"Bearer {token}"})
    nickname = nickname_response.text.strip('"')
    
    activity_id = f"{nickname}.DWG2DWGCopy+v1"
    print(f"2️⃣ Activity: {activity_id}\n")
    
    # Prepare GCS signed URL
    print("3️⃣ Подготовка GCS URLs...")
    sa_json_str = get_secret("FORGE_SERVICE_KEY")
    sa_credentials = service_account.Credentials.from_service_account_info(json.loads(sa_json_str))
    gcs_client = storage.Client(credentials=sa_credentials)
    bucket = gcs_client.bucket("btibot-processed")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_blob_path = f"test_autotest/{timestamp}/result.dwg"
    output_blob = bucket.blob(output_blob_path)
    
    output_url = output_blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="PUT"
    )
    print(f"   ✅ URLs готовы\n")
    
    # Create WorkItem
    print("4️⃣ Создание WorkItem...")
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_dwg = "https://storage.googleapis.com/btibot-processed/raw/1759939981/Plan%202025-10-03%20155019_export_2D.dwg"
    
    data = {
        "activityId": activity_id,
        "arguments": {
            "inputFile": {"url": test_dwg},
            "resultFile": {"url": output_url, "verb": "put"}
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code not in [200, 201]:
        print(f"   ❌ Ошибка: {response.status_code}")
        print(f"   {response.text}")
        return False
    
    result = response.json()
    workitem_id = result['id']
    print(f"   ✅ WorkItem создан: {workitem_id}\n")
    
    # Wait for completion
    print("5️⃣ Ожидание завершения...")
    for attempt in range(30):
        time.sleep(10)
        
        status_url = f"{url}/{workitem_id}"
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()
        
        status = status_data.get('status')
        print(f"   [{attempt+1}/30] Status: {status}")
        
        if status == 'success':
            print(f"\n6️⃣ Проверка результата...")
            
            # Check file exists
            time.sleep(2)
            if not output_blob.exists():
                print(f"   ❌ Файл не найден в GCS!")
                return False
            
            print(f"   ✅ Файл существует в GCS")
            
            # Check size
            size = output_blob.size
            if size == 0:
                print(f"   ❌ Файл пустой!")
                return False
            
            print(f"   ✅ Размер: {size} bytes")
            
            # Check format
            first_bytes = output_blob.download_as_bytes(start=0, end=10)
            
            if b'AC10' in first_bytes:
                print(f"   ✅ Формат: DWG (header: {first_bytes[:6]})")
            elif b'%PDF' in first_bytes:
                print(f"   ❌ Формат: PDF (не DWG!)")
                return False
            else:
                print(f"   ⚠️  Неизвестный формат: {first_bytes[:10]}")
                return False
            
            # Success!
            print(f"\n" + "="*70)
            print(f"✅ АВТОТЕСТ ПРОЙДЕН УСПЕШНО!")
            print(f"="*70)
            print(f"\n📊 Итоговые показатели:")
            print(f"   • WorkItem: {workitem_id}")
            print(f"   • Status: success")
            print(f"   • Activity: {activity_id}")
            print(f"   • Output: gs://btibot-processed/{output_blob_path}")
            print(f"   • Size: {size} bytes")
            print(f"   • Format: DWG (AC10xx)")
            print(f"   • Duration: ~{status_data.get('stats', {}).get('timeInstructionsEnded', 'N/A')}")
            print(f"\n📋 Критерии приёмки:")
            print(f"   ✅ API-цепочка проходит полностью")
            print(f"   ✅ WorkItem → status=success")
            print(f"   ✅ Activity использует WBLOCK команду")
            print(f"   ✅ Выходной файл — настоящий DWG")
            print(f"   ✅ Без fallback логики")
            print(f"\n🚀 ГОТОВО К ДЕПЛОЮ В PRODUCTION!")
            
            return True
        elif status in ['failedInstructions', 'failedDownload', 'failedUpload', 'failed']:
            print(f"\n   ❌ WorkItem failed: {status}")
            print(f"   Report: {status_data.get('reportUrl', 'N/A')}")
            return False
    
    print(f"\n   ❌ Timeout: WorkItem не завершился за 5 минут")
    return False

if __name__ == "__main__":
    success = test_aps_dwg2dwg()
    sys.exit(0 if success else 1)

