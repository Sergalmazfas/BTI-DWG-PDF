#!/usr/bin/env python3
"""
Загрузка BTI AppBundle в Autodesk APS
Версия для Windows VM (без Google Secret Manager)
"""
import os
import sys
import requests
import json
import argparse

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

def get_nickname(token):
    """Получить nickname (ForgeAppName)"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, str):
            return data
        elif isinstance(data, dict) and "id" in data:
            return data["id"]
    return None

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

def create_appbundle(token, nickname, appbundle_name, zip_path):
    """Создать и загрузить AppBundle"""
    print(f"\n📦 Создание AppBundle: {nickname}.{appbundle_name}")
    
    full_id = f"{nickname}.{appbundle_name}"
    
    # Удаляем старую версию
    delete_appbundle(token, full_id)
    
    # Создаём новый AppBundle
    url = "https://developer.api.autodesk.com/da/us-east/v3/appbundles"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "id": f"{nickname}.{appbundle_name}",
        "engine": "Autodesk.AutoCAD+25_1",
        "description": f"BTI {appbundle_name} with LISP scripts"
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
            return None
        
        # Подготовка multipart/form-data
        with open(zip_path, 'rb') as f:
            files = {'file': f}
            upload_response = requests.post(endpoint_url, data=form_data, files=files)
        
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
        print(f"   Full ID: {appbundle_id}+v1")
        return True
    elif response.status_code == 409:
        # Alias существует, обновляем
        patch_url = f"{url}/v1"
        patch_response = requests.patch(patch_url, headers=headers, json={"version": version})
        if patch_response.status_code == 200:
            print(f"✅ Alias v1 обновлён")
            print(f"   Full ID: {appbundle_id}+v1")
            return True
    
    print(f"⚠️  Alias: {response.status_code} - {response.text}")
    return False

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Загрузка BTI AppBundle в Autodesk APS')
    parser.add_argument('--bundle', required=True, help='Путь к bundle.zip файлу')
    parser.add_argument('--appname', default='BtiPlugin', help='Имя AppBundle')
    parser.add_argument('--alias', default='v1', help='Alias для AppBundle')
    args = parser.parse_args()
    
    print(f"\n╔══════════════════════════════════════════════════════════╗")
    print(f"║  🚀 ЗАГРУЗКА BTI APPBUNDLE В AUTODESK APS               ║")
    print(f"╚══════════════════════════════════════════════════════════╝\n")
    
    # Получаем credentials из переменных окружения
    client_id = os.getenv("APS_CLIENT_ID")
    client_secret = os.getenv("APS_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print(f"❌ Не установлены credentials!")
        print(f"\nУстановите переменные окружения:")
        print(f'   $env:APS_CLIENT_ID = "your_client_id"')
        print(f'   $env:APS_CLIENT_SECRET = "your_client_secret"')
        sys.exit(1)
    
    print(f"🔐 Credentials найдены")
    print(f"   Client ID: {client_id[:20]}...")
    
    # Получаем токен
    token = get_access_token(client_id, client_secret)
    
    # Получаем nickname
    print(f"\n📝 Получение nickname...")
    nickname = get_nickname(token)
    if not nickname:
        print(f"❌ Не удалось получить nickname!")
        sys.exit(1)
    
    print(f"✅ Nickname: {nickname}")
    
    # Создаём и загружаем AppBundle
    appbundle_result = create_appbundle(token, nickname, args.appname, args.bundle)
    
    if not appbundle_result:
        print(f"\n❌ Загрузка AppBundle не удалась")
        sys.exit(1)
    
    # Создаём alias
    full_appbundle_id = f"{nickname}.{args.appname}"
    create_alias(token, full_appbundle_id, appbundle_result.get('version', 1))
    
    print(f"\n╔══════════════════════════════════════════════════════════╗")
    print(f"║              ✅ УСПЕХ! APPBUNDLE ЗАГРУЖЕН!              ║")
    print(f"╚══════════════════════════════════════════════════════════╝\n")
    print(f"📋 AppBundle ID: {full_appbundle_id}+v1\n")
    print(f"🎯 СЛЕДУЮЩИЕ ШАГИ:\n")
    print(f"1. Обновите Activity для использования этого AppBundle")
    print(f"2. Задеплойте обновленный сервис")
    print(f"3. Протестируйте обработку DWG\n")

if __name__ == "__main__":
    main()

