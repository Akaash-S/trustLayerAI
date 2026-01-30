"""
TrustLayer AI Setup Script
"""
import subprocess
import sys
import os

def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def download_spacy_model():
    """Download spaCy NLP model"""
    print("Downloading spaCy English model...")
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_lg"])

def setup_directories():
    """Create necessary directories"""
    directories = ["logs", "data", "temp"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

def main():
    """Main setup function"""
    print("🛡️ Setting up TrustLayer AI: Master Builder")
    print("=" * 50)
    
    try:
        setup_directories()
        install_requirements()
        download_spacy_model()
        
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Start Redis: docker run -d -p 6379:6379 redis:7-alpine")
        print("2. Start the proxy: python -m uvicorn app.main:app --reload")
        print("3. Start the dashboard: streamlit run dashboard.py")
        print("4. Or use Docker Compose: docker-compose up -d")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()