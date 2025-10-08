#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  ⏳ АВТОПРОВЕРКА NICKNAME (каждые 10 сек)                       ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Установите nickname 'Forgecloudrun' в Web UI:"
echo "   https://aps.autodesk.com"
echo ""
echo "Скрипт автоматически запустит setup_forgecloudrun_simple.py"
echo "как только nickname будет установлен"
echo ""
echo "Для остановки: Ctrl+C"
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo ""

while true; do
    TIMESTAMP=$(date +"%H:%M:%S")
    echo "[$TIMESTAMP] Проверка nickname..."
    
    # Проверить nickname через Python
    RESULT=$(python3 << 'EOF'
import subprocess, requests, sys

def get_secret(n):
    return subprocess.run(f"gcloud secrets versions access latest --secret={n} --project=talkhint".split(), capture_output=True, text=True).stdout.strip()

client_id = get_secret("FORGE_CLIENT_ID")
client_secret = get_secret("FORGE_CLIENT_SECRET")

r = requests.post("https://developer.api.autodesk.com/authentication/v2/token",
    data={"client_id":client_id,"client_secret":client_secret,"grant_type":"client_credentials","scope":"code:all"})

if r.status_code == 200:
    token = r.json()["access_token"]
    me = requests.get("https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me",
        headers={"Authorization": f"Bearer {token}"})
    
    if me.status_code == 200:
        try:
            app_info = me.json()
            nickname = app_info.get("nickname") if isinstance(app_info, dict) else None
            print(nickname or "NOT_SET")
        except:
            print("NOT_SET")
    else:
        print("ERROR")
else:
    print("ERROR")
EOF
)

    if [ "$RESULT" = "Forgecloudrun" ]; then
        echo ""
        echo "════════════════════════════════════════════════════════════════════"
        echo "🎉 NICKNAME УСТАНОВЛЕН: Forgecloudrun"
        echo "════════════════════════════════════════════════════════════════════"
        echo ""
        echo "🚀 Запуск автоматизации..."
        echo ""
        python3 setup_forgecloudrun_simple.py
        exit $?
    else
        echo "   Nickname: $RESULT (ожидается: Forgecloudrun)"
        echo "   ⏳ Ожидание 10 сек..."
        sleep 10
    fi
done

