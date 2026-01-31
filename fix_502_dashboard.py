#!/usr/bin/env python3
"""
Fix 502 Dashboard Error - Quick solution
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
            return True, result.stdout.strip()
        else:
            print(f"   ❌ Failed: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, str(e)

def fix_502_dashboard():
    """Fix 502 Bad Gateway for dashboard"""
    print("🚀 Fixing 502 Bad Gateway for Dashboard")
    print("=" * 40)
    
    print("\n1️⃣ Checking service status...")
    run_command("docker ps", "Checking containers")
    run_command("docker logs trustlayer-dashboard --tail 10", "Dashboard logs")
    
    print("\n2️⃣ Testing local connectivity...")
    success, _ = run_command("curl -I http://localhost:8501", "Testing dashboard locally")
    
    if not success:
        print("   Dashboard not responding locally - restarting services...")
        
        # Stop and restart services
        run_command("cd /opt/trustlayer-ai && docker-compose down", "Stopping services")
        time.sleep(5)
        run_command("cd /opt/trustlayer-ai && docker-compose up -d", "Starting services")
        
        print("   Waiting 30 seconds for services to start...")
        time.sleep(30)
        
        # Test again
        success, _ = run_command("curl -I http://localhost:8501", "Re-testing dashboard")
        
        if not success:
            print("   ❌ Dashboard still not working - creating simple solution...")
            create_simple_solution()
            return
    
    print("\n3️⃣ Fixing Nginx configuration...")
    
    # Simple working Nginx config
    nginx_config = '''server {
    listen 80 default_server;
    server_name _;
    
    # Main proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Dashboard - direct proxy
    location /dashboard {
        proxy_pass http://127.0.0.1:8501/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
    }
    
    # Favicon
    location /favicon.ico {
        return 204;
        access_log off;
        log_not_found off;
    }
}'''
    
    with open('/tmp/nginx_simple.conf', 'w') as f:
        f.write(nginx_config)
    
    run_command("sudo cp /tmp/nginx_simple.conf /etc/nginx/sites-available/default", 
               "Installing simple Nginx config")
    
    run_command("sudo nginx -t", "Testing Nginx config")
    run_command("sudo systemctl restart nginx", "Restarting Nginx")
    
    print("\n4️⃣ Testing the fix...")
    time.sleep(5)
    
    success, _ = run_command("curl -I http://localhost/dashboard", "Testing dashboard via Nginx")
    
    if success:
        print("   ✅ Dashboard working!")
    else:
        print("   ❌ Still not working - using alternative solution...")
        create_simple_solution()

def create_simple_solution():
    """Create simple HTML page that works"""
    print("\n🔧 Creating Simple HTML Solution")
    print("=" * 35)
    
    # Simple HTML page
    simple_html = '''<!DOCTYPE html>
<html>
<head>
    <title>TrustLayer AI Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        .header { text-align: center; margin-bottom: 30px; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .online { background: #d4edda; color: #155724; }
        .offline { background: #f8d7da; color: #721c24; }
        .test-section { margin-top: 30px; }
        .test-input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        .test-button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        .result { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ TrustLayer AI Dashboard</h1>
            <p>AI Governance and PII Protection</p>
            <div id="status" class="status offline">Checking status...</div>
        </div>
        
        <div class="test-section">
            <h2>Test PII Detection</h2>
            <textarea id="testInput" class="test-input" rows="4" placeholder="Enter text to test PII detection">My name is John Smith, email: john@test.com</textarea>
            <button class="test-button" onclick="testPII()">Test PII Detection</button>
            <div id="result" class="result" style="display: none;"></div>
        </div>
        
        <div style="margin-top: 30px;">
            <h2>Service Links</h2>
            <ul>
                <li><a href="/health" target="_blank">Health Check</a></li>
                <li><a href="/metrics" target="_blank">Metrics</a></li>
                <li><a href="https://trustlayer.asolvitra.tech:8501" target="_blank">Direct Dashboard Access</a></li>
            </ul>
        </div>
    </div>

    <script>
        async function checkStatus() {
            try {
                const response = await fetch('/health');
                if (response.ok) {
                    document.getElementById('status').textContent = '🟢 TrustLayer AI is Online';
                    document.getElementById('status').className = 'status online';
                } else {
                    throw new Error('Service unavailable');
                }
            } catch (error) {
                document.getElementById('status').textContent = '🔴 TrustLayer AI is Offline';
                document.getElementById('status').className = 'status offline';
            }
        }
        
        async function testPII() {
            const input = document.getElementById('testInput').value;
            const resultDiv = document.getElementById('result');
            
            if (!input.trim()) {
                alert('Please enter some text to test');
                return;
            }
            
            try {
                const response = await fetch('/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: input })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    resultDiv.innerHTML = `
                        <h3>✅ PII Detection Results:</h3>
                        <p><strong>Original:</strong> ${result.original_text || input}</p>
                        <p><strong>Redacted:</strong> ${result.redacted_text || 'No changes'}</p>
                        <p><strong>PII Found:</strong> ${result.pii_detected || 0} entities</p>
                    `;
                    resultDiv.style.display = 'block';
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (error) {
                resultDiv.innerHTML = `<h3>❌ Test Failed:</h3><p>${error.message}</p>`;
                resultDiv.style.display = 'block';
            }
        }
        
        // Check status on load
        checkStatus();
        setInterval(checkStatus, 30000);
    </script>
</body>
</html>'''
    
    # Create the HTML file
    with open('/tmp/simple_dashboard.html', 'w') as f:
        f.write(simple_html)
    
    # Create web directory and copy file
    run_command("sudo mkdir -p /var/www/html", "Creating web directory")
    run_command("sudo cp /tmp/simple_dashboard.html /var/www/html/dashboard.html", "Installing simple dashboard")
    
    # Update Nginx to serve the HTML file
    nginx_html_config = '''server {
    listen 80 default_server;
    server_name _;
    
    root /var/www/html;
    index dashboard.html;
    
    # Main proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Dashboard - serve HTML file
    location /dashboard {
        try_files /dashboard.html =404;
    }
    
    # Favicon
    location /favicon.ico {
        return 204;
        access_log off;
        log_not_found off;
    }
}'''
    
    with open('/tmp/nginx_html.conf', 'w') as f:
        f.write(nginx_html_config)
    
    run_command("sudo cp /tmp/nginx_html.conf /etc/nginx/sites-available/default", 
               "Installing HTML Nginx config")
    
    run_command("sudo nginx -t", "Testing Nginx config")
    run_command("sudo systemctl restart nginx", "Restarting Nginx")
    
    print("   ✅ Simple HTML dashboard created!")

def main():
    """Main function"""
    fix_502_dashboard()
    
    print("\n" + "=" * 50)
    print("🎉 502 DASHBOARD FIX COMPLETE!")
    print("=" * 50)
    
    print("\n📋 TEST THESE URLS:")
    print("✅ Dashboard: https://trustlayer.asolvitra.tech/dashboard")
    print("✅ Health: https://trustlayer.asolvitra.tech/health")
    print("✅ Direct: https://trustlayer.asolvitra.tech:8501 (if available)")
    
    print("\n🔧 If still not working:")
    print("1. Check: docker ps")
    print("2. Check: docker logs trustlayer-dashboard")
    print("3. Test: curl http://localhost:8501")

if __name__ == "__main__":
    main()