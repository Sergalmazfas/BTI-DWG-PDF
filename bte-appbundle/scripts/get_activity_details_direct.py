#!/usr/bin/env python3
"""
Получение детальной информации об Activity через разные методы
"""

import os
import sys
import json
import requests

APS_CLIENT_ID = os.getenv('APS_CLIENT_ID', 'm6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4')
APS_CLIENT_SECRET = os.getenv('APS_CLIENT_SECRET', 'tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW')
APS_BASE_URL = "https://developer.api.autodesk.com"

def get_token():
    url = f"{APS_BASE_URL}/authentication/v2/token"
    data = {
        "client_id": APS_CLIENT_ID,
        "client_secret": APS_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all data:write data:read"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return response.json()['access_token']

def get_activity_via_listing(token):
    """Получить Activity через листинг (работает)"""
    url = f"{APS_BASE_URL}/da/us-east/v3/activities"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        activities = response.json().get('data', [])
        bte_acts = [a for a in activities if 'BTEInsert' in a]
        return bte_acts
    return []

def get_activity_by_id(token, activity_id):
    """Получить детали Activity по ID"""
    url = f"{APS_BASE_URL}/da/us-east/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    print(f"\n📋 GET /activities/{activity_id}")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Получено:")
        print(json.dumps(data, indent=2))
        return data
    else:
        print(f"   ❌ Ошибка: {response.text}")
        return None

def main():
    print("=" * 80)
    print("🔍 Детали Activity BTEInsertTemplate")
    print("=" * 80)
    
    token = get_token()
    print("✅ Токен получен\n")
    
    # Получить через листинг
    print("📋 Шаг 1: Получение через листинг")
    activities = get_activity_via_listing(token)
    
    if activities:
        print(f"✅ Найдено Activities:")
        for act in activities:
            print(f"   • {act}")
        
        # Попробуем получить детали для каждого варианта
        print("\n📋 Шаг 2: Попытка получить детали")
        
        # Извлекаем базовое имя (до +)
        if activities:
            base_name = activities[0].split('+')[0]
            print(f"\nБазовое имя: {base_name}")
            
            # Пробуем разные варианты
            variants = [
                base_name,
                "BTEInsertTemplate",
                f"{APS_CLIENT_ID}.BTEInsertTemplate"
            ]
            
            for variant in variants:
                details = get_activity_by_id(token, variant)
                if details:
                    print(f"\n🎯 НАЙДЕНЫ ПАРАМЕТРЫ для {variant}:")
                    params = details.get('parameters', {})
                    for param_name, param_info in params.items():
                        print(f"   • {param_name}")
                        print(f"      verb: {param_info.get('verb')}")
                        print(f"      localName: {param_info.get('localName')}")
                    break
    else:
        print("❌ Activities не найдены")

if __name__ == "__main__":
    main()

