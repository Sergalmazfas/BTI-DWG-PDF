#!/usr/bin/env python3
"""
Setup Autodesk APS Activity для BTI DWG Processing
Создает AppBundle и Activity для обработки DWG файлов
"""

import os
import sys
import json
import requests
from google.cloud import secretmanager

def get_secret(secret_id):
    """Получить секрет из Google Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/talkhint/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_aps_token(client_id, client_secret):
    """Получить APS токен"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "code:all data:read data:write"
    }
    
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()["access_token"]

def list_activities(token, client_id):
    """Список всех Activities"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    activities = response.json().get("data", [])
    my_activities = [a for a in activities if a.startswith(client_id)]
    
    print(f"\n📋 Activities для {client_id[:20]}...:")
    for act in my_activities:
        print(f"  - {act}")
    
    return my_activities

def get_activity_details(token, activity_id):
    """Получить детали Activity"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_nickname(token):
    """Получить nickname (ForgeAppName)"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, str):
            return data
        elif isinstance(data, dict) and "id" in data:
            return data["id"]
    return None

def create_simple_activity(token, client_id):
    """Создать простой DWG2DWG Activity"""
    # Получаем nickname (нужен для owner)
    nickname = get_nickname(token)
    if not nickname:
        print("❌ Не удалось получить nickname. Сначала запустите setup_aps_nickname.py")
        return None
    
    print(f"✅ Используем nickname: {nickname}")
    activity_id = f"{nickname}.SimpleDWG2DWG"
    
    # Проверяем, существует ли уже
    existing = get_activity_details(token, activity_id)
    if existing:
        print(f"✅ Activity {activity_id} уже существует")
        
        # Проверяем alias
        alias_url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}/aliases/v1"
        headers = {"Authorization": f"Bearer {token}"}
        alias_resp = requests.get(alias_url, headers=headers)
        
        if alias_resp.status_code == 200:
            print(f"✅ Alias v1 существует для {activity_id}")
            return {"activityId": f"{activity_id}+v1", "status": "exists"}
        else:
            print(f"⚠️ Alias v1 не найден, создаем...")
            # Создаем alias
            version = existing.get("version", 1)
            alias_data = {
                "version": version,
                "id": "v1"
            }
            alias_resp = requests.post(
                f"https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}/aliases",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=alias_data
            )
            if alias_resp.status_code in [200, 201]:
                print(f"✅ Alias v1 создан для {activity_id}")
                return {"activityId": f"{activity_id}+v1", "status": "alias_created"}
            else:
                print(f"❌ Ошибка создания alias: {alias_resp.text}")
                return None
    
    # Создаем новый Activity
    print(f"🔧 Создаем новый Activity: {activity_id}")
    
    activity_data = {
        "id": activity_id,
        "commandLine": [
            "$(engine.path)\\accoreconsole.exe /i \"$(args[inputFile].path)\" /s \"$(settings[script].path)\""
        ],
        "engine": "Autodesk.AutoCAD+24_2",
        "parameters": {
            "inputFile": {
                "verb": "get",
                "description": "Input DWG file",
                "localName": "input.dwg"
            },
            "resultFile": {
                "verb": "put",
                "description": "Output DWG file",
                "localName": "result.dwg"
            }
        },
        "settings": {
            "script": {
                "value": "(command \"_.open\" \"input.dwg\")(command \"_.qsave\" \"result.dwg\")(command \"_.close\")"
            }
        },
        "description": "Simple DWG to DWG processing activity"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        "https://developer.api.autodesk.com/da/us-east/v3/activities",
        headers=headers,
        json=activity_data
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        version = result.get("version", 1)
        print(f"✅ Activity создан: {activity_id} (version {version})")
        
        # Создаем alias v1
        alias_data = {
            "version": version,
            "id": "v1"
        }
        
        alias_resp = requests.post(
            f"https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}/aliases",
            headers=headers,
            json=alias_data
        )
        
        if alias_resp.status_code in [200, 201]:
            print(f"✅ Alias v1 создан для {activity_id}")
            return {"activityId": f"{activity_id}+v1", "status": "created"}
        else:
            print(f"❌ Ошибка создания alias: {alias_resp.text}")
            return None
    else:
        print(f"❌ Ошибка создания Activity: {response.status_code}")
        print(f"   {response.text}")
        return None

def main():
    print("🚀 Setup Autodesk APS Activity для BTI DWG Processing\n")
    
    # Получаем credentials из Secret Manager
    print("🔑 Получаем credentials из Secret Manager...")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    
    print(f"✅ Client ID: {client_id[:20]}...")
    
    # Получаем токен
    print("\n🔐 Получаем APS токен...")
    token = get_aps_token(client_id, client_secret)
    print("✅ Токен получен")
    
    # Получаем nickname
    print("\n📝 Получаем nickname...")
    nickname = get_nickname(token)
    if not nickname:
        print("❌ Nickname не найден. Сначала запустите setup_aps_nickname.py")
        return
    print(f"✅ Nickname: {nickname}")
    
    # Список текущих Activities
    activities = list_activities(token, nickname)
    
    # Создаем или проверяем Activity
    print("\n🔧 Настройка Activity...")
    result = create_simple_activity(token, client_id)
    
    if result:
        print(f"\n🎉 Готово! Используйте Activity ID: {result['activityId']}")
        print(f"\n📝 Обновите forge_client.py, строка 122:")
        print(f'   "activityId": "{result["activityId"]}"')
        
        # Сохраняем конфиг
        config = {
            "activityId": result["activityId"],
            "clientId": client_id[:20] + "...",
            "status": result["status"]
        }
        
        with open("aps_activity_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"\n💾 Конфигурация сохранена в aps_activity_config.json")
    else:
        print("\n❌ Не удалось настроить Activity")
        sys.exit(1)

if __name__ == "__main__":
    main()

