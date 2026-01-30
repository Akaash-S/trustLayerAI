@echo off
echo 🛡️ TrustLayer AI Local Startup Script
echo =====================================

echo.
echo 📋 Checking prerequisites...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.9+ first.
    pause
    exit /b 1
)
echo ✅ Python found

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not running. Please start Docker Desktop first.
    pause
    exit /b 1
)
echo ✅ Docker is running

echo.
echo 🚀 Starting TrustLayer AI services...

REM Start Redis container
echo 📦 Starting Redis container...
docker run -d --name trustlayer-redis -p 6379:6379 redis:7-alpine >nul 2>&1
if errorlevel 1 (
    echo ℹ️  Redis container already exists, starting it...
    docker start trustlayer-redis >nul 2>&1
)
echo ✅ Redis started on port 6379

REM Wait a moment for Redis to be ready
timeout /t 3 /nobreak >nul

echo.
echo 🔧 Setup complete! Now run these commands in separate terminals:
echo.
echo Terminal 1 - Start Proxy:
echo   venv\Scripts\activate
echo   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
echo.
echo Terminal 2 - Start Dashboard:
echo   venv\Scripts\activate  
echo   streamlit run dashboard.py
echo.
echo Terminal 3 - Run Tests:
echo   venv\Scripts\activate
echo   python test_pii.py
echo.
echo 📊 Dashboard will be available at: http://localhost:8501
echo 🔗 Proxy health check: http://localhost:8000/health
echo.
pause