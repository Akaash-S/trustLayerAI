# TrustLayer AI Local Startup Script (PowerShell)

Write-Host "🛡️ TrustLayer AI Local Startup Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check if Python is installed
try {
    $pythonVersion = python --version 2>$null
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.9+ first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Docker is running
try {
    docker ps 2>$null | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not running. Please start Docker Desktop first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "🚀 Starting TrustLayer AI services..." -ForegroundColor Yellow

# Start Redis container
Write-Host "📦 Starting Redis container..." -ForegroundColor Blue
try {
    docker run -d --name trustlayer-redis -p 6379:6379 redis:7-alpine 2>$null | Out-Null
    Write-Host "✅ Redis container created and started" -ForegroundColor Green
} catch {
    Write-Host "ℹ️  Redis container already exists, starting it..." -ForegroundColor Blue
    docker start trustlayer-redis 2>$null | Out-Null
    Write-Host "✅ Redis container started" -ForegroundColor Green
}

# Wait for Redis to be ready
Write-Host "⏳ Waiting for Redis to be ready..." -ForegroundColor Blue
Start-Sleep -Seconds 3

# Test Redis connection
try {
    docker exec trustlayer-redis redis-cli ping 2>$null | Out-Null
    Write-Host "✅ Redis is ready on port 6379" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Redis might not be fully ready yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔧 Setup complete! Now run these commands in separate terminals:" -ForegroundColor Green
Write-Host ""
Write-Host "Terminal 1 - Start Proxy:" -ForegroundColor Cyan
Write-Host "  venv\Scripts\activate" -ForegroundColor White
Write-Host "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 2 - Start Dashboard:" -ForegroundColor Cyan  
Write-Host "  venv\Scripts\activate" -ForegroundColor White
Write-Host "  streamlit run dashboard.py" -ForegroundColor White
Write-Host ""
Write-Host "Terminal 3 - Run Tests:" -ForegroundColor Cyan
Write-Host "  venv\Scripts\activate" -ForegroundColor White
Write-Host "  python test_pii.py" -ForegroundColor White
Write-Host ""
Write-Host "📊 Dashboard will be available at: http://localhost:8501" -ForegroundColor Magenta
Write-Host "🔗 Proxy health check: http://localhost:8000/health" -ForegroundColor Magenta
Write-Host ""

Read-Host "Press Enter to continue"