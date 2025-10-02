#!/bin/bash

# Setup Cloud Build triggers for BTI DWG → PDF Converter
# Настройка автоматического деплоя через Cloud Build

set -e

echo "🔧 Setting up Cloud Build triggers for BTI DWG → PDF Converter"
echo "=============================================================="

# Переменные
PROJECT_ID="talkhint"  # Замените на ваш проект
REPO_NAME="BTI-DWG-PDF"
REPO_OWNER="Sergalmazfas"
SERVICE_NAME="bti-dwg-pdf"
REGION="europe-west1"

echo "📋 Configuring Cloud Build triggers..."

# 1. Create service account for Cloud Build
echo "🔐 Creating service account..."
gcloud iam service-accounts create bti-dwg-pdf-sa \
  --display-name="BTI DWG PDF Service Account" \
  --description="Service account for BTI DWG → PDF Converter" \
  --project=$PROJECT_ID

# 2. Grant necessary permissions
echo "🔑 Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:bti-dwg-pdf-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:bti-dwg-pdf-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:bti-dwg-pdf-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:bti-dwg-pdf-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 3. Enable APIs
echo "🚀 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable secretmanager.googleapis.com

# 4. Create Cloud Build trigger
echo "⚡ Creating Cloud Build trigger..."
gcloud builds triggers create github \
  --repo-name=$REPO_NAME \
  --repo-owner=$REPO_OWNER \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml" \
  --service-account="bti-dwg-pdf-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --project=$PROJECT_ID

# 5. Create secrets
echo "🔐 Creating secrets..."
echo "Creating BOT_TOKEN secret (you need to set the value manually)..."
gcloud secrets create BOT_TOKEN \
  --replication-policy="automatic" \
  --project=$PROJECT_ID || echo "Secret BOT_TOKEN already exists"

echo ""
echo "✅ Cloud Build setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Set your Telegram bot token:"
echo "   gcloud secrets versions add BOT_TOKEN --data-file=- <<< 'YOUR_BOT_TOKEN'"
echo ""
echo "2. Test the trigger by pushing to main branch"
echo ""
echo "3. Monitor deployments:"
echo "   https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
echo ""
echo "4. View service:"
echo "   https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME?project=$PROJECT_ID"
