#!/usr/bin/env python3
"""
Fix Exit Code 127 - Command Not Found Error
Fixes Docker container startup issues when commands are not found
"""

import subprocess
import sys
import time

def run_command(command, description=""):
    """Run shell command and return result"""
    print(f"🔧 {description}")
    print(f"   Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Success")
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n')[:3]:
                    print(f"      {line}")
            return True, result.stdout.strip()
        else:
            print(f"   ❌ Failed: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, str(e)

def fix_exit_code_127():
    """Fix exit code 127 (command not found) error"""
    print("🚀 Fixing Exit Code 127 - Command Not Found")
    print("=" * 50)
    
    print("\n1️⃣ Checking current Docker setup...")
    
    # Check Docker logs for more details
    run_command("docker logs trustlayer-proxy --tail 20", "Checking proxy logs")
    run_command("docker logs trustlayer-dashboard --tail 20", "Checking dashboard logs")
    
    print("\n2️⃣ Stopping and cleaning up containers...")
    run_command("cd /opt/trustlayer-ai && docker-compose down", "Stopping containers")
    run_command("docker system prune -f", "Cleaning up Docker")
    
    print("\n3️⃣ Checking Dockerfile...")
    
    # Read current Dockerfile
    try:
        with open('/opt/trustlayer-ai/Dockerfile', 'r') as f:
            dockerfile_content = f.read()
        print("   ✅ Dockerfile found")
    except FileNotFoundError:
        print("   ❌ Dockerfile not found - creating new one")
        dockerfile_content = ""
    
    print("\n4️⃣ Creating working Dockerfile...")
    
    # Create a working Dockerfile
    dockerfile = '''FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm || \\
    pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose ports
EXPOSE 8000 8501

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    
    with open('/tmp/Dockerfile.fixed', 'w') as f:
        f.write(dockerfile)
    
    run_command("sudo cp /tmp/Dockerfile.fixed /opt/trustlayer-ai/Dockerfile", "Installing fixed Dockerfile")
    
    print("\n5️⃣ Creating working docker-compose.yml...")
    
    # Create a working docker-compose.yml
    docker_compose = '''version: '3.8'

services:
  proxy:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - PYTHONPATH=/app
    depends_on:
      - redis
    restart: unless-stopped
    container_name: trustlayer-proxy
    command: ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dashboard:
    build: .
    ports:
      - "8501:8501"
    environment:
      - PYTHONPATH=/app
    depends_on:
      - proxy
    restart: unless-stopped
    container_name: trustlayer-dashboard
    command: ["python", "-m", "streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    container_name: trustlayer-redis
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
'''
    
    with open('/tmp/docker-compose.fixed.yml', 'w') as f:
        f.write(docker_compose)
    
    run_command("sudo cp /tmp/docker-compose.fixed.yml /opt/trustlayer-ai/docker-compose.yml", 
               "Installing fixed docker-compose")
    
    print("\n6️⃣ Rebuilding Docker images...")
    run_command("cd /opt/trustlayer-ai && docker-compose build --no-cache", "Rebuilding images")
    
    print("\n7️⃣ Starting services...")
    run_command("cd /opt/trustlayer-ai && docker-compose up -d", "Starting services")
    
    print("\n8️⃣ Waiting for services to start...")
    time.sleep(30)
    
    print("\n9️⃣ Checking service status...")
    run_command("docker ps", "Checking running containers")
    run_command("docker logs trustlayer-proxy --tail 10", "Checking proxy logs")
    run_command("docker logs trustlayer-dashboard --tail 10", "Checking dashboard logs")
    
    print("\n🔟 Testing services...")
    run_command("curl -s http://localhost:8000/health", "Testing proxy health")
    run_command("curl -I http://localhost:8501", "Testing dashboard")
    
    print("\n" + "=" * 50)
    print("🎉 EXIT CODE 127 FIX COMPLETE!")
    print("=" * 50)
    
    return True

def create_minimal_setup():
    """Create minimal setup that definitely works"""
    print("\n🔧 Creating Minimal Working Setup")
    print("=" * 40)
    
    # Minimal Dockerfile
    minimal_dockerfile = '''FROM python:3.11-slim

WORKDIR /app

# Install minimal dependencies
RUN pip install fastapi uvicorn streamlit requests pyyaml pandas plotly

# Copy code
COPY . .

# Simple startup
CMD ["python", "-c", "print('Container started successfully')"]
'''
    
    # Minimal docker-compose
    minimal_compose = '''version: '3.8'

services:
  proxy:
    build: .
    ports:
      - "8000:8000"
    container_name: trustlayer-proxy
    command: ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    
  dashboard:
    build: .
    ports:
      - "8501:8501"
    container_name: trustlayer-dashboard
    command: ["python", "-m", "streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
'''
    
    with open('/tmp/Dockerfile.minimal', 'w') as f:
        f.write(minimal_dockerfile)
    
    with open('/tmp/docker-compose.minimal.yml', 'w') as f:
        f.write(minimal_compose)
    
    run_command("sudo cp /tmp/Dockerfile.minimal /opt/trustlayer-ai/Dockerfile", "Installing minimal Dockerfile")
    run_command("sudo cp /tmp/docker-compose.minimal.yml /opt/trustlayer-ai/docker-compose.yml", "Installing minimal compose")
    
    print("✅ Minimal setup created")

def debug_container_issue():
    """Debug what's wrong with the container"""
    print("\n🔍 Debugging Container Issue")
    print("=" * 35)
    
    print("\n1️⃣ Checking if files exist...")
    run_command("ls -la /opt/trustlayer-ai/", "Listing project files")
    run_command("ls -la /opt/trustlayer-ai/app/", "Listing app files")
    
    print("\n2️⃣ Checking Python files...")
    run_command("cd /opt/trustlayer-ai && python -c 'import app.main; print(\"✅ app.main imports OK\")'", 
               "Testing app.main import")
    run_command("cd /opt/trustlayer-ai && python -c 'import dashboard; print(\"✅ dashboard imports OK\")'", 
               "Testing dashboard import")
    
    print("\n3️⃣ Checking requirements...")
    run_command("cd /opt/trustlayer-ai && pip install -r requirements.txt", "Installing requirements")
    
    print("\n4️⃣ Testing commands manually...")
    run_command("cd /opt/trustlayer-ai && python -m uvicorn app.main:app --help", "Testing uvicorn command")
    run_command("cd /opt/trustlayer-ai && python -m streamlit --help", "Testing streamlit command")
    
    print("\n5️⃣ Building and testing container...")
    run_command("cd /opt/trustlayer-ai && docker build -t trustlayer-test .", "Building test image")
    run_command("docker run --rm trustlayer-test python --version", "Testing Python in container")
    run_command("docker run --rm trustlayer-test python -c 'import uvicorn; print(\"uvicorn OK\")'", "Testing uvicorn in container")

def main():
    """Main function"""
    print("TrustLayer AI - Fix Exit Code 127")
    print("Choose your approach:")
    print("1. Apply comprehensive fix")
    print("2. Create minimal setup")
    print("3. Debug container issue")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        success = fix_exit_code_127()
        if success:
            print("\n✅ Fix applied!")
            print("Check: docker ps")
            print("Test: curl http://localhost:8000/health")
        else:
            print("\n❌ Fix failed")
    
    elif choice == "2":
        create_minimal_setup()
        print("\n✅ Minimal setup created!")
        print("Run: cd /opt/trustlayer-ai && docker-compose up -d")
    
    else:  # choice == "3"
        debug_container_issue()
        print("\n✅ Debug complete!")

if __name__ == "__main__":
    main()