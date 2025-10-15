#!/usr/bin/env python3
"""Проверка деталей Activity BotBti.SimpleDWG2DWG+v1"""

import requests
import json
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
        "scope": "code:all"
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()["access_token"]

def get_activity_details(token, activity_id):
    """Получить детали Activity"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)
        return None

def main():
    print("🔍 Проверка Activity: BotBti.SimpleDWG2DWG+v1\n")
    
    # Получаем credentials
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    
    # Получаем токен
    token = get_aps_token(client_id, client_secret)
    
    # Получаем детали Activity
    activity_id = "BotBti.SimpleDWG2DWG+v1"
    details = get_activity_details(token, activity_id)
    
    if details:
        print(f"✅ Activity найден: {activity_id}\n")
        print("📋 Детали:\n")
        print(json.dumps(details, indent=2))
        
        print("\n\n📝 Параметры для WorkItem:")
        params = details.get("parameters", {})
        print(f"  Input параметры:")
        for name, param in params.items():
            if param.get("verb") == "get":
                print(f"    - {name}: {param.get('description', 'N/A')}")
        
        print(f"\n  Output параметры:")
        for name, param in params.items():
            if param.get("verb") == "put":
                print(f"    - {name}: {param.get('description', 'N/A')}")
        
        print(f"\n\n🎯 Используйте в forge_client.py:")
        print(f'  "activityId": "{activity_id}"')
        
        # Находим названия параметров
        input_param = None
        output_param = None
        for name, param in params.items():
            if param.get("verb") == "get":
                input_param = name
            elif param.get("verb") == "put":
                output_param = name
        
        if input_param and output_param:
            print(f'  "arguments": {{')
            print(f'    "{input_param}": {{"url": input_url}},')
            print(f'    "{output_param}": {{"url": output_url, "verb": "put"}}')
            print(f'  }}')

if __name__ == "__main__":
    main()

