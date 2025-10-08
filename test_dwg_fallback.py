#!/usr/bin/env python3
"""
Тест fallback DWG→DWG без обработки
"""
import os
import tempfile
import shutil
from google.cloud import storage

def test_dwg_copy_fallback(input_gcs_path):
    """
    Тестирует копирование DWG без обработки (fallback режим)
    
    Args:
        input_gcs_path: gs://btibot-processed/raw/.../file.dwg
    """
    print(f"🧪 Тест fallback DWG→DWG")
    print(f"   Input: {input_gcs_path}")
    
    # Парсим GCS путь
    if not input_gcs_path.startswith("gs://btibot-processed/"):
        print("❌ Путь должен начинаться с gs://btibot-processed/")
        return
    
    input_blob_path = input_gcs_path.replace("gs://btibot-processed/", "")
    
    # Создаем GCS client
    gcs_client = storage.Client()
    bucket = gcs_client.bucket("btibot-processed")
    
    # Скачиваем исходный DWG
    print(f"📥 Скачиваем {input_blob_path}...")
    input_blob = bucket.blob(input_blob_path)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dwg') as temp_dwg:
        input_blob.download_to_filename(temp_dwg.name)
        temp_dwg_path = temp_dwg.name
    
    print(f"✅ Скачано: {temp_dwg_path}")
    
    # Проверяем размер
    input_size = os.path.getsize(temp_dwg_path)
    print(f"📊 Размер: {input_size} bytes")
    
    # Копируем в output (тестовый путь)
    output_blob_path = f"test_fallback/test_{os.path.basename(input_blob_path)}"
    output_blob = bucket.blob(output_blob_path)
    
    print(f"📤 Загружаем в {output_blob_path}...")
    output_blob.upload_from_filename(temp_dwg_path)
    
    # Удаляем временный файл
    os.unlink(temp_dwg_path)
    
    # Формируем URL
    output_url = f"https://storage.googleapis.com/btibot-processed/{output_blob_path}"
    
    print(f"\n✅ УСПЕХ!")
    print(f"   Output URL: {output_url}")
    print(f"   Размер: {input_size} bytes")
    print(f"\n💡 DWG скопирован БЕЗ обработки (чистый fallback)")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 test_dwg_fallback.py gs://btibot-processed/raw/.../file.dwg")
        sys.exit(1)
    
    test_dwg_copy_fallback(sys.argv[1])

