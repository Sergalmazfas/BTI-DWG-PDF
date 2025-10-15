#!/usr/bin/env python3
"""
Создание alias v1 для SimpleDWG2DWG_NoTemplate
Эта Activity гарантированно работает
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
        "scope": "code:all"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return response.json()['access_token']

def main():
    print("=" * 80)
    print("🚀 Создание alias v1 для SimpleDWG2DWG_NoTemplate")
    print("=" * 80)
    
    token = get_token()
    print("✅ Токен получен\n")
    
    # Создание alias БЕЗ nickname (как и для BTEInsertTemplate)
    url = f"{APS_BASE_URL}/da/us-east/v3/activities/SimpleDWG2DWG_NoTemplate/aliases"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"id": "v1", "version": 1}
    
    print(f"🏷️  Создание alias...")
    print(f"   Activity: SimpleDWG2DWG_NoTemplate")
    print(f"   Alias: v1 → Version 1")
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\n✅ Alias создан!")
        print(f"   ID: {result.get('id')}")
        print(f"   Version: {result.get('version')}")
        print(f"\n🎯 Используйте:")
        print(f'   "activityId": "BotBti.SimpleDWG2DWG_NoTemplate+v1"')
    elif response.status_code == 409:
        print(f"\n✅ Alias уже существует (это хорошо!)")
    else:
        print(f"\n❌ Ошибка: {response.status_code}")
        print(response.text)
        sys.exit(1)

if __name__ == "__main__":
    main()

