#!/usr/bin/env python3
"""Создание Activity для AppBundle V2 (полный процесс обработки)"""

import requests
import subprocess
import sys
import json

def get_secret(name):
    result = subprocess.run(
        ['gcloud', 'secrets', 'versions', 'access', 'latest', f'--secret={name}', '--project=talkhint'],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def main():
    print("🚀 Создание Activity для BTI Full Room V2")
    print("   AppBundle: BotBti.BtiPluginV2+v2\n")
    
    # Credentials
    client_id = get_secret('FORGE_CLIENT_ID')
    client_secret = get_secret('FORGE_CLIENT_SECRET')
    
    # Token
    token_resp = requests.post(
        'https://developer.api.autodesk.com/authentication/v2/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
            'scope': 'code:all'
        }
    )
    token = token_resp.json()['access_token']
    print("✅ Токен получен")
    
    # Nickname
    nick_resp = requests.get(
        'https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me',
        headers={'Authorization': f'Bearer {token}'}
    )
    nickname_data = nick_resp.json()
    nickname = nickname_data if isinstance(nickname_data, str) else nickname_data.get('id', 'BotBti')
    print(f"✅ Nickname: {nickname}\n")
    
    # Загружаем конфигурацию Activity из JSON
    with open('forge/activity_full_room_v2.json', 'r') as f:
        activity_data = json.load(f)
    
    activity_id = activity_data['id']
    
    # Проверяем существует ли Activity
    print(f"🔍 Проверка Activity {activity_id}...")
    check_resp = requests.get(
        f'https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if check_resp.status_code == 200:
        print(f"⚠️  Activity {activity_id} уже существует")
        print(f"🗑️  Удаление старой версии...")
        
        delete_resp = requests.delete(
            f'https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if delete_resp.status_code in [200, 204]:
            print(f"✅ Удалено")
        else:
            print(f"⚠️  {delete_resp.status_code}")
    
    # Создаем новую Activity
    print(f"\n📦 Создание Activity {activity_id}...")
    
    create_resp = requests.post(
        'https://developer.api.autodesk.com/da/us-east/v3/activities',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json=activity_data
    )
    
    if create_resp.status_code not in [200, 201]:
        print(f"❌ Ошибка создания: {create_resp.status_code}")
        print(create_resp.text)
        sys.exit(1)
    
    result = create_resp.json()
    version = result.get('version', 1)
    
    print(f"✅ Activity создана")
    print(f"   ID: {result['id']}")
    print(f"   Version: {version}")
    print(f"   Engine: {result['engine']}")
    
    # Создаем alias v2
    print(f"\n🏷️  Создание alias v2...")
    
    alias_url = f'https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}/aliases'
    alias_data = {'id': 'v2', 'version': version}
    
    alias_resp = requests.post(
        alias_url,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json=alias_data
    )
    
    if alias_resp.status_code in [200, 201]:
        print("✅ Alias v2 создан")
    else:
        print(f"⚠️  Alias: {alias_resp.status_code}")
        # Может уже существовать, попробуем обновить
        patch_resp = requests.patch(
            f'{alias_url}/v2',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={'version': version}
        )
        if patch_resp.status_code in [200, 201]:
            print("✅ Alias v2 обновлен")
    
    # Итог
    print("\n" + "="*70)
    print("✅ ACTIVITY V2 УСПЕШНО СОЗДАНА!")
    print("="*70)
    print(f"\n📦 Activity: {activity_id}+v2")
    print(f"\n🔄 Процесс обработки:")
    print(f"   1. BTI_APPLY_COLOR - Цветовое распознавание")
    print(f"   2. BTI_ORTHO_ADJUST - Выравнивание углов")
    print(f"   3. BTI_APPLY_OBJECTS - Двери и окна")
    print(f"   4. BTI_DIM_AREA - Размеры и площадь")
    print(f"   5. BTI_CLEANUP - Очистка")
    print(f"\n💡 Используйте в WorkItem:")
    print(f'   "activityId": "{activity_id}+v2"')
    
    # Сохраняем информацию
    activity_info = {
        "activity_id": activity_id,
        "full_id": f"{activity_id}+v2",
        "version": version,
        "engine": result['engine'],
        "appbundle": "BotBti.BtiPluginV2+v2",
        "status": "created"
    }
    
    with open('BTI_ACTIVITY_V2_INFO.json', 'w') as f:
        json.dump(activity_info, f, indent=2)
    
    print(f"\n📄 Информация сохранена в BTI_ACTIVITY_V2_INFO.json")

if __name__ == "__main__":
    main()

