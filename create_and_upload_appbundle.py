#!/usr/bin/env python3
"""
Скрипт для создания и загрузки AppBundle в Autodesk Design Automation
Следует официальной документации Autodesk APS
"""

import os
import sys
import json
import requests
import subprocess
import zipfile
from pathlib import Path

def get_secret(secret_name, project="talkhint"):
    """Получает секрет из Google Secret Manager"""
    cmd = f"gcloud secrets versions access latest --secret={secret_name} --project={project}"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    return result.stdout.strip()

def get_forge_token(client_id, client_secret):
    """Получает access token от Autodesk"""
    auth_url = "https://developer.api.autodesk.com/authentication/v2/token"
    auth_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "code:all data:read data:write bucket:create bucket:read bucket:delete"
    }
    
    response = requests.post(auth_url, data=auth_data)
    response.raise_for_status()
    
    return response.json()["access_token"]

def create_appbundle_zip():
    """Создает AppBundle.zip файл"""
    print("\n📦 Создание AppBundle.zip...")
    
    bundle_dir = Path("BTI_TemplateAppBundle")
    zip_path = Path("BTI_TemplateAppBundle.zip")
    
    # Структура AppBundle
    # BTI_TemplateAppBundle.bundle/
    #   Contents/
    #     BTI_TemplatePlugin.dll
    #     BTI_Template.dwt
    #     PackageContents.xml
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Добавляем PackageContents.xml в корень bundle
        zipf.write(
            bundle_dir / "PackageContents.xml",
            "BTI_TemplateAppBundle.bundle/PackageContents.xml"
        )
        
        # Добавляем файлы в Contents/
        contents_files = [
            # TODO: После компиляции .NET проекта
            # ("BTI_TemplatePlugin.dll", "BTI_TemplateAppBundle.bundle/Contents/BTI_TemplatePlugin.dll"),
            # ("BTI_Template.dwt", "BTI_TemplateAppBundle.bundle/Contents/BTI_Template.dwt"),
        ]
        
        # Пока AppBundle создается без DLL (для тестирования структуры)
        print("   ⚠️ DLL не скомпилирован - создаем пустую структуру")
        
    print(f"   ✅ AppBundle.zip создан: {zip_path}")
    return zip_path

def create_appbundle(client_id, access_token):
    """Создает AppBundle в Autodesk APS"""
    print("\n🔧 Создание AppBundle в Autodesk APS...")
    
    url = "https://developer.api.autodesk.com/da/us-east/v3/appbundles"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    appbundle_data = {
        "id": f"{client_id}.BTI_TemplateAppBundle",
        "engine": "Autodesk.AutoCAD+25_1",
        "description": "BTI Template application plugin for DWG processing"
    }
    
    print(f"   ID: {appbundle_data['id']}")
    
    response = requests.post(url, headers=headers, json=appbundle_data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"   ✅ AppBundle создан!")
        print(f"   Version: {result.get('version')}")
        print(f"   Upload URL: {result.get('uploadParameters', {}).get('endpointURL', 'N/A')}")
        return result
    elif response.status_code == 409:
        print(f"   ℹ️ AppBundle уже существует")
        # Получаем существующий
        get_response = requests.get(f"{url}/{client_id}.BTI_TemplateAppBundle", headers=headers)
        if get_response.status_code == 200:
            return get_response.json()
        return None
    else:
        print(f"   ❌ Ошибка: {response.status_code}")
        print(f"   {response.text}")
        return None

def upload_appbundle_zip(upload_params, zip_path):
    """Загружает AppBundle.zip по signed URL"""
    print("\n📤 Загрузка AppBundle.zip в Autodesk...")
    
    if not upload_params or 'endpointURL' not in upload_params:
        print("   ❌ Нет upload parameters")
        return False
    
    endpoint_url = upload_params['endpointURL']
    form_data = upload_params.get('formData', {})
    
    # Читаем zip файл
    with open(zip_path, 'rb') as f:
        zip_data = f.read()
    
    # Загружаем
    files = {'file': (zip_path.name, zip_data, 'application/zip')}
    
    response = requests.post(endpoint_url, data=form_data, files=files)
    
    if response.status_code in [200, 201, 204]:
        print(f"   ✅ AppBundle.zip загружен успешно!")
        return True
    else:
        print(f"   ❌ Ошибка загрузки: {response.status_code}")
        print(f"   {response.text}")
        return False

def create_appbundle_alias(client_id, access_token, version=1):
    """Создает alias для AppBundle"""
    print(f"\n🏷️ Создание alias 'v1' для версии {version}...")
    
    # Используем прямой HTTP запрос
    url = f"https://developer.api.autodesk.com/da/us-east/v3/appbundles/{client_id}.BTI_TemplateAppBundle/aliases"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    alias_data = {
        "id": "v1",
        "version": version
    }
    
    response = requests.post(url, headers=headers, json=alias_data)
    
    if response.status_code in [200, 201]:
        print(f"   ✅ Alias создан!")
        return True
    elif response.status_code == 409:
        print(f"   ℹ️ Alias уже существует")
        return True
    else:
        print(f"   ⚠️ API Error: {response.text}")
        print(f"   💡 Создайте alias вручную через Forge Web UI")
        return False

def main():
    """Основная функция"""
    print("="*60)
    print("🚀 Создание и загрузка BTI Template AppBundle")
    print("="*60)
    
    # Получаем credentials
    print("\n🔑 Получение Forge credentials...")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    print(f"   Client ID: {client_id[:30]}...")
    
    # Получаем токен
    print("\n🔑 Получение access token...")
    access_token = get_forge_token(client_id, client_secret)
    print(f"   ✅ Token получен")
    
    # Создаем zip (пока без DLL)
    # zip_path = create_appbundle_zip()
    
    # Создаем AppBundle
    appbundle = create_appbundle(client_id, access_token)
    
    if not appbundle:
        print("\n❌ Не удалось создать AppBundle")
        return 1
    
    # Загружаем zip (если есть upload parameters)
    # if 'uploadParameters' in appbundle:
    #     success = upload_appbundle_zip(appbundle['uploadParameters'], zip_path)
    #     if not success:
    #         return 1
    
    # Создаем alias
    create_appbundle_alias(client_id, access_token, appbundle.get('version', 1))
    
    print("\n" + "="*60)
    print("✅ AppBundle настройка завершена!")
    print("="*60)
    print(f"\n📌 Следующий шаг:")
    print(f"   1. Скомпилировать .NET проект BTI_TemplatePlugin.cs")
    print(f"   2. Создать bundle.zip с DLL")
    print(f"   3. Загрузить через Web UI или обновить скрипт")
    print(f"   4. Создать Activity использующую AppBundle")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

