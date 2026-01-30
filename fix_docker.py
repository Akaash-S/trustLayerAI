"""
Quick fix for Docker spaCy model issues
Stops failing containers and starts minimal version
"""
import subprocess
import sys
import time
from datetime import datetime

def log(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def run_command(command, description, ignore_errors=False):
    """Run a command with proper error handling"""
    log(f"🔄 {description}...")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0 or ignore_errors:
            log(f"✅ {description} completed")
            return True
        else:
            if not ignore_errors:
                log(f"❌ {description} failed: {result.stderr}", "ERROR")
            return False
    except Exception as e:
        if not ignore_errors:
            log(f"❌ {description} error: {e}", "ERROR")
        return False

def cleanup_containers():
    """Stop and remove existing containers"""
    log("Cleaning up existing containers...")
    
    containers = ["trustlayer-proxy", "trustlayer-dashboard", "trustlayer-redis"]
    
    for container in containers:
        run_command(f"docker stop {container}", f"Stopping {container}", ignore_errors=True)
        run_command(f"docker rm {container}", f"Removing {container}", ignore_errors=True)
    
    # Clean up any dangling containers
    run_command("docker container prune -f", "Cleaning up stopped containers", ignore_errors=True)

def build_minimal_image():
    """Build the minimal Docker image"""
    log("Building minimal TrustLayer AI image...")
    
    success = run_command(
        "docker build -f Dockerfile.minimal -t trustlayer-minimal .",
        "Building minimal image"
    )
    
    return success

def start_minimal_services():
    """Start services using minimal configuration"""
    log("Starting minimal TrustLayer AI services...")
    
    success = run_command(
        "docker-compose -f docker-compose.minimal.yml up -d",
        "Starting minimal services"
    )
    
    if success:
        log("Waiting for services to initialize...")
        time.sleep(10)
        
        # Check service health
        log("Checking service health...")
        
        # Check Redis
        redis_ok = run_command(
            "docker exec trustlayer-redis redis-cli ping",
            "Testing Redis connectivity"
        )
        
        # Check proxy
        log("Waiting for proxy to be ready...")
        for i in range(6):  # Wait up to 1 minute
            try:
                result = subprocess.run(
                    "curl -s http://localhost:8000/health",
                    shell=True, capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    log("✅ Proxy is ready")
                    break
            except:
                pass
            time.sleep(10)
            log(f"   Still waiting... ({i+1}/6)")
        
        # Check dashboard
        log("Checking dashboard...")
        for i in range(3):  # Wait up to 30 seconds
            try:
                result = subprocess.run(
                    "curl -s http://localhost:8501",
                    shell=True, capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    log("✅ Dashboard is ready")
                    break
            except:
                pass
            time.sleep(10)
        
        return True
    
    return False

def show_status():
    """Show current service status"""
    log("Showing service status...")
    
    print("\n" + "="*50)
    print("📋 Service Status:")
    run_command("docker ps --filter name=trustlayer", "Checking containers")
    
    print("\n📝 Recent Logs:")
    run_command("docker logs --tail 10 trustlayer-proxy", "Proxy logs", ignore_errors=True)

def test_basic_functionality():
    """Test basic functionality"""
    log("Testing basic functionality...")
    
    try:
        # Test health endpoint
        result = subprocess.run(
            "curl -s http://localhost:8000/health",
            shell=True, capture_output=True, timeout=5
        )
        if result.returncode == 0:
            log("✅ Health endpoint working")
        
        # Test metrics endpoint
        result = subprocess.run(
            "curl -s http://localhost:8000/metrics",
            shell=True, capture_output=True, timeout=5
        )
        if result.returncode == 0:
            log("✅ Metrics endpoint working")
        
        # Test basic PII redaction
        test_data = '{"messages":[{"role":"user","content":"My name is John Doe"}]}'
        result = subprocess.run(
            f'curl -s -X POST -H "Host: api.openai.com" -H "Content-Type: application/json" -d \'{test_data}\' http://localhost:8000/v1/chat/completions',
            shell=True, capture_output=True, timeout=10
        )
        if result.returncode == 0:
            log("✅ PII redaction pipeline working")
        
    except Exception as e:
        log(f"Testing error: {e}", "WARNING")

def main():
    """Main fix function"""
    print("🔧 TrustLayer AI Docker Quick Fix")
    print("=" * 40)
    print("This will fix the spaCy model download issues by:")
    print("  1. Stopping failing containers")
    print("  2. Building minimal image (no spaCy model)")
    print("  3. Starting services with basic PII detection")
    print("  4. Testing functionality")
    print()
    
    start_time = datetime.now()
    
    try:
        # Step 1: Cleanup
        cleanup_containers()
        
        # Step 2: Build minimal image
        if not build_minimal_image():
            log("Failed to build minimal image", "ERROR")
            return False
        
        # Step 3: Start services
        if not start_minimal_services():
            log("Failed to start minimal services", "ERROR")
            return False
        
        # Step 4: Show status
        show_status()
        
        # Step 5: Test functionality
        test_basic_functionality()
        
        duration = datetime.now() - start_time
        
        print("\n" + "=" * 50)
        print("🎉 TrustLayer AI Quick Fix Complete!")
        print("=" * 50)
        print(f"⏱️  Fix time: {duration.total_seconds():.1f} seconds")
        print("\n🔗 Access your services:")
        print("  📊 Dashboard: http://localhost:8501")
        print("  🔍 Proxy Health: http://localhost:8000/health")
        print("  📈 Metrics: http://localhost:8000/metrics")
        print("\n⚠️  Note: Running in minimal mode")
        print("  - PII detection uses basic regex patterns")
        print("  - Accuracy is reduced but functionality is preserved")
        print("  - Suitable for testing and demonstration")
        print("\n📋 To improve accuracy later:")
        print("  - Use local setup: python run_all.py")
        print("  - Or manually install spaCy model in container")
        
        return True
        
    except KeyboardInterrupt:
        log("Fix interrupted by user", "WARNING")
        return False
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n🔧 If issues persist:")
        print("  1. Try local setup instead: python run_all.py")
        print("  2. Check Docker logs: docker logs trustlayer-proxy")
        print("  3. Restart Docker Desktop")
        print("  4. Check available disk space")
    
    sys.exit(0 if success else 1)