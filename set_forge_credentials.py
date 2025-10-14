#!/usr/bin/env python3
"""
Быстрая установка Forge credentials из командной строки
"""

import sys
import os

def main():
    if len(sys.argv) != 3:
        print("🔧 Использование: python3 set_forge_credentials.py <CLIENT_ID> <CLIENT_SECRET>")
        print("\n📋 Пример:")
        print("   python3 set_forge_credentials.py m6CK3YOUR_CLIENT_ID YOUR_CLIENT_SECRET")
        print("\n💡 Найти credentials: https://aps.autodesk.com/myapps/")
        sys.exit(1)
    
    client_id = sys.argv[1]
    client_secret = sys.argv[2]
    
    print("🚀 Установка Forge API Credentials")
    print("=" * 50)
    
    # Валидация
    if len(client_id) < 10:
        print("❌ Client ID кажется слишком коротким")
        sys.exit(1)
        
    if len(client_secret) < 10:
        print("❌ Client Secret кажется слишком коротким") 
        sys.exit(1)
    
    # Создаем .env файл
    env_content = f"""# Forge API Credentials
FORGE_CLIENT_ID={client_id}
FORGE_CLIENT_SECRET={client_secret}

# Дополнительные настройки (если нужно)
# AUTO_PDF=false
# GCP_PROJECT_ID=talkhint
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    # Устанавливаем в текущей сессии
    os.environ["FORGE_CLIENT_ID"] = client_id
    os.environ["FORGE_CLIENT_SECRET"] = client_secret
    
    print("✅ Credentials установлены:")
    print(f"   FORGE_CLIENT_ID: {client_id[:8]}...")
    print(f"   FORGE_CLIENT_SECRET: {client_secret[:8]}...")
    print("   📄 Сохранено в .env файле")
    
    # Тестируем
    print("\n🧪 Тестирование credentials...")
    
    try:
        from forge_client import ForgeClient
        
        client = ForgeClient()
        token = client.get_token()
        
        if token:
            print("✅ Отлично! Токен получен.")
            print(f"   Длина токена: {len(token)} символов")
            
            # Проверяем доступ к Design Automation API
            print("\n🚀 Проверка доступа к Design Automation API...")
            result = client.submit_workitem(
                "https://example.com/test.dwg",
                "https://example.com/test.pdf"
            )
            
            if "error" in result:
                error_text = str(result.get('error', '')).lower()
                if "does not have access to the api product" in error_text:
                    print("❌ Client ID все еще не имеет доступа к Design Automation API")
                    print("\n💡 Проверьте:")
                    print("   1. Правильность Client ID (должен начинаться с m6CK3...)")
                    print("   2. Наличие Design Automation API доступа в APS Portal")
                else:
                    print(f"❌ Другая ошибка: {result['error']}")
            else:
                print("🎉 Все работает! Design Automation API доступен!")
                return True
        else:
            print("❌ Не удалось получить токен")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

if __name__ == "__main__":
    main()