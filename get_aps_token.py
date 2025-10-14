#!/usr/bin/env python3
"""
Получение 2-legged OAuth токена от Autodesk APS
Для использования в Update-Activity.ps1
"""
import os
import sys
import requests

def get_token():
    """Получить токен используя env переменные"""
    client_id = os.getenv("APS_CLIENT_ID")
    client_secret = os.getenv("APS_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ Ошибка: Нужно установить APS_CLIENT_ID и APS_CLIENT_SECRET", file=sys.stderr)
        print("\nНа Windows:", file=sys.stderr)
        print('  setx APS_CLIENT_ID "your_id"', file=sys.stderr)
        print('  setx APS_CLIENT_SECRET "your_secret"', file=sys.stderr)
        print('  # Перезапустить PowerShell\n', file=sys.stderr)
        sys.exit(1)
    
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        token = response.json()["access_token"]
        expires_in = response.json().get("expires_in", 3600)
        
        print(f"✅ Токен получен (действует {expires_in//60} минут)")
        print(f"\nACCESS_TOKEN={token}")
        print(f"\n💡 Для использования в PowerShell:")
        print(f'$ACCESS_TOKEN = "{token}"')
        
        return token
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка получения токена: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    get_token()

