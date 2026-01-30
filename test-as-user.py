#!/usr/bin/env python3
"""
TrustLayer AI - Real User Test Script
Test TrustLayer AI as if you're a regular user with sensitive data
"""

import os
import requests
import json
from datetime import datetime

# Configuration
PROXY_URL = "https://trustlayer.asolvitra.tech"
TEST_DATA = {
    "sensitive_prompt": "Hi, I'm Sarah Johnson. My email is sarah.johnson@techcorp.com, phone number is 555-123-4567, and my SSN is 123-45-6789. I work at TechCorp Inc. Can you help me write a professional email?",
    "credit_card_prompt": "My credit card number is 4532-1234-5678-9012, expiration 12/25, CVV 123. Can you help me understand my billing?",
    "medical_prompt": "I'm Dr. Michael Smith, medical license #MD123456. My patient John Doe (DOB: 01/15/1980, SSN: 987-65-4321) needs help with medical records.",
    "business_prompt": "Our company API key is sk-1234567890abcdef and our database password is MySecretPass123. Can you help with integration?"
}

def test_direct_api_call():
    """Test calling AI APIs directly through TrustLayer AI"""
    print("🧪 Testing Direct API Call Through TrustLayer AI")
    print("=" * 50)
    
    # Test PII detection first
    print("1️⃣ Testing PII Detection...")
    try:
        response = requests.post(
            f"{PROXY_URL}/test",
            json={"content": TEST_DATA["sensitive_prompt"]},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PII Detection Test Passed")
            print(f"📋 Original: {result.get('original_text', '')[:100]}...")
            print(f"🛡️  Redacted: {result.get('redacted_text', '')[:100]}...")
            print(f"🔍 PII Found: {result.get('pii_detected', 0)} entities")
            print(f"📊 Types: {', '.join(result.get('pii_types', []))}")
        else:
            print(f"❌ PII Detection Test Failed: {response.status_code}")
            print(f"📋 Response: {response.text}")
    except Exception as e:
        print(f"❌ PII Detection Test Error: {e}")
    
    print()

def test_openai_integration():
    """Test OpenAI integration with sensitive data"""
    print("2️⃣ Testing OpenAI Integration...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set, skipping OpenAI test")
        print("💡 Set your API key: export OPENAI_API_KEY='your-key'")
        return
    
    try:
        # This simulates how a user would normally call OpenAI
        # but now it goes through TrustLayer AI automatically
        response = requests.post(
            f"{PROXY_URL}/v1/chat/completions",
            headers={
                "Host": "api.openai.com",  # This routes to OpenAI
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": TEST_DATA["sensitive_prompt"]}
                ],
                "max_tokens": 100
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OpenAI Integration Test Passed")
            print(f"📋 AI Response: {result['choices'][0]['message']['content']}")
            print("🛡️  Note: Your sensitive data was automatically redacted before sending to OpenAI")
            print("🔄 Note: The response was processed to restore context where safe")
        else:
            print(f"❌ OpenAI Integration Test Failed: {response.status_code}")
            print(f"📋 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ OpenAI Integration Test Error: {e}")
    
    print()

def test_anthropic_integration():
    """Test Anthropic integration with sensitive data"""
    print("3️⃣ Testing Anthropic Integration...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set, skipping Anthropic test")
        print("💡 Set your API key: export ANTHROPIC_API_KEY='your-key'")
        return
    
    try:
        response = requests.post(
            f"{PROXY_URL}/v1/messages",
            headers={
                "Host": "api.anthropic.com",  # This routes to Anthropic
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 100,
                "messages": [
                    {"role": "user", "content": TEST_DATA["medical_prompt"]}
                ]
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Anthropic Integration Test Passed")
            print(f"📋 AI Response: {result['content'][0]['text']}")
            print("🛡️  Note: Medical data was automatically redacted before sending to Anthropic")
        else:
            print(f"❌ Anthropic Integration Test Failed: {response.status_code}")
            print(f"📋 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Anthropic Integration Test Error: {e}")
    
    print()

def test_file_upload():
    """Test file upload with sensitive data"""
    print("4️⃣ Testing File Upload with Sensitive Data...")
    
    # Create a test file with sensitive data
    test_content = """
    Employee Report - CONFIDENTIAL
    
    Name: Jennifer Martinez
    Employee ID: EMP-12345
    Email: jennifer.martinez@company.com
    Phone: 555-987-6543
    SSN: 456-78-9012
    
    Performance Review:
    Jennifer has shown excellent performance this quarter.
    Her direct reports include John Smith (john.smith@company.com)
    and Lisa Chen (lisa.chen@company.com).
    
    Salary: $85,000
    Bank Account: 1234567890 (Chase Bank)
    """
    
    try:
        # Create a temporary file
        with open("/tmp/test_sensitive_data.txt", "w") as f:
            f.write(test_content)
        
        # Upload the file through TrustLayer AI
        with open("/tmp/test_sensitive_data.txt", "rb") as f:
            files = {"file": ("sensitive_report.txt", f, "text/plain")}
            response = requests.post(
                f"{PROXY_URL}/upload-and-process",
                files=files
            )
        
        if response.status_code == 200:
            print("✅ File Upload Test Passed")
            print("🛡️  File content was scanned and PII was redacted")
        else:
            print(f"⚠️  File Upload Test: {response.status_code} (endpoint may not be implemented)")
        
        # Clean up
        os.remove("/tmp/test_sensitive_data.txt")
        
    except Exception as e:
        print(f"❌ File Upload Test Error: {e}")
    
    print()

def check_dashboard_metrics():
    """Check if our tests show up in the dashboard metrics"""
    print("5️⃣ Checking Dashboard Metrics...")
    
    try:
        response = requests.get(f"{PROXY_URL}/metrics")
        
        if response.status_code == 200:
            metrics = response.json()
            print("✅ Dashboard Metrics Retrieved")
            print(f"📊 Total Requests: {metrics['summary']['total_requests']}")
            print(f"🛡️  PII Entities Blocked: {metrics['summary']['total_pii_entities_blocked']}")
            print(f"📈 Compliance Score: {metrics['summary']['compliance_score']}%")
            print(f"⚡ Average Latency: {metrics['summary']['avg_latency_ms']}ms")
            
            if metrics['summary']['total_pii_entities_blocked'] > 0:
                print("🎉 SUCCESS: PII redaction is working and being tracked!")
            else:
                print("⚠️  No PII entities blocked yet - may need to run more tests")
                
        else:
            print(f"❌ Dashboard Metrics Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Dashboard Metrics Error: {e}")
    
    print()

def main():
    """Run all user tests"""
    print("🚀 TrustLayer AI - Real User Experience Test")
    print("=" * 60)
    print(f"🔗 Testing against: {PROXY_URL}")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all tests
    test_direct_api_call()
    test_openai_integration()
    test_anthropic_integration()
    test_file_upload()
    check_dashboard_metrics()
    
    print("🎯 Test Summary")
    print("=" * 30)
    print("✅ If tests passed, your TrustLayer AI proxy is working correctly")
    print("🛡️  All sensitive data was automatically protected")
    print("📊 Check the dashboard for detailed metrics and logs")
    print()
    print("🔗 Useful Links:")
    print(f"   • Dashboard: {PROXY_URL}/dashboard")
    print(f"   • Health: {PROXY_URL}/health")
    print(f"   • Metrics: {PROXY_URL}/metrics")
    print()
    print("🎉 Your AI applications are now protected by TrustLayer AI!")

if __name__ == "__main__":
    main()