"""
Simplified setup script for TrustLayer AI
Handles common setup issues and provides better error messages
"""
import subprocess
import sys
import os
import time
import requests

def run_command(command, description, check_output=False):
    """Run a command with proper error handling"""
    print(f"🔄 {description}...")
    
    try:
        if check_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        else:
            subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if check_output and e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is too old. Need Python 3.9+")
        return False

def check_docker():
    """Check if Docker is available and running"""
    print("🐳 Checking Docker...")
    
    try:
        result = subprocess.run("docker --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker found: {result.stdout.strip()}")
            
            # Check if Docker daemon is running
            result = subprocess.run("docker ps", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Docker daemon is running")
                return True
            else:
                print("❌ Docker daemon is not running. Please start Docker Desktop.")
                return False
        else:
            print("❌ Docker not found. Please install Docker Desktop.")
            return False
    except Exception as e:
        print(f"❌ Docker check failed: {e}")
        return False

def setup_virtual_environment():
    """Create and setup virtual environment"""
    if os.path.exists("venv"):
        print("📁 Virtual environment already exists")
        return True
    
    return run_command("python -m venv venv", "Creating virtual environment")

def install_requirements():
    """Install Python requirements"""
    if os.name == 'nt':  # Windows
        pip_command = "venv\\Scripts\\pip install -r requirements.txt"
        python_command = "venv\\Scripts\\python"
    else:  # Unix-like
        pip_command = "venv/bin/pip install -r requirements.txt"
        python_command = "venv/bin/python"
    
    success = run_command(pip_command, "Installing Python packages")
    if not success:
        return False
    
    # Download spaCy model
    return run_command(f"{python_command} -m spacy download en_core_web_lg", "Downloading spaCy model")

def start_redis():
    """Start Redis container"""
    print("🔴 Starting Redis container...")
    
    # Check if container already exists
    result = subprocess.run("docker ps -a --filter name=trustlayer-redis --format '{{.Names}}'", 
                          shell=True, capture_output=True, text=True)
    
    if "trustlayer-redis" in result.stdout:
        print("📦 Redis container exists, starting it...")
        return run_command("docker start trustlayer-redis", "Starting existing Redis container")
    else:
        print("📦 Creating new Redis container...")
        return run_command("docker run -d --name trustlayer-redis -p 6379:6379 redis:7-alpine", 
                         "Creating Redis container")

def wait_for_redis():
    """Wait for Redis to be ready"""
    print("⏳ Waiting for Redis to be ready...")
    
    for i in range(10):
        try:
            result = subprocess.run("docker exec trustlayer-redis redis-cli ping", 
                                  shell=True, capture_output=True, text=True)
            if result.returncode == 0 and "PONG" in result.stdout:
                print("✅ Redis is ready")
                return True
        except:
            pass
        
        time.sleep(1)
        print(f"   Attempt {i+1}/10...")
    
    print("⚠️  Redis might not be fully ready, but continuing...")
    return True

def test_setup():
    """Test the setup by running basic connectivity tests"""
    print("\n🧪 Testing setup...")
    
    if os.name == 'nt':  # Windows
        python_command = "venv\\Scripts\\python"
    else:  # Unix-like
        python_command = "venv/bin/python"
    
    # Test imports
    test_script = """
import sys
try:
    import fastapi
    import uvicorn
    import redis
    import presidio_analyzer
    import spacy
    print("✅ All required packages imported successfully")
    
    # Test spaCy model
    nlp = spacy.load("en_core_web_lg")
    print("✅ spaCy model loaded successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
"""
    
    with open("test_imports.py", "w") as f:
        f.write(test_script)
    
    success = run_command(f"{python_command} test_imports.py", "Testing package imports")
    
    # Clean up test file
    try:
        os.remove("test_imports.py")
    except:
        pass
    
    return success

def print_next_steps():
    """Print instructions for next steps"""
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("=" * 50)
    
    print("\n📋 Next Steps:")
    print("\n1️⃣  Start the Proxy (Terminal 1):")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    
    print("\n2️⃣  Start the Dashboard (Terminal 2):")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   streamlit run dashboard.py")
    
    print("\n3️⃣  Run Tests (Terminal 3):")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   python test_basic.py")
    print("   python test_pii.py")
    
    print("\n🔗 URLs:")
    print("   Dashboard: http://localhost:8501")
    print("   Proxy Health: http://localhost:8000/health")
    print("   Proxy Metrics: http://localhost:8000/metrics")
    
    print("\n💡 Tips:")
    print("   - Run test_basic.py first to verify connectivity")
    print("   - Check proxy logs for PII redaction messages")
    print("   - Monitor dashboard for real-time metrics")

def main():
    """Main setup function"""
    print("🛡️  TrustLayer AI - Simplified Setup")
    print("=" * 40)
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    if not check_docker():
        return False
    
    # Setup steps
    steps = [
        ("Virtual Environment", setup_virtual_environment),
        ("Python Packages", install_requirements),
        ("Redis Container", start_redis),
        ("Redis Ready", wait_for_redis),
        ("Setup Test", test_setup)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📦 {step_name}")
        print("-" * 30)
        
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            print("\n🔧 Troubleshooting tips:")
            if step_name == "Python Packages":
                print("   - Try: pip install --upgrade pip")
                print("   - Check internet connection")
                print("   - Try: pip install -r requirements.txt --no-cache-dir")
            elif step_name == "Redis Container":
                print("   - Make sure Docker Desktop is running")
                print("   - Try: docker system prune (to clean up)")
            return False
    
    print_next_steps()
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup incomplete. Please resolve the issues above.")
        sys.exit(1)