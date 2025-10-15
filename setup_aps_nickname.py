#!/usr/bin/env python3
"""
Setup Autodesk APS Nickname (ForgeAppName)
Регистрирует Client ID для использования Design Automation API
"""

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
        "scope": "code:all"
    }
    
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()["access_token"]

def get_nickname(token):
    """Получить текущий nickname"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        # API возвращает строку с nickname или пустой объект
        if isinstance(data, dict):
            return data
        elif isinstance(data, str):
            return {"id": data}
        return {"id": data} if data else None
    return None

def create_nickname(token, nickname):
    """Создать nickname (ForgeAppName)"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {"nickname": nickname}
    
    response = requests.patch(url, headers=headers, json=data)
    return response

def main():
    print("🚀 Setup Autodesk APS Nickname (ForgeAppName)\n")
    
    # Получаем credentials
    print("🔑 Получаем credentials из Secret Manager...")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    
    print(f"✅ Client ID: {client_id[:20]}...")
    
    # Получаем токен
    print("\n🔐 Получаем APS токен...")
    token = get_aps_token(client_id, client_secret)
    print("✅ Токен получен")
    
    # Проверяем текущий nickname
    print("\n📝 Проверяем текущий nickname...")
    current = get_nickname(token)
    
    if current and current.get("id"):
        print(f"✅ Nickname уже установлен: {current['id']}")
        return
    
    # Создаем новый nickname
    nickname = "BotBti"  # Используем существующий или новый
    print(f"\n🔧 Создаем nickname: {nickname}")
    
    response = create_nickname(token, nickname)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Nickname создан: {result.get('id')}")
        print(f"\n🎉 Готово! Client ID теперь может использовать Design Automation API")
        print(f"📝 Используйте Owner ID: {result.get('id')}")
    else:
        print(f"❌ Ошибка создания nickname: {response.status_code}")
        print(f"   {response.text}")
        
        # Попробуем другие варианты
        alternatives = ["BotBtiApp", "BTIDWGProcessor", "BTIProcessor", "BTIAutoCAD"]
        for alt_nickname in alternatives:
            print(f"\n🔄 Пробуем альтернативное имя: {alt_nickname}")
            response = create_nickname(token, alt_nickname)
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ Nickname создан: {result.get('id')}")
                print(f"\n🎉 Готово! Client ID теперь может использовать Design Automation API")
                print(f"📝 Используйте Owner ID: {result.get('id')}")
                return
            else:
                print(f"   ❌ {response.status_code}: {response.text}")
        
        print("\n❌ Не удалось создать nickname. Попробуйте через Web UI:")
        print("   https://aps.autodesk.com/en/docs/design-automation/v3/tutorials/autocad/task-1-create-appbundle/")

if __name__ == "__main__":
    main()

