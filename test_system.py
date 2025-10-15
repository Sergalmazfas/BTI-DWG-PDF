#!/usr/bin/env python3
"""
Тест системы обработки DWG файлов
"""

import requests
import json
import time

def test_services():
    """Тестирует все сервисы системы"""
    
    services = {
        "telegram-bot-commands": "https://telegram-bot-commands-637190449180.europe-west1.run.app",
        "dwg-processor": "https://dwg-processor-637190449180.europe-west1.run.app", 
        "dwg-processor-metadata": "https://dwg-processor-metadata-637190449180.europe-west1.run.app"
    }
    
    print("🧪 Тестирование сервисов системы...")
    print("=" * 50)
    
    for name, url in services.items():
        print(f"\n🔍 Тестируем {name}...")
        
        # Health check
        try:
            response = requests.get(f"{url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health: {data.get('status', 'OK')}")
            else:
                print(f"❌ Health: {response.status_code}")
        except Exception as e:
            print(f"❌ Health: {e}")
        
        # Status check (если доступен)
        try:
            response = requests.get(f"{url}/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {data.get('service', 'Unknown')}")
            else:
                print(f"⚠️ Status: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Status: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Тестирование завершено!")

def test_queue():
    """Тестирует очередь обработки"""
    
    print("\n📋 Тестирование очереди...")
    
    try:
        url = "https://telegram-bot-commands-637190449180.europe-west1.run.app/queue-status"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Очередь: {data.get('queue_size', 0)} файлов")
            print(f"✅ Обработка: {'Активна' if data.get('is_processing') else 'Неактивна'}")
        else:
            print(f"❌ Очередь: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Очередь: {e}")

if __name__ == "__main__":
    test_services()
    test_queue()
