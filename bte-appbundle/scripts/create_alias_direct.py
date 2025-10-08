#!/usr/bin/env python3
"""
Прямое создание alias для существующей Activity
Обходной путь для API бага "Cannot parse id"
"""

import os
import sys
import json
import requests

# APS Configuration
APS_CLIENT_ID = os.getenv('APS_CLIENT_ID', 'm6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4')
APS_CLIENT_SECRET = os.getenv('APS_CLIENT_SECRET', 'tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW')
APS_BASE_URL = "https://developer.api.autodesk.com"

def get_token():
    """Получить токен"""
    url = f"{APS_BASE_URL}/authentication/v2/token"
    data = {
        "client_id": APS_CLIENT_ID,
        "client_secret": APS_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all data:write data:read"
    }
    
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    
    if response.status_code != 200:
        print(f"❌ Ошибка токена: {response.status_code}")
        sys.exit(1)
    
    return response.json()['access_token']

def list_all_activities(token):
    """Получить список всех Activities"""
    url = f"{APS_BASE_URL}/da/us-east/v3/activities"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get('data', [])
    return []

def try_create_alias_variants(token):
    """Попробовать разные варианты создания alias"""
    
    variants = [
        ("BTEInsertTemplate", "Без nickname"),
        ("BotBti.BTEInsertTemplate", "С nickname BotBti"),
        (f"{APS_CLIENT_ID}.BTEInsertTemplate", "С полным Client ID"),
    ]
    
    print("\n" + "=" * 80)
    print("🔬 Тестирование различных вариантов Activity ID")
    print("=" * 80)
    
    for activity_id, description in variants:
        print(f"\n📋 Попытка: {description}")
        print(f"   Activity ID: {activity_id}")
        
        url = f"{APS_BASE_URL}/da/us-east/v3/activities/{activity_id}/aliases"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {"id": "v1", "version": 1}
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✅ УСПЕХ! Alias создан:")
            print(f"      ID: {result.get('id')}")
            print(f"      Version: {result.get('version')}")
            return activity_id, result
        elif response.status_code == 409:
            print(f"   ⚠️  Alias уже существует (это хорошо!)")
            return activity_id, {"id": "v1", "version": 1, "status": "exists"}
        else:
            print(f"   ❌ Ошибка {response.status_code}: {response.text}")
    
    return None, None

def main():
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "🎯 Прямое создание Alias" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Получить токен
    print("\n🔑 Получение токена...")
    token = get_token()
    print("✅ Токен получен")
    
    # Список Activities для справки
    print("\n📋 Проверка доступных Activities...")
    activities = list_all_activities(token)
    bte_activities = [a for a in activities if 'BTEInsert' in a or 'BTI' in a]
    
    if bte_activities:
        print(f"✅ Найдено {len(bte_activities)} BTE Activities:")
        for act in bte_activities:
            print(f"   • {act}")
    
    # Попытка создать alias
    activity_id, alias_result = try_create_alias_variants(token)
    
    # Итог
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ")
    print("=" * 80)
    
    if alias_result:
        print(f"\n✅ Alias обработан для Activity: {activity_id}")
        print(f"   Alias ID: v1")
        print(f"   Status: {alias_result.get('status', 'created')}")
        
        print(f"\n🎯 Используйте в WorkItem:")
        print(f'   "activityId": "{activity_id}+v1"')
        
        print(f"\n🚀 Следующий шаг:")
        print(f"   python3 bte-appbundle/scripts/test_bte_insert.py")
        
        sys.exit(0)
    else:
        print(f"\n❌ Не удалось создать alias ни для одного варианта")
        print(f"\n💡 Рекомендация: создайте через Web UI")
        print(f"   https://aps.autodesk.com → Activities → BTEInsertTemplate → Aliases")
        
        sys.exit(1)

if __name__ == "__main__":
    main()

