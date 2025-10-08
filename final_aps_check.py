#!/usr/bin/env python3
"""
Финальная проверка и настройка Autodesk APS
- Проверка Design Automation API
- Создание Activity без AppBundle
- Создание Alias v1
- Тестирование WorkItem
- Генерация отчета
"""

import subprocess
import requests
import json
import sys
import time
from datetime import datetime

BASE_URL = "https://developer.api.autodesk.com/da/us-east/v3"
ENGINE = "Autodesk.AutoCAD+25_1"
ACTIVITY_ID = "SimpleDWG2DWG_NoTemplate"
ALIAS_ID = "v1"

# Для отчета
report = {
    "timestamp": datetime.now().isoformat(),
    "steps": [],
    "success": False
}

def add_step(name, status, details):
    """Добавить шаг в отчет"""
    report["steps"].append({
        "name": name,
        "status": status,
        "details": details
    })
    
    icon = "✅" if status == "success" else "❌" if status == "failed" else "⚠️"
    print(f"\n{icon} {name}")
    if details:
        print(f"   {details}")

def get_secret(name):
    """Получить секрет из Google Secret Manager"""
    cmd = f"gcloud secrets versions access latest --secret={name} --project=talkhint"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()

def main():
    print("=" * 70)
    print("🔍 ФИНАЛЬНАЯ ПРОВЕРКА И НАСТРОЙКА AUTODESK APS")
    print("=" * 70)
    
    # ===== ШАГ 1: Получить credentials =====
    print("\n📋 Шаг 1: Получение credentials из Secret Manager...")
    
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        add_step("Получение credentials", "failed", "Secrets не найдены в Secret Manager")
        print_report()
        sys.exit(1)
    
    add_step("Получение credentials", "success", f"Client ID: {client_id[:30]}...")
    
    # ===== ШАГ 2: Получить токен =====
    print("\n🔑 Шаг 2: Получение access token...")
    
    auth_resp = requests.post(
        "https://developer.api.autodesk.com/authentication/v2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "code:all data:read data:write"
        }
    )
    
    if auth_resp.status_code != 200:
        add_step("Авторизация", "failed", f"HTTP {auth_resp.status_code}: {auth_resp.text}")
        print_report()
        sys.exit(1)
    
    token = auth_resp.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    add_step("Авторизация", "success", "Access token получен")
    
    # ===== ШАГ 3: Проверить Design Automation API =====
    print("\n🔍 Шаг 3: Проверка Design Automation API...")
    
    # Проверить nickname
    me_resp = requests.get(f"{BASE_URL}/forgeapps/me", headers=headers)
    
    if me_resp.status_code == 200:
        try:
            app_info = me_resp.json()
            nickname = app_info.get("nickname") if isinstance(app_info, dict) else None
        except:
            nickname = None
        
        add_step("Design Automation API доступен", "success", f"Nickname: {nickname or 'не установлен'}")
    else:
        add_step("Design Automation API", "failed", f"HTTP {me_resp.status_code}")
    
    # Проверить существующие Activities
    activities_resp = requests.get(f"{BASE_URL}/activities", headers=headers)
    
    if activities_resp.status_code == 200:
        activities = activities_resp.json().get("data", [])
        user_activities = [a for a in activities if client_id in a]
        
        add_step("Проверка Activities", "success", 
                f"Найдено: {len(user_activities)} пользовательских Activities")
        
        if user_activities:
            print(f"   Существующие Activities:")
            for act in user_activities[:5]:
                print(f"     • {act}")
    else:
        add_step("Проверка Activities", "warning", f"HTTP {activities_resp.status_code}")
    
    # ===== ШАГ 4: Создать Activity =====
    print("\n📐 Шаг 4: Создание Activity SimpleDWG2DWG_NoTemplate...")
    
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
    activity_resp = requests.post(f"{BASE_URL}/activities", headers=headers, json=activity_data)
    
    if activity_resp.status_code == 409:
        print("   Activity уже существует, используем существующую...")
        activity_full_id = f"{client_id}.{ACTIVITY_ID}"
        
        # Получить информацию о существующей
        get_resp = requests.get(f"{BASE_URL}/activities/{activity_full_id}", headers=headers)
        if get_resp.status_code == 200:
            activity = get_resp.json()
            add_step("Activity создана/существует", "success", 
                    f"ID: {activity.get('id')}, Version: {activity.get('version')}")
        else:
            add_step("Activity", "warning", "Существует, но не удалось получить информацию")
            
    elif activity_resp.status_code in [200, 201]:
        activity = activity_resp.json()
        add_step("Activity создана", "success", 
                f"ID: {activity.get('id')}, Version: {activity.get('version')}, Engine: {ENGINE}")
    else:
        add_step("Activity создание", "failed", 
                f"HTTP {activity_resp.status_code}: {activity_resp.text}")
        print_report()
        sys.exit(1)
    
    # ===== ШАГ 5: Создать Alias =====
    print(f"\n🏷️  Шаг 5: Создание Alias {ALIAS_ID}...")
    
    activity_full_id = f"{client_id}.{ACTIVITY_ID}"
    
    # Проверить существующие aliases
    aliases_resp = requests.get(f"{BASE_URL}/activities/{activity_full_id}/aliases", headers=headers)
    existing_aliases = aliases_resp.json().get("data", []) if aliases_resp.status_code == 200 else []
    
    print(f"   Существующие aliases: {existing_aliases}")
    
    # Создать alias
    alias_data = {"id": ALIAS_ID, "version": 1}
    
    alias_resp = requests.post(
        f"{BASE_URL}/activities/{activity_full_id}/aliases",
        headers=headers,
        json=alias_data
    )
    
    if alias_resp.status_code in [200, 201]:
        alias = alias_resp.json()
        add_step("Alias создан", "success", 
                f"Alias: {alias.get('id')}, Version: {alias.get('version')}, Full ID: {activity_full_id}+{ALIAS_ID}")
        
    elif alias_resp.status_code == 409:
        # Alias уже существует - это нормально
        add_step("Alias существует", "success", f"Alias {ALIAS_ID} уже создан")
        
    else:
        add_step("Alias создание", "failed", 
                f"HTTP {alias_resp.status_code}: {alias_resp.text}")
        
        if "Cannot parse id" in alias_resp.text:
            add_step("Диагностика Alias", "warning", 
                    "Ошибка 'Cannot parse id' - возможно nickname не установлен")
    
    # ===== ШАГ 6: Тестовый WorkItem =====
    print("\n🧪 Шаг 6: Создание и мониторинг тестового WorkItem...")
    
    input_url = "https://storage.googleapis.com/btibot-processed/raw/1759837370/Plan 2025-10-03 155019_export_2D_room_height.dwg"
    output_url = "https://storage.googleapis.com/btibot-processed/processed/final_test.dwg"
    
    workitem_data = {
        "activityId": f"{activity_full_id}+{ALIAS_ID}",
        "arguments": {
            "inputFile": {"url": input_url},
            "resultFile": {"url": output_url, "verb": "put"}
        }
    }
    
    print(f"   Activity: {workitem_data['activityId']}")
    print(f"   Input: ...{input_url[-60:]}")
    print(f"   Output: ...{output_url[-60:]}")
    
    workitem_resp = requests.post(f"{BASE_URL}/workitems", headers=headers, json=workitem_data)
    
    if workitem_resp.status_code not in [200, 201]:
        add_step("WorkItem создание", "failed", 
                f"HTTP {workitem_resp.status_code}: {workitem_resp.text}")
        print_report()
        sys.exit(1)
    
    workitem = workitem_resp.json()
    workitem_id = workitem.get("id")
    
    print(f"\n   ✅ WorkItem создан: {workitem_id}")
    print(f"   ⏳ Ожидание завершения (max 2 мин)...")
    
    # Мониторинг
    final_status = None
    for i in range(24):  # 24 * 5 сек = 2 мин
        time.sleep(5)
        
        status_resp = requests.get(f"{BASE_URL}/workitems/{workitem_id}", headers=headers)
        status_data = status_resp.json()
        current_status = status_data.get("status")
        
        print(f"   [{i*5}s] Status: {current_status}")
        
        if current_status == "success":
            final_status = "success"
            add_step("WorkItem выполнен", "success", 
                    f"ID: {workitem_id}, Результат: {output_url}")
            report["success"] = True
            break
        elif current_status in ["failed", "cancelled", "error"]:
            final_status = current_status
            report_url = status_data.get("reportUrl", "N/A")
            add_step("WorkItem", "failed", 
                    f"Status: {current_status}, Report: {report_url}")
            break
    
    if not final_status:
        add_step("WorkItem", "warning", "Timeout (2 мин) - статус не получен")
    
    # ===== ОТЧЕТ =====
    print_report()
    
    # Сохранить отчет в файл
    with open("APS_FINAL_REPORT.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Отчет сохранен: APS_FINAL_REPORT.json")
    
    if report["success"]:
        print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
        sys.exit(0)
    else:
        print("\n⚠️  Некоторые проверки не прошли - см. отчет выше")
        sys.exit(1)

def print_report():
    """Вывести финальный отчет"""
    print("\n" + "=" * 70)
    print("📊 ФИНАЛЬНЫЙ ОТЧЕТ")
    print("=" * 70)
    
    print(f"\n⏰ Время: {report['timestamp']}")
    print(f"\n📋 Выполненные шаги:")
    
    for step in report["steps"]:
        icon = "✅" if step["status"] == "success" else "❌" if step["status"] == "failed" else "⚠️"
        print(f"\n{icon} {step['name']}")
        if step["details"]:
            print(f"   {step['details']}")
    
    print("\n" + "=" * 70)
    
    if report["success"]:
        print("✅ СТАТУС: ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
        print("\n🚀 Готово к интеграции с ботом и deploy!")
    else:
        print("⚠️  СТАТУС: ТРЕБУЕТСЯ ВНИМАНИЕ")
        print("\n💡 Проверьте детали шагов выше")
    
    print("=" * 70)

if __name__ == "__main__":
    main()

