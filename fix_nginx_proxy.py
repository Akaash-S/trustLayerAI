#!/usr/bin/env python3
"""
Fix Nginx Proxy Configuration
Simple script to restart Nginx and verify proxy is working
"""

import subprocess
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

def fix_nginx_proxy():
    """Fix Nginx proxy configuration"""
    print("🚀 Fixing Nginx Proxy Configuration")
    print("=" * 50)
    
    # Step 1: Check TrustLayer AI is still running
    print("\n1️⃣ Verifying TrustLayer AI is running...")
    success, output = run_command("curl -s http://localhost:8000/health", "Testing TrustLayer AI")
    if not success or "healthy" not in output:
        print("   ❌ TrustLayer AI not responding - need to start it first")
        run_command("cd /opt/trustlayer-ai && docker-compose up -d", "Starting TrustLayer AI")
        time.sleep(5)
    
    # Step 2: Restart Nginx completely
    print("\n2️⃣ Restarting Nginx...")
    run_command("sudo systemctl restart nginx", "Restarting Nginx service")
    time.sleep(2)
    
    # Step 3: Check Nginx status
    print("\n3️⃣ Checking Nginx status...")
    run_command("sudo systemctl status nginx --no-pager -l", "Checking Nginx status")
    
    # Step 4: Test proxy locally
    print("\n4️⃣ Testing proxy locally...")
    success, output = run_command("curl -s http://localhost:80/health", "Testing health via Nginx")
    
    if success and "healthy" in output:
        print("   ✅ Nginx proxy working locally!")
    else:
        print("   ❌ Nginx proxy still not working")
        print("   Let's check the Nginx configuration...")
        
        # Check if our config is actually active
        run_command("sudo nginx -T | grep -A 10 -B 5 'proxy_pass'", "Checking active Nginx config")
        
        # Try alternative approach - create a simple proxy config
        print("\n   Creating simplified proxy configuration...")
        
        simple_config = '''server {
    listen 80 default_server;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}'''
        
        # Write simple config
        with open('/tmp/simple_nginx.conf', 'w') as f:
            f.write(simple_config)
        
        run_command("sudo cp /tmp/simple_nginx.conf /etc/nginx/sites-available/default", 
                   "Installing simplified config")
        run_command("sudo nginx -t", "Testing simplified config")
        run_command("sudo systemctl restart nginx", "Restarting with simplified config")
        
        time.sleep(2)
        success, output = run_command("curl -s http://localhost:80/health", "Re-testing with simplified config")
        
        if success and "healthy" in output:
            print("   ✅ Simplified proxy working!")
        else:
            print("   ❌ Still not working - may need manual debugging")
    
    # Step 5: Final test
    print("\n5️⃣ Final verification...")
    run_command("curl -s http://localhost:80/health", "Final health check")
    run_command("curl -I http://localhost:80/metrics", "Testing metrics endpoint")
    
    print("\n" + "=" * 50)
    print("🎯 NEXT STEP: Test external access")
    print("   Run: curl http://34.59.4.137/health")
    print("   Should return: TrustLayer AI health status")
    print("=" * 50)

if __name__ == "__main__":
    fix_nginx_proxy()