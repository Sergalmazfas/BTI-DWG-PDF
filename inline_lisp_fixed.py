#!/usr/bin/env python3
"""
ИСПРАВЛЕННАЯ версия: правильные команды AutoCAD (без лишних дефисов)
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
print("║  ✅ ИСПРАВЛЕНО: ПРАВИЛЬНЫЕ КОМАНДЫ AUTOCAD                       ║")
print("╚══════════════════════════════════════════════════════════════════╝")

try:
    # Токен
    print("\n1️⃣  Получение токена...")
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
    
    # Создать Activity с ИСПРАВЛЕННЫМ inline LISP
    print("\n2️⃣  Создание Activity с исправленными командами...")
    
    # ИСПРАВЛЕНО: добавлены "" для завершения команд
    inline_lisp = """
; Создание слоёв БТИ
(command "_.LAYER" "M" "BTI_WALLS" "C" "8" "" "")
(command "_.LAYER" "M" "BTI_MARKERS" "C" "2" "" "")
(command "_.LAYER" "M" "BTI_TEXT" "C" "7" "" "")

; Функция создания метки POINT + TEXT
(defun CREATE_MARKER (pt label / textPt)
  (command "_.LAYER" "S" "BTI_MARKERS" "")
  (command "_.POINT" pt "")
  (setq textPt (list (+ (car pt) 200.0) (cadr pt)))
  (command "_.TEXT" "J" "L" textPt 150.0 0.0 label "")
  (princ (strcat "\\n[BTI] Метка: " label))
)

; Создать метки
(princ "\\n[BTI] Создание меток...")
(CREATE_MARKER (list 1000.0 1500.0) "DOOR")
(CREATE_MARKER (list 2000.0 1500.0) "WINDOW")
(CREATE_MARKER (list 3000.0 1500.0) "MARKER")

(command "_.ZOOM" "E")
(command "_.SAVEAS" "2018" "bti_ready.dwg")
(princ "\\n[BTI] ✅ COMPLETE")
"""
    
    activity_response = requests.post(
        "https://developer.api.autodesk.com/da/us-east/v3/activities/BtiLISPActivity/versions",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "commandLine": [
                "$(engine.path)\\\\accoreconsole.exe /i \"$(args[InputDwg].path)\" /s \"$(settings[script].path)\""
            ],
            "parameters": {
                "InputDwg": {"verb": "get", "required": True, "localName": "input.dwg"},
                "OutputDwg": {"verb": "put", "required": True, "localName": "bti_ready.dwg"}
            },
            "engine": "Autodesk.AutoCAD+25_1",
            "appbundles": [],
            "settings": {"script": inline_lisp},
            "description": "BTI LISP v4 - FIXED commands"
        }
    )
    
    activity_data = activity_response.json()
    activity_version = activity_data.get("version")
    
    print(f"   ✅ Activity версия {activity_version} создана")
    
    # Обновить alias
    requests.patch(
        "https://developer.api.autodesk.com/da/us-east/v3/activities/BtiLISPActivity/aliases/prod",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"version": int(activity_version)}
    )
    
    print(f"   ✅ Alias обновлён на версию {activity_version}")
    
    # Найти DWG
    print("\n3️⃣  Поиск DWG...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_INPUT)
    blobs = list(bucket.list_blobs())
    dwg_blobs = [b for b in blobs if b.name.endswith('.dwg')]
    dwg_blobs.sort(key=lambda x: x.time_created, reverse=True)
    latest = dwg_blobs[0]
    print(f"   📁 {latest.name}")
    
    # Signed URLs
    print("\n4️⃣  Создание signed URLs...")
    from google.oauth2 import service_account
    sa_key_path = "bte-appbundle/dwg-processor-sa-key.json"
    credentials = service_account.Credentials.from_service_account_file(sa_key_path)
    
    input_url = latest.generate_signed_url(version="v4", expiration=timedelta(hours=1), method="GET", credentials=credentials)
    
    output_bucket = storage_client.bucket(BUCKET_OUTPUT)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_blob = output_bucket.blob(f"ready/test_final/bti_ready_{timestamp}.dwg")
    output_url = output_blob.generate_signed_url(version="v4", expiration=timedelta(hours=1), method="PUT", credentials=credentials)
    print(f"   ✅ URLs готовы")
    
    # Запустить WorkItem
    print(f"\n5️⃣  Запуск WorkItem...")
    
    workitem_response = requests.post(
        "https://developer.api.autodesk.com/da/us-east/v3/workitems",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "activityId": "BotBti.BtiLISPActivity+prod",
            "arguments": {
                "InputDwg": {"verb": "get", "url": input_url},
                "OutputDwg": {"verb": "put", "url": output_url}
            }
        }
    )
    
    workitem_id = workitem_response.json()["id"]
    print(f"   🚀 WorkItem ID: {workitem_id}")
    
    # Мониторинг
    print(f"\n6️⃣  Мониторинг...")
    
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
        
        print(f"   ⌛ [{elapsed:3d}s] Попытка {attempt:2d}: {status}")
        
        if status == "success":
            print(f"\n   ✅ WorkItem завершён успешно!")
            
            report_url = data.get("reportUrl")
            if report_url:
                log_response = requests.get(report_url, timeout=10)
                log_text = log_response.text
                
                print(f"\n📝 Анализ лога:")
                if "[BTI] Метка создана" in log_text:
                    count = log_text.count("[BTI] Метка создана")
                    print(f"   ✅ Создано меток: {count}")
                if "[BTI] ✅ COMPLETE" in log_text:
                    print("   ✅ Полный цикл завершён")
                if "BTI_WALLS" in log_text and "BTI_MARKERS" in log_text:
                    print("   ✅ Слои БТИ созданы")
                
                log_file = f"workitem_success_final_{timestamp}.log"
                with open(log_file, "w") as f:
                    f.write(log_text)
                print(f"\n💾 Лог: {log_file}")
            
            print("\n" + "="*70)
            print("╔══════════════════════════════════════════════════════════════════╗")
            print("║        🎉 ПОЛНЫЙ ЦИКЛ УСПЕШНО ЗАВЕРШЁН!                          ║")
            print("╚══════════════════════════════════════════════════════════════════╝")
            print("="*70)
            print(f"\nФайл: {latest.name}")
            print(f"WorkItem ID: {workitem_id}")
            print(f"Статус: success")
            print(f"Время: {elapsed} сек")
            print(f"\nРезультат: gs://{BUCKET_OUTPUT}/ready/test_final/bti_ready_{timestamp}.dwg")
            print()
            sys.exit(0)
        
        elif status and status.startswith("failed"):
            print(f"\n   ❌ Ошибка: {status}")
            
            report_url = data.get("reportUrl")
            if report_url:
                log_response = requests.get(report_url, timeout=10)
                log_text = log_response.text
                
                # Найти конкретную ошибку
                error_lines = [line for line in log_text.split('\n') if 'error' in line.lower() or 'Error' in line]
                if error_lines:
                    print(f"\n🔍 Ошибка:")
                    for err in error_lines[:3]:
                        print(f"   {err}")
                
                log_file = f"workitem_error_{timestamp}.log"
                with open(log_file, "w") as f:
                    f.write(log_text)
                print(f"\n💾 Лог: {log_file}")
            
            sys.exit(1)
        
        time.sleep(15)
    
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

