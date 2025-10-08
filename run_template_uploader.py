#!/usr/bin/env python3
"""
Запуск загрузчика эталонных шаблонов БТИ
"""

import os
import sys
import logging
from upload_template import main as uploader_main
from verify_template import TemplateVerifier

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def check_environment():
    """Проверяет необходимые переменные окружения"""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'GOOGLE_CLOUD_PROJECT'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        return False
    
    return True

def check_template_status():
    """Проверяет статус существующего шаблона"""
    try:
        verifier = TemplateVerifier()
        gcs_check = verifier.check_template_exists()
        
        if gcs_check['exists']:
            logger.info("✅ Шаблон уже существует в GCS")
            logger.info(f"📍 Путь: {gcs_check['path']}")
            logger.info(f"📏 Размер: {gcs_check['size_mb']:.2f} MB")
            logger.info(f"📅 Создан: {gcs_check['created'][:16]}")
            
            metadata = gcs_check['metadata']
            if metadata:
                logger.info("🏷️ Метаданные:")
                for key, value in metadata.items():
                    logger.info(f"   {key}: {value}")
            
            return True
        else:
            logger.info("❌ Шаблон не найден в GCS")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки статуса: {e}")
        return False

def main():
    """Основная функция"""
    print("🤖 Загрузчик эталонных шаблонов БТИ")
    print("=" * 50)
    
    # Проверяем переменные окружения
    if not check_environment():
        print("\n💡 Установите переменные окружения:")
        print("export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("export GOOGLE_CLOUD_PROJECT='talkhint'")
        return 1
    
    # Проверяем существующий шаблон
    print("\n🔍 Проверка существующего шаблона...")
    template_exists = check_template_status()
    
    if template_exists:
        print("\n❓ Шаблон уже существует. Что делать?")
        print("1. Перезапустить бота для загрузки нового файла")
        print("2. Проверить существующий шаблон через Forge API")
        print("3. Выйти")
        
        choice = input("\nВыберите действие (1-3): ").strip()
        
        if choice == "1":
            print("\n🚀 Запуск бота для загрузки нового файла...")
            uploader_main()
        elif choice == "2":
            print("\n🔍 Проверка шаблона через Forge API...")
            from verify_template import main as verify_main
            verify_main()
        elif choice == "3":
            print("👋 Выход...")
            return 0
        else:
            print("❌ Неверный выбор")
            return 1
    else:
        print("\n📁 Шаблон не найден. Запуск бота для загрузки...")
        print("\n💡 Инструкция:")
        print("1. Отправьте файл 'Басманное — новые обмерные планы.dwg' в Telegram")
        print("2. Бот автоматически загрузит его как шаблон 'basmanoe-bti.dwg'")
        print("3. Система проверит доступность через Forge API")
        print("\n🚀 Запуск бота...")
        
        try:
            uploader_main()
        except KeyboardInterrupt:
            print("\n👋 Бот остановлен пользователем")
            return 0
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
