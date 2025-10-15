#!/usr/bin/env python3
"""Детальная проверка BTI Template Activities"""

import requests
import json
from google.cloud import secretmanager

def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/talkhint/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_aps_token(client_id, client_secret):
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
    url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def main():
    print("🔍 Детальная проверка BTI Template Activities\n")
    
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    token = get_aps_token(client_id, client_secret)
    
    # Проверяем BTI Template Activities
    activities_to_check = [
        "BotBti.BTI_INSERT_Basman+v1",
        "BotBti.BTI_INSERT_Template+v1",
        "BotBti.DWG2DWG_BTI_Basman+v1",
        "BotBti.DWG_MergeTemplate+v1"
    ]
    
    best_activity = None
    best_score = 0
    
    for activity_id in activities_to_check:
        print(f"\n{'='*60}")
        print(f"Activity: {activity_id}")
        print(f"{'='*60}\n")
        
        details = get_activity_details(token, activity_id)
        if not details:
            print("❌ Не удалось получить детали")
            continue
        
        # Выводим основную информацию
        print(f"Описание: {details.get('description', 'N/A')}")
        print(f"Engine: {details.get('engine', 'N/A')}")
        print(f"Version: {details.get('version', 'N/A')}")
        
        # CommandLine
        cmd = details.get('commandLine', [])
        if cmd:
            print(f"\nКоманда:")
            for c in cmd:
                print(f"  {c}")
        
        # Parameters
        params = details.get('parameters', {})
        print(f"\nПараметры:")
        input_params = []
        output_params = []
        for name, param in params.items():
            verb = param.get('verb', 'N/A')
            desc = param.get('description', 'N/A')
            required = param.get('required', False)
            print(f"  {name}:")
            print(f"    - verb: {verb}")
            print(f"    - description: {desc}")
            print(f"    - required: {required}")
            
            if verb == 'get':
                input_params.append(name)
            elif verb == 'put':
                output_params.append(name)
        
        # Settings (LISP скрипты)
        settings = details.get('settings', {})
        if settings:
            print(f"\nSettings (скрипты):")
            for key, setting in settings.items():
                value = setting.get('value', '')
                if value:
                    print(f"  {key}:")
                    # Показываем первые 200 символов
                    if len(value) > 200:
                        print(f"    {value[:200]}...")
                    else:
                        print(f"    {value}")
        
        # AppBundles
        appbundles = details.get('appbundles', [])
        if appbundles:
            print(f"\nAppBundles:")
            for ab in appbundles:
                print(f"  - {ab}")
        
        # Оценка качества Activity
        score = 0
        if input_params and output_params:
            score += 2
        if 'Basman' in activity_id or 'BTI' in activity_id:
            score += 1
        if appbundles:
            score += 3  # .NET плагин лучше
        if details.get('version', 0) >= 1:
            score += 1
        
        print(f"\n⭐ Оценка: {score}/7")
        
        if score > best_score:
            best_score = score
            best_activity = {
                'id': activity_id,
                'score': score,
                'input_params': input_params,
                'output_params': output_params,
                'details': details
            }
    
    # Итоговая рекомендация
    print(f"\n\n{'='*60}")
    print("🎯 РЕКОМЕНДАЦИЯ")
    print(f"{'='*60}\n")
    
    if best_activity:
        print(f"✅ Лучший Activity: {best_activity['id']}")
        print(f"⭐ Оценка: {best_activity['score']}/7")
        print(f"\nПараметры:")
        print(f"  Input: {', '.join(best_activity['input_params'])}")
        print(f"  Output: {', '.join(best_activity['output_params'])}")
        
        print(f"\n📝 Код для forge_client.py:")
        print(f'```python')
        print(f'"activityId": "{best_activity["id"]}",')
        print(f'"arguments": {{')
        
        for param in best_activity['input_params']:
            print(f'  "{param}": {{"url": input_url}},')
        
        for param in best_activity['output_params']:
            print(f'  "{param}": {{"url": output_url, "verb": "put"}}')
        
        print(f'}}')
        print(f'```')
    else:
        print("❌ Не найдено подходящих Activities")
        print("\n💡 Используйте BotBti.SimpleDWG2DWG+v1 (уже настроен)")

if __name__ == "__main__":
    main()

