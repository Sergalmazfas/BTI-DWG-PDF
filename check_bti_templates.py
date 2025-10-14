#!/usr/bin/env python3
"""Проверка BTI Template Activities"""

import requests
import json
from google.cloud import secretmanager

def get_secret(secret_id):
    """Получить секрет из Google Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/talkhint/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_aps_token(client_id, client_secret):
    """Получить APS токен"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()["access_token"]

def get_activity_details(token, activity_id):
    """Получить детали Activity"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def list_all_activities(token):
    """Список всех Activities"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

def main():
    print("🔍 Проверка BTI Template Activities\n")
    
    # Получаем credentials
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    
    # Получаем токен
    token = get_aps_token(client_id, client_secret)
    
    # Получаем все Activities
    all_activities = list_all_activities(token)
    
    # Фильтруем BTI Activities
    bti_activities = [a for a in all_activities if "BotBti" in a and ("BTI" in a or "Template" in a or "INSERT" in a)]
    
    print("📋 BTI Template Activities:\n")
    
    template_activities = []
    
    for activity_id in sorted(bti_activities):
        details = get_activity_details(token, activity_id)
        if details:
            desc = details.get("description", "N/A")
            engine = details.get("engine", "N/A")
            
            # Проверяем наличие AppBundle
            appbundles = details.get("appbundles", [])
            has_appbundle = len(appbundles) > 0
            
            print(f"{'✅' if has_appbundle else '⚪'} {activity_id}")
            print(f"   Описание: {desc}")
            print(f"   Engine: {engine}")
            if has_appbundle:
                print(f"   AppBundle: {appbundles[0] if appbundles else 'N/A'}")
                template_activities.append({
                    "id": activity_id,
                    "description": desc,
                    "appbundle": appbundles[0] if appbundles else None,
                    "details": details
                })
            print()
    
    # Выбираем лучший Activity для типового шаблона
    if template_activities:
        print("\n🎯 Рекомендуемые Activities с .NET плагином:")
        for i, act in enumerate(template_activities, 1):
            print(f"{i}. {act['id']}")
            print(f"   AppBundle: {act['appbundle']}")
            print(f"   Описание: {act['description']}")
            
            # Проверяем параметры
            params = act['details'].get('parameters', {})
            print(f"   Параметры:")
            for name, param in params.items():
                print(f"     - {name}: {param.get('verb', 'N/A')} ({param.get('description', 'N/A')})")
            print()
        
        print("\n💡 Рекомендация:")
        best = template_activities[0]
        print(f"   Используйте: {best['id']}")
        print(f"\n   В forge_client.py:")
        print(f'   "activityId": "{best["id"]}"')
        
        # Находим параметры
        params = best['details'].get('parameters', {})
        args = {}
        for name, param in params.items():
            if param.get('verb') == 'get':
                args[name] = 'input_url'
            elif param.get('verb') == 'put':
                args[name] = 'output_url (verb: put)'
        
        if args:
            print(f'\n   "arguments": {{')
            for name, value in args.items():
                if 'verb' in value:
                    print(f'     "{name}": {{"url": <url>, "verb": "put"}},')
                else:
                    print(f'     "{name}": {{"url": <{value}>}},')
            print(f'   }}')
    else:
        print("❌ Не найдено Activities с AppBundle")
        print("\n💡 Используйте простой DWG2DWG без шаблона:")
        print("   BotBti.SimpleDWG2DWG+v1")

if __name__ == "__main__":
    main()

