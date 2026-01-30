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
echo 📥 Activating virtual environment...
call venv\Scripts\activate.bat

echo 🚀 Running simplified setup...
python setup_simple.py
if errorlevel 1 (
    echo ❌ Setup encountered issues
    echo 📖 Check SPACY_MODEL_INSTALL.md for manual spaCy model installation
    pause
    exit /b 1
)

echo.
echo ✅ Setup completed!
echo.
echo 🚀 Next steps:
echo 1. Run start_local.bat to start Redis
echo 2. Open 3 separate terminals and run the commands shown
echo 3. Test with: python test_pii.py
echo.
pause