#!/usr/bin/env python3
"""
Подключение Forgecloudrun к Autodesk APS без шаблона
Простая Activity для тестирования базовой функциональности
"""

import subprocess
import requests
import json
import sys
import time

# Константы
NICKNAME = "Forgecloudrun"
ENGINE = "Autodesk.AutoCAD+25_1"
ACTIVITY_ID = "SimpleDWG2DWG_NoTemplate"
ALIAS_ID = "v1"
BASE_URL = "https://developer.api.autodesk.com/da/us-east/v3"

def print_step(step, message):
    """Красивый вывод шагов"""
    print(f"\n{'=' * 70}")
    print(f"🔹 {step}")
    print(f"{message}")
    print(f"{'=' * 70}\n")

def get_secret(name):
    """Получить секрет из Google Secret Manager"""
    cmd = f"gcloud secrets versions access latest --secret={name} --project=talkhint"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Ошибка получения секрета {name}: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def get_token(client_id, client_secret):
    """Получить Access Token"""
    print("🔑 Получение access token...")
    resp = requests.post(
        "https://developer.api.autodesk.com/authentication/v2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "code:all data:read data:write"
        }
    )
    
    if resp.status_code != 200:
        print(f"❌ Ошибка авторизации: {resp.text}")
        sys.exit(1)
    
    token = resp.json()["access_token"]
    print(f"✅ Token получен")
    return token

def check_nickname(headers, client_id):
    """Проверить что nickname установлен"""
    print("🏷️  Проверка nickname...")
    
    resp = requests.get(f"{BASE_URL}/forgeapps/me", headers=headers)
    
    if resp.status_code == 200:
        try:
            app_info = resp.json()
            nickname = app_info.get("nickname") if isinstance(app_info, dict) else None
        except:
            nickname = None
        
        print(f"   Client ID: {client_id[:30]}...")
        print(f"   Nickname: {nickname or 'НЕ УСТАНОВЛЕН'}")
        
        if nickname == NICKNAME:
            print(f"   ✅ Nickname правильный: {NICKNAME}")
            return True
        else:
            print(f"   ❌ Nickname не установлен или неправильный!")
            print(f"\n   Ожидается: {NICKNAME}")
            print(f"   Получено: {nickname}")
            return False
    else:
        print(f"   ❌ Ошибка проверки приложения: {resp.status_code}")
        return False

def create_simple_activity(headers, client_id):
    """Создать простую Activity без AppBundle"""
    print_step("📐 ШАГ 1: Создание Activity SimpleDWG2DWG_NoTemplate", 
               f"ID: {NICKNAME}.{ACTIVITY_ID}")
    
    activity_data = {
        "id": ACTIVITY_ID,
        "commandLine": [
            '$(engine.path)\\accoreconsole.exe /i "$(args[inputFile].path)" /s "$(settings[script].path)"'
        ],
        "engine": ENGINE,
        "parameters": {
            "inputFile": {
                "verb": "get",
                "description": "Input DWG file",
                "localName": "input.dwg"
            },
            "resultFile": {
                "verb": "put",
                "description": "Output DWG file",
                "localName": "output.dwg"
            }
        },
        "settings": {
            "script": {
                "value": "_QSAVE\n_QUIT\n"
            }
        },
        "description": "Simple DWG processor without template"
    }
    
    # Попробовать создать
    resp = requests.post(f"{BASE_URL}/activities", headers=headers, json=activity_data)
    
    if resp.status_code == 409:
        print("⚠️  Activity уже существует, удаляем и создаем заново...")
        # Удалить старую
        requests.delete(f"{BASE_URL}/activities/{client_id}.{ACTIVITY_ID}", headers=headers)
        time.sleep(2)
        # Создать новую
        resp = requests.post(f"{BASE_URL}/activities", headers=headers, json=activity_data)
    
    if resp.status_code not in [200, 201]:
        print(f"❌ Ошибка создания Activity: {resp.status_code}")
        print(resp.text)
        sys.exit(1)
    
    activity = resp.json()
    print(f"✅ Activity создана:")
    print(f"   ID: {activity.get('id')}")
    print(f"   Version: {activity.get('version')}")
    print(f"   Engine: {activity.get('engine')}")
    
    return activity

def create_alias(headers, client_id):
    """Создать Alias для Activity"""
    print_step("🏷️  ШАГ 2: Создание Alias v1", 
               f"Для: {NICKNAME}.{ACTIVITY_ID}")
    
    # Проверить существующие aliases
    resp = requests.get(
        f"{BASE_URL}/activities/{client_id}.{ACTIVITY_ID}/aliases",
        headers=headers
    )
    
    existing_aliases = resp.json().get("data", [])
    print(f"   Существующие aliases: {existing_aliases}")
    
    # Создать alias
    alias_data = {
        "id": ALIAS_ID,
        "version": 1
    }
    
    resp = requests.post(
        f"{BASE_URL}/activities/{client_id}.{ACTIVITY_ID}/aliases",
        headers=headers,
        json=alias_data
    )
    
    if resp.status_code == 409:
        print(f"⚠️  Alias {ALIAS_ID} уже существует, обновляем...")
        # Обновить существующий
        resp = requests.patch(
            f"{BASE_URL}/activities/{client_id}.{ACTIVITY_ID}/aliases/{ALIAS_ID}",
            headers=headers,
            json={"version": 1}
        )
    
    if resp.status_code in [200, 201]:
        alias = resp.json()
        print(f"✅ Alias создан/обновлен:")
        print(f"   Alias: {alias.get('id')}")
        print(f"   Version: {alias.get('version')}")
        print(f"   Full ID: {client_id}.{ACTIVITY_ID}+{ALIAS_ID}")
        return True
    else:
        print(f"❌ Ошибка создания alias: {resp.status_code}")
        print(f"   Response: {resp.text}")
        return False

def test_workitem(headers, client_id):
    """Протестировать WorkItem"""
    print_step("🧪 ШАГ 3: Тестирование WorkItem", 
               f"Activity: {NICKNAME}.{ACTIVITY_ID}+{ALIAS_ID}")
    
    # Входной и выходной файлы
    input_url = "https://storage.googleapis.com/btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg"
    output_url = "https://storage.googleapis.com/btibot-processed/processed/forgecloudrun_test.dwg"
    
    workitem_data = {
        "activityId": f"{client_id}.{ACTIVITY_ID}+{ALIAS_ID}",
        "arguments": {
            "inputFile": {
                "url": input_url
            },
            "resultFile": {
                "url": output_url,
                "verb": "put"
            }
        }
    }
    
    print(f"   Input: ...{input_url[-50:]}")
    print(f"   Output: ...{output_url[-50:]}")
    
    resp = requests.post(f"{BASE_URL}/workitems", headers=headers, json=workitem_data)
    
    if resp.status_code not in [200, 201]:
        print(f"❌ Ошибка создания WorkItem: {resp.status_code}")
        print(resp.text)
        return None
    
    workitem = resp.json()
    workitem_id = workitem.get("id")
    
    print(f"✅ WorkItem создан: {workitem_id}")
    print(f"   Status: {workitem.get('status')}")
    
    # Мониторинг статуса
    print(f"\n⏳ Ожидание завершения (max 2 мин)...")
    
    for i in range(24):  # 24 * 5 сек = 2 мин
        time.sleep(5)
        
        status_resp = requests.get(
            f"{BASE_URL}/workitems/{workitem_id}",
            headers=headers
        )
        
        status_data = status_resp.json()
        current_status = status_data.get("status")
        
        print(f"   [{i*5}s] Status: {current_status}")
        
        if current_status == "success":
            print(f"\n🎉 УСПЕХ! WorkItem выполнен!")
            print(f"   Результат: {output_url}")
            return workitem_id
        elif current_status == "failed":
            print(f"\n❌ WorkItem FAILED!")
            print(f"   Report: {json.dumps(status_data, indent=2)}")
            return None
        elif current_status in ["cancelled", "error"]:
            print(f"\n❌ WorkItem {current_status}!")
            return None
    
    print(f"\n⏱️  Timeout (2 мин) - проверьте статус позже")
    return None

def update_forge_client(client_id):
    """Обновить forge_client.py с новым activityId"""
    print_step("🔧 ШАГ 4: Обновление forge_client.py", 
               "Установка нового activityId")
    
    activity_id = f"{client_id}.{ACTIVITY_ID}+{ALIAS_ID}"
    
    print(f"   Новый activityId: {activity_id}")
    print(f"\n   📝 Обновите forge_client.py (строка ~119):")
    print(f'   "activityId": f"{{{activity_id}}}"')
    
    # Попробовать обновить автоматически
    try:
        with open("forge_client.py", "r") as f:
            content = f.read()
        
        # Найти и заменить activityId
        import re
        
        # Паттерн для поиска activityId в submit_workitem
        pattern = r'"activityId":\s*f?"[^"]*"'
        replacement = f'"activityId": "{activity_id}"'
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open("forge_client.py", "w") as f:
                f.write(new_content)
            print(f"   ✅ forge_client.py обновлен автоматически")
        else:
            print(f"   ⚠️  Не удалось найти activityId для замены")
            print(f"   Обновите вручную")
    except Exception as e:
        print(f"   ⚠️  Ошибка автоматического обновления: {e}")
        print(f"   Обновите вручную")

def main():
    """Главная функция"""
    print(f"\n{'=' * 70}")
    print(f"🚀 ПОДКЛЮЧЕНИЕ FORGECLOUDRUN К AUTODESK APS")
    print(f"   (Без шаблона, простая Activity)")
    print(f"{'=' * 70}\n")
    
    # 1. Получить credentials
    print("📋 Получение credentials из Google Secret Manager...")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    print(f"   Client ID: {client_id[:30]}...")
    
    # 2. Получить токен
    token = get_token(client_id, client_secret)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 3. Проверить nickname
    if not check_nickname(headers, client_id):
        print(f"\n❌ ОШИБКА: Nickname не установлен!")
        print(f"\n📝 Установите nickname '{NICKNAME}' через Web UI:")
        print(f"   1. https://aps.autodesk.com")
        print(f"   2. My Apps → [Ваше приложение] → Settings")
        print(f"   3. Nickname: {NICKNAME} → Save")
        sys.exit(1)
    
    # 4. Создать Activity
    activity = create_simple_activity(headers, client_id)
    
    # 5. Создать Alias
    alias_created = create_alias(headers, client_id)
    
    if not alias_created:
        print(f"\n⚠️  Alias не создан - возможна проблема с nickname")
        print(f"   Проверьте что nickname = '{NICKNAME}' установлен правильно")
        sys.exit(1)
    
    # 6. Тест WorkItem
    workitem_id = test_workitem(headers, client_id)
    
    if not workitem_id:
        print(f"\n⚠️  WorkItem не выполнен успешно")
        print(f"   Проверьте логи выше")
        sys.exit(1)
    
    # 7. Обновить forge_client.py
    update_forge_client(client_id)
    
    # 8. Итоги
    print(f"\n{'=' * 70}")
    print(f"✅ ВСЕ ГОТОВО! FORGECLOUDRUN ПОДКЛЮЧЕН К APS")
    print(f"{'=' * 70}\n")
    
    print(f"📊 Созданные ресурсы:")
    print(f"   ✅ Activity: {client_id}.{ACTIVITY_ID}+1")
    print(f"   ✅ Alias: {ALIAS_ID} → version 1")
    print(f"   ✅ WorkItem: {workitem_id} (success)")
    
    print(f"\n🚀 Следующие шаги:")
    print(f"\n1. Проверить forge_client.py:")
    print(f'   grep "activityId" forge_client.py')
    
    print(f"\n2. Deploy бота:")
    print(f"""
   gcloud run deploy telegram-bot-commands \\
     --source . \\
     --region europe-west1 \\
     --platform managed \\
     --allow-unauthenticated \\
     --set-env-vars GOOGLE_CLOUD_PROJECT=talkhint,GCS_BUCKET=btibot-processed,AUTO_PDF=false \\
     --set-secrets FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,BOT_TOKEN=BOT_TOKEN:latest \\
     --cpu 1 --memory 1Gi --timeout 300
""")
    
    print(f"3. Тест через Telegram:")
    print(f"   - Загрузить DWG в бот")
    print(f"   - Проверить что обработка прошла успешно")
    
    print(f"\n🎉 ГОТОВО К PRODUCTION!")

if __name__ == "__main__":
    main()

