#!/usr/bin/env python3
"""
Fix Streamlit Dashboard - Complete solution for static file issues
This addresses the 403 Forbidden and MIME type issues with Streamlit dashboard
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

def fix_streamlit_config():
    """Fix Streamlit configuration for proper static file serving"""
    print("🚀 Fixing Streamlit Dashboard Configuration")
    print("=" * 60)
    
    print("\n1️⃣ Stopping current services...")
    run_command("docker-compose down", "Stopping Docker services")
    
    print("\n2️⃣ Creating Streamlit configuration...")
    
    # Create Streamlit config directory
    run_command("mkdir -p /opt/trustlayer-ai/.streamlit", "Creating Streamlit config directory")
    
    # Create Streamlit config file
    streamlit_config = '''[server]
port = 8501
address = "0.0.0.0"
baseUrlPath = "/dashboard"
enableCORS = false
enableXsrfProtection = false

[browser]
serverAddress = "trustlayer.asolvitra.tech"
serverPort = 443

[theme]
base = "dark"
primaryColor = "#FF6B6B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"

[client]
toolbarMode = "minimal"
showErrorDetails = true

[logger]
level = "info"
'''
    
    with open('/tmp/streamlit_config.toml', 'w') as f:
        f.write(streamlit_config)
    
    run_command("sudo cp /tmp/streamlit_config.toml /opt/trustlayer-ai/.streamlit/config.toml", 
               "Installing Streamlit config")
    
    print("\n3️⃣ Updating Docker Compose for Streamlit...")
    
    # Read current docker-compose.yml
    try:
        with open('/opt/trustlayer-ai/docker-compose.yml', 'r') as f:
            docker_compose = f.read()
    except:
        print("   ❌ Could not read docker-compose.yml")
        return False
    
    # Update docker-compose.yml to include Streamlit config
    updated_compose = docker_compose.replace(
        'command: streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0',
        '''command: streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0 --server.baseUrlPath=/dashboard
    volumes:
      - ./.streamlit:/app/.streamlit'''
    )
    
    with open('/tmp/docker-compose-updated.yml', 'w') as f:
        f.write(updated_compose)
    
    run_command("sudo cp /tmp/docker-compose-updated.yml /opt/trustlayer-ai/docker-compose.yml", 
               "Updating Docker Compose")
    
    print("\n4️⃣ Creating comprehensive Nginx configuration...")
    
    nginx_config = '''server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
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
    
    # Dashboard root - redirect to proper path
    location = /dashboard {
        return 301 $scheme://$host/dashboard/;
    }
    
    # Dashboard main application
    location /dashboard/ {
        proxy_pass http://127.0.0.1:8501/dashboard/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Streamlit specific settings
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400;
    }
    
    # Static files with correct MIME types
    location /static/ {
        proxy_pass http://127.0.0.1:8501/static/;
        proxy_set_header Host $host;
        
        # CSS files
        location ~* \\.css$ {
            proxy_pass http://127.0.0.1:8501;
            proxy_hide_header Content-Type;
            add_header Content-Type "text/css" always;
        }
        
        # JavaScript files
        location ~* \\.js$ {
            proxy_pass http://127.0.0.1:8501;
            proxy_hide_header Content-Type;
            add_header Content-Type "application/javascript" always;
        }
        
        # Font files
        location ~* \\.(woff|woff2|ttf|eot)$ {
            proxy_pass http://127.0.0.1:8501;
            proxy_hide_header Content-Type;
            add_header Content-Type "font/woff2" always;
        }
        
        # Image files
        location ~* \\.(png|jpg|jpeg|gif|ico|svg)$ {
            proxy_pass http://127.0.0.1:8501;
            proxy_hide_header Content-Type;
            add_header Content-Type "image/png" always;
        }
        
        # Cache static files
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # WebSocket endpoint for Streamlit
    location /_stcore/stream {
        proxy_pass http://127.0.0.1:8501/_stcore/stream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket headers
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
    
    # Backup and install new config
    run_command("sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d_%H%M%S)", 
               "Backing up Nginx config")
    
    with open('/tmp/nginx_streamlit_fix.conf', 'w') as f:
        f.write(nginx_config)
    
    run_command("sudo cp /tmp/nginx_streamlit_fix.conf /etc/nginx/sites-available/default", 
               "Installing new Nginx config")
    
    print("\n5️⃣ Testing and restarting services...")
    
    # Test Nginx config
    success, output = run_command("sudo nginx -t", "Testing Nginx configuration")
    if not success:
        print("   ❌ Nginx config failed, restoring backup")
        run_command("sudo cp /etc/nginx/sites-available/default.backup.* /etc/nginx/sites-available/default", 
                   "Restoring backup")
        return False
    
    # Restart Nginx
    run_command("sudo systemctl restart nginx", "Restarting Nginx")
    
    # Start Docker services
    run_command("cd /opt/trustlayer-ai && docker-compose up -d", "Starting Docker services")
    
    print("\n6️⃣ Waiting for services to start...")
    time.sleep(15)
    
    print("\n7️⃣ Testing dashboard access...")
    run_command("curl -I http://localhost/dashboard/", "Testing dashboard")
    run_command("curl -I http://localhost/static/css/main.77d1c464.css", "Testing CSS file")
    
    print("\n" + "=" * 60)
    print("🎉 STREAMLIT DASHBOARD FIX COMPLETE!")
    print("=" * 60)
    
    return True

def create_simple_dashboard():
    """Create a simple custom dashboard that works better with reverse proxy"""
    print("\n🔧 ALTERNATIVE: Creating Simple Custom Dashboard")
    print("=" * 50)
    
    simple_dashboard = '''import streamlit as st
import requests
import json
from datetime import datetime
import time

# Configure Streamlit page
st.set_page_config(
    page_title="TrustLayer AI Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to fix styling issues
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #262730;
        border: 1px solid #464646;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def get_metrics():
    """Get metrics from TrustLayer AI"""
    try:
        response = requests.get("http://localhost:8000/metrics", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {
        "summary": {
            "total_requests": 0,
            "pii_detected": 0,
            "blocked_requests": 0
        },
        "recent_activity": []
    }

def main():
    st.title("🛡️ TrustLayer AI Dashboard")
    st.markdown("Real-time AI governance and PII protection monitoring")
    
    # Get metrics
    metrics = get_metrics()
    summary = metrics.get("summary", {})
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", summary.get("total_requests", 0))
    
    with col2:
        st.metric("PII Detected", summary.get("pii_detected", 0))
    
    with col3:
        st.metric("Blocked Requests", summary.get("blocked_requests", 0))
    
    with col4:
        st.metric("Status", "🟢 Active")
    
    # Recent activity
    st.subheader("Recent Activity")
    
    recent = metrics.get("recent_activity", [])
    if recent:
        for activity in recent[-10:]:  # Show last 10
            with st.expander(f"Request at {activity.get('timestamp', 'Unknown')}"):
                st.json(activity)
    else:
        st.info("No recent activity")
    
    # Test section
    st.subheader("Test PII Detection")
    
    test_text = st.text_area("Enter text to test PII detection:", 
                            "My name is John Smith, email: john@test.com")
    
    if st.button("Test PII Detection"):
        try:
            response = requests.post("http://localhost:8000/test", 
                                   json={"content": test_text}, 
                                   timeout=10)
            if response.status_code == 200:
                result = response.json()
                st.success("PII Detection Test Results:")
                st.write("**Original:**", result.get("original_text", ""))
                st.write("**Redacted:**", result.get("redacted_text", ""))
                st.write("**PII Found:**", result.get("pii_detected", 0), "entities")
            else:
                st.error(f"Test failed: {response.status_code}")
        except Exception as e:
            st.error(f"Test error: {e}")
    
    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()
'''
    
    # Write simple dashboard
    with open('/tmp/simple_dashboard.py', 'w') as f:
        f.write(simple_dashboard)
    
    run_command("sudo cp /tmp/simple_dashboard.py /opt/trustlayer-ai/simple_dashboard.py", 
               "Installing simple dashboard")
    
    # Update docker-compose to use simple dashboard
    simple_compose = '''version: '3.8'

services:
  proxy:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    restart: unless-stopped
    container_name: trustlayer-proxy

  dashboard:
    build: .
    ports:
      - "8501:8501"
    command: streamlit run simple_dashboard.py --server.port=8501 --server.address=0.0.0.0
    depends_on:
      - proxy
    restart: unless-stopped
    container_name: trustlayer-dashboard

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    container_name: trustlayer-redis
'''
    
    with open('/tmp/simple_compose.yml', 'w') as f:
        f.write(simple_compose)
    
    run_command("sudo cp /tmp/simple_compose.yml /opt/trustlayer-ai/docker-compose.yml", 
               "Installing simple compose")
    
    print("Simple dashboard created. Restart services to use it.")

def main():
    """Main function"""
    print("TrustLayer AI Dashboard Fix Options:")
    print("1. Fix Streamlit configuration (comprehensive)")
    print("2. Create simple custom dashboard")
    print("3. Use direct port access (bypass Nginx)")
    
    choice = input("Choose option (1-3): ").strip()
    
    if choice == "1":
        success = fix_streamlit_config()
        if success:
            print("\n✅ Streamlit fix applied!")
            print("Clear browser cache and visit: https://trustlayer.asolvitra.tech/dashboard")
        else:
            print("\n❌ Fix failed")
    
    elif choice == "2":
        create_simple_dashboard()
        print("\n✅ Simple dashboard created!")
        print("Restart services and visit: https://trustlayer.asolvitra.tech/dashboard")
    
    else:  # choice == "3"
        print("\n🔧 DIRECT ACCESS SOLUTION:")
        print("Instead of fixing Nginx, use direct port access:")
        print("- Dashboard: https://trustlayer.asolvitra.tech:8501")
        print("- This bypasses all Nginx proxy issues")
        print("\nMake sure port 8501 is open in your firewall rules.")

if __name__ == "__main__":
    main()