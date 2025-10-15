#!/usr/bin/env python3
"""
Получение APS токена для использования в других скриптах
"""

import os
import requests
import sys

# APS credentials
APS_CLIENT_ID = os.getenv('APS_CLIENT_ID', 'm6CK3EHpibW1XrHpPFiOfs83BCfp0zHDGtaAc6vcLatU6Pp4')
APS_CLIENT_SECRET = os.getenv('APS_CLIENT_SECRET', 'tm9AyCWiSGmBytA1VVhXMrZu4hKsGFUudPDae9bdboHWstG08ySRITBYNGt1nRjW')
APS_BASE_URL = "https://developer.api.autodesk.com"

def get_access_token():
    """Получить токен доступа"""
    url = f"{APS_BASE_URL}/authentication/v2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": APS_CLIENT_ID,
        "client_secret": APS_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all data:write data:read bucket:create bucket:read"
    }
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code != 200:
        print(f"❌ Ошибка получения токена: {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        sys.exit(1)
    
    return response.json()['access_token']

if __name__ == "__main__":
    # Вывод только токена для использования в export
    token = get_access_token()
    print(token)

