@echo off
echo 🛡️ TrustLayer AI Quick Setup
echo ============================

echo.
echo 📦 Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment created

echo.
echo 📥 Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat

echo 📦 Installing Python packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install requirements
    pause
    exit /b 1
)

echo 🧠 Downloading spaCy model (this may take a few minutes)...
python -m spacy download en_core_web_lg
if errorlevel 1 (
    echo ❌ Failed to download spaCy model
    pause
    exit /b 1
)

echo.
echo ✅ Setup completed successfully!
echo.
echo 🚀 Next steps:
echo 1. Run start_local.bat to start Redis
echo 2. Open 3 separate terminals and run the commands shown
echo 3. Test with: python test_pii.py
echo.
pause