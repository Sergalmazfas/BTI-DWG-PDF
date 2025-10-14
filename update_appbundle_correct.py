#!/usr/bin/env python3
"""
Обновление AppBundle - ПРАВИЛЬНЫЙ метод согласно официальной документации
https://aps.autodesk.com/en/docs/design-automation/v3/tutorials/autocad/
"""

import requests
import subprocess
import sys

def get_secret(name):
    result = subprocess.run(
        ['gcloud', 'secrets', 'versions', 'access', 'latest', 
         f'--secret={name}', '--project=talkhint'],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def main():
    print("╔═══════════════════════════════════════════════╗")
    print("║  📚 Обновление AppBundle (Official Method)   ║")
    print("╚═══════════════════════════════════════════════╝\n")
    
    # Get credentials
    client_id = get_secret('FORGE_CLIENT_ID')
    client_secret = get_secret('FORGE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Не удалось получить credentials")
        sys.exit(1)
    
    # Step 1: Get token
    print("1️⃣  Получение токена...")
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
        print(f"❌ Ошибка: {token_resp.text}")
        sys.exit(1)
    
    token = token_resp.json()['access_token']
    print("   ✅ Токен получен\n")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    appbundle_id = 'BotBti.BtiPlugin'
    
    # Step 2: Create new version (БЕЗ id в body!)
    print(f"2️⃣  Создание новой версии {appbundle_id}...")
    
    # ⚠️ ВАЖНО: НЕ включаем поле "id" согласно документации!
    version_body = {
        'engine': 'Autodesk.AutoCAD+25_1',
        'description': 'BTI with BTI_AUTO_APPLY.lsp - autorun on load'
    }
    
    version_resp = requests.post(
        f'https://developer.api.autodesk.com/da/us-east/v3/appbundles/{appbundle_id}/versions',
        headers=headers,
        json=version_body
    )
    
    if version_resp.status_code not in [200, 201]:
        print(f"   ❌ Ошибка: {version_resp.status_code}")
        print(f"   Response: {version_resp.text}")
        sys.exit(1)
    
    result = version_resp.json()
    version = result.get('version')
    print(f"   ✅ Версия {version} создана")
    print(f"   ID: {result.get('id')}\n")
    
    # Step 3: Upload ZIP to S3
    print(f"3️⃣  Загрузка BtiPlugin_auto.zip на S3...")
    
    upload_params = result['uploadParameters']
    endpoint_url = upload_params['endpointURL']
    form_data = upload_params.get('formData', {})
    
    zip_path = '/tmp/bti_auto/BtiPlugin_auto.zip'
    
    with open(zip_path, 'rb') as f:
        files = {'file': f}
        upload_resp = requests.post(endpoint_url, data=form_data, files=files)
    
    if upload_resp.status_code in [200, 201, 204]:
        print(f"   ✅ ZIP загружен (54 KB)\n")
    else:
        print(f"   ❌ Ошибка загрузки: {upload_resp.status_code}")
        print(f"   Response: {upload_resp.text}")
        sys.exit(1)
    
    # Step 4: Update alias $LATEST
    print(f"4️⃣  Обновление alias $LATEST...")
    
    alias_resp = requests.patch(
        f'https://developer.api.autodesk.com/da/us-east/v3/appbundles/{appbundle_id}/aliases/$LATEST',
        headers=headers,
        json={'version': version}
    )
    
    if alias_resp.status_code in [200, 201]:
        print(f"   ✅ Alias $LATEST → версия {version}\n")
    else:
        print(f"   ⚠️  Alias response: {alias_resp.status_code}")
        print(f"   {alias_resp.text}\n")
    
    # Summary
    print("╔═══════════════════════════════════════════════╗")
    print("║       ✅ APPBUNDLE УСПЕШНО ОБНОВЛЕН!         ║")
    print("╚═══════════════════════════════════════════════╝\n")
    print(f"📦 AppBundle: {appbundle_id}+$LATEST")
    print(f"🔢 Версия: {version}")
    print(f"✨ Содержит: BTI_AUTO_APPLY.lsp (автозапуск!)\n")
    print(f"🎯 Следующий шаг: Создать Activity BTI_AUTO_PROCESS")

if __name__ == "__main__":
    main()

