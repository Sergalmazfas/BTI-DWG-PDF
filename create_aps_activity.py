"""
Скрипт для создания Activity в Autodesk APS
Запускается один раз для настройки BTIProcessor.GenerateDWG
"""

import os
import sys
from forge_client import ForgeClient

def main():
    """Создает Activity BTIProcessor.GenerateDWG в Autodesk APS"""
    
    print("🚀 Создание Activity BTIProcessor.GenerateDWG в Autodesk APS...")
    
    try:
        # Создаем клиент
        forge_client = ForgeClient()
        
        # Проверяем credentials
        print(f"✅ Client ID: {forge_client.client_id[:10]}...")
        print(f"✅ Engine: {forge_client.engine}")
        
        # Получаем токен для проверки
        token = forge_client.get_access_token()
        print(f"✅ Access Token получен: {token[:20]}...")
        
        # Создаем Activity
        result = forge_client.create_activity()
        
        if result.get("status") == "exists":
            print("ℹ️ Activity BTIProcessor.GenerateDWG уже существует")
        else:
            print("✅ Activity BTIProcessor.GenerateDWG успешно создан")
            print(f"📋 Activity ID: {result.get('id', 'Unknown')}")
        
        print("\n🎉 Готово! Activity настроен для использования в BTI Processor")
        
    except Exception as e:
        print(f"❌ Ошибка создания Activity: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
