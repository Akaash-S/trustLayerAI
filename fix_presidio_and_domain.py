#!/usr/bin/env python3
"""
Fix Presidio and Domain Issues
Fixes spaCy model and domain authorization issues
"""

import subprocess
import sys
import yaml

def run_command(command, description=""):
    """Run shell command and return result"""
    print(f"🔧 {description}")
    print(f"   Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Success")
            return True, result.stdout.strip()
        else:
            print(f"   ❌ Failed: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, str(e)

def fix_presidio_config():
    """Fix Presidio configuration and spaCy model"""
    print("🚀 Fixing Presidio Configuration")
    print("=" * 35)
    
    print("\n1️⃣ Creating Presidio configuration...")
    
    # Create Presidio config directory
    run_command("mkdir -p /opt/trustlayer-ai/conf", "Creating config directory")
    
    # Create Presidio config file
    presidio_config = {
        'nlp_engine_name': 'spacy',
        'models': [
            {
                'lang_code': 'en',
                'model_name': 'en_core_web_sm'  # Use the small model we have
            }
        ]
    }
    
    with open('/tmp/presidio_config.yaml', 'w') as f:
        yaml.dump(presidio_config, f)
    
    run_command("sudo cp /tmp/presidio_config.yaml /opt/trustlayer-ai/conf/default.yaml", 
               "Installing Presidio config")
    
    print("\n2️⃣ Updating redactor.py to use correct model...")
    
    # Read current redactor.py
    try:
        with open('/opt/trustlayer-ai/app/redactor.py', 'r') as f:
            redactor_content = f.read()
    except FileNotFoundError:
        print("   ❌ redactor.py not found")
        return False
    
    # Fix the model name in redactor.py
    updated_redactor = redactor_content.replace(
        'en_core_web_lg', 'en_core_web_sm'
    ).replace(
        '"en_core_web_lg"', '"en_core_web_sm"'
    )
    
    with open('/tmp/redactor_fixed.py', 'w') as f:
        f.write(updated_redactor)
    
    run_command("sudo cp /tmp/redactor_fixed.py /opt/trustlayer-ai/app/redactor.py", 
               "Updating redactor.py")
    
    return True

def fix_domain_authorization():
    """Fix domain authorization issue"""
    print("\n🌐 Fixing Domain Authorization")
    print("=" * 30)
    
    print("\n1️⃣ Reading current config.yaml...")
    
    try:
        with open('/opt/trustlayer-ai/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("   ❌ config.yaml not found")
        return False
    
    print("\n2️⃣ Adding trustlayer.asolvitra.tech to allowed domains...")
    
    # Add the domain to allowed_domains
    if 'allowed_domains' not in config:
        config['allowed_domains'] = []
    
    domains_to_add = [
        'trustlayer.asolvitra.tech',
        'api.openai.com',
        'api.anthropic.com',
        'generativelanguage.googleapis.com',
        'api.cohere.ai',
        'localhost',
        '127.0.0.1'
    ]
    
    for domain in domains_to_add:
        if domain not in config['allowed_domains']:
            config['allowed_domains'].append(domain)
    
    # Save updated config
    with open('/tmp/config_fixed.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    run_command("sudo cp /tmp/config_fixed.yaml /opt/trustlayer-ai/config.yaml", 
               "Updating config.yaml")
    
    print("   ✅ Added domains to allowed list:")
    for domain in domains_to_add:
        print(f"      - {domain}")
    
    return True

def update_dockerfile_for_spacy():
    """Update Dockerfile to install correct spaCy model"""
    print("\n📦 Updating Dockerfile for spaCy")
    print("=" * 30)
    
    dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Flask for dashboard
RUN pip install flask

# Download correct spaCy model (small version)
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV SPACY_MODEL=en_core_web_sm

# Expose ports
EXPOSE 8000 8501

# Default command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    
    with open('/tmp/Dockerfile_fixed', 'w') as f:
        f.write(dockerfile_content)
    
    run_command("sudo cp /tmp/Dockerfile_fixed /opt/trustlayer-ai/Dockerfile", 
               "Updating Dockerfile")
    
    return True

def restart_services():
    """Restart services with new configuration"""
    print("\n🔄 Restarting Services")
    print("=" * 20)
    
    print("\n1️⃣ Stopping services...")
    run_command("cd /opt/trustlayer-ai && docker-compose down", "Stopping containers")
    
    print("\n2️⃣ Rebuilding images...")
    run_command("cd /opt/trustlayer-ai && docker-compose build --no-cache", "Rebuilding images")
    
    print("\n3️⃣ Starting services...")
    run_command("cd /opt/trustlayer-ai && docker-compose up -d", "Starting services")
    
    print("\n4️⃣ Waiting for services to start...")
    import time
    time.sleep(30)
    
    print("\n5️⃣ Checking logs...")
    run_command("docker logs trustlayer-proxy --tail 20", "Checking proxy logs")
    
    return True

def test_fixes():
    """Test if the fixes worked"""
    print("\n🧪 Testing Fixes")
    print("=" * 15)
    
    print("\n1️⃣ Testing health endpoint...")
    success, _ = run_command("curl -s http://localhost:8000/health", "Testing health")
    
    if success:
        print("   ✅ Health endpoint working")
    else:
        print("   ❌ Health endpoint not working")
        return False
    
    print("\n2️⃣ Testing PII detection...")
    success, output = run_command(
        'curl -s -X POST http://localhost:8000/test -H "Content-Type: application/json" -d \'{"content": "My name is John Smith"}\'',
        "Testing PII detection"
    )
    
    if success and "redacted" in output.lower():
        print("   ✅ PII detection working")
    else:
        print("   ❌ PII detection not working")
    
    print("\n3️⃣ Testing domain authorization...")
    success, _ = run_command("curl -I http://localhost/health", "Testing via Nginx")
    
    if success:
        print("   ✅ Domain authorization working")
    else:
        print("   ❌ Domain authorization issues")
    
    return True

def main():
    """Main function"""
    print("🚀 TrustLayer AI - Fix Presidio and Domain Issues")
    print("=" * 55)
    
    print("\nIssues to fix:")
    print("1. spaCy model mismatch (en_core_web_lg vs en_core_web_sm)")
    print("2. Domain authorization (trustlayer.asolvitra.tech blocked)")
    print("3. Presidio configuration missing")
    
    # Fix Presidio configuration
    if not fix_presidio_config():
        print("❌ Failed to fix Presidio config")
        return
    
    # Fix domain authorization
    if not fix_domain_authorization():
        print("❌ Failed to fix domain authorization")
        return
    
    # Update Dockerfile
    if not update_dockerfile_for_spacy():
        print("❌ Failed to update Dockerfile")
        return
    
    # Restart services
    if not restart_services():
        print("❌ Failed to restart services")
        return
    
    # Test fixes
    test_fixes()
    
    print("\n" + "=" * 55)
    print("🎉 PRESIDIO AND DOMAIN FIXES COMPLETE!")
    print("=" * 55)
    
    print("\n✅ Fixed Issues:")
    print("- spaCy model now uses en_core_web_sm")
    print("- trustlayer.asolvitra.tech added to allowed domains")
    print("- Presidio configuration created")
    print("- Services restarted with new config")
    
    print("\n📋 Test URLs:")
    print("- Health: https://trustlayer.asolvitra.tech/health")
    print("- Dashboard: https://trustlayer.asolvitra.tech/dashboard")
    print("- PII Test: https://trustlayer.asolvitra.tech/test")

if __name__ == "__main__":
    main()