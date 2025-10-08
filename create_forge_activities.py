#!/usr/bin/env python3
"""
Создание Activity в Forge API для обработки DWG файлов
"""

import os
import json
import requests
from google.cloud import secretmanager

def get_secret(secret_name):
    """Получает секрет из Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/talkhint/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": secret_path})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"❌ Ошибка получения секрета {secret_name}: {e}")
        return None

def get_forge_token():
    """Получает токен доступа Forge"""
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ Не удалось получить Forge credentials")
        return None
    
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "data:write data:read bucket:read bucket:create"
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            result = response.json()
            return result["access_token"]
        else:
            print(f"❌ Ошибка аутентификации: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Ошибка запроса токена: {e}")
        return None

def create_activity(token, activity_id, activity_name):
    """Создает Activity в Forge"""
    
    base_url = "https://developer.api.autodesk.com/da/us-east/v3"
    
    # Определяем параметры в зависимости от типа Activity
    if "BTI" in activity_id:
        activity_data = {
            "id": activity_id,
            "commandLine": ["$(engine.path)\\accoreconsole.exe /i \"$(args[inputFile].path)\" /s \"$(settings[script].path)\""],
            "parameters": {
                "inputFile": {
                    "verb": "get",
                    "localName": "input.dwg",
                    "description": "Input DWG file"
                },
                "resultPdf": {
                    "verb": "put", 
                    "localName": "output.pdf",
                    "description": "Output PDF file"
                }
            },
            "settings": {
                "script": {
                    "value": "plot_bti.scr"
                }
            },
            "engine": "Autodesk.AutoCAD+25_1"
        }
    else:  # TZ
        activity_data = {
            "id": activity_id,
            "commandLine": ["$(engine.path)\\accoreconsole.exe /i \"$(args[inputFile].path)\" /s \"$(settings[script].path)\""],
            "parameters": {
                "inputFile": {
                    "verb": "get",
                    "localName": "input.dwg", 
                    "description": "Input DWG file"
                },
                "resultPdf": {
                    "verb": "put",
                    "localName": "output.pdf",
                    "description": "Output PDF file"
                }
            },
            "settings": {
                "script": {
                    "value": "plot_tz.scr"
                }
            },
            "engine": "Autodesk.AutoCAD+25_1"
        }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{base_url}/activities",
            headers=headers,
            json=activity_data
        )
        
        if response.status_code == 200:
            print(f"✅ Activity {activity_id} создан успешно")
            return True
        elif response.status_code == 409:
            print(f"⚠️ Activity {activity_id} уже существует")
            return True
        else:
            print(f"❌ Ошибка создания Activity {activity_id}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка запроса создания Activity: {e}")
        return False

def main():
    """Основная функция"""
    
    print("🚀 Создание Activity в Forge API...")
    print("=" * 50)
    
    # Получаем токен
    token = get_forge_token()
    if not token:
        print("❌ Не удалось получить токен Forge")
        return
    
    print("✅ Токен Forge получен")
    
    # Создаем Activity
    activities = [
        ("BTI2PDFActivity", "BTI to PDF Conversion"),
        ("TZ2PDFActivity", "TZ to PDF Conversion")
    ]
    
    success_count = 0
    for activity_id, activity_name in activities:
        print(f"\n🔧 Создаем Activity: {activity_id}")
        if create_activity(token, activity_id, activity_name):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 Создано {success_count}/{len(activities)} Activity")
    
    if success_count == len(activities):
        print("✅ Все Activity созданы успешно!")
    else:
        print("❌ Некоторые Activity не удалось создать")

if __name__ == "__main__":
    main()
