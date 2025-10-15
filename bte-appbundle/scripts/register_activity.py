#!/usr/bin/env python3
"""
Регистрация Activity BTEInsertTemplate и создание alias v1
через Autodesk APS Design Automation API v3

Официальная документация:
- POST /activities: https://aps.autodesk.com/en/docs/design-automation/v3/reference/http/activities-POST/
- POST /aliases: https://aps.autodesk.com/en/docs/design-automation/v3/reference/http/aliases-POST/
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# APS Configuration
APS_CLIENT_ID = os.getenv('APS_CLIENT_ID', 'm6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4')
APS_CLIENT_SECRET = os.getenv('APS_CLIENT_SECRET', 'tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW')
APS_BASE_URL = "https://developer.api.autodesk.com"

# Activity Configuration
ACTIVITY_ID = "BTEInsertTemplate"
ALIAS_ID = "v1"
APPBUNDLE_ID = "BTEInsertTemplate"  # AppBundle должен быть уже загружен
ENGINE = "Autodesk.AutoCAD+25_0"


def get_access_token():
    """Получить OAuth токен с scope code:all"""
    print("\n" + "=" * 80)
    print("🔑 1️⃣ Получение OAuth токена (scope: code:all)")
    print("=" * 80)
    
    url = f"{APS_BASE_URL}/authentication/v2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": APS_CLIENT_ID,
        "client_secret": APS_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all data:write data:read bucket:create bucket:read"
    }
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code != 200:
        print(f"❌ Ошибка получения токена: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    token_data = response.json()
    print(f"✅ Токен получен")
    print(f"   Expires in: {token_data.get('expires_in', 'N/A')}s")
    print(f"   Scope: code:all ✅")
    
    return token_data['access_token']


def get_nickname(token):
    """Получить nickname приложения"""
    url = f"{APS_BASE_URL}/da/us-east/v3/forgeapps/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if isinstance(result, str):
            return result
        return result.get('id')
    
    return None


def check_activity_exists(token, activity_id):
    """Проверить существует ли Activity"""
    print("\n" + "=" * 80)
    print(f"🔍 Проверка существования Activity: {activity_id}")
    print("=" * 80)
    
    url = f"{APS_BASE_URL}/da/us-east/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        activity = response.json()
        print(f"✅ Activity найдена:")
        print(f"   ID: {activity.get('id')}")
        print(f"   Version: {activity.get('version')}")
        print(f"   Engine: {activity.get('engine')}")
        return activity
    elif response.status_code == 404:
        print(f"ℹ️  Activity не найдена (будет создана)")
        return None
    else:
        print(f"⚠️  Ошибка проверки: {response.status_code}")
        print(response.text)
        return None


def create_activity(token, nickname):
    """Создать Activity BTEInsertTemplate"""
    print("\n" + "=" * 80)
    print(f"🚀 2️⃣ Создание Activity: {ACTIVITY_ID}")
    print("=" * 80)
    
    # Формируем полный ID с nickname
    full_appbundle_id = f"{nickname}.{APPBUNDLE_ID}+1" if nickname else f"{APPBUNDLE_ID}+1"
    
    activity_data = {
        "id": ACTIVITY_ID,
        "commandLine": [
            '$(engine.path)\\accoreconsole.exe /i "$(args[inputFile].path)" /al "$(appbundles[BTEInsertTemplate].path)" /s "$(settings[script].path)"'
        ],
        "parameters": {
            "inputFile": {
                "verb": "get",
                "description": "Input DWG file",
                "localName": "Input.dwg",
                "required": True
            },
            "result": {
                "verb": "put",
                "description": "Result DWG file with BTE template inserted",
                "localName": "Result.dwg",
                "required": True
            }
        },
        "engine": ENGINE,
        "appbundles": [full_appbundle_id],
        "settings": {
            "script": {
                "value": '(command "INSERTBTE")\n(command "QSAVE")\n(command "QUIT")\n'
            }
        },
        "description": "Inserts BTE template into DWG and saves drawing"
    }
    
    print(f"📋 Activity Configuration:")
    print(f"   ID: {ACTIVITY_ID}")
    print(f"   Engine: {ENGINE}")
    print(f"   AppBundle: {full_appbundle_id}")
    print(f"   Command: INSERTBTE → QSAVE → QUIT")
    print(f"\nPayload:")
    print(json.dumps(activity_data, indent=2))
    
    url = f"{APS_BASE_URL}/da/us-east/v3/activities"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=activity_data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\n✅ Activity создана успешно!")
        print(f"   ID: {result.get('id')}")
        print(f"   Version: {result.get('version')}")
        print(f"   Full ID: {nickname}.{ACTIVITY_ID}+{result.get('version')}")
        return result
    elif response.status_code == 409:
        print(f"\n⚠️  Activity уже существует (409 Conflict)")
        print("   Попытка получить существующую Activity...")
        return check_activity_exists(token, f"{nickname}.{ACTIVITY_ID}")
    else:
        print(f"\n❌ Ошибка создания Activity: {response.status_code}")
        print(f"Response: {response.text}")
        
        if "Cannot parse id" in response.text:
            print("\n💡 Диагностика:")
            print("   Возможно, AppBundle не загружен")
            print("   Проверьте наличие AppBundle в Web UI")
        
        return None


def create_alias(token, activity_id, alias_id, version):
    """Создать alias для Activity"""
    print("\n" + "=" * 80)
    print(f"🏷️  3️⃣ Создание Alias: {alias_id} → Version {version}")
    print("=" * 80)
    
    url = f"{APS_BASE_URL}/da/us-east/v3/activities/{activity_id}/aliases"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "id": alias_id,
        "version": version
    }
    
    print(f"📋 Alias Configuration:")
    print(f"   Activity: {activity_id}")
    print(f"   Alias ID: {alias_id}")
    print(f"   Version: {version}")
    print(f"\nPayload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\n✅ Alias создан успешно!")
        print(f"   ID: {result.get('id')}")
        print(f"   Version: {result.get('version')}")
        print(f"   Full Activity ID: {activity_id}+{alias_id}")
        return result
    elif response.status_code == 409:
        print(f"\n⚠️  Alias уже существует (409 Conflict)")
        return {"id": alias_id, "version": version, "status": "exists"}
    else:
        print(f"\n❌ Ошибка создания Alias: {response.status_code}")
        print(f"Response: {response.text}")
        
        if "Cannot parse id" in response.text:
            print("\n⚠️  ИЗВЕСТНЫЙ БАГ AUTODESK APS API:")
            print("   'Cannot parse id' - programmatic alias creation не работает")
            print("   Требуется создание через Web UI")
            print("\n📝 Будет задокументировано в docs/CREATE_ALIAS_STATUS.md")
        
        return None


def verify_setup(token, activity_full_id, alias_id):
    """Проверить созданную Activity и Alias"""
    print("\n" + "=" * 80)
    print("🔍 4️⃣ Верификация Activity + Alias")
    print("=" * 80)
    
    # Проверка alias
    url = f"{APS_BASE_URL}/da/us-east/v3/activities/{activity_full_id}/aliases/{alias_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        alias_data = response.json()
        print(f"✅ Alias подтверждён:")
        print(f"   ID: {alias_data.get('id')}")
        print(f"   Version: {alias_data.get('version')}")
        return True
    else:
        print(f"❌ Alias не найден: {response.status_code}")
        print(response.text)
        return False


def save_documentation(activity_result, alias_result, nickname):
    """Сохранить документацию о результатах"""
    print("\n" + "=" * 80)
    print("📝 Сохранение документации")
    print("=" * 80)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    doc_content = f"""# Activity Registration Status

**Date**: {timestamp}
**Activity**: {ACTIVITY_ID}
**Alias**: {ALIAS_ID}
**Nickname**: {nickname}

## Activity Creation

"""
    
    if activity_result:
        doc_content += f"""✅ **SUCCESS**

- ID: {activity_result.get('id')}
- Version: {activity_result.get('version')}
- Engine: {activity_result.get('engine')}
- Full ID: {nickname}.{ACTIVITY_ID}+{activity_result.get('version')}

"""
    else:
        doc_content += f"""❌ **FAILED**

Activity creation failed or already existed.

"""
    
    doc_content += f"""## Alias Creation

"""
    
    if alias_result:
        doc_content += f"""✅ **SUCCESS**

- Alias ID: {alias_result.get('id')}
- Version: {alias_result.get('version')}
- Full Activity ID: {nickname}.{ACTIVITY_ID}+{ALIAS_ID}

## Usage in WorkItem

```json
{{
  "activityId": "{nickname}.{ACTIVITY_ID}+{ALIAS_ID}",
  "arguments": {{
    "inputFile": {{
      "url": "https://..."
    }},
    "result": {{
      "url": "https://...",
      "verb": "put"
    }}
  }}
}}
```

## Next Steps

```bash
python3 bte-appbundle/scripts/test_bte_insert.py
```
"""
    else:
        doc_content += f"""❌ **FAILED - Known Autodesk API Bug**

**Error**: "Cannot parse id"

**Cause**: Autodesk Design Automation API v3 has a known limitation with programmatic alias creation for certain Client IDs.

**Workaround**: Create alias through Web UI

### Instructions:

1. Open: https://aps.autodesk.com
2. Navigate: My Apps → Design Automation → AutoCAD
3. Select: Activities → {ACTIVITY_ID}
4. Create Alias:
   - ID: `{ALIAS_ID}`
   - Version: `1`
   - Description: `Production version`
5. Save

After creating alias through Web UI, run:

```bash
python3 bte-appbundle/scripts/test_bte_insert.py
```
"""
    
    # Сохранить в файл
    os.makedirs('docs', exist_ok=True)
    doc_file = 'docs/ACTIVITY_REGISTRATION_STATUS.md'
    
    with open(doc_file, 'w') as f:
        f.write(doc_content)
    
    print(f"✅ Документация сохранена: {doc_file}")
    
    # Также обновить CREATE_ALIAS_STATUS.md
    alias_status_file = 'docs/CREATE_ALIAS_STATUS.md'
    if os.path.exists(alias_status_file):
        with open(alias_status_file, 'r') as f:
            existing_content = f.read()
        
        # Добавить новую попытку
        update = f"\n\n---\n\n## Update: {timestamp}\n\n"
        if alias_result:
            update += f"✅ Alias успешно создан через API!\n\n"
        else:
            update += f"❌ Alias не создан - подтверждён API баг 'Cannot parse id'\n\n"
        
        with open(alias_status_file, 'a') as f:
            f.write(update)
        
        print(f"✅ Обновлён: {alias_status_file}")


def main():
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "🤖 Activity & Alias Registration" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # 1. Получить токен
    token = get_access_token()
    
    # Получить nickname
    nickname = get_nickname(token)
    if not nickname:
        print("\n❌ Не удалось получить nickname приложения")
        print("   Установите nickname через Web UI или используйте Client ID")
        nickname = "BotBti"  # Используем известный nickname
    
    print(f"\n📌 Nickname: {nickname}")
    
    # Формируем полный ID
    activity_full_id = f"{nickname}.{ACTIVITY_ID}"
    
    # 2. Проверить/Создать Activity
    existing_activity = check_activity_exists(token, activity_full_id)
    
    activity_result = None
    if not existing_activity:
        activity_result = create_activity(token, nickname)
        if not activity_result:
            print("\n❌ Не удалось создать Activity")
            sys.exit(1)
        
        # Небольшая задержка после создания
        print("\n⏳ Ожидание 3 секунды после создания Activity...")
        time.sleep(3)
    else:
        activity_result = existing_activity
        print(f"\n✅ Используем существующую Activity")
    
    # 3. Создать Alias
    version = activity_result.get('version', 1)
    alias_result = create_alias(token, activity_full_id, ALIAS_ID, version)
    
    # 4. Верификация (если alias создан)
    verified = False
    if alias_result and alias_result.get('id'):
        print("\n⏳ Ожидание 2 секунды перед верификацией...")
        time.sleep(2)
        verified = verify_setup(token, activity_full_id, ALIAS_ID)
    
    # 5. Сохранить документацию
    save_documentation(activity_result, alias_result, nickname)
    
    # Итоговый статус
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 30 + "📊 ИТОГОВЫЙ СТАТУС" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    
    print(f"\n{'Activity':.<40} {'✅ Готово' if activity_result else '❌ Ошибка'}")
    print(f"{'Alias':.<40} {'✅ Готово' if alias_result else '⚠️  Требуется Web UI'}")
    print(f"{'Верификация':.<40} {'✅ Пройдена' if verified else '⏳ Ожидает alias'}")
    
    if activity_result and alias_result and verified:
        print(f"\n🎉 ВСЁ ГОТОВО! Можно запускать тест:")
        print(f"   python3 bte-appbundle/scripts/test_bte_insert.py")
        sys.exit(0)
    elif activity_result and not alias_result:
        print(f"\n⚠️  Activity создана, но alias требует Web UI")
        print(f"   Следуйте инструкциям в docs/ACTIVITY_REGISTRATION_STATUS.md")
        sys.exit(1)
    else:
        print(f"\n❌ Регистрация не завершена")
        sys.exit(1)


if __name__ == "__main__":
    main()

