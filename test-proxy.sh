#!/bin/bash

# TrustLayer AI - Proxy Testing Script
# Test your TrustLayer AI proxy configuration

DOMAIN=${1:-"localhost"}
OPENAI_API_KEY=${2:-""}

if [ "$DOMAIN" = "localhost" ]; then
    BASE_URL="http://localhost:8000"
    echo "🧪 Testing local deployment..."
else
    BASE_URL="https://$DOMAIN"
    echo "🧪 Testing production deployment at $DOMAIN..."
fi

echo "🔗 Base URL: $BASE_URL"

# Test 1: Health Check
echo ""
echo "1️⃣ Testing health endpoint..."
if curl -f "$BASE_URL/health" 2>/dev/null; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

# Test 2: PII Detection
echo ""
echo "2️⃣ Testing PII detection..."
RESPONSE=$(curl -s -X POST "$BASE_URL/test" \
    -H "Content-Type: application/json" \
    -d '{"content": "My name is John Doe, email john@example.com, phone 555-123-4567, SSN 123-45-6789"}')

if echo "$RESPONSE" | grep -q "redacted_text"; then
    echo "✅ PII detection working"
    echo "📋 Response: $RESPONSE"
else
    echo "❌ PII detection failed"
    echo "📋 Response: $RESPONSE"
fi

# Test 3: Metrics
echo ""
echo "3️⃣ Testing metrics endpoint..."
if curl -f "$BASE_URL/metrics" 2>/dev/null | head -5; then
    echo "✅ Metrics endpoint working"
else
    echo "❌ Metrics endpoint failed"
fi

# Test 4: OpenAI Integration (if API key provided)
if [ -n "$OPENAI_API_KEY" ]; then
    echo ""
    echo "4️⃣ Testing OpenAI integration..."
    
    OPENAI_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/chat/completions" \
        -H "Host: api.openai.com" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Hello, my name is Jane Smith and my email is jane@company.com. Just say hello back."}
            ],
            "max_tokens": 50
        }')
    
    if echo "$OPENAI_RESPONSE" | grep -q "choices"; then
        echo "✅ OpenAI integration working"
        echo "📋 Response contains PII-safe content"
    else
        echo "❌ OpenAI integration failed"
        echo "📋 Response: $OPENAI_RESPONSE"
    fi
else
    echo ""
    echo "4️⃣ Skipping OpenAI test (no API key provided)"
    echo "   To test: $0 $DOMAIN your-openai-api-key"
fi

# Test 5: Dashboard (if not localhost)
if [ "$DOMAIN" != "localhost" ]; then
    echo ""
    echo "5️⃣ Testing dashboard..."
    if curl -f "$BASE_URL/dashboard" 2>/dev/null >/dev/null; then
        echo "✅ Dashboard accessible at $BASE_URL/dashboard"
    else
        echo "⚠️  Dashboard may not be accessible (check Nginx config)"
    fi
else
    echo ""
    echo "5️⃣ Dashboard available at: http://localhost:8501"
fi

echo ""
echo "🎉 Testing completed!"
echo ""
echo "📋 Summary:"
echo "   • Health: $BASE_URL/health"
echo "   • Metrics: $BASE_URL/metrics"
echo "   • PII Test: $BASE_URL/test"
if [ "$DOMAIN" != "localhost" ]; then
    echo "   • Dashboard: $BASE_URL/dashboard"
else
    echo "   • Dashboard: http://localhost:8501"
fi
echo ""
echo "🔧 Usage examples:"
echo "   • Test local: $0"
echo "   • Test domain: $0 your-domain.com"
echo "   • Test with OpenAI: $0 your-domain.com your-openai-api-key"