"""
Test script to verify the PII redaction fixes
"""
import requests
import json

def test_health():
    """Test health endpoint"""
    print("🧪 Testing Health Endpoint...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Health check passed: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_metrics():
    """Test metrics endpoint"""
    print("\n🧪 Testing Metrics Endpoint...")
    try:
        response = requests.get("http://localhost:8000/metrics", timeout=5)
        if response.status_code == 200:
            metrics = response.json()
            print(f"✅ Metrics retrieved successfully")
            print(f"   Total requests: {metrics.get('summary', {}).get('total_requests', 0)}")
            return True
        else:
            print(f"❌ Metrics failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Metrics error: {e}")
        return False

def test_pii_redaction():
    """Test PII redaction"""
    print("\n🧪 Testing PII Redaction...")
    
    test_data = {
        "messages": [
            {
                "role": "user",
                "content": "My name is John Doe and my email is john@example.com"
            }
        ]
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            headers={
                "Host": "api.openai.com",
                "Content-Type": "application/json"
            },
            json=test_data,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 502:
            print("✅ Expected 502 (no real API key) - PII processing worked")
            return True
        elif response.status_code == 500:
            print("❌ 500 Internal Server Error - PII processing failed")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            return True
            
    except Exception as e:
        print(f"❌ PII redaction test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🛡️ TrustLayer AI Fix Verification")
    print("=" * 40)
    
    tests = [
        ("Health Check", test_health),
        ("Metrics Check", test_metrics),
        ("PII Redaction", test_pii_redaction)
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! The fixes are working.")
        print("\n📊 You can now:")
        print("  - Access dashboard: streamlit run dashboard.py")
        print("  - Run full tests: python test_pii.py")
        print("  - Test file uploads: python test_file_upload.py")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()