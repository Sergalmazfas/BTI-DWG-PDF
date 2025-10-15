#!/usr/bin/env python3
"""
Тест BTEInsertTemplate Activity на файле Басманной
Команда INSERTBTE для вставки BTI шаблона
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

# Файлы
DWG_FILE = "bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg"
SERVICE_ACCOUNT_KEY = "bte-appbundle/dwg-processor-sa-key.json"

def get_access_token():
    """Получить APS токен"""
    url = f"{APS_BASE_URL}/authentication/v2/token"
    data = {
        "client_id": APS_CLIENT_ID,
        "client_secret": APS_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all data:write data:read bucket:create bucket:read"
    }
    
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    
    if response.status_code != 200:
        print(f"❌ Ошибка получения токена: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
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

def create_workitem(token, activity_id, input_url, output_url):
    """Создать WorkItem"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Правильные параметры для BTEInsertTemplate
    payload = {
        "activityId": activity_id,
        "arguments": {
            "inputFile": {
                "url": input_url
            },
            "resultFile": {
                "url": output_url,
                "verb": "put"
            }
        }
    }
    
    print(f"📋 Payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    response = requests.post(f"{APS_BASE_URL}/da/us-east/v3/workitems", headers=headers, json=payload)
    
    if response.status_code not in [200, 201]:
        print(f"❌ Ошибка создания WorkItem: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    return response.json()

def wait_for_completion(token, workitem_id, timeout=300):
    """Ожидание завершения WorkItem"""
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(
            f"{APS_BASE_URL}/da/us-east/v3/workitems/{workitem_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка получения статуса: {response.status_code}")
            time.sleep(5)
            continue
        
        data = response.json()
        status = data.get('status')
        elapsed = int(time.time() - start_time)
        
        print(f"📊 Статус: {status} (прошло {elapsed}s)")
        
        if status == 'success':
            return data
        elif status in ['failedInstructions', 'failedDownload', 'failedUpload', 'failed', 'cancelled']:
            return data
        
        time.sleep(5)
    
    print(f"⏰ Timeout ({timeout}s)")
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
    print("🧩 Тест BTEInsertTemplate Activity")
    print("=" * 80)
    print()
    
    # Проверка файла
    if not os.path.exists(DWG_FILE):
        print(f"❌ DWG файл не найден: {DWG_FILE}")
        sys.exit(1)
    
    print(f"📂 DWG файл: {DWG_FILE} ({os.path.getsize(DWG_FILE)} bytes)")
    
    # Загрузка DWG в GCS (без ZIP!)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    gcs_input_path = f"gs://btibot-queue/test_input/basmannyi_{timestamp}.dwg"
    gcs_output_path = f"gs://btibot-processed/test_output/basmannyi_result_{timestamp}.dwg"
    
    print(f"☁️  Загрузка DWG в GCS: {gcs_input_path}")
    os.system(f'gcloud storage cp "{DWG_FILE}" "{gcs_input_path}"')
    
    # Генерация signed URLs
    print("🔗 Генерация signed URLs...")
    input_url = generate_signed_url(gcs_input_path, "GET")
    output_url = generate_signed_url(gcs_output_path, "PUT")
    
    print(f"✅ Input URL: {input_url[:80]}...")
    print(f"✅ Output URL: {output_url[:80]}...")
    print()
    
    # Получение токена
    print("🔑 Получение токена APS...")
    token = get_access_token()
    print("✅ Токен получен\n")
    
    # Создание WorkItem
    print("🚀 Создание WorkItem...")
    
    # Пробуем разные варианты Activity ID
    activity_variants = [
        "BTEInsertTemplate+v1",  # БЕЗ nickname - работает!
        "BotBti.BTEInsertTemplate+v1",
        "BTEInsertTemplate+1",
    ]
    
    workitem = None
    for activity_id in activity_variants:
        print(f"\n🔄 Попытка с Activity: {activity_id}")
        try:
            workitem = create_workitem(token, activity_id, input_url, output_url)
            print(f"✅ WorkItem создан: {workitem['id']}")
            break
        except SystemExit:
            continue
    
    if not workitem:
        print("\n❌ Не удалось создать WorkItem ни с одним вариантом Activity ID")
        print("\n💡 Необходимо создать alias 'v1' через Web UI:")
        print("   1. https://aps.autodesk.com")
        print("   2. My Apps → Design Automation → AutoCAD")
        print("   3. Activities → BTEInsertTemplate → Aliases → Create")
        print("   4. ID: v1, Version: 1, Save")
        sys.exit(1)
    
    workitem_id = workitem['id']
    
    # Ожидание завершения
    print(f"\n⏳ Ожидание завершения...")
    result = wait_for_completion(token, workitem_id, timeout=300)
    
    if not result:
        print("❌ Не удалось получить результат")
        sys.exit(1)
    
    # Сохранение результата
    result_file = f"bte-appbundle/reports/bte_insert_result_{timestamp}.json"
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n📝 Результат сохранён: {result_file}")
    
    # Скачивание отчёта
    if 'reportUrl' in result:
        report_file = f"bte-appbundle/reports/bte_insert_report_{timestamp}.log"
        if download_report(result['reportUrl'], report_file):
            print(f"📥 Отчёт сохранён: {report_file}")
            
            # Показать отчёт
            print("\n" + "=" * 80)
            print("📋 Отчёт WorkItem:")
            print("=" * 80)
            with open(report_file, 'r') as f:
                report_content = f.read()
                print(report_content)
            print("=" * 80)
            
            # Проверка на INSERTBTE
            if 'INSERTBTE' in report_content or 'APPLYBTITEMPLATE' in report_content:
                print("\n✅ Команда INSERTBTE/APPLYBTITEMPLATE найдена в отчёте!")
            else:
                print("\n⚠️  Команда INSERTBTE не найдена в отчёте")
    
    # Итоговый статус
    print("\n" + "=" * 80)
    print(f"🎯 ИТОГОВЫЙ СТАТУС: {result['status']}")
    print("=" * 80)
    
    if result['status'] == 'success':
        print("✅ ТЕСТ УСПЕШНО ЗАВЕРШЁН!")
        print(f"📁 Результат: {gcs_output_path}")
        
        # Проверка результата в GCS
        check_cmd = f'gcloud storage ls -l "{gcs_output_path}"'
        check_result = os.popen(check_cmd).read()
        if 'TOTAL' in check_result:
            print("✅ Файл результата найден в GCS:")
            for line in check_result.split('\n'):
                if '.dwg' in line:
                    print(f"   {line.strip()}")
        
        sys.exit(0)
    else:
        print(f"❌ ТЕСТ ЗАВЕРШИЛСЯ С ОШИБКОЙ: {result['status']}")
        sys.exit(1)

if __name__ == "__main__":
    main()

