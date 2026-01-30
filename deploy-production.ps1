# TrustLayer AI - Production Deployment Script for GCP (PowerShell)
# This script deploys TrustLayer AI to Google Cloud Platform

param(
    [string]$ProjectId = $env:PROJECT_ID,
    [string]$Region = "us-central1",
    [string]$ServiceName = "trustlayer-ai-proxy"
)

# Check if required parameters are provided
if (-not $ProjectId) {
    Write-Host "❌ PROJECT_ID is required. Set it as environment variable or pass as parameter." -ForegroundColor Red
    Write-Host "Usage: .\deploy-production.ps1 -ProjectId 'your-gcp-project-id'" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Starting TrustLayer AI Production Deployment" -ForegroundColor Green
Write-Host "Project: $ProjectId" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Redis Endpoint: 10.97.237.131:6379" -ForegroundColor Cyan

# Check if gcloud is installed
try {
    $null = Get-Command gcloud -ErrorAction Stop
} catch {
    Write-Host "❌ gcloud CLI is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Set the project
Write-Host "🔧 Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Enable required APIs
Write-Host "📋 Enabling required GCP APIs..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com run.googleapis.com

# Build and push Docker image
Write-Host "🔨 Building production Docker image..." -ForegroundColor Yellow
docker build -t "gcr.io/$ProjectId/trustlayer-ai:latest" .

Write-Host "📤 Pushing image to Google Container Registry..." -ForegroundColor Yellow
docker push "gcr.io/$ProjectId/trustlayer-ai:latest"

# Update the Cloud Run configuration with the correct project ID
Write-Host "📝 Updating Cloud Run configuration..." -ForegroundColor Yellow
$configContent = Get-Content "gcp-deployment/cloud-run-production.yaml" -Raw
$configContent = $configContent -replace "PROJECT_ID", $ProjectId
$configContent | Out-File -FilePath "$env:TEMP/cloud-run-production.yaml" -Encoding UTF8

# Deploy to Cloud Run
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run services replace "$env:TEMP/cloud-run-production.yaml" --region=$Region

# Get the service URL
Write-Host "🔗 Getting service URL..." -ForegroundColor Yellow
$serviceUrl = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)"

Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
Write-Host "🌐 Service URL: $serviceUrl" -ForegroundColor Cyan
Write-Host "🔗 Health Check: $serviceUrl/health" -ForegroundColor Cyan
Write-Host "📊 Metrics: $serviceUrl/metrics" -ForegroundColor Cyan

# Test the deployment
Write-Host "🧪 Testing deployment..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$serviceUrl/health" -Method Get -TimeoutSec 30
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Health check passed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Health check returned status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Health check failed - please check the logs" -ForegroundColor Yellow
    Write-Host "View logs: gcloud run services logs read $ServiceName --region=$Region" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🎉 TrustLayer AI is now running in production!" -ForegroundColor Green
Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "   • Service URL: $serviceUrl" -ForegroundColor White
Write-Host "   • Redis Endpoint: 10.97.237.131:6379" -ForegroundColor White
Write-Host "   • Server: Gunicorn with Uvicorn workers" -ForegroundColor White
Write-Host "   • Auto-scaling: 1-10 instances" -ForegroundColor White

# Clean up temporary file
Remove-Item "$env:TEMP/cloud-run-production.yaml" -ErrorAction SilentlyContinue