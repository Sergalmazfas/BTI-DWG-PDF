#!/usr/bin/env python3
"""
ПРОДАКШЕН ВЕРСИЯ: Тест DWG-обработки через Forge
Activity: BotBti.BtiLISPActivity+prod (inline LISP)
"""

import os
import sys
import time
import requests
from datetime import datetime, timedelta
from google.cloud import storage, secretmanager

PROJECT_ID = "talkhint"
BUCKET_INPUT = "btibot-queue"
BUCKET_OUTPUT = "btibot-processed"


def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


print("╔══════════════════════════════════════════════════════════════════╗")
print("║  🚀 FORGE DWG PROCESSOR - PRODUCTION TEST                        ║")
print("╚══════════════════════════════════════════════════════════════════╝")

try:
    # 1. Токен
    print("\n1️⃣  Аутентификация Forge...")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    
    token_response = requests.post(
        "https://developer.api.autodesk.com/authentication/v2/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "code:all"
        }
    )
    token = token_response.json()["access_token"]
    print(f"   ✅ Токен получен")
    
    # 2. Найти DWG
    print("\n2️⃣  Поиск DWG в очереди...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_INPUT)
    blobs = list(bucket.list_blobs())
    dwg_blobs = [b for b in blobs if b.name.endswith('.dwg')]
    
    if not dwg_blobs:
        print("   ⚠️  Нет DWG-файлов в очереди")
        sys.exit(1)
    
    dwg_blobs.sort(key=lambda x: x.time_created, reverse=True)
    latest = dwg_blobs[0]
    print(f"   📁 {latest.name} ({latest.size} байт)")
    
    # 3. Signed URLs
    print("\n3️⃣  Создание signed URLs...")
    from google.oauth2 import service_account
    sa_key_path = "bte-appbundle/dwg-processor-sa-key.json"
    credentials = service_account.Credentials.from_service_account_file(sa_key_path)
    
    input_url = latest.generate_signed_url(version="v4", expiration=timedelta(hours=1), method="GET", credentials=credentials)
    
    output_bucket = storage_client.bucket(BUCKET_OUTPUT)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    job_id = f"job_{timestamp}"
    output_blob = output_bucket.blob(f"ready/{job_id}/bti_ready.dwg")
    output_url = output_blob.generate_signed_url(version="v4", expiration=timedelta(hours=1), method="PUT", credentials=credentials)
    print(f"   ✅ URLs созданы (Job ID: {job_id})")
    
    # 4. Запустить WorkItem
    print("\n4️⃣  Запуск Forge WorkItem...")
    print(f"   Activity: BotBti.BTI_AUTO_PROCESS+prod")
    
    workitem_response = requests.post(
        "https://developer.api.autodesk.com/da/us-east/v3/workitems",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "activityId": "BotBti.BTI_AUTO_PROCESS+prod",
            "arguments": {
                "inputFile": {"verb": "get", "url": input_url},
                "outputFile": {"verb": "put", "url": output_url}
            }
        }
    )
    
    if workitem_response.status_code != 200:
        print(f"   ❌ Ошибка запуска: {workitem_response.status_code}")
        print(f"   {workitem_response.text}")
        sys.exit(1)
    
    workitem_id = workitem_response.json()["id"]
    print(f"   🚀 WorkItem ID: {workitem_id}")
    
    # 5. Мониторинг
    print("\n5️⃣  Ожидание завершения...")
    
    start_time = time.time()
    attempt = 0
    
    while (time.time() - start_time) < 600:
        elapsed = int(time.time() - start_time)
        attempt += 1
        
        status_response = requests.get(
            f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        data = status_response.json()
        status = data.get("status")
        
        print(f"   ⌛ [{elapsed:3d}s] {status}")
        
        if status == "success":
            print(f"\n   ✅ Обработка успешно завершена!")
            
            # Лог
            report_url = data.get("reportUrl")
            if report_url:
                log_response = requests.get(report_url, timeout=10)
                log_text = log_response.text
                
                # Сохранить лог
                log_file = f"forge_log_{timestamp}.log"
                with open(log_file, "w") as f:
                    f.write(log_text)
                print(f"   💾 Лог: {log_file}")
            
            print("\n" + "="*70)
            print("✅ УСПЕХ! ФАЙЛ ОБРАБОТАН И СОХРАНЁН")
            print("="*70)
            print(f"\nВходной файл: {latest.name}")
            print(f"Размер: {latest.size} → {output_blob.name}")
            print(f"\nРезультат: gs://{BUCKET_OUTPUT}/ready/{job_id}/bti_ready.dwg")
            print()
            sys.exit(0)
        
        elif status and status.startswith("failed"):
            print(f"\n   ❌ Ошибка: {status}")
            
            report_url = data.get("reportUrl")
            if report_url:
                log_response = requests.get(report_url, timeout=10)
                log_file = f"forge_error_{timestamp}.log"
                with open(log_file, "w") as f:
                    f.write(log_response.text)
                print(f"   💾 Лог ошибки: {log_file}")
            
            sys.exit(1)
        
        time.sleep(15)
    
    print(f"\n⏰ Таймаут!")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    sys.exit(1)

