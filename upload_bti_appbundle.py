#!/usr/bin/env python3
"""
Автоматическая загрузка BTI AppBundle в Autodesk APS
После компиляции на Windows
"""
import os
import sys
import subprocess
import requests
import json
import argparse

def get_secret(name):
    """Получить секрет из Google Secret Manager"""
    result = subprocess.run(
        ["gcloud", "secrets", "versions", "access", "latest", f"--secret={name}", "--project=talkhint"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def get_access_token(client_id, client_secret):
    """Получить OAuth2 токен от Autodesk"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    
    response = requests.post(url, data=data)
    response.raise_for_status()
    
    token = response.json()["access_token"]
    print(f"✅ OAuth2 токен получен")
    return token

def delete_appbundle(token, appbundle_id):
    """Удалить существующий AppBundle"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/appbundles/{appbundle_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.delete(url, headers=headers)
    if response.status_code in [200, 204]:
        print(f"🗑️  Старый AppBundle удалён")
    elif response.status_code == 404:
        print(f"ℹ️  AppBundle не существовал")
    else:
        print(f"⚠️  Удаление: {response.status_code}")

def create_appbundle(token, client_id, zip_path):
    """Создать и загрузить AppBundle"""
    print(f"\n📦 Создание AppBundle: BTI_InsertBasman")
    
    appbundle_id = "BTI_InsertBasman"
    full_id = f"{client_id}.{appbundle_id}"
    
    # Удаляем старую версию
    delete_appbundle(token, full_id)
    
    # Создаём новый AppBundle
    url = "https://developer.api.autodesk.com/da/us-east/v3/appbundles"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "id": appbundle_id,
        "engine": "Autodesk.AutoCAD+25_1",
        "description": "BTI Insert Basmann Template Plugin (.NET)"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code not in [200, 201]:
        print(f"❌ Ошибка создания AppBundle: {response.status_code}")
        print(response.text)
        return None
    
    result = response.json()
    print(f"✅ AppBundle создан: {result['id']}")
    print(f"   Version: {result.get('version', 1)}")
    
    # Загружаем ZIP
    if "uploadParameters" in result:
        upload_params = result["uploadParameters"]
        endpoint_url = upload_params["endpointURL"]
        form_data = upload_params.get("formData", {})
        
        print(f"\n📤 Загрузка ZIP: {zip_path}")
        
        if not os.path.exists(zip_path):
            print(f"❌ ZIP не найден: {zip_path}")
            print(f"\n💡 Скомпилируйте плагин на Windows:")
            print(f"   cd BTI_TemplateAppBundle")
            print(f"   msbuild BTI_InsertBasman.csproj /p:Configuration=Release")
            return None
        
        # Подготовка multipart/form-data
        files = {'file': open(zip_path, 'rb')}
        upload_response = requests.post(endpoint_url, data=form_data, files=files)
        files['file'].close()
        
        if upload_response.status_code in [200, 201, 204]:
            print(f"✅ ZIP загружен успешно")
        else:
            print(f"❌ Ошибка загрузки: {upload_response.status_code}")
            print(upload_response.text)
            return None
    
    return result

def create_alias(token, appbundle_id, version=1):
    """Создать alias для AppBundle"""
    print(f"\n🏷️  Создание alias v1...")
    
    url = f"https://developer.api.autodesk.com/da/us-east/v3/appbundles/{appbundle_id}/aliases"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {"id": "v1", "version": version}
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"✅ Alias v1 создан")
        return True
    elif response.status_code == 409:
        # Alias существует, обновляем
        patch_url = f"{url}/v1"
        patch_response = requests.patch(patch_url, headers=headers, json={"version": version})
        if patch_response.status_code == 200:
            print(f"✅ Alias v1 обновлён")
            return True
    
    print(f"⚠️  Alias: {response.status_code} - {response.text}")
    return False

def create_activity(token, client_id, appbundle_id):
    """Создать Activity с AppBundle"""
    print(f"\n🎯 Создание Activity: DWG2DWG_InsertBasman")
    
    activity_id = "DWG2DWG_InsertBasman"
    full_id = f"{client_id}.{activity_id}"
    
    # Удаляем старую
    delete_url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{full_id}"
    requests.delete(delete_url, headers={"Authorization": f"Bearer {token}"})
    
    # Создаём новую Activity
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # URL шаблона Басманная
    template_url = "https://storage.googleapis.com/btibot-processed/templates/basmanny-template.dwg"
    
    activity_spec = {
        "id": activity_id,
        "commandLine": [
            '$(engine.path)\\\\accoreconsole.exe /i "$(args[inputFile].path)" /al "$(appbundles[BTI_InsertBasman].path)" /s "InsertBTIBasman\\n"'
        ],
        "parameters": {
            "inputFile": {
                "verb": "get",
                "description": "Input DWG file",
                "required": True,
                "localName": "input.dwg"
            },
            "templateFile": {
                "verb": "get",
                "description": "BTI Basmann template",
                "required": True,
                "localName": "template.dwg",
                "url": template_url
            },
            "resultFile": {
                "verb": "put",
                "description": "Output DWG with BTI template",
                "required": True,
                "localName": "result.dwg"
            }
        },
        "engine": "Autodesk.AutoCAD+25_1",
        "appbundles": [f"{client_id}.{appbundle_id}+v1"],
        "description": "Insert BTI Basmann template using .NET plugin"
    }
    
    response = requests.post(url, headers=headers, json=activity_spec)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✅ Activity создан: {result['id']}")
        print(f"   Version: {result.get('version', 1)}")
        print(f"   AppBundles: {result.get('appbundles', [])}")
        
        # Создаём alias для Activity
        alias_url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}/aliases"
        alias_response = requests.post(
            alias_url,
            headers=headers,
            json={"id": "v1", "version": 1}
        )
        
        if alias_response.status_code in [200, 201, 409]:
            print(f"✅ Alias v1 создан для Activity")
            print(f"\n🎯 Полный ID: {client_id}.{activity_id}+v1")
            return True
    else:
        print(f"❌ Ошибка создания Activity: {response.status_code}")
        print(response.text)
        return False

def main():
    """Главная функция"""
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description='Загрузка BTI AppBundle в Autodesk APS')
    parser.add_argument('--bundle', default='out/BTI_InsertBasman.bundle.zip', 
                        help='Путь к bundle.zip файлу')
    parser.add_argument('--appname', default='BTI_InsertBasman',
                        help='Имя AppBundle')
    parser.add_argument('--alias', default='v1',
                        help='Alias для AppBundle')
    args = parser.parse_args()
    
    print(f"\n╔══════════════════════════════════════════════════════════╗")
    print(f"║  🚀 ЗАГРУЗКА BTI APPBUNDLE В AUTODESK APS               ║")
    print(f"╚══════════════════════════════════════════════════════════╝\n")
    
    # Путь к ZIP
    zip_path = args.bundle
    appbundle_name = args.appname
    
    if not os.path.exists(zip_path):
        print(f"❌ ZIP файл не найден: {zip_path}\n")
        print(f"📋 ЗАПУСТИТЕ НА WINDOWS:\n")
        print(f"   pwsh .\\Build-BTI-AppBundle.ps1\n")
        print(f"Затем запустите этот скрипт снова с:")
        print(f"   python upload_bti_appbundle.py --bundle {zip_path}\n")
        sys.exit(1)
    
    # Получаем credentials
    print(f"🔐 Получение credentials...")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    print(f"   Client ID: {client_id[:20]}...")
    
    # Получаем токен
    token = get_access_token(client_id, client_secret)
    
    # Создаём и загружаем AppBundle
    appbundle_result = create_appbundle(token, client_id, zip_path)
    
    if not appbundle_result:
        print(f"\n❌ Загрузка AppBundle не удалась")
        sys.exit(1)
    
    # Создаём alias
    create_alias(token, f"{client_id}.BTI_InsertBasman", appbundle_result.get('version', 1))
    
    # Создаём Activity
    success = create_activity(token, client_id, "BTI_InsertBasman")
    
    if success:
        print(f"\n╔══════════════════════════════════════════════════════════╗")
        print(f"║              ✅ УСПЕХ! APPBUNDLE ЗАГРУЖЕН!              ║")
        print(f"╚══════════════════════════════════════════════════════════╝\n")
        print(f"📋 СЛЕДУЮЩИЕ ШАГИ:\n")
        print(f"1. Обновите forge_client.py:")
        print(f'   activityId = "{client_id}.DWG2DWG_InsertBasman+v1"\n')
        print(f"2. Задеплойте бота:")
        print(f"   gcloud run deploy telegram-bti-bot ...\n")
        print(f"3. Протестируйте через Telegram")
    else:
        print(f"\n❌ Создание Activity не удалось")
        sys.exit(1)

if __name__ == "__main__":
    main()

