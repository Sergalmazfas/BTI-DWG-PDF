#!/usr/bin/env python3
"""
Список всех AppBundles в Autodesk APS
Проверка наличия BTEInsertTemplate AppBundle
"""

import os
import json
import requests

# APS credentials
APS_CLIENT_ID = os.getenv('APS_CLIENT_ID', 'm6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4')
APS_CLIENT_SECRET = os.getenv('APS_CLIENT_SECRET', 'tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW')
APS_BASE_URL = "https://developer.api.autodesk.com"

def get_token():
    url = f"{APS_BASE_URL}/authentication/v2/token"
    data = {
        "client_id": APS_CLIENT_ID,
        "client_secret": APS_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return response.json()['access_token']

def list_appbundles(token):
    """Список всех AppBundles"""
    url = f"{APS_BASE_URL}/da/us-east/v3/appbundles"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def main():
    print("=" * 80)
    print("📦 Список AppBundles в Autodesk APS")
    print("=" * 80)
    print()
    
    token = get_token()
    print("✅ Токен получен\n")
    
    print("📋 Получение списка AppBundles...\n")
    
    appbundles = list_appbundles(token)
    
    if appbundles:
        bundle_list = appbundles.get('data', [])
        
        if bundle_list:
            print(f"✅ Найдено AppBundles: {len(bundle_list)}\n")
            
            bte_bundles = []
            other_bundles = []
            
            for bundle in bundle_list:
                if 'BTEInsert' in bundle or 'BTE' in bundle or 'BTI' in bundle or 'SimpleDWG' in bundle:
                    bte_bundles.append(bundle)
                else:
                    other_bundles.append(bundle)
            
            if bte_bundles:
                print("🎯 BTE/BTI AppBundles:")
                for bundle in bte_bundles:
                    print(f"   • {bundle}")
                print()
            
            if other_bundles:
                print("📦 Другие AppBundles:")
                for bundle in other_bundles[:10]:
                    print(f"   • {bundle}")
                if len(other_bundles) > 10:
                    print(f"   ... и ещё {len(other_bundles) - 10}")
            
            # Проверка наличия BTEInsertTemplate
            print("\n" + "=" * 80)
            print("🔍 Проверка BTEInsertTemplate AppBundle")
            print("=" * 80)
            
            if any('BTEInsert' in b for b in bundle_list):
                print("✅ BTEInsertTemplate AppBundle найден!")
                print("   Activity может использовать этот AppBundle")
            else:
                print("⚠️  BTEInsertTemplate AppBundle НЕ найден")
                print("\n📝 Для создания AppBundle:")
                print("   1. Подготовить bundle.zip с .NET плагином")
                print("   2. POST /appbundles (создать AppBundle)")
                print("   3. Загрузить ZIP через uploadParameters")
                print("   4. Создать alias для AppBundle")
                print("   5. Использовать в Activity")
        else:
            print("⚠️  AppBundles не найдены")
    else:
        print("❌ Не удалось получить список AppBundles")

if __name__ == "__main__":
    main()

