#!/usr/bin/env python3
"""
Список всех Activities в APS
"""

import os
import requests

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

def list_activities(token):
    """Список всех Activities"""
    url = f"{APS_BASE_URL}/da/us-east/v3/activities"
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
    print("📋 Получение списка Activities...\n")
    
    activities = list_activities(token)
    
    if activities:
        print(f"Найдено Activities: {len(activities.get('data', []))}\n")
        
        for activity in activities.get('data', []):
            if isinstance(activity, str):
                print(f"• {activity}")
            else:
                print(f"• {activity.get('id', activity)}")
                if 'version' in activity:
                    print(f"  Version: {activity['version']}")
                if 'description' in activity:
                    print(f"  Description: {activity['description']}")
            print()
    else:
        print("❌ Не удалось получить список Activities")

if __name__ == "__main__":
    main()

