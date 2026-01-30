"""
One-Command TrustLayer AI Setup and Test
This script does everything: setup, start services, and run tests
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
            subprocess.run(command, shell=True, check=True, timeout=timeout)
        log(f"✅ {description} completed")
        return True
    except subprocess.TimeoutExpired:
        log(f"⏰ {description} timed out", "WARNING")
        return False
    except subprocess.CalledProcessError as e:
        log(f"❌ {description} failed: {e}", "ERROR")
        if check_output and e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False
    except Exception as e:
        log(f"❌ {description} error: {e}", "ERROR")
        return False

def check_prerequisites():
    """Check if basic prerequisites are met"""
    log("Checking prerequisites...")
    
    # Check Python version
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        log(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    else:
        log(f"❌ Python {version.major}.{version.minor}.{version.micro} is too old. Need Python 3.9+", "ERROR")
        return False
    
    # Check Docker
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
                log("❌ Docker daemon is not running. Please start Docker Desktop.", "ERROR")
                return False
        else:
            log("❌ Docker not found. Please install Docker Desktop.", "ERROR")
            return False
    except Exception as e:
        log(f"❌ Docker check failed: {e}", "ERROR")
        return False

def setup_environment():
    """Set up the Python environment"""
    log("Setting up Python environment...")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists("venv"):
        if not run_command("python -m venv venv", "Creating virtual environment"):
            return False
    else:
        log("✅ Virtual environment already exists")
    
    # Determine pip command
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
    
    # Download spaCy model
    if not run_command(f"{python_cmd} -m spacy download en_core_web_lg", "Downloading spaCy model"):
        log("Trying to download smaller model as fallback...", "WARNING")
        if not run_command(f"{python_cmd} -m spacy download en_core_web_sm", "Downloading spaCy small model"):
            return False
    
    return True

def main():
    """Main execution function"""
    print("🛡️  TrustLayer AI - Complete Setup and Test")
    print("=" * 50)
    print("This will:")
    print("  1. Check prerequisites")
    print("  2. Set up Python environment")
    print("  3. Start all services")
    print("  4. Run comprehensive tests")
    print("  5. Keep services running for manual testing")
    print()
    
    start_time = datetime.now()
    
    try:
        # Phase 1: Prerequisites
        log("Phase 1: Checking Prerequisites")
        if not check_prerequisites():
            log("Prerequisites check failed. Please resolve issues and try again.", "ERROR")
            return False
        
        # Phase 2: Environment Setup
        log("Phase 2: Setting up Environment")
        if not setup_environment():
            log("Environment setup failed. Please check error messages above.", "ERROR")
            return False
        
        # Phase 3: Automated Testing
        log("Phase 3: Starting Automated Tests")
        
        # Determine Python command
        if os.name == 'nt':  # Windows
            python_cmd = "venv\\Scripts\\python"
        else:  # Unix-like
            python_cmd = "venv/bin/python"
        
        # Run the automated test suite
        log("Launching automated test runner...")
        result = subprocess.run(f"{python_cmd} auto_test.py", shell=True)
        
        duration = datetime.now() - start_time
        
        if result.returncode == 0:
            print("\n" + "=" * 50)
            print("🎉 SUCCESS! TrustLayer AI is fully operational")
            print("=" * 50)
            print(f"⏱️  Total setup time: {duration.total_seconds():.1f} seconds")
            print("\n🔗 Access your TrustLayer AI system:")
            print("  📊 Dashboard: http://localhost:8501")
            print("  🔍 Proxy Health: http://localhost:8000/health")
            print("  📈 Metrics: http://localhost:8000/metrics")
            print("\n💡 What's running:")
            print("  - FastAPI Proxy Server (Port 8000)")
            print("  - Streamlit Dashboard (Port 8501)")
            print("  - Redis Container (Port 6379)")
            print("\n🧪 Test Results:")
            print("  - PII redaction is working")
            print("  - Security features are active")
            print("  - File processing is operational")
            print("  - Real-time monitoring is available")
            return True
        else:
            print("\n" + "=" * 50)
            print("⚠️  Setup completed but some tests failed")
            print("=" * 50)
            print("Check the test output above for specific issues.")
            print("You may still be able to use the system manually.")
            return False
            
    except KeyboardInterrupt:
        log("Setup interrupted by user", "WARNING")
        return False
    except Exception as e:
        log(f"Unexpected error during setup: {e}", "ERROR")
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n🔧 Troubleshooting:")
        print("  1. Check TROUBLESHOOTING.md for common issues")
        print("  2. Ensure Docker Desktop is running")
        print("  3. Verify Python 3.9+ is installed")
        print("  4. Check internet connection for package downloads")
        print("  5. Try running individual components manually")
        
    sys.exit(0 if success else 1)