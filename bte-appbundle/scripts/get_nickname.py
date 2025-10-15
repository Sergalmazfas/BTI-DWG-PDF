#!/usr/bin/env python3
"""
Получение nickname для Forge App
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

def get_forge_app(token):
    """Получить информацию о Forge App"""
    url = f"{APS_BASE_URL}/da/us-east/v3/forgeapps/me"
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
    print("📋 Получение информации о Forge App...\n")
    
    app_info = get_forge_app(token)
    
    if app_info:
        print("Информация о приложении:")
        print(f"  Client ID: {APS_CLIENT_ID}")
        
        # Ответ может быть строкой (nickname) или объектом
        if isinstance(app_info, str):
            nickname = app_info
            print(f"  Nickname: {nickname}")
        else:
            nickname = app_info.get('id')
            print(f"  Nickname: {nickname if nickname else 'НЕ УСТАНОВЛЕН'}")
            print(f"  Данные: {app_info}")
        
        if not nickname:
            print("\n❌ NICKNAME НЕ УСТАНОВЛЕН!")
            print("\n📝 Установите nickname:")
            print("   PATCH https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me")
            print('   Body: {"id": "YourNickname"}')
            print("\n   Или используйте стандартные Activities:")
            print("   • AutoCAD.PlotToPDF+25_0")
            print("   • AutoCAD.PlotToPDF+prod")
        else:
            print(f"\n✅ Nickname установлен: {nickname}")
            print(f"\n🎯 Используйте Activity ID:")
            print(f"   {nickname}.SimpleDWG2DWG_NoTemplate+1")
            print(f"   {nickname}.BTEInsertTemplate+1")
    else:
        print("❌ Не удалось получить информацию о приложении")
        print("\n💡 Альтернатива - используйте стандартную Activity:")
        print("   AutoCAD.PlotToPDF+25_0")

if __name__ == "__main__":
    main()

