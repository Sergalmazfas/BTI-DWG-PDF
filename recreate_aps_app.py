#!/usr/bin/env python3
"""
Пересоздание Autodesk APS приложения с nickname для поддержки API aliases
"""

import subprocess
import requests
import json
import sys
import time

NICKNAME = "Forgecloudrun"

def get_secret(name):
    """Получить секрет из Google Secret Manager"""
    cmd = f"gcloud secrets versions access latest --secret={name} --project=talkhint"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Ошибка получения секрета {name}: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def save_secret(name, value):
    """Сохранить секрет в Google Secret Manager"""
    # Создать новую версию секрета
    cmd = f"echo -n '{value}' | gcloud secrets versions add {name} --data-file=- --project=talkhint"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️  Ошибка обновления секрета {name}: {result.stderr}")
        print(f"   Попробуйте создать секрет вручную или обновить через консоль")
    else:
        print(f"   ✅ Секрет {name} обновлен")

def get_token(client_id, client_secret):
    """Получить Access Token"""
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
        return None
    
    return resp.json()["access_token"]

def main():
    print("=" * 70)
    print("🔄 ПЕРЕСОЗДАНИЕ AUTODESK APS ПРИЛОЖЕНИЯ С NICKNAME")
    print("=" * 70)
    
    # 1. Получить текущие credentials
    print("\n📋 Шаг 1: Получение текущих credentials...")
    try:
        old_client_id = get_secret("FORGE_CLIENT_ID")
        old_client_secret = get_secret("FORGE_CLIENT_SECRET")
        print(f"   Текущий Client ID: {old_client_id[:30]}...")
    except:
        print("   ⚠️  Текущие credentials не найдены - пропускаем удаление")
        old_client_id = None
        old_client_secret = None
    
    # 2. Попробовать получить токен для старого приложения
    if old_client_id and old_client_secret:
        print("\n🔍 Шаг 2: Проверка текущего приложения...")
        token = get_token(old_client_id, old_client_secret)
        
        if token:
            print("   ✅ Текущее приложение активно")
            
            # Проверить текущий nickname
            headers = {"Authorization": f"Bearer {token}"}
            me_resp = requests.get(
                "https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me",
                headers=headers
            )
            
            if me_resp.status_code == 200:
                try:
                    app_info = me_resp.json()
                    current_nickname = app_info.get("nickname") if isinstance(app_info, dict) else None
                except:
                    current_nickname = None
                print(f"   Текущий nickname: {current_nickname or 'НЕ УСТАНОВЛЕН'}")
                
                if current_nickname == NICKNAME:
                    print(f"\n✅ Приложение уже имеет nickname '{NICKNAME}'!")
                    print("   Пересоздание не требуется.")
                    print("\n🚀 Запустите: python3 setup_bti_template.py")
                    return
                
                # Попробовать установить nickname на существующее приложение
                print(f"\n🔧 Попытка установить nickname '{NICKNAME}' на текущее приложение...")
                patch_resp = requests.patch(
                    "https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me",
                    headers={**headers, "Content-Type": "application/json"},
                    json={"nickname": NICKNAME}
                )
                
                if patch_resp.status_code in [200, 204]:
                    print(f"   ✅ Nickname установлен успешно!")
                    print("\n🚀 Запустите: python3 setup_bti_template.py")
                    return
                else:
                    print(f"   ⚠️  Не удалось установить nickname: {patch_resp.status_code}")
                    print(f"   Response: {patch_resp.text}")
                    print("\n   Возможно nickname уже занят или требуется пересоздание приложения")
            else:
                print(f"   ⚠️  Не удалось получить информацию о приложении: {me_resp.status_code}")
        else:
            print("   ⚠️  Не удалось авторизоваться со старыми credentials")
    
    # 3. Инструкции по созданию нового приложения
    print("\n" + "=" * 70)
    print("📝 ИНСТРУКЦИЯ: СОЗДАНИЕ НОВОГО ПРИЛОЖЕНИЯ С NICKNAME")
    print("=" * 70)
    
    print("""
К сожалению, Autodesk APS API не предоставляет программный способ:
1. Удаления существующих приложений
2. Создания новых приложений
3. Получения Client Secret для новых приложений

Эти операции доступны ТОЛЬКО через Web UI.

╔══════════════════════════════════════════════════════════════════╗
║  РУЧНОЕ СОЗДАНИЕ ПРИЛОЖЕНИЯ (5-7 минут)                         ║
╚══════════════════════════════════════════════════════════════════╝

ШАГ 1: Удалить старое приложение (опционально)
───────────────────────────────────────────────
1. Открыть: https://aps.autodesk.com
2. Login в аккаунт
3. My Apps → Найти текущее приложение
4. Click "⋮" (три точки) → Delete
5. Подтвердить удаление


ШАГ 2: Создать новое приложение
────────────────────────────────
1. My Apps → Create App
2. Заполнить форму:
   
   App Name: BTI Processor
   App Type: Design Automation API
   Callback URL: https://telegram-bot-commands-637190449180.europe-west1.run.app/callback
   Description: BTI DWG Template Processor
   
3. Click "Create App"


ШАГ 3: ВАЖНО - Установить Nickname СРАЗУ
──────────────────────────────────────────
1. После создания приложения откроется страница с Client ID/Secret
2. ⚠️  НЕ ЗАКРЫВАЙТЕ ЭТУ СТРАНИЦУ - Client Secret показывается только один раз!
3. Найти поле "Nickname" (может быть внизу страницы)
4. Ввести: Forgecloudrun
5. Click "Save" или "Update"


ШАГ 4: Скопировать новые credentials
─────────────────────────────────────
Client ID: [скопировать]
Client Secret: [скопировать - показывается только один раз!]


ШАГ 5: Обновить Secret Manager
───────────────────────────────
Запустите команды ниже, заменив YOUR_CLIENT_ID и YOUR_CLIENT_SECRET:

echo -n 'YOUR_CLIENT_ID' | gcloud secrets versions add FORGE_CLIENT_ID --data-file=- --project=talkhint
echo -n 'YOUR_CLIENT_SECRET' | gcloud secrets versions add FORGE_CLIENT_SECRET --data-file=- --project=talkhint


ШАГ 6: Проверка
───────────────
python3 << 'EOF'
import subprocess, requests

def get_secret(n):
    return subprocess.run(f"gcloud secrets versions access latest --secret={n} --project=talkhint".split(), capture_output=True, text=True).stdout.strip()

client_id = get_secret("FORGE_CLIENT_ID")
client_secret = get_secret("FORGE_CLIENT_SECRET")

print(f"Client ID: {client_id[:30]}...")

# Get token
r = requests.post("https://developer.api.autodesk.com/authentication/v2/token",
    data={"client_id":client_id,"client_secret":client_secret,"grant_type":"client_credentials","scope":"code:all"})

if r.status_code == 200:
    token = r.json()["access_token"]
    
    # Check nickname
    me = requests.get("https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me",
        headers={"Authorization": f"Bearer {token}"})
    
    if me.status_code == 200:
        nickname = me.json().get("nickname")
        print(f"✅ Nickname: {nickname}")
        
        if nickname == "Forgecloudrun":
            print("\\n🎉 ВСЕ ГОТОВО! Запустите: python3 setup_bti_template.py")
        else:
            print(f"\\n⚠️  Nickname не установлен или неправильный!")
            print("   Установите nickname 'Forgecloudrun' через Web UI")
    else:
        print(f"❌ Ошибка проверки приложения: {me.status_code}")
else:
    print(f"❌ Ошибка авторизации: {r.status_code}")
EOF


╔══════════════════════════════════════════════════════════════════╗
║  ПОСЛЕ СОЗДАНИЯ И НАСТРОЙКИ                                      ║
╚══════════════════════════════════════════════════════════════════╝

1. Убедитесь что nickname = 'Forgecloudrun' ✅
2. Убедитесь что credentials обновлены в Secret Manager ✅
3. Запустите полную автоматизацию:

   python3 setup_bti_template.py

4. Проверьте что alias 'v1' создается БЕЗ ОШИБОК ✅
5. Запустите тест:

   python3 test_bti_workitem.py

6. ✅ ГОТОВО!

═══════════════════════════════════════════════════════════════════
    """)

if __name__ == "__main__":
    main()

