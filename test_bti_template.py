#!/usr/bin/env python3
"""
Тест типового шаблона BTI
Проверяет работу Activity BotBti.BTI_INSERT_Basman+v1
"""

import os
import sys
import time
from google.cloud import storage
from forge_client import ForgeClient
from google.cloud import secretmanager
from google.oauth2 import service_account
from datetime import timedelta
import json

def get_secret(secret_id):
    """Получить секрет из Google Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/talkhint/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def test_bti_template():
    """Тест типового шаблона BTI"""
    print("🧪 Тест типового шаблона BTI\n")
    
    # 1. Проверяем доступность шаблона
    print("1️⃣ Проверка доступности шаблона...")
    template_url = "https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg"
    
    import requests
    response = requests.head(template_url)
    if response.status_code == 200:
        print(f"   ✅ Шаблон доступен: {template_url}")
        print(f"   📏 Размер: {int(response.headers.get('content-length', 0)) / 1024:.1f} KB")
    else:
        print(f"   ❌ Шаблон недоступен: {response.status_code}")
        return False
    
    # 2. Подготовка тестового файла
    print("\n2️⃣ Подготовка тестового DWG...")
    
    # Используем шаблон как тестовый входной файл
    test_input_url = template_url
    print(f"   📥 Входной файл: {test_input_url}")
    
    # 3. Создание signed URL для выхода
    print("\n3️⃣ Создание signed URL для результата...")
    
    # Получаем Service Account credentials
    sa_json = get_secret("FORGE_SERVICE_KEY")
    sa_credentials = service_account.Credentials.from_service_account_info(
        json.loads(sa_json)
    )
    
    gcs_client = storage.Client(credentials=sa_credentials)
    bucket = gcs_client.bucket("btibot-processed")
    
    # Путь для результата
    test_id = f"test_{int(time.time())}"
    output_path = f"test_results/bti_template_{test_id}.dwg"
    output_blob = bucket.blob(output_path)
    
    # Signed URL для записи
    output_url = output_blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="PUT"
    )
    
    print(f"   📤 Output path: {output_path}")
    print(f"   📤 Signed URL создан")
    
    # 4. Запуск WorkItem с шаблоном
    print("\n4️⃣ Запуск WorkItem с типовым шаблоном BTI...")
    
    try:
        forge_client = ForgeClient()
        
        # Запускаем с шаблоном
        workitem = forge_client.submit_workitem(
            test_input_url, 
            output_url, 
            use_template=True
        )
        
        workitem_id = workitem['id']
        print(f"   ✅ WorkItem создан: {workitem_id}")
        
        # 5. Ожидание результата
        print("\n5️⃣ Ожидание результата...")
        result = forge_client.wait_for_completion(workitem_id, timeout_minutes=5)
        
        status = result.get('status')
        print(f"\n   📊 Статус: {status}")
        
        if status == 'success':
            print(f"   ✅ Успешно!")
            
            # Проверяем результат
            print("\n6️⃣ Проверка результата...")
            
            # Делаем файл публичным для проверки
            output_blob.make_public()
            public_url = f"https://storage.googleapis.com/btibot-processed/{output_path}"
            
            # Проверяем размер
            output_blob.reload()
            result_size = output_blob.size
            
            print(f"   📏 Размер результата: {result_size / 1024:.1f} KB")
            print(f"   🔗 URL результата: {public_url}")
            
            # Статистика
            stats = result.get('stats', {})
            if stats:
                print(f"\n   📈 Статистика:")
                print(f"      Время загрузки: {stats.get('downloadResult', {}).get('timeDownload', 'N/A')}")
                print(f"      Время обработки: {stats.get('timeInstructionsMs', 'N/A')} ms")
            
            print("\n   🎉 Тест пройден успешно!")
            return True
            
        else:
            print(f"   ❌ WorkItem failed: {status}")
            
            # Показываем детали ошибки
            if 'reportUrl' in result:
                print(f"   📋 Report URL: {result['reportUrl']}")
            
            return False
            
    except Exception as e:
        print(f"\n   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_mode():
    """Тест простого режима (без шаблона) для сравнения"""
    print("\n\n🧪 Тест простого режима (без шаблона)\n")
    
    # Используем тот же файл
    test_input_url = "https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg"
    
    # Создание signed URL для выхода
    sa_json = get_secret("FORGE_SERVICE_KEY")
    sa_credentials = service_account.Credentials.from_service_account_info(
        json.loads(sa_json)
    )
    
    gcs_client = storage.Client(credentials=sa_credentials)
    bucket = gcs_client.bucket("btibot-processed")
    
    test_id = f"test_simple_{int(time.time())}"
    output_path = f"test_results/simple_{test_id}.dwg"
    output_blob = bucket.blob(output_path)
    
    output_url = output_blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="PUT"
    )
    
    print(f"📤 Output path: {output_path}")
    
    try:
        forge_client = ForgeClient()
        
        # Запускаем БЕЗ шаблона
        workitem = forge_client.submit_workitem(
            test_input_url, 
            output_url, 
            use_template=False
        )
        
        workitem_id = workitem['id']
        print(f"✅ WorkItem создан: {workitem_id}")
        
        result = forge_client.wait_for_completion(workitem_id, timeout_minutes=5)
        
        status = result.get('status')
        print(f"\n📊 Статус: {status}")
        
        if status == 'success':
            output_blob.reload()
            result_size = output_blob.size
            print(f"📏 Размер результата: {result_size / 1024:.1f} KB")
            print(f"✅ Тест пройден успешно!")
            return True
        else:
            print(f"❌ WorkItem failed: {status}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🧪 ТЕСТИРОВАНИЕ ТИПОВОГО ШАБЛОНА BTI")
    print("="*60)
    
    # Тест с шаблоном
    result1 = test_bti_template()
    
    # Тест без шаблона (для сравнения)
    result2 = test_simple_mode()
    
    # Итог
    print("\n" + "="*60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*60)
    print(f"С типовым шаблоном BTI: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Простой режим (без шаблона): {'✅ PASS' if result2 else '❌ FAIL'}")
    
    if result1 and result2:
        print("\n🎉 Все тесты пройдены успешно!")
        sys.exit(0)
    else:
        print("\n❌ Некоторые тесты провалились")
        sys.exit(1)

