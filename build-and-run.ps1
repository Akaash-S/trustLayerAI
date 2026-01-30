# TrustLayer AI - Build and Run Script for Compute Engine VM (PowerShell)
# This script builds the Docker image and runs the containers

param(
    [string]$ProjectId = "your-gcp-project-id"
)

if ($ProjectId -eq "your-gcp-project-id") {
    Write-Host "❌ Please provide your GCP project ID as an argument" -ForegroundColor Red
    Write-Host "Usage: .\build-and-run.ps1 -ProjectId 'your-project-id'" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Building and running TrustLayer AI containers" -ForegroundColor Green
Write-Host "Project: $ProjectId" -ForegroundColor Cyan
Write-Host "Redis Endpoint: 10.97.237.131:6379" -ForegroundColor Cyan

# Stop existing containers if running
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
try {
    docker-compose down 2>$null
} catch {
    # Ignore errors if no containers are running
}

# Build the Docker image
Write-Host "🔨 Building Docker image..." -ForegroundColor Yellow
docker build -t trustlayer-ai:latest .

# Tag for GCR (optional, for future pushes)
docker tag trustlayer-ai:latest "gcr.io/$ProjectId/trustlayer-ai:latest"

# Update docker-compose with project ID
Write-Host "📝 Updating docker-compose configuration..." -ForegroundColor Yellow
$composeContent = Get-Content "gcp-deployment/docker-compose.production.yml" -Raw
$composeContent = $composeContent -replace "PROJECT_ID", $ProjectId
$composeContent | Out-File -FilePath "docker-compose.yml" -Encoding UTF8

# Start the containers
Write-Host "🚀 Starting containers..." -ForegroundColor Yellow
docker-compose up -d

# Wait for containers to start
Write-Host "⏳ Waiting for containers to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check container status
Write-Host "📊 Container status:" -ForegroundColor Yellow
docker-compose ps

# Test health endpoints
Write-Host "🧪 Testing health endpoints..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Proxy health check passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Proxy health check failed" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Proxy health check failed" -ForegroundColor Red
    Write-Host "📋 Proxy logs:" -ForegroundColor Yellow
    docker-compose logs proxy --tail=10
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8501" -Method Get -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Dashboard is accessible" -ForegroundColor Green
    } else {
        Write-Host "❌ Dashboard is not accessible" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Dashboard is not accessible" -ForegroundColor Red
    Write-Host "📋 Dashboard logs:" -ForegroundColor Yellow
    docker-compose logs dashboard --tail=10
}

Write-Host ""
Write-Host "🎉 TrustLayer AI is now running!" -ForegroundColor Green
Write-Host "📋 Services:" -ForegroundColor Yellow
Write-Host "   • Proxy: http://localhost:8000" -ForegroundColor White
Write-Host "   • Health: http://localhost:8000/health" -ForegroundColor White
Write-Host "   • Metrics: http://localhost:8000/metrics" -ForegroundColor White
Write-Host "   • Dashboard: http://localhost:8501" -ForegroundColor White
Write-Host "   • Redis: 10.97.237.131:6379" -ForegroundColor White

Write-Host ""
Write-Host "📊 Management commands:" -ForegroundColor Yellow
Write-Host "   • View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   • Restart: docker-compose restart" -ForegroundColor White
Write-Host "   • Stop: docker-compose down" -ForegroundColor White
Write-Host "   • Update: .\build-and-run.ps1 -ProjectId '$ProjectId'" -ForegroundColor White