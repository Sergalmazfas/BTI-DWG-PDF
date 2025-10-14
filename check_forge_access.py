#!/usr/bin/env python3
"""
Скрипт для проверки доступа к Forge Design Automation API
Помогает диагностировать проблемы с Client ID и API доступами
"""

import os
import json
import sys
from forge_client import ForgeClient

def main():
    print("🔍 Диагностика доступа к Forge Design Automation API")
    print("=" * 60)
    
    # Создаем клиент
    client = ForgeClient()
    
    # Получаем информацию о клиенте
    client_info = client.get_client_info()
    print("\n📋 Информация о клиенте:")
    for key, value in client_info.items():
        print(f"   {key}: {value}")
    
    # Проверяем получение токена
    print("\n🔑 Проверка получения токена...")
    token = client.get_token()
    
    if token:
        print("✅ Токен получен успешно")
        print(f"   Длина токена: {len(token)} символов")
        print(f"   Первые 10 символов: {token[:10]}...")
        
        # Пробуем создать тестовый WorkItem (без реальных URL)
        print("\n🚀 Проверка создания WorkItem (тест доступа к API)...")
        
        # Используем фиктивные URL для проверки доступа
        test_input = "https://example.com/test.dwg"
        test_output = "https://example.com/test.pdf"
        
        try:
            result = client.submit_workitem(test_input, test_output)
            
            if "error" in result:
                print(f"❌ Ошибка создания WorkItem: {result['error']}")
                
                # Проверяем специфичные ошибки
                error_text = str(result.get('error', '')).lower()
                
                if "does not have access to the api product" in error_text:
                    print("\n🚨 ПРОБЛЕМА: Client ID не имеет доступа к Design Automation API")
                    print("\n💡 РЕШЕНИЯ:")
                    print("1. Дать доступ к Design Automation API для текущего Client ID:")
                    print("   - Зайти на https://aps.autodesk.com/myapps/")
                    print(f"   - Найти приложение с Client ID: {client_info['client_id_masked']}")
                    print("   - Добавить 'Design Automation API' в список APIs")
                    print("   - Сохранить изменения")
                    print("\n2. Использовать другой Client ID:")
                    print("   - Обновить секрет FORGE_CLIENT_ID в Google Secret Manager")
                    print("   - Использовать Client ID, который уже имеет доступ (например, m6CK3...)")
                    print("   - Обновить также FORGE_CLIENT_SECRET если нужно")
                    
                elif "invalid" in error_text or "not found" in error_text:
                    print("\n🚨 ПРОБЛЕМА: Недействительный Client ID или секрет")
                    print("\n💡 РЕШЕНИЯ:")
                    print("- Проверить правильность Client ID и Client Secret")
                    print("- Убедиться, что приложение активно в APS портале")
                    
                else:
                    print(f"\n🚨 НЕИЗВЕСТНАЯ ОШИБКА: {result['error']}")
                    
                return False
            else:
                print("✅ WorkItem создан успешно (тестовый)")
                print(f"   WorkItem ID: {result.get('id', 'N/A')}")
                print("\n🎉 Client ID имеет доступ к Design Automation API!")
                return True
                
        except Exception as e:
            print(f"❌ Исключение при проверке: {e}")
            return False
            
    else:
        print("❌ Не удалось получить токен")
        print("\n💡 Возможные причины:")
        print("- Неправильный Client ID или Client Secret")
        print("- Проблемы с сетевым подключением")
        print("- Приложение заблокировано или удалено")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)