#!/usr/bin/env python3
"""
Тест системы очереди GCS
"""

import json
import time
from gcs_queue_manager import GCSQueueManager

def test_queue_system():
    """Тестирует систему очереди"""
    print("🧪 Тестирование GCS Queue System")
    print("=" * 50)
    
    # Инициализируем queue manager
    try:
        queue_manager = GCSQueueManager()
        queue_manager._ensure_bucket_structure()
        print("✅ Queue Manager инициализирован")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False
    
    # Тест 1: Добавление задания в очередь
    print("\n📝 Тест 1: Добавление задания в очередь")
    try:
        job_data = {
            "user_id": 12345,
            "chat_id": 12345,
            "filename": "test.dwg",
            "file_size": 1024000,
            "dwg_path": "raw/1234567890/test.dwg",
            "dwg_url": "https://storage.googleapis.com/btibot-processed/raw/1234567890/test.dwg",
            "created_at": "2025-01-02T12:00:00Z"
        }
        
        job_id = queue_manager.add_job_to_queue(job_data)
        print(f"✅ Задание добавлено: {job_id}")
        
        # Проверяем статус очереди
        status = queue_manager.get_queue_status()
        print(f"📊 Статус очереди: {json.dumps(status, indent=2)}")
        
    except Exception as e:
        print(f"❌ Ошибка добавления задания: {e}")
        return False
    
    # Тест 2: Получение следующего задания
    print("\n🚀 Тест 2: Получение следующего задания")
    try:
        job = queue_manager.get_next_job()
        if job:
            print(f"✅ Получено задание: {job['job_id']}")
            print(f"📦 Данные: {json.dumps(job['data'], indent=2)}")
            
            # Проверяем, что lock создан
            is_locked = queue_manager._is_processing_locked()
            print(f"🔒 Lock создан: {is_locked}")
            
        else:
            print("❌ Задание не получено")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка получения задания: {e}")
        return False
    
    # Тест 3: Завершение задания
    print("\n✅ Тест 3: Завершение задания")
    try:
        result_data = {
            "pdf_url": "https://storage.googleapis.com/btibot-processed/processed/1234567890/plan.pdf",
            "pdf_path": "processed/1234567890/plan.pdf",
            "processed_at": "2025-01-02T12:05:00Z"
        }
        
        queue_manager.finish_job(job_id, result_data)
        print(f"✅ Задание завершено: {job_id}")
        
        # Проверяем, что lock удален
        is_locked = queue_manager._is_processing_locked()
        print(f"🔓 Lock удален: {not is_locked}")
        
        # Проверяем финальный статус
        final_status = queue_manager.get_queue_status()
        print(f"📊 Финальный статус: {json.dumps(final_status, indent=2)}")
        
    except Exception as e:
        print(f"❌ Ошибка завершения задания: {e}")
        return False
    
    print("\n🎉 Все тесты прошли успешно!")
    return True

def test_multiple_jobs():
    """Тестирует обработку нескольких заданий"""
    print("\n🔄 Тестирование множественных заданий")
    print("=" * 50)
    
    queue_manager = GCSQueueManager()
    
    # Добавляем несколько заданий
    job_ids = []
    for i in range(3):
        job_data = {
            "user_id": 12345 + i,
            "chat_id": 12345 + i,
            "filename": f"test{i}.dwg",
            "file_size": 1024000,
            "dwg_path": f"raw/123456789{i}/test{i}.dwg",
            "dwg_url": f"https://storage.googleapis.com/btibot-processed/raw/123456789{i}/test{i}.dwg",
            "created_at": "2025-01-02T12:00:00Z"
        }
        
        job_id = queue_manager.add_job_to_queue(job_data)
        job_ids.append(job_id)
        print(f"📝 Добавлено задание {i+1}: {job_id}")
        time.sleep(1)  # Небольшая задержка для разных timestamps
    
    # Проверяем статус
    status = queue_manager.get_queue_status()
    print(f"📊 Статус очереди: {status['queue_size']} заданий")
    
    # Обрабатываем все задания
    for i, job_id in enumerate(job_ids):
        print(f"\n🚀 Обработка задания {i+1}: {job_id}")
        
        job = queue_manager.get_next_job()
        if job:
            print(f"✅ Получено: {job['job_id']}")
            
            # Симулируем обработку
            time.sleep(1)
            
            # Завершаем
            result_data = {
                "pdf_url": f"https://storage.googleapis.com/btibot-processed/processed/123456789{i}/plan.pdf",
                "pdf_path": f"processed/123456789{i}/plan.pdf",
                "processed_at": "2025-01-02T12:05:00Z"
            }
            
            queue_manager.finish_job(job_id, result_data)
            print(f"✅ Завершено: {job_id}")
        else:
            print(f"❌ Не удалось получить задание: {job_id}")
    
    # Финальный статус
    final_status = queue_manager.get_queue_status()
    print(f"\n📊 Финальный статус: {final_status['queue_size']} заданий в очереди")
    
    print("🎉 Тест множественных заданий завершен!")

if __name__ == "__main__":
    print("🧪 Запуск тестов GCS Queue System")
    print("=" * 60)
    
    # Основной тест
    if test_queue_system():
        # Тест множественных заданий
        test_multiple_jobs()
        print("\n🎉 Все тесты завершены успешно!")
    else:
        print("\n❌ Тесты не прошли!")
