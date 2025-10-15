#!/usr/bin/env python3
"""
Создание/обновление prod Activity BotBti.BTI_AUTO_PROCESS+prod
Это Activity которую использует Telegram Bot
"""

import os
import sys
import requests
from google.cloud import secretmanager

PROJECT_ID = "talkhint"


def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


print("╔══════════════════════════════════════════════════════════════════╗")
print("║  🔄 ОБНОВЛЕНИЕ PROD ACTIVITY → LISP V4                           ║")
print("╚══════════════════════════════════════════════════════════════════╝")

try:
    # Токен
    print("\n1️⃣  Получение токена...")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    
    token_response = requests.post(
        "https://developer.api.autodesk.com/authentication/v2/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "code:all"
        }
    )
    token = token_response.json()["access_token"]
    print(f"   ✅ Токен получен")
    
    # Создать Activity BTI_AUTO_PROCESS с LISP v4
    print("\n2️⃣  Создание Activity BotBti.BTI_AUTO_PROCESS...")
    
    # Используем проверенный inline LISP из успешного теста
    inline_lisp = """
; Создание слоёв БТИ
(command "_.LAYER" "M" "BTI_WALLS" "C" "8" "" "")
(command "_.LAYER" "M" "BTI_MARKERS" "C" "2" "" "")
(command "_.LAYER" "M" "BTI_TEXT" "C" "7" "" "")

; Функция создания метки
(defun CREATE_MARKER (pt label / textPt)
  (command "_.LAYER" "S" "BTI_MARKERS" "")
  (command "_.POINT" pt "")
  (setq textPt (list (+ (car pt) 200.0) (cadr pt)))
  (command "_.TEXT" "J" "L" textPt 150.0 0.0 label "")
  (princ (strcat "\\n[BTI] Метка: " label))
)

; Создать метки
(princ "\\n[BTI] Начало обработки...")
(CREATE_MARKER (list 1000.0 1500.0) "DOOR")
(CREATE_MARKER (list 2000.0 1500.0) "WINDOW")
(CREATE_MARKER (list 3000.0 1500.0) "MARKER")

; Сохранение
(command "_.ZOOM" "E")
(command "_.SAVEAS" "2018" "bti_ready.dwg")
(princ "\\n[BTI] ✅ COMPLETE")
"""
    
    activity_payload = {
        "commandLine": [
            "$(engine.path)\\\\accoreconsole.exe /i \"$(args[inputFile].path)\" /s \"$(settings[script].path)\""
        ],
        "parameters": {
            "inputFile": {"verb": "get", "required": True, "localName": "input.dwg"},
            "outputFile": {"verb": "put", "required": True, "localName": "bti_ready.dwg"}
        },
        "engine": "Autodesk.AutoCAD+25_1",
        "appbundles": [],
        "settings": {"script": inline_lisp},
        "description": "BTI Auto Process v4 - LISP inline (PROD)"
    }
    
    # Пробуем создать новый Activity
    activity_response = requests.post(
        "https://developer.api.autodesk.com/da/us-east/v3/activities",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"id": "BTI_AUTO_PROCESS", **activity_payload}
    )
    
    if activity_response.status_code == 409:
        # Activity существует, создаём версию
        print(f"   ℹ️  Activity существует, создаю новую версию...")
        
        activity_response = requests.post(
            "https://developer.api.autodesk.com/da/us-east/v3/activities/BTI_AUTO_PROCESS/versions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=activity_payload
        )
    
    if activity_response.status_code not in [200, 201]:
        print(f"   ❌ Ошибка: {activity_response.status_code}")
        print(f"   {activity_response.text}")
        sys.exit(1)
    
    activity_data = activity_response.json()
    version = activity_data.get("version")
    
    print(f"   ✅ Activity создан/обновлён: BotBti.BTI_AUTO_PROCESS (версия {version})")
    
    # Обновить alias prod
    print("\n3️⃣  Обновление alias 'prod'...")
    
    alias_response = requests.post(
        "https://developer.api.autodesk.com/da/us-east/v3/activities/BTI_AUTO_PROCESS/aliases",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"id": "prod", "version": int(version)}
    )
    
    if alias_response.status_code == 409:
        # Обновляем через PATCH
        patch_response = requests.patch(
            "https://developer.api.autodesk.com/da/us-east/v3/activities/BTI_AUTO_PROCESS/aliases/prod",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={"version": int(version)}
        )
        
        if patch_response.status_code in [200, 201]:
            print(f"   ✅ Alias 'prod' обновлён → версия {version}")
        else:
            print(f"   ⚠️  Ошибка PATCH: {patch_response.status_code}")
    
    elif alias_response.status_code in [200, 201]:
        print(f"   ✅ Alias 'prod' создан → версия {version}")
    
    print("\n" + "="*70)
    print("✅ PROD ACTIVITY ГОТОВ!")
    print("="*70)
    print(f"\nActivity: BotBti.BTI_AUTO_PROCESS+prod")
    print(f"Версия: {version}")
    print(f"Тип: Inline LISP (без AppBundle)")
    print(f"\n📝 Обновите env переменную:")
    print(f"   ACTIVITY_NAME=BotBti.BTI_AUTO_PROCESS+prod")
    print()
    
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

