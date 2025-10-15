#!/usr/bin/env python3
"""Создание простой Activity без цветового распознавания"""

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

print("🚀 Создание Activity BTI_SIMPLE_PROCESS")
print("   Без цветового распознавания, только слои\n")

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

if 'access_token' not in token_resp.json():
    print(f"❌ Ошибка получения токена: {token_resp.text}")
    sys.exit(1)

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

# Загружаем конфигурацию
with open('forge/activity_bti_simple.json', 'r') as f:
    activity_data = json.load(f)

activity_id = activity_data['id']

# Удаляем старую если есть
print(f"🗑️  Удаление старой Activity (если есть)...")
delete_resp = requests.delete(
    f'https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}',
    headers={'Authorization': f'Bearer {token}'}
)
if delete_resp.status_code in [200, 204]:
    print("✅ Удалено")

# Создаем новую
print(f"\n📦 Создание Activity {activity_id}...")
create_resp = requests.post(
    'https://developer.api.autodesk.com/da/us-east/v3/activities',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    json=activity_data
)

if create_resp.status_code not in [200, 201]:
    print(f"❌ Ошибка: {create_resp.status_code}")
    print(create_resp.text)
    sys.exit(1)

result = create_resp.json()
version = result.get('version', 1)

print(f"✅ Activity создана")
print(f"   ID: {result['id']}")
print(f"   Version: {version}")

# Создаем alias $LATEST
print(f"\n🏷️  Создание alias $LATEST...")
alias_url = f'https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}/aliases'
alias_data = {'id': '$LATEST', 'version': version}

alias_resp = requests.post(
    alias_url,
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    json=alias_data
)

if alias_resp.status_code in [200, 201]:
    print("✅ Alias $LATEST создан")
elif alias_resp.status_code == 409:
    # Alias уже существует, обновляем
    patch_resp = requests.patch(
        f'{alias_url}/$LATEST',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={'version': version}
    )
    if patch_resp.status_code in [200, 201]:
        print("✅ Alias $LATEST обновлен")

print("\n" + "="*60)
print("✅ ACTIVITY СОЗДАНА!")
print("="*60)
print(f"\n📦 Activity: {activity_id}+$LATEST")
print(f"\n💡 Используйте в forge_client.py:")
print(f'   BTI_SIMPLE_PROCESS = "{activity_id}+$LATEST"')
