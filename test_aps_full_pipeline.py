#!/usr/bin/env python3
"""
Автоматический тест полного APS pipeline (аналог Postman коллекции)
Тестирует весь цикл DWG → Autodesk APS → DWG без запуска Cloud Run
"""

import subprocess
import requests
import json
import time
import sys
from datetime import timedelta

def get_secret(secret_name, project="talkhint"):
    """Получает секрет из Google Secret Manager"""
    try:
        # Пробуем через gcloud CLI (для локального запуска)
        cmd = f"gcloud secrets versions access latest --secret={secret_name} --project={project}"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    
    # Если gcloud нет (в Cloud Build), используем Python библиотеку
    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def step_1_get_token(client_id, client_secret):
    """Шаг 1: Получить Access Token"""
    print("\n" + "="*70)
    print("🔸 ШАГ 1: Получение Access Token")
    print("="*70)
    
    auth_url = "https://developer.api.autodesk.com/authentication/v2/token"
    auth_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "code:all data:read data:write bucket:create bucket:read bucket:delete"
    }
    
    response = requests.post(auth_url, data=auth_data)
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Access token получен")
        print(f"   Expires in: {token_data.get('expires_in')}s")
        return token_data["access_token"]
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(f"   {response.text}")
        return None

def step_2_check_bucket(access_token, bucket_key="btibot-queue"):
    """Шаг 2: Проверить/создать Bucket"""
    print("\n" + "="*70)
    print("🔸 ШАГ 2: Проверка Bucket")
    print("="*70)
    
    url = "https://developer.api.autodesk.com/oss/v2/buckets"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Проверяем существование
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        buckets = response.json().get('items', [])
        bucket_exists = any(b.get('bucketKey') == bucket_key for b in buckets)
        
        if bucket_exists:
            print(f"✅ Bucket {bucket_key} существует")
            return True
        else:
            print(f"⚠️ Bucket {bucket_key} не найден, создаем...")
            
            # Создаем bucket
            create_data = {
                "bucketKey": bucket_key,
                "policyKey": "persistent"
            }
            
            create_response = requests.post(url, headers=headers, json=create_data)
            
            if create_response.status_code in [200, 201, 409]:
                print(f"✅ Bucket создан")
                return True
            else:
                print(f"❌ Ошибка создания: {create_response.text}")
                return False
    
    return False

def step_3_upload_dwg(access_token, bucket_key, dwg_path, object_key):
    """Шаг 3: Загрузить DWG в bucket (используем GCS)"""
    print("\n" + "="*70)
    print("🔸 ШАГ 3: Загрузка DWG в GCS bucket")
    print("="*70)
    
    from google.cloud import storage
    
    # Используем публичный bucket btibot-processed (публичные URLs)
    gcs_path = f"btibot-processed/test_pipeline/{object_key}"
    
    print(f"   Файл: {dwg_path}")
    print(f"   GCS Path: gs://{gcs_path}")
    
    # Загрузка в GCS
    storage_client = storage.Client()
    bucket = storage_client.bucket("btibot-processed")
    blob = bucket.blob(f"test_pipeline/{object_key}")
    
    blob.upload_from_filename(dwg_path)
    
    # Используем публичный URL (bucket уже публичный)
    public_url = f"https://storage.googleapis.com/btibot-processed/test_pipeline/{object_key}"
    
    print(f"✅ DWG загружен в GCS")
    print(f"   Public URL: {public_url[:80]}...")
    
    return public_url

def step_4_check_activity(client_id, access_token):
    """Шаг 4: Проверить существование Activity"""
    print("\n" + "="*70)
    print("🔸 ШАГ 4: Проверка Activity")
    print("="*70)
    
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        activities = response.json().get('data', [])
        
        # Ищем наши Activities
        our_activities = [a for a in activities if client_id in a]
        
        print(f"   Найдено наших Activities: {len(our_activities)}")
        for activity in our_activities:
            short_name = activity.replace(f"{client_id}.", "")
            print(f"   - {short_name}")
        
        # Проверяем BTI_DWG2DWG
        bti_activity = f"{client_id}.BTI_DWG2DWG+1"
        if any(bti_activity in a for a in our_activities):
            print(f"\n✅ Activity найдена: BTI_DWG2DWG+1")
            return "BTI_DWG2DWG+1"
        
        # Используем SimpleDWG2DWG если есть
        simple_activity = f"{client_id}.SimpleDWG2DWG+1"
        if any(simple_activity in a for a in our_activities):
            print(f"\n✅ Используем: SimpleDWG2DWG+1")
            return "SimpleDWG2DWG+1"
        
        print(f"\n⚠️ BTI Activities не найдены, используем стандартную")
        return "AutoCAD.PlotToPDF+25_0"
    
    return None

def step_5_create_workitem(client_id, access_token, activity_id, input_url, output_url):
    """Шаг 5: Создать WorkItem"""
    print("\n" + "="*70)
    print("🔸 ШАГ 5: Создание WorkItem")
    print("="*70)
    
    # Определяем параметры в зависимости от Activity
    if "SimpleDWG2DWG" in activity_id or "BTI_DWG2DWG" in activity_id:
        arguments = {
            "inputFile": {"url": input_url},
            "resultFile": {"url": output_url, "verb": "put"}
        }
    else:  # AutoCAD.PlotToPDF
        arguments = {
            "HostDwg": {"url": input_url},
            "Result": {"url": output_url, "verb": "put"}
        }
    
    workitem_data = {
        "activityId": f"{client_id}.{activity_id}" if not activity_id.startswith("AutoCAD") else activity_id,
        "arguments": arguments
    }
    
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"   Activity: {workitem_data['activityId']}")
    print(f"   Input: {input_url[:60]}...")
    print(f"   Output: {output_url[:60]}...")
    
    response = requests.post(url, headers=headers, json=workitem_data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        workitem_id = result.get('id')
        print(f"\n✅ WorkItem создан!")
        print(f"   ID: {workitem_id}")
        print(f"   Status: {result.get('status')}")
        return workitem_id
    else:
        print(f"\n❌ Ошибка создания WorkItem:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def step_6_check_status(workitem_id, access_token, max_wait=180):
    """Шаг 6: Проверить статус WorkItem"""
    print("\n" + "="*70)
    print("🔸 ШАГ 6: Проверка статуса WorkItem")
    print("="*70)
    
    url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            
            if status != last_status:
                print(f"   Status: {status}")
                last_status = status
            
            if status == 'success':
                print(f"\n🎉 УСПЕХ! WorkItem выполнен!")
                stats = result.get('stats', {})
                for key, value in stats.items():
                    print(f"   {key}: {value}")
                return True, result
            elif status in ['failed', 'failedInstructions', 'failedDownload', 'failedUpload', 'cancelled']:
                print(f"\n❌ WorkItem failed: {status}")
                if result.get('reportUrl'):
                    print(f"   Report URL: {result.get('reportUrl')}")
                return False, result
            else:
                time.sleep(5)
        else:
            print(f"   ❌ Ошибка проверки: {response.status_code}")
            return False, None
    
    print(f"\n⏱️ Timeout после {max_wait}s")
    return False, None

def main():
    """Основная функция - выполняет весь pipeline"""
    print("="*70)
    print("🧪 APS POSTMAN PIPELINE TEST")
    print("="*70)
    
    # Получаем credentials
    print("\n🔑 Получение credentials из Secret Manager...")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    print(f"   Client ID: {client_id[:40]}...")
    
    # Шаг 1: Token
    access_token = step_1_get_token(client_id, client_secret)
    if not access_token:
        return 1
    
    # Шаг 2: Bucket
    if not step_2_check_bucket(access_token):
        return 1
    
    # Шаг 3: Upload DWG
    dwg_path = "/tmp/test_plan.dwg"
    
    # Скачиваем тестовый файл из GCS
    print("\n📥 Скачивание тестового DWG из GCS...")
    from google.cloud import storage
    storage_client = storage.Client()
    bucket = storage_client.bucket("btibot-processed")
    blob = bucket.blob("raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg")
    blob.download_to_filename(dwg_path)
    print(f"   Downloaded to {dwg_path}")
    
    object_id = step_3_upload_dwg(access_token, "btibot-queue", dwg_path, "test_plan_input.dwg")
    if not object_id:
        return 1
    
    # Шаг 4: Check Activity
    activity_id = step_4_check_activity(client_id, access_token)
    if not activity_id:
        return 1
    
    # Шаг 5: Create WorkItem
    input_url = object_id  # Это публичный URL из step_3
    
    # Создаем signed URL для output с правом записи
    print("\n📤 Создание output signed URL...")
    
    from google.cloud import storage, secretmanager
    from google.oauth2 import service_account
    
    # Получаем Service Account credentials из Secret Manager
    secret_client = secretmanager.SecretManagerServiceClient()
    secret_name = "projects/talkhint/secrets/FORGE_SERVICE_KEY/versions/latest"
    secret_response = secret_client.access_secret_version(request={"name": secret_name})
    sa_credentials_json = json.loads(secret_response.payload.data.decode("UTF-8"))
    
    # Создаем credentials из JSON
    sa_credentials = service_account.Credentials.from_service_account_info(sa_credentials_json)
    
    # Создаем GCS client с Service Account credentials
    gcs_client = storage.Client(credentials=sa_credentials)
    bucket = gcs_client.bucket("btibot-processed")
    
    # Output blob
    output_blob = bucket.blob("test_pipeline/test_plan_output.dwg")
    
    # Создаем signed URL для записи (PUT)
    # НЕ указываем content_type, чтобы APS мог загружать без этого заголовка
    output_url = output_blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="PUT"
    )
    
    print(f"✅ Output signed URL создан")
    print(f"   URL: {output_url[:80]}...")
    
    workitem_id = step_5_create_workitem(client_id, access_token, activity_id, input_url, output_url)
    if not workitem_id:
        return 1
    
    # Шаг 6: Check Status
    success, result = step_6_check_status(workitem_id, access_token)
    
    # Итоговый отчет
    print("\n" + "="*70)
    print("📋 ИТОГОВЫЙ ОТЧЕТ")
    print("="*70)
    
    if success:
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print(f"✅ Access token: OK")
        print(f"✅ Bucket: OK")
        print(f"✅ DWG upload: OK")
        print(f"✅ Activity: {activity_id}")
        print(f"✅ WorkItem: {workitem_id}")
        print(f"✅ Status: success")
        print(f"\n🎉 AUTODESK APS PIPELINE РАБОТАЕТ!")
        print(f"\n📊 Проверьте Usage в панели APS:")
        print(f"   https://aps.autodesk.com/dashboard")
        return 0
    else:
        print("\n❌ ТЕСТ НЕ ПРОЙДЕН")
        print(f"   WorkItem: {workitem_id}")
        print(f"   Status: {result.get('status') if result else 'N/A'}")
        if result and result.get('reportUrl'):
            print(f"   Report: {result.get('reportUrl')}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

