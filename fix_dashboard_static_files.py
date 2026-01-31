#!/usr/bin/env python3
"""
Fix Dashboard Static Files
Fixes Nginx configuration to properly serve Streamlit dashboard static files
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
                for line in result.stdout.strip().split('\n')[:3]:
                    print(f"      {line}")
            return True, result.stdout.strip()
        else:
            print(f"   ❌ Failed: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, str(e)

def fix_nginx_for_dashboard():
    """Fix Nginx configuration for Streamlit dashboard static files"""
    print("🚀 Fixing Nginx Configuration for Dashboard Static Files")
    print("=" * 60)
    
    # Create improved Nginx configuration
    nginx_config = '''server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    # Main TrustLayer AI Proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
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
    
    # Dashboard - Main application
    location /dashboard {
        rewrite ^/dashboard(.*) /$1 break;
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Important: Don't buffer responses for Streamlit
        proxy_buffering off;
        proxy_cache off;
    }
    
    # Dashboard static files - CSS, JS, fonts, images
    location /dashboard/static/ {
        rewrite ^/dashboard/static/(.*) /static/$1 break;
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Set correct MIME types for static files
        location ~* \\.css$ {
            proxy_pass http://127.0.0.1:8501;
            add_header Content-Type text/css;
        }
        
        location ~* \\.js$ {
            proxy_pass http://127.0.0.1:8501;
            add_header Content-Type application/javascript;
        }
        
        location ~* \\.(woff|woff2|ttf|eot)$ {
            proxy_pass http://127.0.0.1:8501;
            add_header Content-Type font/woff2;
        }
        
        location ~* \\.(png|jpg|jpeg|gif|ico|svg)$ {
            proxy_pass http://127.0.0.1:8501;
            add_header Content-Type image/png;
        }
        
        # Cache static files
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # Dashboard WebSocket endpoint
    location /dashboard/stream {
        rewrite ^/dashboard/stream(.*) /stream$1 break;
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket specific headers
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Metrics endpoint
    location /metrics {
        proxy_pass http://127.0.0.1:8000/metrics;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Test endpoint
    location /test {
        proxy_pass http://127.0.0.1:8000/test;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}'''
    
    print("\n1️⃣ Backing up current Nginx configuration...")
    run_command("sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d_%H%M%S)", 
               "Creating timestamped backup")
    
    print("\n2️⃣ Creating improved Nginx configuration...")
    # Write config to temporary file
    with open('/tmp/nginx_dashboard_fix.conf', 'w') as f:
        f.write(nginx_config)
    
    # Copy to Nginx sites-available
    run_command("sudo cp /tmp/nginx_dashboard_fix.conf /etc/nginx/sites-available/default", 
               "Installing improved Nginx config")
    
    print("\n3️⃣ Testing Nginx configuration...")
    success, output = run_command("sudo nginx -t", "Testing Nginx config syntax")
    
    if not success:
        print("   ❌ Nginx configuration has errors")
        print("   Restoring backup...")
        run_command("sudo cp /etc/nginx/sites-available/default.backup.* /etc/nginx/sites-available/default", 
                   "Restoring backup")
        return False
    
    print("\n4️⃣ Restarting Nginx...")
    run_command("sudo systemctl restart nginx", "Restarting Nginx service")
    
    print("\n5️⃣ Testing dashboard access...")
    success, output = run_command("curl -I http://localhost/dashboard", "Testing dashboard access")
    
    if success and "200" in output:
        print("   ✅ Dashboard accessible")
    else:
        print("   ⚠️  Dashboard may have issues")
    
    print("\n6️⃣ Testing static file access...")
    run_command("curl -I http://localhost/dashboard/static/css/main.77d1c464.css", "Testing CSS file")
    run_command("curl -I http://localhost/dashboard/static/js/main.d090770a.js", "Testing JS file")
    
    print("\n" + "=" * 60)
    print("🎉 NGINX DASHBOARD FIX COMPLETE!")
    print("=" * 60)
    
    print("\n📋 NEXT STEPS:")
    print("1. Clear your browser cache (Ctrl+Shift+Delete)")
    print("2. Visit: https://trustlayer.asolvitra.tech/dashboard")
    print("3. Check browser console for any remaining errors")
    
    return True

def alternative_simple_fix():
    """Alternative simple fix - direct proxy to dashboard"""
    print("\n🔧 ALTERNATIVE SIMPLE FIX")
    print("=" * 40)
    
    simple_config = '''server {
    listen 80 default_server;
    server_name _;
    
    # Main proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Dashboard - simple direct proxy
    location /dashboard {
        return 301 http://$host:8501/;
    }
}'''
    
    print("Creating simple configuration that redirects /dashboard to port 8501...")
    
    with open('/tmp/nginx_simple.conf', 'w') as f:
        f.write(simple_config)
    
    run_command("sudo cp /tmp/nginx_simple.conf /etc/nginx/sites-available/default", 
               "Installing simple config")
    run_command("sudo nginx -t", "Testing simple config")
    run_command("sudo systemctl restart nginx", "Restarting Nginx")
    
    print("\nWith this config, use:")
    print("- Main proxy: https://trustlayer.asolvitra.tech")
    print("- Dashboard: https://trustlayer.asolvitra.tech:8501")

def main():
    """Main function"""
    print("Choose fix method:")
    print("1. Advanced fix (recommended) - Fixes static file serving")
    print("2. Simple fix - Redirect to port 8501")
    print("3. Both (try advanced first, fallback to simple)")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        success = fix_nginx_for_dashboard()
    elif choice == "2":
        alternative_simple_fix()
        success = True
    else:  # choice == "3" or default
        success = fix_nginx_for_dashboard()
        if not success:
            print("\n⚠️  Advanced fix failed, trying simple fix...")
            alternative_simple_fix()
    
    if success:
        print("\n✅ Configuration updated!")
        print("Clear browser cache and try: https://trustlayer.asolvitra.tech/dashboard")
    else:
        print("\n❌ Fix failed - you may need to configure manually")

if __name__ == "__main__":
    main()