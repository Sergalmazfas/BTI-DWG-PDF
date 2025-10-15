#!/usr/bin/env python3
"""
Получение информации о BTEInsertTemplate Activity
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
    print("📋 Поиск BTEInsertTemplate Activity...\n")
    
    activities = list_activities(token)
    
    if activities:
        bte_activities = [a for a in activities.get('data', []) if 'BTEInsert' in a or 'BTI' in a]
        
        if bte_activities:
            print(f"Найдено BTE/BTI Activities: {len(bte_activities)}\n")
            for activity in bte_activities:
                print(f"• {activity}")
        else:
            print("❌ BTEInsertTemplate Activity не найдена!")
            print("\n📝 Доступные Activities:")
            for activity in activities.get('data', [])[:10]:
                print(f"  • {activity}")
            
            print("\n💡 Рекомендация:")
            print("1. Проверьте, что AppBundle загружен через Web UI")
            print("2. Создайте Activity BTEInsertTemplate через Web UI")
            print("3. Создайте alias 'v1' для использования в тестах")
    else:
        print("❌ Не удалось получить список Activities")

if __name__ == "__main__":
    main()

