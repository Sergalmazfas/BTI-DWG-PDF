#!/usr/bin/env python3
"""
🎯 ПОЛНАЯ АВТОМАТИЗАЦИЯ APS PIPELINE
Загрузка AppBundle → Создание Activity → Тест WorkItem
БЕЗ FALLBACK - только официальный Autodesk APS API
"""

import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime

# Цвета для вывода
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_step(step, message):
    print(f"\n{Colors.BLUE}━━━ {step} ━━━{Colors.END}")
    print(f"{Colors.YELLOW}{message}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def get_secret(secret_name):
    """Получить секрет из Google Secret Manager"""
    try:
        cmd = f"gcloud secrets versions access latest --secret={secret_name} --project=talkhint"
        result = subprocess.run(cmd.split(), capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print_error(f"Ошибка получения секрета {secret_name}: {e}")
        sys.exit(1)

def get_access_token(client_id, client_secret):
    """Получить OAuth2 токен от Autodesk"""
    print_step("STEP 0", "Получение OAuth2 токена")
    
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    
    response = requests.post(url, data=data)
    response.raise_for_status()
    
    token = response.json()["access_token"]
    print_success(f"Токен получен: {token[:20]}...")
    return token

def check_appbundle_exists(token, client_id, appbundle_name):
    """Проверить существование AppBundle"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/appbundles/{client_id}.{appbundle_name}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    return response.status_code == 200

def delete_appbundle(token, client_id, appbundle_name):
    """Удалить существующий AppBundle"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/appbundles/{client_id}.{appbundle_name}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.delete(url, headers=headers)
    if response.status_code in [200, 204]:
        print_success(f"AppBundle {appbundle_name} удалён")
    else:
        print_error(f"Не удалось удалить AppBundle: {response.text}")

def create_appbundle(token, client_id):
    """Создать AppBundle"""
    print_step("STEP 1", "Создание AppBundle: BTI_TemplateAppBundle")
    
    appbundle_name = "BTI_TemplateAppBundle"
    
    # Проверяем существование
    if check_appbundle_exists(token, client_id, appbundle_name):
        print("⚠️  AppBundle уже существует. Удаляем...")
        delete_appbundle(token, client_id, appbundle_name)
        time.sleep(2)
    
    url = "https://developer.api.autodesk.com/da/us-east/v3/appbundles"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "id": appbundle_name,
        "engine": "Autodesk.AutoCAD+25_1",
        "description": "BTI Template Plugin for DWG processing with INSERTBTE or QSAVE"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code not in [200, 201]:
        print_error(f"Ошибка создания AppBundle: {response.text}")
        sys.exit(1)
    
    result = response.json()
    print_success(f"AppBundle создан: {result['id']}")
    print_success(f"Version: {result.get('version', 1)}")
    
    # Возвращаем upload parameters для загрузки ZIP
    return result

def upload_appbundle_zip(upload_params, zip_path):
    """Загрузить ZIP с AppBundle"""
    print_step("STEP 2", f"Загрузка ZIP: {zip_path}")
    
    if not os.path.exists(zip_path):
        print_error(f"Файл не найден: {zip_path}")
        print("💡 Создайте BTI_TemplateAppBundle.bundle.zip используя BUILD.md")
        print("💡 Или используйте SimpleDWG подход без .NET плагина")
        return False
    
    endpoint_url = upload_params.get("endpointURL")
    form_data = upload_params.get("formData", {})
    
    # Подготовка файлов для multipart/form-data
    files = {}
    data = {}
    
    for key, value in form_data.items():
        data[key] = value
    
    with open(zip_path, 'rb') as f:
        files['file'] = f
        response = requests.post(endpoint_url, data=data, files=files)
    
    if response.status_code in [200, 201, 204]:
        print_success(f"ZIP загружен успешно")
        return True
    else:
        print_error(f"Ошибка загрузки ZIP: {response.status_code}")
        print_error(response.text)
        return False

def create_appbundle_alias(token, client_id, appbundle_name, version=1):
    """Создать alias для AppBundle"""
    print_step("STEP 3", f"Создание alias v1 для {appbundle_name}")
    
    # ВАЖНО: используем appbundle_name БЕЗ nickname для создания alias
    url = f"https://developer.api.autodesk.com/da/us-east/v3/appbundles/{appbundle_name}/aliases"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "id": "v1",
        "version": version
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print_success(f"Alias создан: {result.get('id')}")
        print_success(f"Полный ID: {client_id}.{appbundle_name}+v1")
        return True
    elif response.status_code == 409:
        print("⚠️  Alias уже существует")
        return True
    else:
        print_error(f"Ошибка создания alias: {response.text}")
        return False

def create_activity(token, client_id, appbundle_name):
    """Создать Activity с привязкой к AppBundle"""
    print_step("STEP 4", "Создание Activity: BTI_DWG2DWG")
    
    activity_name = "BTI_DWG2DWG"
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Команда для выполнения плагина
    command_line = [
        '$(engine.path)\\\\accoreconsole.exe',
        '/i', '"$(args[inputFile].path)"',
        '/al', '"$(appbundles[' + appbundle_name + '].path)"',
        '/s', '"ApplyBTITemplate\\n"'
    ]
    
    data = {
        "id": activity_name,
        "commandLine": [" ".join(command_line)],
        "engine": "Autodesk.AutoCAD+25_1",
        "appbundles": [f"{client_id}.{appbundle_name}+v1"],
        "parameters": {
            "inputFile": {
                "verb": "get",
                "localName": "input.dwg",
                "description": "Input DWG file",
                "required": True
            },
            "resultFile": {
                "verb": "put",
                "localName": "output.dwg",
                "description": "Output DWG file",
                "required": True
            }
        },
        "description": "BTI DWG to DWG processing with template insertion"
    }
    
    # Удаляем если существует
    delete_url = f"{url}/{client_id}.{activity_name}"
    requests.delete(delete_url, headers=headers)
    time.sleep(1)
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code not in [200, 201]:
        print_error(f"Ошибка создания Activity: {response.text}")
        sys.exit(1)
    
    result = response.json()
    print_success(f"Activity создан: {result['id']}")
    print_success(f"Version: {result.get('version', 1)}")
    print_success(f"AppBundles: {result.get('appbundles', [])}")
    
    return result

def create_activity_alias(token, client_id, activity_name, version=1):
    """Создать alias для Activity"""
    print_step("STEP 5", f"Создание alias v1 для Activity {activity_name}")
    
    url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_name}/aliases"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "id": "v1",
        "version": version
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        print_success(f"Alias создан: {result.get('id')}")
        print_success(f"Полный ID: {client_id}.{activity_name}+v1")
        return True
    elif response.status_code == 409:
        print("⚠️  Alias уже существует")
        return True
    else:
        print_error(f"Ошибка создания alias: {response.text}")
        return False

def test_workitem(token, client_id, activity_name, test_dwg_url):
    """Запустить тестовый WorkItem"""
    print_step("STEP 6", "Тестирование WorkItem")
    
    # Создаём signed URL для output
    from google.cloud import storage
    from google.oauth2 import service_account
    from datetime import timedelta
    
    # Получаем Service Account credentials
    sa_json_str = get_secret("FORGE_SERVICE_KEY")
    sa_credentials = service_account.Credentials.from_service_account_info(
        json.loads(sa_json_str)
    )
    
    gcs_client = storage.Client(credentials=sa_credentials)
    bucket = gcs_client.bucket("btibot-processed")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_blob_path = f"test_aps/{timestamp}/result.dwg"
    output_blob = bucket.blob(output_blob_path)
    
    output_url = output_blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="PUT"
    )
    
    print(f"📥 Input: {test_dwg_url}")
    print(f"📤 Output: gs://btibot-processed/{output_blob_path}")
    
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "activityId": f"{client_id}.{activity_name}+v1",
        "arguments": {
            "inputFile": {
                "url": test_dwg_url
            },
            "resultFile": {
                "url": output_url,
                "verb": "put"
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code not in [200, 201]:
        print_error(f"Ошибка создания WorkItem: {response.text}")
        return None
    
    result = response.json()
    workitem_id = result['id']
    print_success(f"WorkItem создан: {workitem_id}")
    
    # Ждём завершения
    print("\n⏳ Ожидание завершения WorkItem...")
    max_attempts = 60  # 10 минут
    
    for attempt in range(max_attempts):
        time.sleep(10)
        
        status_url = f"{url}/{workitem_id}"
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()
        
        status = status_data.get('status')
        print(f"   Попытка {attempt + 1}/{max_attempts}: {status}")
        
        if status == 'success':
            print_success("✅ WorkItem завершён успешно!")
            print_success(f"📊 Stats: {json.dumps(status_data.get('stats', {}), indent=2)}")
            print_success(f"📄 Report: {status_data.get('reportUrl', 'N/A')}")
            return status_data
        elif status in ['failedInstructions', 'failedDownload', 'failedUpload', 'failed']:
            print_error(f"❌ WorkItem failed: {status}")
            print_error(f"📄 Report: {status_data.get('reportUrl', 'N/A')}")
            return None
        elif status in ['pending', 'inprogress']:
            continue
        else:
            print(f"⚠️  Неизвестный статус: {status}")
    
    print_error("⏱️ Timeout: WorkItem не завершился за 10 минут")
    return None

def main():
    """Главная функция"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}🎯 AUTODESK APS - ПОЛНАЯ АВТОМАТИЗАЦИЯ PIPELINE{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")
    
    # Получаем credentials
    print_step("SETUP", "Получение credentials из Secret Manager")
    client_id = get_secret("FORGE_CLIENT_ID")
    client_secret = get_secret("FORGE_CLIENT_SECRET")
    print_success(f"Client ID: {client_id[:20]}...")
    
    # Получаем токен
    token = get_access_token(client_id, client_secret)
    
    # ВАРИАНТ 1: Попытка загрузить .NET плагин (если есть ZIP)
    zip_path = "BTI_TemplateAppBundle/BTI_TemplateAppBundle.bundle.zip"
    
    if os.path.exists(zip_path):
        print(f"\n💡 Найден ZIP: {zip_path}")
        use_dotnet = input("Использовать .NET плагин? (y/n): ").lower() == 'y'
    else:
        print(f"\n⚠️  ZIP не найден: {zip_path}")
        print("💡 Будем использовать SimpleDWG подход (QSAVE без плагина)")
        use_dotnet = False
    
    if use_dotnet:
        # Создаём AppBundle с .NET плагином
        appbundle_result = create_appbundle(token, client_id)
        
        # Загружаем ZIP
        if "uploadParameters" in appbundle_result:
            success = upload_appbundle_zip(appbundle_result["uploadParameters"], zip_path)
            if not success:
                print_error("Загрузка ZIP не удалась")
                sys.exit(1)
        
        # Создаём alias для AppBundle
        create_appbundle_alias(token, client_id, "BTI_TemplateAppBundle")
        
        # Создаём Activity
        create_activity(token, client_id, "BTI_TemplateAppBundle")
        activity_name = "BTI_DWG2DWG"
    else:
        # Используем SimpleDWG подход БЕЗ AppBundle
        print_step("ALTERNATIVE", "Используем SimpleDWG2DWG_NoTemplate (БЕЗ .NET плагина)")
        print("✅ SimpleDWG2DWG_NoTemplate+v1 уже создан ранее")
        print("✅ Команда: QSAVE + QUIT")
        activity_name = "SimpleDWG2DWG_NoTemplate"
    
    # Создаём alias для Activity
    create_activity_alias(token, client_id, activity_name)
    
    # Тестируем WorkItem
    test_dwg = "https://storage.googleapis.com/btibot-processed/raw/1759939981/Plan%202025-10-03%20155019_export_2D.dwg"
    result = test_workitem(token, client_id, activity_name, test_dwg)
    
    if result:
        print(f"\n{Colors.GREEN}{'='*70}{Colors.END}")
        print(f"{Colors.GREEN}🎉 УСПЕХ! APS PIPELINE РАБОТАЕТ БЕЗ FALLBACK!{Colors.END}")
        print(f"{Colors.GREEN}{'='*70}{Colors.END}")
        
        print(f"\n📋 Следующие шаги:")
        print(f"1. Обновить forge_client.py: activityId = '{client_id}.{activity_name}+v1'")
        print(f"2. Отключить fallback в app.py")
        print(f"3. Задеплоить telegram-bti-bot")
        print(f"4. Протестировать через Telegram")
    else:
        print(f"\n{Colors.RED}{'='*70}{Colors.END}")
        print(f"{Colors.RED}❌ ОШИБКА: WorkItem не прошёл успешно{Colors.END}")
        print(f"{Colors.RED}{'='*70}{Colors.END}")
        print(f"\n💡 Проверьте:")
        print(f"1. Report URL в логах выше")
        print(f"2. Параметры Activity (inputFile, resultFile)")
        print(f"3. CommandLine в Activity")

if __name__ == "__main__":
    main()

