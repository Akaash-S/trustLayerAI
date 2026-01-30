#!/bin/bash

# TrustLayer AI - Production Deployment Script for GCP
# This script deploys TrustLayer AI to Google Cloud Platform

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"trustlayer-ai-suite"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="trustlayer-ai-proxy"

echo "🚀 Starting TrustLayer AI Production Deployment"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Redis Endpoint: 10.97.237.131:6379"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📋 Enabling required GCP APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com

# Build and push Docker image
echo "🔨 Building production Docker image..."
docker build -t gcr.io/$PROJECT_ID/trustlayer-ai:latest .

echo "📤 Pushing image to Google Container Registry..."
docker push gcr.io/$PROJECT_ID/trustlayer-ai:latest

# Update the Cloud Run configuration with the correct project ID
sed "s/PROJECT_ID/$PROJECT_ID/g" gcp-deployment/cloud-run-production.yaml > /tmp/cloud-run-production.yaml

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run services replace /tmp/cloud-run-production.yaml --region=$REGION

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: $SERVICE_URL"
echo "🔗 Health Check: $SERVICE_URL/health"
echo "📊 Metrics: $SERVICE_URL/metrics"

# Test the deployment
echo "🧪 Testing deployment..."
if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "⚠️  Health check failed - please check the logs"
    echo "View logs: gcloud run services logs read $SERVICE_NAME --region=$REGION"
fi

echo ""
echo "🎉 TrustLayer AI is now running in production!"
echo "📋 Configuration:"
echo "   • Service URL: $SERVICE_URL"
echo "   • Redis Endpoint: 10.97.237.131:6379"
echo "   • Server: Gunicorn with Uvicorn workers"
echo "   • Auto-scaling: 1-10 instances"

# Clean up temporary file
rm -f /tmp/cloud-run-production.yaml