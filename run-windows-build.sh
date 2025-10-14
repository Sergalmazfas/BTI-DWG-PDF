#!/bin/bash
# ========================================
# ЗАПУСК АВТОМАТИЧЕСКОЙ СБОРКИ НА WINDOWS VM
# Выполнять из Google Cloud Shell или Mac
# ========================================

set -e

PROJECT="talkhint"
ZONE="us-east1-c"
INSTANCE="instance-20251013-145106"
BUCKET="btibot-processed"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         🪟 АВТОМАТИЧЕСКАЯ СБОРКА BTI PLUGIN                  ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# 1. Загрузить скрипт в GCS
echo "📤 Step 1: Uploading build script to GCS..."
gsutil cp windows-auto-build.ps1 gs://${BUCKET}/scripts/windows-auto-build.ps1
echo "✅ Script uploaded"
echo ""

# 2. Применить скрипт к VM через metadata
echo "⚙️ Step 2: Applying startup script to VM..."
gcloud compute instances add-metadata "${INSTANCE}" \
  --zone="${ZONE}" \
  --project="${PROJECT}" \
  --metadata=windows-startup-script-url=gs://${BUCKET}/scripts/windows-auto-build.ps1
echo "✅ Startup script configured"
echo ""

# 3. Перезапустить VM
echo "🔄 Step 3: Restarting VM to execute build script..."
gcloud compute instances reset "${INSTANCE}" \
  --zone="${ZONE}" \
  --project="${PROJECT}"
echo "✅ VM restarted"
echo ""

# 4. Ожидание
echo "⏳ Step 4: Waiting for build to complete..."
echo "   This will take approximately 15-20 minutes:"
echo "   - 5 min: VM boot"
echo "   - 10 min: Install tools (Chocolatey, Git, Python, .NET)"
echo "   - 3 min: Clone repo and build"
echo "   - 2 min: Create bundle and upload"
echo ""

for i in {1..20}; do
    echo "   ⏱️  Minute $i/20..."
    sleep 60
    
    # Проверять каждые 5 минут
    if [ $((i % 5)) -eq 0 ]; then
        echo "   🔍 Checking if bundle is ready..."
        if gsutil -q stat gs://${BUCKET}/appbundles/BTI_InsertBasman.bundle.zip 2>/dev/null; then
            echo ""
            echo "╔═══════════════════════════════════════════════════════════════╗"
            echo "║                    ✅ BUILD SUCCESSFUL!                      ║"
            echo "╚═══════════════════════════════════════════════════════════════╝"
            echo ""
            echo "📦 Bundle location: gs://${BUCKET}/appbundles/BTI_InsertBasman.bundle.zip"
            echo ""
            echo "📥 Downloading bundle..."
            gsutil cp gs://${BUCKET}/appbundles/BTI_InsertBasman.bundle.zip ./
            
            echo ""
            echo "🔐 Bundle hash:"
            shasum -a 256 BTI_InsertBasman.bundle.zip
            
            echo ""
            echo "📋 Next steps:"
            echo "   1. Upload to Autodesk APS:"
            echo "      python3 upload_bti_appbundle.py --bundle ./BTI_InsertBasman.bundle.zip --appname BTI.InsertBasman --alias v1"
            echo ""
            echo "   2. Update Activity (after upload)"
            echo ""
            echo "   3. Test with 5 DWG files through Telegram bot"
            echo ""
            exit 0
        fi
    fi
done

echo ""
echo "⚠️  Build is taking longer than expected."
echo "📋 Manual check:"
echo "   1. Check VM logs:"
echo "      gcloud compute instances get-serial-port-output ${INSTANCE} --zone=${ZONE} | tail -n 50"
echo ""
echo "   2. Check if bundle was created:"
echo "      gsutil ls gs://${BUCKET}/appbundles/"
echo ""
echo "   3. Or connect via RDP and check C:\build-log.txt"
echo ""

