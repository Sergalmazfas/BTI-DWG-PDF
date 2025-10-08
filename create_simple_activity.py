#!/usr/bin/env python3
"""
Создает простую DWG→DWG Activity БЕЗ AppBundle и БЕЗ шаблона
Для проверки что Autodesk APS вообще работает
"""

import subprocess
import requests
import json

def get_secret(secret_name, project="talkhint"):
    """Получает секрет из Google Secret Manager"""
    cmd = f"gcloud secrets versions access latest --secret={secret_name} --project={project}"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    return result.stdout.strip()

def get_forge_token(client_id, client_secret):
    """Получает access token от Autodesk"""
    auth_url = "https://developer.api.autodesk.com/authentication/v2/token"
    auth_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "code:all data:read data:write"
    }
    
    response = requests.post(auth_url, data=auth_data)
    response.raise_for_status()
    
    return response.json()["access_token"]

def create_simple_activity(client_id, access_token):
    """Создает простую Activity БЕЗ AppBundle"""
    print("\n🔧 Создание SimpleDWG2DWG_NoTemplate Activity...")
    
    activity_data = {
        "id": f"{client_id}.SimpleDWG2DWG_NoTemplate",
        "commandLine": [
            "$(engine.path)\\accoreconsole.exe /i \"$(args[inputFile].path)\" /s \"_QSAVE\\n_QUIT\\n\""
        ],
        "engine": "Autodesk.AutoCAD+25_1",
        "parameters": {
            "inputFile": {
                "verb": "get",
                "localName": "input.dwg",
                "description": "Input DWG file",
                "required": True
            },
            "resultFile": {
                "verb": "put",
                "localName": "result.dwg",
                "description": "Output DWG file",
                "required": True
            }
        },
        "description": "Simple DWG passthrough without template or AppBundle"
    }
    
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"   ID: {activity_data['id']}")
    print(f"   Engine: {activity_data['engine']}")
    print(f"   CommandLine: {activity_data['commandLine'][0][:80]}...")
    
    response = requests.post(url, headers=headers, json=activity_data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\n✅ Activity создана!")
        print(f"   ID: {result.get('id')}")
        print(f"   Version: {result.get('version')}")
        print(f"\n🎯 Используйте: {client_id}.SimpleDWG2DWG_NoTemplate+{result.get('version', 1)}")
        return result.get('version', 1)
    elif response.status_code == 409:
        print(f"\n ℹ️ Activity уже существует")
        print(f"   🎯 Используйте: {client_id}.SimpleDWG2DWG_NoTemplate+1")
        return 1
    else:
        print(f"\n❌ Ошибка создания Activity:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_workitem(client_id, access_token, version):
    """Тестирует Activity создав WorkItem"""
    print("\n🧪 Создание тестового WorkItem...")
    
    workitem_data = {
        "activityId": f"{client_id}.SimpleDWG2DWG_NoTemplate+{version}",
        "arguments": {
            "inputFile": {
                "url": "https://storage.googleapis.com/btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg"
            },
            "resultFile": {
                "url": "https://storage.googleapis.com/btibot-processed/processed/test_simple_no_template_result.dwg",
                "verb": "put"
            }
        }
    }
    
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"   Activity: {workitem_data['activityId']}")
    
    response = requests.post(url, headers=headers, json=workitem_data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        workitem_id = result.get('id')
        print(f"\n✅ WorkItem создан!")
        print(f"   ID: {workitem_id}")
        print(f"   Status: {result.get('status')}")
        print(f"\n⏳ Проверьте статус через 30 секунд:")
        print(f"   curl -H 'Authorization: Bearer $TOKEN' https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}")
        return workitem_id
    else:
        print(f"\n❌ Ошибка создания WorkItem:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def main():
    """Основная функция"""
    print("="*70)
    print("🚀 Создание простой Activity БЕЗ шаблона и БЕЗ AppBundle")
    print("="*70)
    
    # Получаем credentials
    print("\n🔑 Получение credentials...")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    print(f"   Client ID: {client_id[:40]}...")
    
    # Получаем токен
    print("\n🔑 Получение access token...")
    access_token = get_forge_token(client_id, client_secret)
    print(f"   ✅ Token получен")
    
    # Создаем Activity
    version = create_simple_activity(client_id, access_token)
    
    if not version:
        print("\n❌ Не удалось создать Activity")
        return 1
    
    # Тестируем WorkItem
    workitem_id = test_workitem(client_id, access_token, version)
    
    if workitem_id:
        print("\n" + "="*70)
        print("✅ ACTIVITY СОЗДАНА И WORKITEM ЗАПУЩЕН!")
        print("="*70)
        print(f"\nТеперь обновите forge_client.py:")
        print(f"   activityId = f\"{{self.client_id}}.SimpleDWG2DWG_NoTemplate+{version}\"")
        return 0
    else:
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

