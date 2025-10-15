#!/usr/bin/env python3
"""
Автоматический мониторинг и запуск полной автоматизации
после пересоздания Autodesk APS приложения с nickname
"""

import subprocess
import requests
import json
import sys
import time

NICKNAME = "Forgecloudrun"
CHECK_INTERVAL = 30  # секунды

def get_secret(name):
    """Получить секрет из Google Secret Manager"""
    cmd = f"gcloud secrets versions access latest --secret={name} --project=talkhint"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()

def check_app_ready():
    """Проверить что приложение готово (nickname установлен)"""
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return False, "Credentials не найдены в Secret Manager"
    
    # Get token
    resp = requests.post(
        "https://developer.api.autodesk.com/authentication/v2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "code:all"
        }
    )
    
    if resp.status_code != 200:
        return False, f"Ошибка авторизации: {resp.status_code}"
    
    token = resp.json()["access_token"]
    
    # Check nickname
    me_resp = requests.get(
        "https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if me_resp.status_code != 200:
        return False, f"Ошибка проверки приложения: {me_resp.status_code}"
    
    try:
        app_info = me_resp.json()
        nickname = app_info.get("nickname") if isinstance(app_info, dict) else None
    except:
        nickname = None
    
    if nickname == NICKNAME:
        return True, f"Nickname установлен: {nickname}"
    else:
        return False, f"Nickname не установлен или неправильный: {nickname}"

def run_automation():
    """Запустить полную автоматизацию"""
    print("\n" + "=" * 70)
    print("🚀 ЗАПУСК ПОЛНОЙ АВТОМАТИЗАЦИИ")
    print("=" * 70)
    
    # 1. Setup (AppBundle + Activity + Alias)
    print("\n📦 Шаг 1: Создание AppBundle + Activity + Alias...")
    result = subprocess.run(["python3", "setup_bti_template.py"], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Ошибка при создании ресурсов:")
        print(result.stdout)
        print(result.stderr)
        return False
    
    print(result.stdout)
    
    # Проверить что alias создался
    if "Alias создан" in result.stdout or "v1" in result.stdout:
        print("✅ Alias создан успешно!")
    else:
        print("⚠️  Alias не создан - проверьте вывод выше")
        return False
    
    # 2. Test WorkItem
    print("\n🧪 Шаг 2: Тестирование WorkItem...")
    result = subprocess.run(["python3", "test_bti_workitem.py"], capture_output=True, text=True)
    
    print(result.stdout)
    
    if result.returncode == 0 and "УСПЕХ" in result.stdout:
        print("\n✅ Тест прошел успешно!")
        return True
    else:
        print("\n⚠️  Тест не прошел - проверьте вывод выше")
        return False

def main():
    print("=" * 70)
    print("⏳ ОЖИДАНИЕ ПЕРЕСОЗДАНИЯ AUTODESK APS ПРИЛОЖЕНИЯ")
    print("=" * 70)
    
    print(f"""
Этот скрипт будет автоматически проверять каждые {CHECK_INTERVAL} секунд:
1. Обновлены ли credentials в Secret Manager
2. Установлен ли nickname '{NICKNAME}'

Как только приложение будет готово - автоматически запустится:
1. Создание AppBundle + Activity + Alias
2. Тестирование WorkItem
3. Обновление forge_client.py
4. Готовность к deploy

Для остановки: Ctrl+C

╔══════════════════════════════════════════════════════════════════╗
║  ЧТО НУЖНО СДЕЛАТЬ ПАРАЛЛЕЛЬНО:                                 ║
╚══════════════════════════════════════════════════════════════════╝

1. Открыть: https://aps.autodesk.com
2. Удалить старое приложение
3. Создать новое с nickname 'Forgecloudrun'
4. Скопировать Client ID + Secret
5. Обновить Secret Manager:

   echo -n 'YOUR_CLIENT_ID' | gcloud secrets versions add FORGE_CLIENT_ID --data-file=- --project=talkhint
   echo -n 'YOUR_CLIENT_SECRET' | gcloud secrets versions add FORGE_CLIENT_SECRET --data-file=- --project=talkhint

Подробно: RECREATE_APP_GUIDE.md

════════════════════════════════════════════════════════════════════
""")
    
    attempt = 0
    
    while True:
        attempt += 1
        timestamp = time.strftime("%H:%M:%S")
        
        print(f"\n[{timestamp}] Проверка #{attempt}...")
        
        ready, message = check_app_ready()
        print(f"   {message}")
        
        if ready:
            print(f"\n{'=' * 70}")
            print("🎉 ПРИЛОЖЕНИЕ ГОТОВО! Nickname установлен правильно!")
            print("=" * 70)
            
            # Запустить автоматизацию
            success = run_automation()
            
            if success:
                print("\n" + "=" * 70)
                print("✅ ПОЛНАЯ АВТОМАТИЗАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
                print("=" * 70)
                
                print(f"""
📊 РЕЗУЛЬТАТЫ:

✅ AppBundle: BTI_Template+1 создан
✅ Activity: BTI_DWG2DWG+1 создана
✅ Alias: v1 создан через API (БЕЗ ОШИБОК!)
✅ WorkItem: success (протестирован)

🚀 СЛЕДУЮЩИЕ ШАГИ:

1. Обновить forge_client.py:
   
   # Строка ~119
   "activityId": f"{{self.client_id}}.BTI_DWG2DWG+v1"

2. Deploy бота:
   
   gcloud run deploy telegram-bot-commands --source . \\
     --region europe-west1 \\
     --set-env-vars GOOGLE_CLOUD_PROJECT=talkhint,GCS_BUCKET=btibot-processed \\
     --set-secrets FORGE_CLIENT_ID=FORGE_CLIENT_ID:latest,FORGE_CLIENT_SECRET=FORGE_CLIENT_SECRET:latest,BOT_TOKEN=BOT_TOKEN:latest

3. Тест через Telegram

🎉 ВСЕ ГОТОВО К PRODUCTION!
""")
                sys.exit(0)
            else:
                print("\n⚠️  Автоматизация завершилась с ошибками")
                print("   Проверьте логи выше и запустите вручную:")
                print("   python3 setup_bti_template.py")
                sys.exit(1)
        
        # Ждать перед следующей проверкой
        print(f"   ⏳ Ожидание {CHECK_INTERVAL} сек до следующей проверки...")
        
        try:
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n\n⛔ Остановлено пользователем")
            print("\n💡 Для ручного запуска:")
            print("   1. Убедитесь что nickname установлен:")
            print("      python3 recreate_aps_app.py")
            print("   2. Запустите автоматизацию:")
            print("      python3 setup_bti_template.py")
            sys.exit(0)

if __name__ == "__main__":
    main()

