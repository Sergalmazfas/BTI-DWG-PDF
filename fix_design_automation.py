#!/usr/bin/env python3
"""
Универсальный скрипт для исправления проблем с Design Automation API
"""

import os
import sys
import json
import webbrowser
from forge_client import ForgeClient

def print_header():
    print("🔧 Design Automation API - Диагностика и исправление")
    print("=" * 60)

def diagnose_issue():
    """Диагностика текущей проблемы"""
    print("\n🔍 Диагностика проблемы...")
    
    client = ForgeClient()
    client_info = client.get_client_info()
    
    print(f"\n📋 Текущая конфигурация:")
    print(f"   Client ID: {client_info['client_id_masked']}")
    print(f"   Имеется токен: {client_info['has_token']}")
    
    # Попытка получить токен
    print(f"\n🔑 Тест получения токена...")
    token = client.get_token()
    
    if token:
        print("   ✅ Токен получен успешно")
        
        # Тест создания WorkItem
        print("\n🚀 Тест Design Automation API...")
        test_result = client.submit_workitem(
            "https://example.com/test.dwg",
            "https://example.com/test.pdf"
        )
        
        if "error" not in test_result:
            print("   ✅ Design Automation API доступен!")
            return "success"
        else:
            print(f"   ❌ Ошибка API: {test_result['error']}")
            return "api_error"
    else:
        print("   ❌ Не удалось получить токен")
        
        if not client_info['client_id'] or client_info['client_id'] == 'Not set':
            print("   🔍 Client ID не настроен")
            return "no_credentials"
        else:
            print("   🔍 Client ID настроен, но токен не получается")
            return "invalid_credentials"

def show_solution_options(issue_type):
    """Показать варианты решения"""
    print(f"\n💡 Варианты решения:")
    
    if issue_type == "success":
        print("   🎉 Все работает корректно!")
        return
    
    elif issue_type == "no_credentials":
        print("   1. Настроить переменные окружения:")
        print("      export FORGE_CLIENT_ID='ваш_client_id'")
        print("      export FORGE_CLIENT_SECRET='ваш_client_secret'")
        print("")
        print("   2. Использовать скрипт обновления:")
        print("      python3 update_forge_credentials.py")
    
    elif issue_type in ["invalid_credentials", "api_error"]:
        client = ForgeClient()
        client_info = client.get_client_info()
        
        print("   🎯 Рекомендуемое решение: Дать доступ к Design Automation API")
        print("")
        print("   📋 Пошаговая инструкция:")
        print("   1. Открыть APS Portal (откроется в браузере)")
        print("   2. Найти приложение с Client ID:", client_info['client_id_masked'])
        print("   3. В разделе 'API Access' добавить 'Design Automation API'")
        print("   4. Сохранить изменения")
        print("   5. Вернуться сюда и нажать Enter для проверки")
        print("")
        print("   🔄 Альтернативно: Использовать другой Client ID")
        print("      python3 update_forge_credentials.py")

def open_aps_portal():
    """Открыть APS Portal в браузере"""
    try:
        webbrowser.open("https://aps.autodesk.com/myapps/")
        print("   🌐 APS Portal открыт в браузере")
        return True
    except Exception as e:
        print(f"   ⚠️ Не удалось открыть браузер: {e}")
        print("   🔗 Откройте вручную: https://aps.autodesk.com/myapps/")
        return False

def wait_for_fix():
    """Ожидание исправления от пользователя"""
    print("\n⏳ После добавления Design Automation API доступа нажмите Enter для проверки...")
    input()
    
    # Повторная диагностика
    print("\n🔄 Повторная проверка...")
    issue_type = diagnose_issue()
    
    if issue_type == "success":
        print("\n🎉 Отлично! Design Automation API теперь работает!")
        return True
    else:
        print("\n❌ Проблема все еще присутствует.")
        print("   💡 Попробуйте:")
        print("   1. Подождать 1-2 минуты (изменения могут применяться с задержкой)")
        print("   2. Проверить правильность Client ID в APS Portal")
        print("   3. Использовать другой Client ID с помощью update_forge_credentials.py")
        return False

def interactive_menu():
    """Интерактивное меню действий"""
    while True:
        print(f"\n🎯 Выберите действие:")
        print("   1. Открыть APS Portal для добавления API доступа")
        print("   2. Использовать другой Client ID")
        print("   3. Повторить диагностику")
        print("   4. Выйти")
        
        choice = input("\nВаш выбор (1-4): ").strip()
        
        if choice == "1":
            open_aps_portal()
            if wait_for_fix():
                break
        
        elif choice == "2":
            print("\n🔄 Запуск скрипта обновления credentials...")
            os.system("python3 update_forge_credentials.py")
            print("\n🔄 Повторная диагностика после обновления...")
            issue_type = diagnose_issue()
            if issue_type == "success":
                break
        
        elif choice == "3":
            issue_type = diagnose_issue()
            if issue_type == "success":
                break
            show_solution_options(issue_type)
        
        elif choice == "4":
            print("👋 До свидания!")
            break
        
        else:
            print("❌ Неверный выбор. Попробуйте еще раз.")

def main():
    print_header()
    
    # Начальная диагностика
    issue_type = diagnose_issue()
    
    if issue_type == "success":
        print("\n🎉 Все отлично! Design Automation API работает корректно.")
        return
    
    # Показываем варианты решения
    show_solution_options(issue_type)
    
    # Интерактивное меню
    interactive_menu()
    
    print("\n✅ Исправление завершено!")
    print("\n📋 Рекомендации:")
    print("   - Протестируйте бота с реальным DWG файлом")
    print("   - Проверьте логи на отсутствие ошибок")
    print("   - Настройте мониторинг API вызовов")

if __name__ == "__main__":
    main()