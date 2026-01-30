"""
TrustLayer AI Setup Script
Complete setup for local development and Docker deployment
"""
import subprocess
import sys
import os
import time
from datetime import datetime

def log(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def run_command(command, description, check_output=False, timeout=None):
    """Run a command with proper error handling"""
    log(f"🔄 {description}...")
    
    try:
        if check_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, timeout=timeout)
            return result.stdout.strip()
        else:
            result = subprocess.run(command, shell=True, timeout=timeout)
            if result.returncode == 0:
                log(f"✅ {description} completed")
                return True
            else:
                log(f"❌ {description} failed with exit code {result.returncode}", "ERROR")
                return False
    except subprocess.TimeoutExpired:
        log(f"⏰ {description} timed out", "WARNING")
        return False
    except subprocess.CalledProcessError as e:
        log(f"❌ {description} failed: {e}", "ERROR")
        return False
    except Exception as e:
        log(f"❌ {description} error: {e}", "ERROR")
        return False

def check_prerequisites():
    """Check system prerequisites"""
    log("Checking prerequisites...")
    
    # Check Python version
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        log(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    else:
        log(f"❌ Python {version.major}.{version.minor}.{version.micro} is too old. Need Python 3.9+", "ERROR")
        return False
    
    # Check Docker (optional)
    try:
        result = subprocess.run("docker --version", shell=True, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            log(f"✅ Docker found: {result.stdout.strip()}")
            
            # Check if Docker daemon is running
            result = subprocess.run("docker ps", shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                log("✅ Docker daemon is running")
                return True
            else:
                log("⚠️  Docker daemon not running (Docker setup will be skipped)", "WARNING")
                return True
        else:
            log("⚠️  Docker not found (Docker setup will be skipped)", "WARNING")
            return True
    except Exception:
        log("⚠️  Docker check failed (Docker setup will be skipped)", "WARNING")
        return True

def setup_local_environment():
    """Set up local Python environment"""
    log("Setting up local Python environment...")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists("venv"):
        if not run_command("python -m venv venv", "Creating virtual environment"):
            return False
    else:
        log("✅ Virtual environment already exists")
    
    # Determine pip and python commands
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix-like
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    # Upgrade pip
    run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip")
    
    # Install requirements
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing Python packages"):
        return False
    
    # Download spaCy model (optional)
    log("Downloading spaCy model (this may take a few minutes)...")
    if not run_command(f"{python_cmd} -m spacy download en_core_web_lg", "Downloading large spaCy model"):
        log("Large model failed, trying small model...", "WARNING")
        if not run_command(f"{python_cmd} -m spacy download en_core_web_sm", "Downloading small spaCy model"):
            log("spaCy model download failed - will use basic PII detection", "WARNING")
    
    return True

def setup_docker_environment():
    """Set up Docker environment"""
    log("Setting up Docker environment...")
    
    # Check if Docker is available
    try:
        result = subprocess.run("docker ps", shell=True, capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            log("Docker not available, skipping Docker setup", "WARNING")
            return True
    except Exception:
        log("Docker not available, skipping Docker setup", "WARNING")
        return True
    
    # Build Docker image
    if not run_command("docker build -t trustlayer-ai .", "Building Docker image", timeout=600):
        log("Docker build failed", "ERROR")
        return False
    
    log("✅ Docker image built successfully")
    return True

def show_usage_instructions():
    """Show usage instructions"""
    print("\n" + "=" * 60)
    print("🎉 TrustLayer AI Setup Complete!")
    print("=" * 60)
    
    print("\n🚀 Usage Options:")
    
    print("\n1️⃣  Local Development:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   python run_all.py")
    
    print("\n2️⃣  Docker Deployment:")
    print("   docker-compose up -d")
    
    print("\n3️⃣  Manual Testing:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   # Terminal 1: uvicorn app.main:app --reload")
    print("   # Terminal 2: streamlit run dashboard.py")
    print("   # Terminal 3: python test_pii.py")
    
    print("\n🔗 Access Points:")
    print("   📊 Dashboard: http://localhost:8501")
    print("   🔍 Proxy Health: http://localhost:8000/health")
    print("   📈 Metrics: http://localhost:8000/metrics")
    
    print("\n📚 Documentation:")
    print("   📖 README.md - Complete documentation")
    print("   🔧 TROUBLESHOOTING.md - Issue resolution")
    print("   🧪 LOCAL_TESTING_GUIDE.md - Testing guide")

def main():
    """Main setup function"""
    print("🛡️  TrustLayer AI Setup")
    print("=" * 30)
    print("This will set up TrustLayer AI for both local and Docker deployment")
    print()
    
    start_time = datetime.now()
    
    try:
        # Check prerequisites
        if not check_prerequisites():
            log("Prerequisites check failed", "ERROR")
            return False
        
        # Setup local environment
        if not setup_local_environment():
            log("Local environment setup failed", "ERROR")
            return False
        
        # Setup Docker environment (optional)
        setup_docker_environment()
        
        # Show usage instructions
        show_usage_instructions()
        
        duration = datetime.now() - start_time
        print(f"\n⏱️  Total setup time: {duration.total_seconds():.1f} seconds")
        
        return True
        
    except KeyboardInterrupt:
        log("Setup interrupted by user", "WARNING")
        return False
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n🔧 Troubleshooting:")
        print("  1. Check TROUBLESHOOTING.md for common issues")
        print("  2. Ensure Python 3.9+ is installed")
        print("  3. Check internet connection for package downloads")
        print("  4. For Docker issues, ensure Docker Desktop is running")
        
    sys.exit(0 if success else 1)