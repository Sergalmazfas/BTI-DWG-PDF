#!/usr/bin/env python3
"""
Тестирование всех API эндпоинтов после исправления
"""

import requests
import json
from datetime import datetime

def test_endpoint(url, method='GET', data=None, description=''):
    """Тестирует один эндпоинт"""
    print(f"\n🧪 {description}")
    print(f"   {method} {url}")
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            if data:
                response = requests.post(url, json=data, timeout=10)
            else:
                response = requests.post(url, timeout=10)
        
        print(f"   📊 Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                json_data = response.json()
                print(f"   📄 Response: {json.dumps(json_data, indent=2, ensure_ascii=False)[:200]}...")
            except:
                print(f"   📄 Response: {response.text[:100]}...")
        else:
            print(f"   📄 Response: {response.text[:100]}...")
        
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🚀 Тестирование всех API эндпоинтов")
    print("=" * 60)
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Базовый URL (локальный для тестирования)
    base_url = "http://localhost:8080"
    
    results = {}
    
    # Список эндпоинтов для тестирования
    endpoints = [
        {
            'url': f"{base_url}/health",
            'method': 'GET',
            'description': 'Health Check'
        },
        {
            'url': f"{base_url}/status", 
            'method': 'GET',
            'description': 'Service Status'
        },
        {
            'url': f"{base_url}/queue-status",
            'method': 'GET', 
            'description': 'Queue Status'
        },
        {
            'url': f"{base_url}/process-dwg",
            'method': 'POST',
            'data': {
                "file_url": "gs://btibot-processed/test/sample.dwg",
                "mode": "bti",
                "chat_id": "test",
                "job_id": "test-123"
            },
            'description': 'Process DWG (Test Payload)'
        },
        {
            'url': f"{base_url}/process-queue",
            'method': 'POST',
            'description': 'Process Queue'
        }
    ]
    
    # Тестируем каждый эндпоинт
    for endpoint in endpoints:
        success = test_endpoint(
            endpoint['url'],
            endpoint['method'],
            endpoint.get('data'),
            endpoint['description']
        )
        results[endpoint['description']] = success
    
    # Итоговый отчет
    print(f"\n📊 Итоговые результаты:")
    print("-" * 40)
    
    success_count = 0
    total_count = len(results)
    
    for desc, success in results.items():
        status = "✅ OK" if success else "❌ FAIL"
        print(f"   {desc}: {status}")
        if success:
            success_count += 1
    
    print(f"\n🎯 Итог: {success_count}/{total_count} эндпоинтов работают")
    
    if success_count == total_count:
        print("🎉 Все эндпоинты работают корректно!")
        print("\n📋 Следующие шаги:")
        print("   1. Исправить доступ к Design Automation API")
        print("   2. Протестировать с реальным DWG файлом")
        print("   3. Проверить Telegram бота")
    else:
        print("⚠️ Некоторые эндпоинты не работают")
        print("   Проверьте логи приложения и конфигурацию")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)