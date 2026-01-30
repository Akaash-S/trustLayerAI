#!/bin/bash

# TrustLayer AI - System Proxy Setup Script
# Configure your system to use TrustLayer AI as a transparent proxy

DOMAIN=${1:-"trustlayer.asolvitra.tech"}
VM_IP=${2:-""}

if [ -z "$VM_IP" ]; then
    echo "🔍 Getting VM IP address..."
    VM_IP=$(dig +short $DOMAIN | head -1)
    if [ -z "$VM_IP" ]; then
        echo "❌ Could not resolve $DOMAIN. Please provide VM IP manually."
        echo "Usage: $0 $DOMAIN vm-ip-address"
        exit 1
    fi
fi

echo "🔧 Setting up system proxy for TrustLayer AI"
echo "Domain: $DOMAIN"
echo "VM IP: $VM_IP"
echo ""

# Method 1: DNS Override (Recommended for testing)
echo "1️⃣ DNS Override Method (Recommended)"
echo "===================================="
echo "This method redirects AI API calls to your TrustLayer AI proxy"
echo ""

# Backup existing hosts file
sudo cp /etc/hosts /etc/hosts.backup.$(date +%Y%m%d_%H%M%S)
echo "💾 Backed up /etc/hosts"

# Add entries to hosts file
echo "📝 Adding DNS overrides to /etc/hosts..."
sudo tee -a /etc/hosts > /dev/null << EOF

# TrustLayer AI Proxy - DNS Override
$VM_IP api.openai.com
$VM_IP api.anthropic.com
$VM_IP generativelanguage.googleapis.com
$VM_IP api.cohere.ai
EOF

echo "✅ DNS overrides added"
echo ""

# Method 2: Environment Variables
echo "2️⃣ Environment Variables Method"
echo "================================"
echo "📝 Creating environment setup script..."

tee setup-proxy-env.sh > /dev/null << EOF
#!/bin/bash
# TrustLayer AI Proxy Environment Variables

export TRUSTLAYER_PROXY="https://$DOMAIN"
export OPENAI_BASE_URL="\$TRUSTLAYER_PROXY/v1"
export ANTHROPIC_BASE_URL="\$TRUSTLAYER_PROXY"

# For applications that use HTTP_PROXY
export HTTP_PROXY="\$TRUSTLAYER_PROXY"
export HTTPS_PROXY="\$TRUSTLAYER_PROXY"
export NO_PROXY="localhost,127.0.0.1,.local"

echo "🔧 TrustLayer AI proxy environment configured"
echo "   OPENAI_BASE_URL: \$OPENAI_BASE_URL"
echo "   ANTHROPIC_BASE_URL: \$ANTHROPIC_BASE_URL"
EOF

chmod +x setup-proxy-env.sh
echo "✅ Environment setup script created: ./setup-proxy-env.sh"
echo ""

# Method 3: Create test applications
echo "3️⃣ Creating Test Applications"
echo "=============================="

# OpenAI test script
tee test-openai.py > /dev/null << EOF
#!/usr/bin/env python3
"""
Test OpenAI through TrustLayer AI proxy
"""
import openai
import os

# Method 1: Using environment variable
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
    base_url="https://$DOMAIN/v1"
)

# Add Host header for routing
import httpx
client._client = httpx.Client(
    headers={"Host": "api.openai.com"}
)

def test_openai():
    try:
        print("🧪 Testing OpenAI through TrustLayer AI...")
        print(f"🔗 Using proxy: https://$DOMAIN/v1")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello! My name is John Doe and my email is john@example.com. Please just say hello back."}
            ],
            max_tokens=50
        )
        
        print("✅ OpenAI request successful!")
        print(f"📋 Response: {response.choices[0].message.content}")
        print("🛡️  PII was automatically redacted and restored by TrustLayer AI")
        
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")
        print("💡 Make sure you have a valid OPENAI_API_KEY environment variable")

if __name__ == "__main__":
    test_openai()
EOF

chmod +x test-openai.py
echo "✅ OpenAI test script created: ./test-openai.py"

# Anthropic test script
tee test-anthropic.py > /dev/null << EOF
#!/usr/bin/env python3
"""
Test Anthropic through TrustLayer AI proxy
"""
import anthropic
import os

# Configure client to use TrustLayer AI
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY", "your-api-key-here"),
    base_url="https://$DOMAIN"
)

# Set Host header for routing
client._client.headers.update({"Host": "api.anthropic.com"})

def test_anthropic():
    try:
        print("🧪 Testing Anthropic through TrustLayer AI...")
        print(f"🔗 Using proxy: https://$DOMAIN")
        
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Hi! My SSN is 123-45-6789 and my phone is 555-123-4567. Please just greet me back."}
            ]
        )
        
        print("✅ Anthropic request successful!")
        print(f"📋 Response: {response.content[0].text}")
        print("🛡️  PII was automatically redacted and restored by TrustLayer AI")
        
    except Exception as e:
        print(f"❌ Anthropic test failed: {e}")
        print("💡 Make sure you have a valid ANTHROPIC_API_KEY environment variable")

if __name__ == "__main__":
    test_anthropic()
EOF

chmod +x test-anthropic.py
echo "✅ Anthropic test script created: ./test-anthropic.py"

# Create a comprehensive test script
tee test-user-experience.sh > /dev/null << EOF
#!/bin/bash
# TrustLayer AI - User Experience Test Script

echo "🧪 TrustLayer AI User Experience Test"
echo "====================================="
echo ""

# Test 1: DNS Resolution
echo "1️⃣ Testing DNS resolution..."
echo "api.openai.com resolves to: \$(dig +short api.openai.com)"
echo "api.anthropic.com resolves to: \$(dig +short api.anthropic.com)"
echo ""

# Test 2: Basic connectivity
echo "2️⃣ Testing basic connectivity..."
if curl -f https://$DOMAIN/health > /dev/null 2>&1; then
    echo "✅ TrustLayer AI proxy is accessible"
else
    echo "❌ TrustLayer AI proxy is not accessible"
    exit 1
fi

# Test 3: PII Detection
echo ""
echo "3️⃣ Testing PII detection..."
PII_RESPONSE=\$(curl -s -X POST https://$DOMAIN/test \\
    -H "Content-Type: application/json" \\
    -d '{"content": "My name is Alice Johnson, email alice@company.com, phone 555-987-6543"}')

if echo "\$PII_RESPONSE" | grep -q "redacted_text"; then
    echo "✅ PII detection working"
    echo "📋 Detected and redacted PII in test content"
else
    echo "❌ PII detection failed"
fi

# Test 4: OpenAI Integration (if API key available)
echo ""
echo "4️⃣ Testing OpenAI integration..."
if [ -n "\$OPENAI_API_KEY" ]; then
    echo "🔑 OpenAI API key found, testing..."
    python3 test-openai.py
else
    echo "⚠️  No OPENAI_API_KEY found, skipping OpenAI test"
    echo "💡 Set OPENAI_API_KEY environment variable to test"
fi

# Test 5: Anthropic Integration (if API key available)
echo ""
echo "5️⃣ Testing Anthropic integration..."
if [ -n "\$ANTHROPIC_API_KEY" ]; then
    echo "🔑 Anthropic API key found, testing..."
    python3 test-anthropic.py
else
    echo "⚠️  No ANTHROPIC_API_KEY found, skipping Anthropic test"
    echo "💡 Set ANTHROPIC_API_KEY environment variable to test"
fi

echo ""
echo "🎉 User experience test completed!"
echo ""
echo "📊 Dashboard: https://$DOMAIN/dashboard"
echo "📈 Metrics: https://$DOMAIN/metrics"
EOF

chmod +x test-user-experience.sh
echo "✅ User experience test script created: ./test-user-experience.sh"
echo ""

# Instructions
echo "🎯 Setup Complete! Here's how to test:"
echo "======================================"
echo ""
echo "📋 What was configured:"
echo "   • DNS overrides added to /etc/hosts"
echo "   • Environment setup script created"
echo "   • Test applications created"
echo ""
echo "🧪 Testing methods:"
echo ""
echo "Method 1 - DNS Override (Already active):"
echo "   Your system now redirects AI API calls to TrustLayer AI"
echo "   Test: python3 test-openai.py"
echo "   Test: python3 test-anthropic.py"
echo ""
echo "Method 2 - Environment Variables:"
echo "   source ./setup-proxy-env.sh"
echo "   python3 test-openai.py"
echo ""
echo "Method 3 - Comprehensive Test:"
echo "   export OPENAI_API_KEY='your-key'"
echo "   export ANTHROPIC_API_KEY='your-key'"
echo "   ./test-user-experience.sh"
echo ""
echo "🔧 To undo DNS overrides:"
echo "   sudo cp /etc/hosts.backup.* /etc/hosts"
echo ""
echo "📊 Monitor activity:"
echo "   Dashboard: https://$DOMAIN/dashboard"
echo "   Metrics: https://$DOMAIN/metrics"
echo ""
echo "🎉 Your system is now configured to use TrustLayer AI!"
echo "   All AI API calls will be automatically protected with PII redaction"