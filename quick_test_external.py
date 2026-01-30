#!/usr/bin/env python3
"""
TrustLayer AI - Quick External IP Test
Simple script to quickly test if external IP is accessible
"""

import requests
import socket
import sys
import json

def quick_test(external_ip):
    """Quick test of external IP accessibility"""
    print(f"🧪 Quick Test: TrustLayer AI on {external_ip}")
    print("=" * 50)
    
    # Test 1: TCP Connection
    print("1. Testing TCP connection...")
    try:
        sock = socket.create_connection((external_ip, 8000), timeout=5)
        sock.close()
        print("   ✅ Port 8000 is reachable")
    except Exception as e:
        print(f"   ❌ Port 8000 not reachable: {e}")
        return False
    
    # Test 2: Health Check
    print("2. Testing health endpoint...")
    try:
        response = requests.get(f"http://{external_ip}:8000/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Health check OK: {health.get('status')}")
        else:
            print(f"   ❌ Health check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 3: PII Detection
    print("3. Testing PII detection...")
    try:
        test_data = {"content": "My name is John Doe"}
        response = requests.post(
            f"http://{external_ip}:8000/test",
            json=test_data,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ PII detection working: {result.get('pii_detected', 0)} entities found")
        else:
            print(f"   ❌ PII test failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ PII test error: {e}")
    
    # Test 4: Dashboard
    print("4. Testing dashboard...")
    try:
        response = requests.get(f"http://{external_ip}:8501", timeout=10)
        if response.status_code == 200:
            print("   ✅ Dashboard accessible")
        else:
            print(f"   ❌ Dashboard failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Dashboard error: {e}")
    
    print("\n🎉 Quick test completed!")
    print(f"\n🔧 If tests passed, use this proxy configuration:")
    print(f"   HTTP Proxy:  {external_ip}:8000")
    print(f"   HTTPS Proxy: {external_ip}:8000")
    print(f"   Dashboard:   http://{external_ip}:8501")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_test_external.py <EXTERNAL_IP>")
        print("Example: python quick_test_external.py 34.123.45.67")
        sys.exit(1)
    
    external_ip = sys.argv[1]
    quick_test(external_ip)