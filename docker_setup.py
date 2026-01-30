"""
Docker-specific setup for TrustLayer AI
Handles spaCy model downloads and Docker build issues
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

def check_docker():
    """Check Docker availability"""
    log("Checking Docker availability...")
    
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

def cleanup_docker():
    """Clean up existing Docker containers and images"""
    log("Cleaning up existing Docker resources...")
    
    # Stop and remove containers
    containers = ["trustlayer-proxy", "trustlayer-dashboard", "trustlayer-redis"]
    for container in containers:
        run_command(f"docker stop {container}", f"Stopping {container}")
        run_command(f"docker rm {container}", f"Removing {container}")
    
    # Remove images (optional)
    run_command("docker image prune -f", "Cleaning up unused images")

def build_lightweight_image():
    """Build a lightweight Docker image without spaCy model"""
    log("Building lightweight Docker image...")
    
    # Create a temporary Dockerfile without spaCy download
    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    gcc \\
    g++ \\
    wget \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create startup script
RUN echo '#!/bin/bash\\n\\
echo "Starting TrustLayer AI..."\\n\\
echo "Checking spaCy model..."\\n\\
python -c "import spacy; spacy.load(\\"en_core_web_lg\\")" 2>/dev/null && echo "Large model available" || {\\n\\
    python -c "import spacy; spacy.load(\\"en_core_web_sm\\")" 2>/dev/null && echo "Small model available" || {\\n\\
        echo "Downloading spaCy model..."\\n\\
        python -m spacy download en_core_web_sm || echo "Warning: Model download failed"\\n\\
    }\\n\\
}\\n\\
exec "$@"' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 trustlayer && chown -R trustlayer:trustlayer /app
USER trustlayer

EXPOSE 8000 8501
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    with open("Dockerfile.temp", "w") as f:
        f.write(dockerfile_content)
    
    # Build the image
    success = run_command(
        "docker build -f Dockerfile.temp -t trustlayer-ai:latest .", 
        "Building Docker image",
        timeout=600  # 10 minutes timeout
    )
    
    # Clean up temporary file
    try:
        os.remove("Dockerfile.temp")
    except:
        pass
    
    return success

def create_docker_compose_override():
    """Create docker-compose override for lightweight deployment"""
    log("Creating Docker Compose override...")
    
    override_content = """version: '3.8'

services:
  proxy:
    image: trustlayer-ai:latest
    command: >
      sh -c "
        echo 'Initializing TrustLayer AI Proxy...' &&
        python -c 'import spacy; spacy.load(\"en_core_web_lg\")' 2>/dev/null ||
        python -c 'import spacy; spacy.load(\"en_core_web_sm\")' 2>/dev/null ||
        python -m spacy download en_core_web_sm &&
        echo 'Starting proxy server...' &&
        uvicorn app.main:app --host 0.0.0.0 --port 8000
      "
    
  dashboard:
    image: trustlayer-ai:latest
    command: >
      sh -c "
        echo 'Starting TrustLayer AI Dashboard...' &&
        streamlit run dashboard.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
      "
"""
    
    with open("docker-compose.override.yml", "w") as f:
        f.write(override_content)
    
    log("✅ Docker Compose override created")

def start_services():
    """Start all services using Docker Compose"""
    log("Starting TrustLayer AI services...")
    
    # Start services
    success = run_command(
        "docker-compose up -d", 
        "Starting Docker Compose services",
        timeout=300  # 5 minutes timeout
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
        
        # Check proxy (may take time to download model)
        log("Waiting for proxy to be ready (this may take a few minutes for model download)...")
        for i in range(12):  # Wait up to 2 minutes
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
            log(f"   Still waiting... ({i+1}/12)")
        
        # Check dashboard
        log("Checking dashboard...")
        for i in range(6):  # Wait up to 1 minute
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

def show_logs():
    """Show service logs"""
    log("Showing service logs...")
    
    print("\n" + "="*50)
    print("📋 Service Status:")
    run_command("docker-compose ps", "Checking service status")
    
    print("\n📝 Recent Proxy Logs:")
    run_command("docker logs --tail 20 trustlayer-proxy", "Proxy logs")
    
    print("\n📝 Recent Dashboard Logs:")
    run_command("docker logs --tail 10 trustlayer-dashboard", "Dashboard logs")

def main():
    """Main Docker setup function"""
    print("🐳 TrustLayer AI Docker Setup")
    print("=" * 40)
    print("This will build and start TrustLayer AI using Docker")
    print("Note: spaCy model will be downloaded at runtime to avoid build issues")
    print()
    
    start_time = datetime.now()
    
    try:
        # Check prerequisites
        if not check_docker():
            return False
        
        # Clean up existing resources
        cleanup_docker()
        
        # Build lightweight image
        if not build_lightweight_image():
            log("Failed to build Docker image", "ERROR")
            return False
        
        # Create override configuration
        create_docker_compose_override()
        
        # Start services
        if not start_services():
            log("Failed to start services", "ERROR")
            return False
        
        # Show status
        show_logs()
        
        duration = datetime.now() - start_time
        
        print("\n" + "=" * 50)
        print("🎉 TrustLayer AI Docker Setup Complete!")
        print("=" * 50)
        print(f"⏱️  Setup time: {duration.total_seconds():.1f} seconds")
        print("\n🔗 Access your services:")
        print("  📊 Dashboard: http://localhost:8501")
        print("  🔍 Proxy Health: http://localhost:8000/health")
        print("  📈 Metrics: http://localhost:8000/metrics")
        print("\n📋 Useful commands:")
        print("  docker-compose logs -f proxy     # Follow proxy logs")
        print("  docker-compose logs -f dashboard # Follow dashboard logs")
        print("  docker-compose down              # Stop all services")
        print("  docker-compose up -d             # Restart services")
        
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
        print("  1. Ensure Docker Desktop is running")
        print("  2. Check available disk space (need ~2GB)")
        print("  3. Check internet connection for downloads")
        print("  4. Try: docker system prune -f (to clean up)")
        print("  5. Use local setup instead: python run_all.py")
    
    sys.exit(0 if success else 1)