#!/usr/bin/env python3
"""Проверка AppBundle BotBti.BtiPlugin в APS"""

import requests, subprocess, json

def get_secret(n):
    r = subprocess.run(['gcloud', 'secrets', 'versions', 'access', 'latest', f'--secret={n}', '--project=talkhint'], capture_output=True, text=True)
    return r.stdout.strip()

# Credentials
cid = get_secret('FORGE_CLIENT_ID')
cs = get_secret('FORGE_CLIENT_SECRET')

# Token
tr = requests.post('https://developer.api.autodesk.com/authentication/v2/token', 
    data={'client_id': cid, 'client_secret': cs, 'grant_type': 'client_credentials', 'scope': 'code:all'})
token = tr.json()['access_token']

# Проверяем AppBundle
print("🔍 Проверка AppBundle: BotBti.BtiPlugin\n")

ab_url = 'https://developer.api.autodesk.com/da/us-east/v3/appbundles/BotBti.BtiPlugin'
ab_resp = requests.get(ab_url, headers={'Authorization': f'Bearer {token}'})

if ab_resp.status_code == 200:
    ab = ab_resp.json()
    print(f"✅ AppBundle найден!")
    print(f"   ID: {ab.get('id')}")
    print(f"   Version: {ab.get('version')}")
    print(f"   Engine: {ab.get('engine')}")
    print(f"   Description: {ab.get('description')}")
    print(f"\n🎯 Используйте: BotBti.BtiPlugin (version {ab.get('version')})")
    print(f"   Или с $LATEST: BotBti.BtiPlugin+$LATEST")
else:
    print(f"❌ AppBundle не найден: {ab_resp.status_code}")
    print(ab_resp.text)

