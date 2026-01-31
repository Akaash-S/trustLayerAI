#!/usr/bin/env python3
"""
Final Dashboard Fix - Complete solution for static file and MIME type issues
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
                for line in result.stdout.strip().split('\n')[:2]:
                    print(f"      {line}")
            return True, result.stdout.strip()
        else:
            print(f"   ❌ Failed: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, str(e)

def final_dashboard_fix():
    """Apply final comprehensive fix for dashboard"""
    print("🚀 Applying Final Dashboard Fix")
    print("=" * 50)
    
    print("\n1️⃣ Stopping services...")
    run_command("cd /opt/trustlayer-ai && docker-compose down", "Stopping Docker services")
    
    print("\n2️⃣ Creating Streamlit config directory...")
    run_command("mkdir -p /opt/trustlayer-ai/.streamlit", "Creating config directory")
    
    print("\n3️⃣ Installing Streamlit configuration...")
    streamlit_config = '''[server]
port = 8501
address = "0.0.0.0"
baseUrlPath = ""
enableCORS = false
enableXsrfProtection = false
maxUploadSize = 200

[browser]
gatherUsageStats = false
showErrorDetails = true

[theme]
base = "light"
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[client]
toolbarMode = "minimal"
showErrorDetails = true

[logger]
level = "info"

[global]
developmentMode = false
'''
    
    with open('/tmp/streamlit_config.toml', 'w') as f:
        f.write(streamlit_config)
    
    run_command("sudo cp /tmp/streamlit_config.toml /opt/trustlayer-ai/.streamlit/config.toml", 
               "Installing Streamlit config")
    
    print("\n4️⃣ Creating working Nginx configuration...")
    
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
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        client_max_body_size 10M;
    }
    
    # Dashboard redirect - simple solution
    location = /dashboard {
        return 301 $scheme://$host:8501/;
    }
    
    # Alternative dashboard path
    location /dashboard/ {
        return 301 $scheme://$host:8501/;
    }
}'''
    
    with open('/tmp/nginx_final.conf', 'w') as f:
        f.write(nginx_config)
    
    # Backup and install
    run_command("sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.final", 
               "Backing up Nginx config")
    
    run_command("sudo cp /tmp/nginx_final.conf /etc/nginx/sites-available/default", 
               "Installing final Nginx config")
    
    print("\n5️⃣ Testing and restarting services...")
    
    success, _ = run_command("sudo nginx -t", "Testing Nginx config")
    if not success:
        print("   Restoring backup...")
        run_command("sudo cp /etc/nginx/sites-available/default.backup.final /etc/nginx/sites-available/default", 
                   "Restoring backup")
        return False
    
    run_command("sudo systemctl restart nginx", "Restarting Nginx")
    
    print("\n6️⃣ Starting Docker services with new config...")
    run_command("cd /opt/trustlayer-ai && docker-compose up -d", "Starting services")
    
    print("\n7️⃣ Waiting for services to start...")
    time.sleep(20)
    
    print("\n8️⃣ Testing access...")
    run_command("curl -I http://localhost:8501", "Testing direct dashboard access")
    run_command("curl -I http://localhost/dashboard", "Testing dashboard redirect")
    
    print("\n" + "=" * 50)
    print("🎉 FINAL DASHBOARD FIX COMPLETE!")
    print("=" * 50)
    
    print("\n📋 DASHBOARD ACCESS OPTIONS:")
    print("1. Direct access: https://trustlayer.asolvitra.tech:8501")
    print("2. Via redirect: https://trustlayer.asolvitra.tech/dashboard")
    print("   (This will redirect to option 1)")
    
    print("\n🔧 RECOMMENDED:")
    print("Use direct access: https://trustlayer.asolvitra.tech:8501")
    print("This bypasses all proxy issues and works reliably.")
    
    return True

def create_minimal_dashboard():
    """Create a minimal dashboard that works without static files"""
    print("\n🔧 Creating Minimal Dashboard (No Static Files)")
    print("=" * 50)
    
    minimal_dashboard = '''import streamlit as st
import requests
import json
from datetime import datetime
import time

# Minimal page config - no custom styling
st.set_page_config(
    page_title="TrustLayer AI Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# No custom CSS - use Streamlit defaults only
st.title("🛡️ TrustLayer AI Dashboard")
st.markdown("**Real-time AI governance and PII protection monitoring**")

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
            "total_pii_entities_blocked": 0,
            "avg_latency_ms": 0,
            "compliance_score": 100
        }
    }

def test_connection():
    """Test connection to proxy"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    # Connection status
    if test_connection():
        st.success("✅ Connected to TrustLayer AI Proxy")
    else:
        st.error("❌ Cannot connect to TrustLayer AI Proxy")
        st.stop()
    
    # Get metrics
    metrics = get_metrics()
    summary = metrics.get("summary", {})
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", summary.get("total_requests", 0))
    
    with col2:
        st.metric("PII Blocked", summary.get("total_pii_entities_blocked", 0))
    
    with col3:
        st.metric("Avg Latency", f"{summary.get('avg_latency_ms', 0):.1f}ms")
    
    with col4:
        st.metric("Compliance", f"{summary.get('compliance_score', 100):.1f}%")
    
    # Test section
    st.subheader("Test PII Detection")
    
    test_text = st.text_area("Enter text to test:", 
                            "My name is John Smith, email: john@test.com")
    
    if st.button("Test PII Detection"):
        try:
            response = requests.post("http://localhost:8000/test", 
                                   json={"content": test_text}, 
                                   timeout=10)
            if response.status_code == 200:
                result = response.json()
                st.success("✅ PII Detection Results:")
                st.write("**Original:**", result.get("original_text", ""))
                st.write("**Redacted:**", result.get("redacted_text", ""))
                st.write("**PII Found:**", result.get("pii_detected", 0), "entities")
            else:
                st.error(f"Test failed: {response.status_code}")
        except Exception as e:
            st.error(f"Test error: {e}")
    
    # Auto-refresh
    if st.checkbox("Auto-refresh (10s)"):
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()
'''
    
    with open('/tmp/minimal_dashboard.py', 'w') as f:
        f.write(minimal_dashboard)
    
    run_command("sudo cp /tmp/minimal_dashboard.py /opt/trustlayer-ai/minimal_dashboard.py", 
               "Installing minimal dashboard")
    
    print("✅ Minimal dashboard created!")
    print("To use it, update docker-compose.yml to run minimal_dashboard.py instead")

def main():
    """Main function"""
    print("TrustLayer AI Dashboard Final Fix")
    print("Choose your approach:")
    print("1. Apply comprehensive fix (recommended)")
    print("2. Create minimal dashboard (fallback)")
    print("3. Use direct port access (simplest)")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        success = final_dashboard_fix()
        if success:
            print("\n✅ Fix applied! Try these URLs:")
            print("- https://trustlayer.asolvitra.tech:8501 (direct)")
            print("- https://trustlayer.asolvitra.tech/dashboard (redirect)")
        else:
            print("\n❌ Fix failed")
    
    elif choice == "2":
        create_minimal_dashboard()
        print("\n✅ Minimal dashboard created!")
        print("Update docker-compose.yml to use minimal_dashboard.py")
    
    else:  # choice == "3"
        print("\n🔧 DIRECT ACCESS SOLUTION:")
        print("Simply use: https://trustlayer.asolvitra.tech:8501")
        print("This bypasses all static file issues completely.")
        print("\nMake sure port 8501 is open in your firewall.")

if __name__ == "__main__":
    main()