#!/usr/bin/env python3
"""
Скрипт для обновления Forge credentials
Поддерживает как локальные переменные окружения, так и Google Secret Manager
"""

import os
import sys
import json
import subprocess
from typing import Tuple, Optional

def check_gcloud_auth() -> bool:
    """Проверить, аутентифицирован ли gcloud"""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            accounts = json.loads(result.stdout)
            return len(accounts) > 0
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return False

def update_local_env(client_id: str, client_secret: str):
    """Обновить локальные переменные окружения"""
    print("🔧 Обновление локальных переменных окружения...")
    
    # Запись в .env файл
    env_content = f"""# Forge API Credentials
FORGE_CLIENT_ID={client_id}
FORGE_CLIENT_SECRET={client_secret}
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    # Установка в текущей сессии
    os.environ["FORGE_CLIENT_ID"] = client_id
    os.environ["FORGE_CLIENT_SECRET"] = client_secret
    
    print("✅ Локальные переменные обновлены:")
    print(f"   FORGE_CLIENT_ID: {client_id[:8]}...")
    print(f"   FORGE_CLIENT_SECRET: {client_secret[:8]}...")
    print(f"   📄 Сохранено в .env файле")

def update_gcp_secrets(client_id: str, client_secret: str) -> bool:
    """Обновить секреты в Google Cloud Secret Manager"""
    print("☁️ Обновление секретов в Google Cloud...")
    
    try:
        # Обновляем Client ID
        print("   📝 Обновление FORGE_CLIENT_ID...")
        result1 = subprocess.run(
            ["gcloud", "secrets", "versions", "add", "FORGE_CLIENT_ID", "--data-file=-"],
            input=client_id,
            text=True,
            capture_output=True,
            timeout=30
        )
        
        if result1.returncode != 0:
            print(f"   ❌ Ошибка обновления Client ID: {result1.stderr}")
            return False
        
        # Обновляем Client Secret
        print("   🔐 Обновление FORGE_CLIENT_SECRET...")
        result2 = subprocess.run(
            ["gcloud", "secrets", "versions", "add", "FORGE_CLIENT_SECRET", "--data-file=-"],
            input=client_secret,
            text=True,
            capture_output=True,
            timeout=30
        )
        
        if result2.returncode != 0:
            print(f"   ❌ Ошибка обновления Client Secret: {result2.stderr}")
            return False
        
        print("✅ Секреты Google Cloud обновлены:")
        print(f"   FORGE_CLIENT_ID: {client_id[:8]}... (новая версия)")
        print(f"   FORGE_CLIENT_SECRET: {client_secret[:8]}... (новая версия)")
        return True
        
    except subprocess.TimeoutExpired:
        print("   ❌ Таймаут при обновлении секретов")
        return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False

def validate_credentials(client_id: str, client_secret: str) -> bool:
    """Проверить валидность credentials"""
    if not client_id or not client_secret:
        return False
    
    if len(client_id) < 10:
        print("   ⚠️ Client ID кажется слишком коротким")
        return False
        
    if len(client_secret) < 10:
        print("   ⚠️ Client Secret кажется слишком коротким")
        return False
    
    return True

def get_credentials_input() -> Tuple[str, str]:
    """Получить credentials от пользователя"""
    print("\n🔑 Введите новые Forge credentials:")
    print("   (Найти их можно на https://aps.autodesk.com/myapps/)")
    print()
    
    client_id = input("📋 Client ID: ").strip()
    client_secret = input("🔐 Client Secret: ").strip()
    
    return client_id, client_secret

def test_credentials():
    """Протестировать новые credentials"""
    print("\n🧪 Тестирование новых credentials...")
    try:
        # Импортируем и тестируем forge_client
        from forge_client import ForgeClient
        
        client = ForgeClient()
        token = client.get_token()
        
        if token:
            print("✅ Credentials работают! Токен получен.")
            return True
        else:
            print("❌ Не удалось получить токен с новыми credentials")
            return False
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

def main():
    print("🚀 Обновление Forge API Credentials")
    print("=" * 50)
    
    # Получаем новые credentials
    client_id, client_secret = get_credentials_input()
    
    # Валидируем
    if not validate_credentials(client_id, client_secret):
        print("❌ Некорректные credentials")
        sys.exit(1)
    
    # Определяем доступные методы обновления
    gcloud_available = check_gcloud_auth()
    
    print(f"\n📊 Доступные методы обновления:")
    print(f"   Локальные переменные: ✅")
    print(f"   Google Cloud Secrets: {'✅' if gcloud_available else '❌ (gcloud не настроен)'}")
    
    # Выбираем методы обновления
    methods = ["local"]
    if gcloud_available:
        methods.append("gcp")
    
    success_count = 0
    
    # Локальное обновление
    try:
        update_local_env(client_id, client_secret)
        success_count += 1
    except Exception as e:
        print(f"❌ Ошибка локального обновления: {e}")
    
    # GCP обновление (если доступно)
    if gcloud_available:
        if update_gcp_secrets(client_id, client_secret):
            success_count += 1
    
    # Результат
    if success_count > 0:
        print(f"\n🎉 Credentials обновлены! ({success_count}/{len(methods)} методов)")
        
        # Тестируем
        if test_credentials():
            print("\n✅ Все готово! Design Automation API должен теперь работать.")
            
            print("\n📋 Следующие шаги:")
            if gcloud_available:
                print("   1. Перезапустить сервис в Cloud Run:")
                print("      gcloud run deploy dwg-processor-metadata --region europe-west1")
            print("   2. Протестировать бота с DWG файлом")
            print("   3. Проверить логи на отсутствие ошибок")
        else:
            print("\n⚠️ Credentials обновлены, но тест не прошел.")
            print("   Проверьте правильность Client ID и Secret.")
    else:
        print("\n❌ Не удалось обновить credentials")
        sys.exit(1)

if __name__ == "__main__":
    main()