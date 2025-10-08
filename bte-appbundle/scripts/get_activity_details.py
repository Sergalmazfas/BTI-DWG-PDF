#!/usr/bin/env python3
"""
Получение деталей конкретной Activity
"""

import os
import requests
import json

# APS credentials
APS_CLIENT_ID = os.getenv('APS_CLIENT_ID', 'm6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4')
APS_CLIENT_SECRET = os.getenv('APS_CLIENT_SECRET', 'tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW')
APS_BASE_URL = "https://developer.api.autodesk.com"

def get_access_token():
    """Получить токен доступа"""
    url = f"{APS_BASE_URL}/authentication/v2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": APS_CLIENT_ID,
        "client_secret": APS_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all data:write data:read bucket:create bucket:read"
    }
    
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        print(f"❌ Ошибка получения токена: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()['access_token']

def get_activity_details(token, activity_name):
    """Получить детали Activity"""
    url = f"{APS_BASE_URL}/da/us-east/v3/activities/{activity_name}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def get_activity_versions(token, activity_name):
    """Получить все версии Activity"""
    url = f"{APS_BASE_URL}/da/us-east/v3/activities/{activity_name}/versions"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def get_activity_aliases(token, activity_name):
    """Получить все aliases Activity"""
    url = f"{APS_BASE_URL}/da/us-east/v3/activities/{activity_name}/aliases"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def main():
    print("🔑 Получение токена...")
    token = get_access_token()
    
    if not token:
        return
    
    print("✅ Токен получен\n")
    
    activities_to_check = [
        "BotBti.SimpleDWG2DWG_NoTemplate",
        "BotBti.BTEInsertTemplate"
    ]
    
    for activity_name in activities_to_check:
        print("=" * 80)
        print(f"📋 Activity: {activity_name}")
        print("=" * 80)
        
        # Детали Activity
        print("\n🔍 Детали:")
        details = get_activity_details(token, activity_name)
        if details:
            print(json.dumps(details, indent=2))
        
        # Версии
        print("\n📦 Версии:")
        versions = get_activity_versions(token, activity_name)
        if versions:
            print(f"Доступно версий: {len(versions.get('data', []))}")
            for version in versions.get('data', []):
                print(f"  • Version {version}")
        
        # Aliases
        print("\n🏷️  Aliases:")
        aliases = get_activity_aliases(token, activity_name)
        if aliases:
            alias_list = aliases.get('data', [])
            if alias_list:
                print(f"Доступно aliases: {len(alias_list)}")
                for alias in alias_list:
                    print(f"  • {alias}")
            else:
                print("  Нет aliases (нужно создать вручную через Web UI)")
        
        print()

if __name__ == "__main__":
    main()

