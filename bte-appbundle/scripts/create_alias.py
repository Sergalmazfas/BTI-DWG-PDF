#!/usr/bin/env python3
"""
Создание alias 'v1' для Activity BotBti.BTEInsertTemplate через Autodesk APS API

Официальная документация:
https://aps.autodesk.com/en/docs/design-automation/v3/reference/http/aliases-POST/

Endpoint: POST /activities/{activity_id}/aliases
"""

import os
import sys
import json
import requests

# APS credentials
APS_CLIENT_ID = os.getenv('APS_CLIENT_ID', 'm6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4')
APS_CLIENT_SECRET = os.getenv('APS_CLIENT_SECRET', 'tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW')
APS_BASE_URL = "https://developer.api.autodesk.com"

# Конфигурация alias
ACTIVITY_ID = "BotBti.BTEInsertTemplate"
ALIAS_ID = "v1"
ALIAS_VERSION = 1


def get_access_token():
    """Получить токен доступа APS"""
    # Проверяем переменную окружения
    token = os.getenv("APS_TOKEN")
    if token:
        print(f"🔑 Используется токен из APS_TOKEN")
        return token
    
    # Получаем новый токен
    print("🔑 Получение нового токена APS...")
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
        sys.exit(1)
    
    token = response.json()['access_token']
    print("✅ Токен получен")
    return token


def get_activity_info(token, activity_id):
    """Получить информацию о Activity для проверки версии"""
    url = f"{APS_BASE_URL}/da/us-east/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"⚠️  Не удалось получить информацию о Activity: {response.status_code}")
        print(response.text)
        return None


def check_existing_aliases(token, activity_id):
    """Проверить существующие aliases"""
    url = f"{APS_BASE_URL}/da/us-east/v3/activities/{activity_id}/aliases"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n📋 Проверка существующих aliases для {activity_id}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        aliases = response.json()
        alias_list = aliases.get('data', [])
        
        if alias_list:
            print(f"   Найдено aliases: {len(alias_list)}")
            for alias in alias_list:
                print(f"   • {alias}")
            return alias_list
        else:
            print("   Aliases не найдены")
            return []
    else:
        print(f"⚠️  Ошибка проверки aliases: {response.status_code}")
        print(response.text)
        return None


def delete_alias(token, activity_id, alias_id):
    """Удалить существующий alias"""
    url = f"{APS_BASE_URL}/da/us-east/v3/activities/{activity_id}/aliases/{alias_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"🗑️  Удаление существующего alias '{alias_id}'...")
    response = requests.delete(url, headers=headers)
    
    if response.status_code in [200, 204]:
        print(f"✅ Alias '{alias_id}' удалён")
        return True
    else:
        print(f"⚠️  Не удалось удалить alias: {response.status_code}")
        print(response.text)
        return False


def create_alias(token, activity_id, alias_id, version):
    """Создать alias для Activity
    
    Официальная документация:
    https://aps.autodesk.com/en/docs/design-automation/v3/reference/http/aliases-POST/
    
    Request Body:
    {
        "id": "string",      # Alias ID (например "v1", "prod")
        "version": integer,  # Версия Activity (например 1, 2, 3)
        "receiver": "string" # Опционально, обычно не используется
    }
    """
    
    url = f"{APS_BASE_URL}/da/us-east/v3/activities/{activity_id}/aliases"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Согласно документации, receiver не обязателен
    payload = {
        "id": alias_id,
        "version": version
    }
    
    print(f"\n🚀 Создание alias '{alias_id}' для {activity_id}...")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\n✅ Alias создан successfully!")
        print(f"   ID: {result.get('id')}")
        print(f"   Version: {result.get('version')}")
        print(f"   Full Activity ID: {activity_id}+{alias_id}")
        return result
    elif response.status_code == 409:
        print(f"\n⚠️  Alias уже существует (409 Conflict)")
        print(response.text)
        return None
    else:
        print(f"\n❌ Ошибка создания alias: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Дополнительная диагностика
        if "Cannot parse id" in response.text:
            print("\n💡 Диагностика:")
            print("   Ошибка 'Cannot parse id' может означать:")
            print("   1. Activity ID неправильный")
            print("   2. Activity не существует")
            print("   3. У вас нет прав на создание alias")
            print("   4. Nickname не установлен для приложения")
        
        return None


def verify_alias(token, activity_id, alias_id):
    """Проверить созданный alias"""
    url = f"{APS_BASE_URL}/da/us-east/v3/activities/{activity_id}/aliases/{alias_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n🔍 Проверка alias '{alias_id}'...")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        alias_data = response.json()
        print(f"✅ Alias найден и активен:")
        print(f"   ID: {alias_data.get('id')}")
        print(f"   Version: {alias_data.get('version')}")
        return True
    else:
        print(f"❌ Alias не найден: {response.status_code}")
        return False


def main():
    print("=" * 80)
    print("🤖 Создание Alias для BTEInsertTemplate Activity")
    print("=" * 80)
    
    # Получить токен
    token = get_access_token()
    
    # Получить информацию о Activity
    print(f"\n📋 Проверка Activity: {ACTIVITY_ID}")
    activity_info = get_activity_info(token, ACTIVITY_ID)
    
    if activity_info:
        print(f"✅ Activity найдена:")
        print(f"   ID: {activity_info.get('id')}")
        print(f"   Version: {activity_info.get('version')}")
        print(f"   Engine: {activity_info.get('engine')}")
    else:
        print(f"⚠️  Activity информация недоступна")
    
    # Проверить существующие aliases
    existing_aliases = check_existing_aliases(token, ACTIVITY_ID)
    
    # Если alias уже существует, предложить удалить
    if existing_aliases and ALIAS_ID in existing_aliases:
        print(f"\n⚠️  Alias '{ALIAS_ID}' уже существует!")
        response = input("Удалить и пересоздать? (y/N): ")
        if response.lower() == 'y':
            delete_alias(token, ACTIVITY_ID, ALIAS_ID)
            # Небольшая задержка после удаления
            import time
            time.sleep(2)
        else:
            print("Выход без изменений")
            sys.exit(0)
    
    # Создать alias
    result = create_alias(token, ACTIVITY_ID, ALIAS_ID, ALIAS_VERSION)
    
    if result:
        # Проверить созданный alias
        if verify_alias(token, ACTIVITY_ID, ALIAS_ID):
            print("\n" + "=" * 80)
            print("🎉 УСПЕХ! Alias готов к использованию")
            print("=" * 80)
            print(f"\n🎯 Используйте в WorkItem:")
            print(f'   "activityId": "{ACTIVITY_ID}+{ALIAS_ID}"')
            print(f"\n📝 Пример WorkItem:")
            print(f'''
{{
  "activityId": "{ACTIVITY_ID}+{ALIAS_ID}",
  "arguments": {{
    "inputFile": {{
      "url": "https://..."
    }},
    "resultFile": {{
      "url": "https://...",
      "verb": "put"
    }}
  }}
}}
            ''')
            
            # Теперь можно запустить тест
            print("\n🚀 Следующий шаг:")
            print("   python3 bte-appbundle/scripts/test_bte_insert.py")
            
            sys.exit(0)
        else:
            print("\n❌ Alias создан, но проверка не прошла")
            sys.exit(1)
    else:
        print("\n❌ Не удалось создать alias")
        print("\n💡 Альтернатива:")
        print("   Создайте alias через Web UI:")
        print("   1. https://aps.autodesk.com")
        print("   2. My Apps → Design Automation → AutoCAD")
        print("   3. Activities → BTEInsertTemplate → Aliases → Create")
        print("   4. ID: v1, Version: 1, Save")
        sys.exit(1)


if __name__ == "__main__":
    main()

