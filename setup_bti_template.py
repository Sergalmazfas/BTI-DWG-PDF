#!/usr/bin/env python3
"""
Автоматическая настройка Autodesk APS для BTI Template
- Создание AppBundle
- Загрузка template_bti.zip
- Создание Activity
- Создание Alias
- Тестовый WorkItem
"""

import subprocess
import requests
import json
import sys
import time
import os

# Константы
NICKNAME = "Forgecloudrun"
ENGINE = "Autodesk.AutoCAD+25_1"
APPBUNDLE_ID = "BTI_Template"
ACTIVITY_ID = "BTI_DWG2DWG"
ALIAS_ID = "v1"
ZIP_FILE = "template_bti.zip"
BASE_URL = "https://developer.api.autodesk.com/da/us-east/v3"

# Цвета для консоли
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_step(step, message):
    """Красивый вывод шагов"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}{step}{Colors.END}")
    print(f"{message}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")

def get_secret(name):
    """Получить секрет из Google Secret Manager"""
    cmd = f"gcloud secrets versions access latest --secret={name} --project=talkhint"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{Colors.RED}❌ Ошибка получения секрета {name}: {result.stderr}{Colors.END}")
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
        print(f"{Colors.RED}❌ Ошибка авторизации: {resp.text}{Colors.END}")
        sys.exit(1)
    
    token = resp.json()["access_token"]
    print(f"{Colors.GREEN}✅ Token получен{Colors.END}")
    return token

def create_appbundle(headers, client_id):
    """Создать AppBundle"""
    print_step("📦 ШАГ 1: Создание AppBundle", f"ID: {NICKNAME}.{APPBUNDLE_ID}")
    
    appbundle_data = {
        "id": APPBUNDLE_ID,
        "engine": ENGINE,
        "description": "BTI DWG template bundle with BTI_Template.dwt"
    }
    
    resp = requests.post(f"{BASE_URL}/appbundles", headers=headers, json=appbundle_data)
    
    if resp.status_code == 409:
        print(f"{Colors.YELLOW}⚠️  AppBundle уже существует, удаляем и создаем заново...{Colors.END}")
        # Удалить старый
        requests.delete(f"{BASE_URL}/appbundles/{client_id}.{APPBUNDLE_ID}", headers=headers)
        time.sleep(2)
        # Создать новый
        resp = requests.post(f"{BASE_URL}/appbundles", headers=headers, json=appbundle_data)
    
    if resp.status_code not in [200, 201]:
        print(f"{Colors.RED}❌ Ошибка создания AppBundle: {resp.status_code}{Colors.END}")
        print(resp.text)
        sys.exit(1)
    
    bundle = resp.json()
    print(f"{Colors.GREEN}✅ AppBundle создан:{Colors.END}")
    print(f"   ID: {bundle.get('id')}")
    print(f"   Version: {bundle.get('version')}")
    
    return bundle

def upload_zip(bundle, zip_file):
    """Загрузить ZIP-файл в Autodesk S3"""
    print_step("⬆️  ШАГ 2: Загрузка ZIP-файла", f"Файл: {zip_file}")
    
    if not os.path.exists(zip_file):
        print(f"{Colors.RED}❌ Файл {zip_file} не найден!{Colors.END}")
        print(f"{Colors.YELLOW}💡 Создайте template_bti.zip с BTI_Template.dwt и скриптом{Colors.END}")
        sys.exit(1)
    
    upload_params = bundle.get("uploadParameters")
    if not upload_params:
        print(f"{Colors.RED}❌ Нет uploadParameters в ответе{Colors.END}")
        sys.exit(1)
    
    endpoint = upload_params["endpointURL"]
    form_data = upload_params["formData"]
    
    with open(zip_file, "rb") as f:
        files = {"file": f}
        resp = requests.post(endpoint, data=form_data, files=files)
    
    if resp.status_code not in [200, 201, 204]:
        print(f"{Colors.RED}❌ Ошибка загрузки ZIP: {resp.status_code}{Colors.END}")
        print(resp.text)
        sys.exit(1)
    
    print(f"{Colors.GREEN}✅ ZIP загружен успешно{Colors.END}")
    print(f"   Размер: {os.path.getsize(zip_file)} bytes")

def create_activity(headers, client_id):
    """Создать Activity"""
    print_step("⚙️  ШАГ 3: Создание Activity", f"ID: {NICKNAME}.{ACTIVITY_ID}")
    
    activity_data = {
        "id": ACTIVITY_ID,
        "appbundles": [f"{client_id}.{APPBUNDLE_ID}+1"],
        "commandLine": [
            '$(engine.path)\\accoreconsole.exe /i "$(args[inputFile].path)" /al "$(appbundles[BTI_Template].path)" /s "_QSAVE\\n_QUIT\\n"'
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
                "description": "Output DWG with BTI template applied",
                "localName": "output.dwg"
            }
        },
        "description": "Apply BTI template to DWG files"
    }
    
    resp = requests.post(f"{BASE_URL}/activities", headers=headers, json=activity_data)
    
    if resp.status_code == 409:
        print(f"{Colors.YELLOW}⚠️  Activity уже существует, удаляем и создаем заново...{Colors.END}")
        # Удалить старый
        requests.delete(f"{BASE_URL}/activities/{client_id}.{ACTIVITY_ID}", headers=headers)
        time.sleep(2)
        # Создать новый
        resp = requests.post(f"{BASE_URL}/activities", headers=headers, json=activity_data)
    
    if resp.status_code not in [200, 201]:
        print(f"{Colors.RED}❌ Ошибка создания Activity: {resp.status_code}{Colors.END}")
        print(resp.text)
        sys.exit(1)
    
    activity = resp.json()
    print(f"{Colors.GREEN}✅ Activity создана:{Colors.END}")
    print(f"   ID: {activity.get('id')}")
    print(f"   Version: {activity.get('version')}")
    print(f"   Engine: {activity.get('engine')}")
    
    return activity

def create_alias(headers, client_id):
    """Создать Alias для Activity"""
    print_step("🏷️  ШАГ 4: Создание Alias", f"Alias: {ALIAS_ID} → version 1")
    
    # Сначала проверим существующие aliases
    resp = requests.get(
        f"{BASE_URL}/activities/{client_id}.{ACTIVITY_ID}/aliases",
        headers=headers
    )
    
    existing_aliases = resp.json().get("data", [])
    print(f"   Существующие aliases: {existing_aliases}")
    
    # Попробуем создать alias
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
        print(f"{Colors.YELLOW}⚠️  Alias {ALIAS_ID} уже существует{Colors.END}")
        # Обновить существующий alias
        resp = requests.patch(
            f"{BASE_URL}/activities/{client_id}.{ACTIVITY_ID}/aliases/{ALIAS_ID}",
            headers=headers,
            json={"version": 1}
        )
    
    if resp.status_code in [200, 201]:
        alias = resp.json()
        print(f"{Colors.GREEN}✅ Alias создан/обновлен:{Colors.END}")
        print(f"   Alias: {alias.get('id')}")
        print(f"   Version: {alias.get('version')}")
        print(f"   Full ID: {client_id}.{ACTIVITY_ID}+{ALIAS_ID}")
        return True
    else:
        print(f"{Colors.YELLOW}⚠️  Не удалось создать alias программно: {resp.status_code}{Colors.END}")
        print(f"   Response: {resp.text}")
        print(f"\n{Colors.YELLOW}💡 АЛЬТЕРНАТИВА: Создайте alias вручную через Web UI{Colors.END}")
        print(f"   1. https://aps.autodesk.com")
        print(f"   2. My Apps → Design Automation → AutoCAD")
        print(f"   3. Activities → {ACTIVITY_ID} → Aliases → Create")
        print(f"   4. ID: {ALIAS_ID}, Version: 1, Save")
        return False

def test_workitem(headers, client_id):
    """Запустить тестовый WorkItem"""
    print_step("🚀 ШАГ 5: Тестовый WorkItem", f"Activity: {client_id}.{ACTIVITY_ID}+{ALIAS_ID}")
    
    # Проверяем наличие входного файла
    input_url = "https://storage.googleapis.com/btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg"
    output_url = "https://storage.googleapis.com/btibot-processed/processed/test_with_template.dwg"
    
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
    
    print(f"   Input: {input_url}")
    print(f"   Output: {output_url}")
    
    resp = requests.post(f"{BASE_URL}/workitems", headers=headers, json=workitem_data)
    
    if resp.status_code not in [200, 201]:
        print(f"{Colors.RED}❌ Ошибка создания WorkItem: {resp.status_code}{Colors.END}")
        print(resp.text)
        return None
    
    workitem = resp.json()
    workitem_id = workitem.get("id")
    
    print(f"{Colors.GREEN}✅ WorkItem создан: {workitem_id}{Colors.END}")
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
            print(f"\n{Colors.GREEN}🎉 УСПЕХ! WorkItem выполнен!{Colors.END}")
            print(f"   Результат: {output_url}")
            return workitem_id
        elif current_status == "failed":
            print(f"\n{Colors.RED}❌ WorkItem FAILED!{Colors.END}")
            print(f"   Report: {json.dumps(status_data, indent=2)}")
            return None
        elif current_status in ["cancelled", "error"]:
            print(f"\n{Colors.RED}❌ WorkItem {current_status}!{Colors.END}")
            return None
    
    print(f"\n{Colors.YELLOW}⏱️  Timeout (2 мин) - проверьте статус позже{Colors.END}")
    return None

def main():
    """Главная функция"""
    print(f"\n{Colors.BLUE}{'='*70}")
    print("🏗️  АВТОМАТИЧЕСКАЯ НАСТРОЙКА AUTODESK APS ДЛЯ BTI TEMPLATE")
    print(f"{'='*70}{Colors.END}\n")
    
    # 1. Получить credentials
    print("🔐 Получение credentials из Google Secret Manager...")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    print(f"   Client ID: {client_id[:30]}...")
    
    # 2. Получить токен
    token = get_token(client_id, client_secret)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 3. Создать AppBundle
    bundle = create_appbundle(headers, client_id)
    
    # 4. Загрузить ZIP
    upload_zip(bundle, ZIP_FILE)
    
    # 5. Создать Activity
    activity = create_activity(headers, client_id)
    
    # 6. Создать Alias
    alias_created = create_alias(headers, client_id)
    
    # 7. Тестовый WorkItem (только если alias создан)
    if alias_created:
        workitem_id = test_workitem(headers, client_id)
        
        if workitem_id:
            print(f"\n{Colors.GREEN}{'='*70}")
            print("✅ ВСЕ ГОТОВО! AUTODESK APS НАСТРОЕН И РАБОТАЕТ!")
            print(f"{'='*70}{Colors.END}\n")
            print(f"📊 Итоги:")
            print(f"   - AppBundle: {client_id}.{APPBUNDLE_ID}+1")
            print(f"   - Activity: {client_id}.{ACTIVITY_ID}+1")
            print(f"   - Alias: {client_id}.{ACTIVITY_ID}+{ALIAS_ID}")
            print(f"   - WorkItem: {workitem_id} (success)")
            print(f"\n🎯 Следующие шаги:")
            print(f"   1. Проверить результат в GCS: test_with_template.dwg")
            print(f"   2. Обновить forge_client.py с новым activityId")
            print(f"   3. Deploy бота")
        else:
            print(f"\n{Colors.YELLOW}⚠️  WorkItem не выполнен - проверьте логи{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{'='*70}")
        print("⚠️  ALIAS НЕ СОЗДАН ПРОГРАММНО")
        print(f"{'='*70}{Colors.END}\n")
        print(f"📌 Создайте alias вручную через Web UI:")
        print(f"   https://aps.autodesk.com")
        print(f"   → My Apps → Design Automation → AutoCAD")
        print(f"   → Activities → {ACTIVITY_ID} → Aliases → Create")
        print(f"   → ID: {ALIAS_ID}, Version: 1, Save")
        print(f"\n   После создания запустите тест:")
        print(f"   python3 test_bti_workitem.py")

if __name__ == "__main__":
    main()

