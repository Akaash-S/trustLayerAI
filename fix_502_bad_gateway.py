#!/usr/bin/env python3
"""
Fix 502 Bad Gateway Error
Diagnoses and fixes backend connectivity issues causing 502 errors
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

def diagnose_502_error():
    """Diagnose the cause of 502 Bad Gateway errors"""
    print("🚀 Diagnosing 502 Bad Gateway Error")
    print("=" * 50)
    
    print("\n1️⃣ Checking if services are running...")
    
    # Check Docker containers
    success, output = run_command("docker ps", "Checking Docker containers")
    if success:
        if "trustlayer-dashboard" in output and "trustlayer-proxy" in output:
            print("   ✅ Both containers are running")
        else:
            print("   ❌ Some containers are missing")
            print("   Starting services...")
            run_command("cd /opt/trustlayer-ai && docker-compose up -d", "Starting Docker services")
            time.sleep(15)
    
    print("\n2️⃣ Testing local connectivity...")
    
    # Test proxy locally
    success, output = run_command("curl -s http://localhost:8000/health", "Testing proxy locally")
    if success and "healthy" in output:
        print("   ✅ Proxy is responding locally")
    else:
        print("   ❌ Proxy not responding locally")
        return False
    
    # Test dashboard locally
    success, output = run_command("curl -I http://localhost:8501", "Testing dashboard locally")
    if success and "200" in output:
        print("   ✅ Dashboard is responding locally")
    else:
        print("   ❌ Dashboard not responding locally")
        print("   Checking dashboard logs...")
        run_command("docker logs trustlayer-dashboard --tail 10", "Dashboard logs")
        return False
    
    print("\n3️⃣ Checking Nginx configuration...")
    
    # Test Nginx config
    success, output = run_command("sudo nginx -t", "Testing Nginx config")
    if not success:
        print("   ❌ Nginx configuration has errors")
        return False
    
    # Check what Nginx is actually configured to do
    run_command("sudo nginx -T | grep -A 5 -B 5 'location /dashboard'", "Checking dashboard location config")
    
    print("\n4️⃣ Testing Nginx proxy...")
    
    # Test if Nginx can reach the backend
    success, output = run_command("curl -I http://localhost/dashboard", "Testing Nginx proxy to dashboard")
    if success and "200" in output:
        print("   ✅ Nginx proxy working locally")
    elif "502" in output:
        print("   ❌ Nginx getting 502 locally - backend connection issue")
        return False
    else:
        print("   ⚠️  Unexpected response from Nginx")
    
    return True

def fix_502_error():
    """Fix 502 Bad Gateway error"""
    print("\n🔧 Applying 502 Bad Gateway Fix")
    print("=" * 40)
    
    print("\n1️⃣ Stopping all services...")
    run_command("cd /opt/trustlayer-ai && docker-compose down", "Stopping Docker services")
    run_command("sudo systemctl stop nginx", "Stopping Nginx")
    
    print("\n2️⃣ Creating working Nginx configuration...")
    
    # Simple working Nginx config
    nginx_config = '''server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    # Add timeout settings
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    
    # Main TrustLayer AI Proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Error handling
        proxy_intercept_errors on;
        error_page 502 503 504 /50x.html;
    }
    
    # Dashboard - simple proxy without rewrite
    location /dashboard {
        proxy_pass http://127.0.0.1:8501/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Streamlit specific
        proxy_buffering off;
        proxy_cache off;
        
        # Error handling
        proxy_intercept_errors on;
        error_page 502 503 504 /50x.html;
    }
    
    # Static files for dashboard
    location /static/ {
        proxy_pass http://127.0.0.1:8501/static/;
        proxy_set_header Host $host;
        
        # Cache static files
        expires 1d;
        add_header Cache-Control "public";
        
        # Error handling
        proxy_intercept_errors on;
        error_page 502 503 504 /50x.html;
    }
    
    # Error page
    location = /50x.html {
        root /var/www/html;
        internal;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
    }
    
    # Metrics
    location /metrics {
        proxy_pass http://127.0.0.1:8000/metrics;
        proxy_set_header Host $host;
    }
}'''
    
    # Create error page
    error_page = '''<!DOCTYPE html>
<html>
<head>
    <title>TrustLayer AI - Service Unavailable</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .error { color: #d32f2f; }
        .info { color: #1976d2; margin-top: 20px; }
    </style>
</head>
<body>
    <h1 class="error">🛡️ TrustLayer AI - Service Temporarily Unavailable</h1>
    <p>The service is starting up or experiencing issues.</p>
    <p class="info">Please wait a moment and refresh the page.</p>
    <p class="info">If the problem persists, contact your administrator.</p>
</body>
</html>'''
    
    # Install error page
    run_command("sudo mkdir -p /var/www/html", "Creating web directory")
    with open('/tmp/50x.html', 'w') as f:
        f.write(error_page)
    run_command("sudo cp /tmp/50x.html /var/www/html/50x.html", "Installing error page")
    
    # Backup and install Nginx config
    run_command("sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.502fix", 
               "Backing up Nginx config")
    
    with open('/tmp/nginx_502fix.conf', 'w') as f:
        f.write(nginx_config)
    
    run_command("sudo cp /tmp/nginx_502fix.conf /etc/nginx/sites-available/default", 
               "Installing new Nginx config")
    
    print("\n3️⃣ Testing Nginx configuration...")
    success, output = run_command("sudo nginx -t", "Testing Nginx config")
    if not success:
        print("   Restoring backup...")
        run_command("sudo cp /etc/nginx/sites-available/default.backup.502fix /etc/nginx/sites-available/default", 
                   "Restoring backup")
        return False
    
    print("\n4️⃣ Starting services in correct order...")
    
    # Start Docker services first
    run_command("cd /opt/trustlayer-ai && docker-compose up -d", "Starting Docker services")
    
    print("   Waiting 20 seconds for services to fully start...")
    time.sleep(20)
    
    # Verify services are running
    run_command("docker ps", "Checking Docker containers")
    run_command("curl -s http://localhost:8000/health", "Testing proxy")
    run_command("curl -I http://localhost:8501", "Testing dashboard")
    
    # Start Nginx
    run_command("sudo systemctl start nginx", "Starting Nginx")
    
    print("\n5️⃣ Testing the fix...")
    time.sleep(5)
    
    success, output = run_command("curl -I http://localhost/dashboard", "Testing dashboard via Nginx")
    if success and "200" in output:
        print("   ✅ Dashboard working via Nginx!")
    elif "502" in output:
        print("   ❌ Still getting 502 - backend issue")
        return False
    else:
        print("   ⚠️  Unexpected response")
    
    success, output = run_command("curl -s http://localhost/health", "Testing health endpoint")
    if success and "healthy" in output:
        print("   ✅ Health endpoint working!")
    else:
        print("   ❌ Health endpoint not working")
    
    print("\n" + "=" * 50)
    print("🎉 502 BAD GATEWAY FIX COMPLETE!")
    print("=" * 50)
    
    return True

def create_simple_error_page():
    """Create a simple error page for debugging"""
    print("\n📋 Creating Debug Error Page")
    
    debug_page = '''<!DOCTYPE html>
<html>
<head>
    <title>TrustLayer AI Debug</title>
    <meta http-equiv="refresh" content="10">
</head>
<body>
    <h1>🛡️ TrustLayer AI Debug Page</h1>
    <p><strong>Time:</strong> <span id="time"></span></p>
    <p><strong>Status:</strong> Checking services...</p>
    
    <h2>Service Status:</h2>
    <ul>
        <li>Proxy (8000): <a href="/health" target="_blank">Test Health</a></li>
        <li>Dashboard (8501): <a href="http://localhost:8501" target="_blank">Direct Access</a></li>
        <li>Metrics: <a href="/metrics" target="_blank">Test Metrics</a></li>
    </ul>
    
    <h2>Troubleshooting:</h2>
    <ol>
        <li>Check if Docker containers are running</li>
        <li>Verify services respond locally</li>
        <li>Check Nginx configuration</li>
        <li>Review error logs</li>
    </ol>
    
    <script>
        document.getElementById('time').textContent = new Date().toLocaleString();
    </script>
</body>
</html>'''
    
    with open('/tmp/debug.html', 'w') as f:
        f.write(debug_page)
    
    run_command("sudo cp /tmp/debug.html /var/www/html/debug.html", "Installing debug page")
    print("Debug page available at: /debug.html")

def main():
    """Main function"""
    print("TrustLayer AI - 502 Bad Gateway Fix")
    print("Choose your approach:")
    print("1. Diagnose the issue first")
    print("2. Apply comprehensive fix")
    print("3. Create debug page")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        success = diagnose_502_error()
        if success:
            print("\n✅ Diagnosis complete - services appear to be working")
            print("The issue might be with your reverse proxy/load balancer")
        else:
            print("\n❌ Found issues - try option 2 to fix")
    
    elif choice == "2":
        success = fix_502_error()
        if success:
            print("\n✅ Fix applied!")
            print("Try: https://trustlayer.asolvitra.tech/dashboard")
        else:
            print("\n❌ Fix failed - manual intervention needed")
    
    else:  # choice == "3"
        create_simple_error_page()
        print("\n✅ Debug page created!")
        print("Visit: https://trustlayer.asolvitra.tech/debug.html")

if __name__ == "__main__":
    main()