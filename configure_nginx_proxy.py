#!/usr/bin/env python3
"""
Configure Nginx Proxy for TrustLayer AI
This script configures Nginx to proxy TrustLayer AI services through port 80
Run this from Google Cloud Shell or SSH into the VM
"""

import subprocess
import sys

def run_command(command, description=""):
    """Run shell command and return result"""
    print(f"🔧 {description}")
    print(f"   Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Success")
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n')[:5]:  # Show first 5 lines
                    print(f"      {line}")
            return True, result.stdout.strip()
        else:
            print(f"   ❌ Failed: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, str(e)

def create_nginx_config():
    """Create Nginx configuration for TrustLayer AI"""
    
    nginx_config = '''server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name _;
    
    # TrustLayer AI Proxy - Main proxy functionality
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Handle timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Handle large requests
        client_max_body_size 10M;
    }
    
    # Dashboard access via /dashboard path
    location /dashboard {
        rewrite ^/dashboard(.*) /$1 break;
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Metrics endpoint
    location /metrics {
        proxy_pass http://localhost:8000/metrics;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Test endpoint
    location /test {
        proxy_pass http://localhost:8000/test;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}'''
    
    return nginx_config

def configure_nginx():
    """Configure Nginx to proxy TrustLayer AI"""
    print("🚀 Configuring Nginx Proxy for TrustLayer AI")
    print("=" * 60)
    
    # Step 1: Check if TrustLayer AI is running locally
    print("\n1️⃣ Checking if TrustLayer AI services are running...")
    success, _ = run_command("curl -s http://localhost:8000/health", "Testing TrustLayer AI health")
    
    if not success:
        print("   ⚠️  TrustLayer AI not responding locally")
        print("   Starting TrustLayer AI services...")
        
        # Try to start TrustLayer AI
        run_command("cd /opt/trustlayer-ai && docker-compose up -d", "Starting TrustLayer AI")
        
        # Wait a bit and test again
        print("   Waiting 10 seconds for services to start...")
        import time
        time.sleep(10)
        
        success, _ = run_command("curl -s http://localhost:8000/health", "Re-testing TrustLayer AI health")
        if not success:
            print("   ❌ TrustLayer AI still not responding")
            print("   You may need to check the Docker setup manually")
            return False
    
    # Step 2: Backup existing Nginx config
    print("\n2️⃣ Backing up existing Nginx configuration...")
    run_command("sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup", 
               "Creating backup")
    
    # Step 3: Create new Nginx config
    print("\n3️⃣ Creating new Nginx configuration...")
    config = create_nginx_config()
    
    # Write config to temporary file
    with open('/tmp/nginx_trustlayer.conf', 'w') as f:
        f.write(config)
    
    # Copy to Nginx sites-available
    run_command("sudo cp /tmp/nginx_trustlayer.conf /etc/nginx/sites-available/default", 
               "Installing new Nginx config")
    
    # Step 4: Test Nginx configuration
    print("\n4️⃣ Testing Nginx configuration...")
    success, _ = run_command("sudo nginx -t", "Testing Nginx config syntax")
    
    if not success:
        print("   ❌ Nginx configuration has errors")
        print("   Restoring backup...")
        run_command("sudo cp /etc/nginx/sites-available/default.backup /etc/nginx/sites-available/default", 
                   "Restoring backup")
        return False
    
    # Step 5: Reload Nginx
    print("\n5️⃣ Reloading Nginx...")
    success, _ = run_command("sudo systemctl reload nginx", "Reloading Nginx")
    
    if not success:
        print("   ❌ Failed to reload Nginx")
        return False
    
    # Step 6: Test the proxy
    print("\n6️⃣ Testing the proxy configuration...")
    
    # Test health endpoint through Nginx
    success, output = run_command("curl -s http://localhost:80/health", "Testing health endpoint via Nginx")
    if success and "healthy" in output:
        print("   ✅ Health endpoint working through Nginx")
    else:
        print("   ⚠️  Health endpoint not working through Nginx")
    
    # Test dashboard access
    success, _ = run_command("curl -I http://localhost:80/dashboard", "Testing dashboard via Nginx")
    if success:
        print("   ✅ Dashboard accessible through Nginx")
    else:
        print("   ⚠️  Dashboard not accessible through Nginx")
    
    print("\n" + "=" * 60)
    print("🎉 NGINX PROXY CONFIGURATION COMPLETE!")
    print("=" * 60)
    
    print("\n🔧 NEW PROXY CONFIGURATION:")
    print("   HTTP Proxy:  34.59.4.137:80")
    print("   HTTPS Proxy: 34.59.4.137:80")
    print("   Dashboard:   http://34.59.4.137/dashboard")
    print("   Health:      http://34.59.4.137/health")
    print("   Metrics:     http://34.59.4.137/metrics")
    
    print("\n📋 TESTING COMMANDS:")
    print("   curl http://34.59.4.137/health")
    print("   curl http://34.59.4.137/metrics")
    print("   curl http://34.59.4.137/dashboard")
    
    return True

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Configure Nginx Proxy for TrustLayer AI")
        print("Usage: python configure_nginx_proxy.py")
        print("\nThis script should be run on the VM (via SSH) or from Google Cloud Shell")
        print("It configures Nginx to proxy TrustLayer AI services through port 80")
        sys.exit(0)
    
    # Check if running as root or with sudo access
    result = subprocess.run("sudo -n true", shell=True, capture_output=True)
    if result.returncode != 0:
        print("❌ This script requires sudo access")
        print("Run with: sudo python configure_nginx_proxy.py")
        print("Or run from an account with sudo privileges")
        sys.exit(1)
    
    success = configure_nginx()
    
    if success:
        print("\n✅ Configuration successful!")
        print("You can now use 34.59.4.137:80 as your proxy")
    else:
        print("\n❌ Configuration failed!")
        print("Check the error messages above and try manual configuration")

if __name__ == "__main__":
    main()