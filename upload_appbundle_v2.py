#!/usr/bin/env python3
"""Загрузка AppBundle V2 с расширенными LISP скриптами"""

import requests
import subprocess
import sys
import os

def get_secret(name):
    result = subprocess.run(
        ['gcloud', 'secrets', 'versions', 'access', 'latest', f'--secret={name}', '--project=talkhint'],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def main():
    print("🚀 Загрузка AppBundle V2 в Autodesk APS")
    print("   6 LISP скриптов для полного формирования БТИ-чертежа\n")
    
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
    
    # Удаляем старый AppBundle
    appbundle_id = f'{nickname}.BtiPlugin'
    print(f"🗑️  Удаление старого {appbundle_id}...")
    
    delete_resp = requests.delete(
        f'https://developer.api.autodesk.com/da/us-east/v3/appbundles/{appbundle_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if delete_resp.status_code in [200, 204]:
        print("✅ Старый AppBundle удален")
    else:
        print(f"ℹ️  {delete_resp.status_code} (возможно не существовал)")
    
    # Создаем новый AppBundle V2
    new_appbundle_id = f'{nickname}.BtiPluginV2'
    print(f"\n📦 Создание нового {new_appbundle_id}...")
    
    create_data = {
        'id': new_appbundle_id,
        'engine': 'Autodesk.AutoCAD+25_1',
        'description': 'BTI Full Room Processor v2.0 - Ortho, Doors, Windows, Dimensions, Area (6 LISP scripts)'
    }
    
    create_resp = requests.post(
        'https://developer.api.autodesk.com/da/us-east/v3/appbundles',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json=create_data
    )
    
    if create_resp.status_code not in [200, 201]:
        print(f"❌ Ошибка создания: {create_resp.status_code}")
        print(create_resp.text)
        sys.exit(1)
    
    result = create_resp.json()
    version = result.get('version', 1)
    print(f"✅ AppBundle создан")
    print(f"   ID: {result['id']}")
    print(f"   Version: {version}")
    
    # Загрузка ZIP
    upload_params = result['uploadParameters']
    endpoint_url = upload_params['endpointURL']
    form_data = upload_params.get('formData', {})
    
    zip_path = '/tmp/bti_appbundle_v2/BtiPlugin_v2.zip'
    print(f"\n📤 Загрузка {os.path.basename(zip_path)} на S3...")
    
    with open(zip_path, 'rb') as f:
        files = {'file': f}
        upload_resp = requests.post(endpoint_url, data=form_data, files=files)
    
    if upload_resp.status_code in [200, 201, 204]:
        print("✅ ZIP загружен успешно")
    else:
        print(f"❌ Ошибка загрузки: {upload_resp.status_code}")
        sys.exit(1)
    
    # Создаем alias v2
    print(f"\n🏷️  Создание alias v2...")
    
    alias_url = f'https://developer.api.autodesk.com/da/us-east/v3/appbundles/{new_appbundle_id}/aliases'
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
    
    # Итог
    print("\n" + "="*60)
    print("✅ APPBUNDLE V2 УСПЕШНО ЗАГРУЖЕН!")
    print("="*60)
    print(f"\n📦 AppBundle: {new_appbundle_id}+v2")
    print(f"\n📝 Содержимое (6 LISP скриптов):")
    print(f"   🎨 BTI_APPLY_COLOR.lsp - Цветовое распознавание")
    print(f"   🔧 BTI_ORTHO_ADJUST.lsp - Выравнивание углов")
    print(f"   🚪 BTI_APPLY_OBJECTS.lsp - Двери и окна")
    print(f"   📏 BTI_DIM_AREA.lsp - Размеры и площадь")
    print(f"   📐 BTI_APPLY.lsp - Слоевое распознавание")
    print(f"   🧹 BTI_CLEANUP.lsp - Очистка")
    print(f"\n💡 Используйте в Activity:")
    print(f'   "appbundles": ["{new_appbundle_id}+v2"]')

if __name__ == "__main__":
    main()

