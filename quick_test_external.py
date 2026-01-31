#!/usr/bin/env python3
"""
Quick External IP Test - Simple 4-step connectivity test
"""

import socket
import requests
import sys
from datetime import datetime

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_external_ip(ip):
    log(f"🧪 Quick Test for External IP: {ip}")
    log("=" * 50)
    
    # Test 1: Basic TCP connectivity
    log("1️⃣ Testing TCP connection to port 8000...")
    try:
        sock = socket.create_connection((ip, 8000), timeout=10)
        sock.close()
        log("   ✅ TCP connection successful")
        tcp_works = True
    except Exception as e:
        log(f"   ❌ TCP connection failed: {e}")
        tcp_works = False
    
    # Test 2: HTTP health check
    log("2️⃣ Testing HTTP health endpoint...")
    try:
        response = requests.get(f"http://{ip}:8000/health", timeout=10)
        if response.status_code == 200:
            log(f"   ✅ Health check successful: {response.json()}")
            health_works = True
        else:
            log(f"   ❌ Health check failed: HTTP {response.status_code}")
            health_works = False
    except Exception as e:
        log(f"   ❌ Health check error: {e}")
        health_works = False
    
    # Test 3: Dashboard port
    log("3️⃣ Testing dashboard port 8501...")
    try:
        sock = socket.create_connection((ip, 8501), timeout=10)
        sock.close()
        log("   ✅ Dashboard port accessible")
        dashboard_tcp = True
    except Exception as e:
        log(f"   ❌ Dashboard port failed: {e}")
        dashboard_tcp = False
    
    # Test 4: Dashboard HTTP
    log("4️⃣ Testing dashboard HTTP...")
    try:
        response = requests.get(f"http://{ip}:8501", timeout=10)
        if response.status_code == 200:
            log("   ✅ Dashboard HTTP successful")
            dashboard_http = True
        else:
            log(f"   ❌ Dashboard HTTP failed: HTTP {response.status_code}")
            dashboard_http = False
    except Exception as e:
        log(f"   ❌ Dashboard HTTP error: {e}")
        dashboard_http = False
    
    # Summary
    log("=" * 50)
    log("📊 QUICK TEST SUMMARY:")
    log(f"   TCP Port 8000:     {'✅ PASS' if tcp_works else '❌ FAIL'}")
    log(f"   Health Endpoint:   {'✅ PASS' if health_works else '❌ FAIL'}")
    log(f"   TCP Port 8501:     {'✅ PASS' if dashboard_tcp else '❌ FAIL'}")
    log(f"   Dashboard HTTP:    {'✅ PASS' if dashboard_http else '❌ FAIL'}")
    
    if not any([tcp_works, health_works, dashboard_tcp, dashboard_http]):
        log("\n❌ ALL TESTS FAILED - This indicates:")
        log("   1. Firewall is still blocking external access")
        log("   2. VM network tags are missing")
        log("   3. Services might not be running on the VM")
        log("\n🔧 NEXT STEPS:")
        log("   1. Verify network tags are added to VM: 'trustlayer-web'")
        log("   2. Check if services are running on VM")
        log("   3. Try SSH tunnel as alternative")
        log(f"\n🚇 SSH TUNNEL (immediate solution):")
        log(f"   ssh -L 8000:localhost:8000 -L 8501:localhost:8501 {ip}")
        log("   Then use proxy: 127.0.0.1:8000")
    elif tcp_works and health_works:
        log("\n🎉 EXTERNAL ACCESS IS WORKING!")
        log(f"\n🔧 Use these proxy settings:")
        log(f"   HTTP Proxy:  {ip}:8000")
        log(f"   HTTPS Proxy: {ip}:8000")
        log(f"   Dashboard:   http://{ip}:8501")
    else:
        log("\n⚠️ PARTIAL SUCCESS - Some services working")
        log("   Check VM services and firewall configuration")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_test_external.py <EXTERNAL_IP>")
        print("Example: python quick_test_external.py 34.59.4.137")
        sys.exit(1)
    
    ip = sys.argv[1]
    test_external_ip(ip)