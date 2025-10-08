#!/usr/bin/env python3
"""
Тестирование BTI WorkItem после создания alias через Web UI
"""

import subprocess
import requests
import json
import time
import sys

def get_secret(name):
    """Получить секрет из Google Secret Manager"""
    cmd = f"gcloud secrets versions access latest --secret={name} --project=talkhint"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Ошибка получения секрета {name}: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def main():
    print("=" * 70)
    print("🧪 ТЕСТИРОВАНИЕ BTI WORKITEM")
    print("=" * 70)
    
    # 1. Получить credentials
    print("\n🔑 Получение credentials...")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    print(f"   Client ID: {client_id[:30]}...")
    
    # 2. Получить токен
    print("\n🔑 Получение access token...")
    resp = requests.post(
        "https://developer.api.autodesk.com/authentication/v2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "code:all"
        }
    )
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("   ✅ Token получен")
    
    # 3. Проверить alias
    print("\n🏷️  Проверка alias v1...")
    aliases_resp = requests.get(
        f"https://developer.api.autodesk.com/da/us-east/v3/activities/{client_id}.BTI_DWG2DWG/aliases",
        headers=headers
    )
    aliases = aliases_resp.json().get("data", [])
    print(f"   Найденные aliases: {aliases}")
    
    if not any("v1" in a for a in aliases):
        print("\n❌ Alias 'v1' НЕ НАЙДЕН!")
        print("📝 Создайте alias через Web UI:")
        print("   1. https://aps.autodesk.com")
        print("   2. My Apps → Design Automation → AutoCAD")
        print("   3. Activities → BTI_DWG2DWG → Aliases → Create")
        print("   4. ID: v1, Version: 1, Save")
        sys.exit(1)
    
    print("   ✅ Alias v1 найден!")
    
    # 4. Создать WorkItem
    print("\n🚀 Создание тестового WorkItem...")
    
    activity_id = f"{client_id}.BTI_DWG2DWG+v1"
    input_url = "https://storage.googleapis.com/btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg"
    output_url = "https://storage.googleapis.com/btibot-processed/processed/test_bti_template_final.dwg"
    
    workitem_data = {
        "activityId": activity_id,
        "arguments": {
            "inputFile": {"url": input_url},
            "resultFile": {"url": output_url, "verb": "put"}
        }
    }
    
    print(f"   Activity: {activity_id}")
    print(f"   Input: {input_url}")
    print(f"   Output: {output_url}")
    
    resp = requests.post(
        "https://developer.api.autodesk.com/da/us-east/v3/workitems",
        headers=headers,
        json=workitem_data
    )
    
    if resp.status_code not in [200, 201]:
        print(f"\n❌ Ошибка создания WorkItem: {resp.status_code}")
        print(resp.text)
        sys.exit(1)
    
    workitem = resp.json()
    workitem_id = workitem.get("id")
    
    print(f"\n✅ WorkItem создан: {workitem_id}")
    print(f"   Initial status: {workitem.get('status')}")
    
    # 5. Мониторинг
    print("\n⏳ Ожидание завершения (max 3 мин)...")
    
    for i in range(36):  # 36 * 5 сек = 3 мин
        time.sleep(5)
        
        status_resp = requests.get(
            f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}",
            headers=headers
        )
        
        status_data = status_resp.json()
        current_status = status_data.get("status")
        
        print(f"   [{i*5}s] Status: {current_status}")
        
        if current_status == "success":
            print("\n" + "=" * 70)
            print("🎉 УСПЕХ! BTI WORKITEM ВЫПОЛНЕН!")
            print("=" * 70)
            print(f"\n📊 Результаты:")
            print(f"   WorkItem ID: {workitem_id}")
            print(f"   Status: success")
            print(f"   Output: {output_url}")
            print(f"\n🎯 Следующие шаги:")
            print(f"   1. Скачать и проверить: test_bti_template_final.dwg")
            print(f"   2. Обновить forge_client.py:")
            print(f"      activityId: \"{client_id}.BTI_DWG2DWG+v1\"")
            print(f"   3. Deploy бота")
            print(f"   4. Тест через Telegram")
            sys.exit(0)
            
        elif current_status == "failed":
            print(f"\n❌ WorkItem FAILED!")
            print(f"   Report URL: {status_data.get('reportUrl', 'N/A')}")
            print(f"\n📋 Детали:")
            print(json.dumps(status_data, indent=2))
            sys.exit(1)
            
        elif current_status in ["cancelled", "error"]:
            print(f"\n❌ WorkItem {current_status}!")
            print(json.dumps(status_data, indent=2))
            sys.exit(1)
    
    print("\n⏱️  Timeout (3 мин) - WorkItem все еще выполняется")
    print(f"   Проверьте статус позже: {workitem_id}")

if __name__ == "__main__":
    main()
