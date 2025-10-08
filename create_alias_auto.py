#!/usr/bin/env python3
"""
Автоматическое создание alias 'v1' для SimpleDWG2DWG_NoTemplate
через Autodesk APS API
"""

import subprocess
import requests
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
    print("🏷️  СОЗДАНИЕ ALIAS 'v1' ДЛЯ SimpleDWG2DWG_NoTemplate")
    print("=" * 70)
    
    # 1. Получить credentials
    print("\n🔑 Получение credentials...")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    print(f"   Client ID: {client_id[:30]}...")
    
    # 2. Получить токен
    print("\n🔑 Получение access token...")
    auth_response = requests.post(
        "https://developer.api.autodesk.com/authentication/v2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "code:all"
        }
    )
    
    if auth_response.status_code != 200:
        print(f"❌ Ошибка авторизации: {auth_response.text}")
        sys.exit(1)
    
    access_token = auth_response.json()["access_token"]
    print("   ✅ Token получен")
    
    # 3. Создать alias
    print("\n🏷️  Создание alias 'v1' → version 1...")
    
    activity_id = f"{client_id}.SimpleDWG2DWG_NoTemplate"
    alias_data = {
        "id": "v1",
        "version": 1
    }
    
    alias_response = requests.post(
        f"https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}/aliases",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json=alias_data
    )
    
    print(f"   Response: {alias_response.status_code}")
    
    if alias_response.status_code in [200, 201]:
        result = alias_response.json()
        print(f"\n✅ ALIAS СОЗДАН УСПЕШНО!")
        print(f"   Alias: {result.get('id')}")
        print(f"   Version: {result.get('version')}")
        print(f"   Full ID: {activity_id}+v1")
        print(f"\n🎯 Теперь можно использовать в bot:")
        print(f"   activityId: \"{activity_id}+v1\"")
        return True
        
    elif alias_response.status_code == 409:
        print(f"   ⚠️  Alias 'v1' уже существует")
        print(f"   Full ID: {activity_id}+v1")
        print(f"\n✅ МОЖНО ИСПОЛЬЗОВАТЬ!")
        return True
        
    else:
        print(f"\n❌ ОШИБКА создания alias:")
        print(f"   Status: {alias_response.status_code}")
        print(f"   Response: {alias_response.text}")
        print(f"\n💡 АЛЬТЕРНАТИВА:")
        print(f"   1. Открыть: https://aps.autodesk.com")
        print(f"   2. My Apps → Design Automation → AutoCAD")
        print(f"   3. Activities → SimpleDWG2DWG_NoTemplate")
        print(f"   4. Aliases → Create Alias")
        print(f"   5. ID: v1, Version: 1, Save")
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 70)
    sys.exit(0 if success else 1)

