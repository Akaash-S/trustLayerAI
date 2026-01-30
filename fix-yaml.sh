#!/bin/bash

# TrustLayer AI - YAML Configuration Fix Script
# Run this if you encounter YAML parsing errors

echo "🔧 TrustLayer AI - YAML Configuration Fix"
echo "=========================================="

cd /opt/trustlayer-ai

echo "📋 Backing up existing files..."
if [ -f "docker-compose.prod.yml" ]; then
    cp docker-compose.prod.yml docker-compose.prod.yml.backup
    echo "✅ Backed up docker-compose.prod.yml"
fi

if [ -f "config.yaml" ]; then
    cp config.yaml config.yaml.backup
    echo "✅ Backed up config.yaml"
fi

echo ""
echo "🔧 Creating corrected docker-compose.prod.yml..."

cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  # TrustLayer AI Proxy
  proxy:
    build: .
    container_name: trustlayer-proxy
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
    environment:
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 90s

  # Streamlit Dashboard
  dashboard:
    build: .
    container_name: trustlayer-dashboard
    ports:
      - "8501:8501"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./dashboard.py:/app/dashboard.py:ro
    environment:
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
    depends_on:
      - proxy
    restart: unless-stopped
    command: streamlit run dashboard.py --server.address 0.0.0.0 --server.port 8501 --server.headless true

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: trustlayer-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - proxy
      - dashboard
    restart: unless-stopped
EOF

echo "✅ Created corrected docker-compose.prod.yml"

echo ""
echo "🧪 Validating YAML syntax..."

if python3 -c "import yaml; yaml.safe_load(open('docker-compose.prod.yml'))" 2>/dev/null; then
    echo "✅ docker-compose.prod.yml is valid!"
else
    echo "❌ docker-compose.prod.yml still has issues"
    exit 1
fi

if [ -f "config.yaml" ]; then
    if python3 -c "import yaml; yaml.safe_load(open('config.yaml'))" 2>/dev/null; then
        echo "✅ config.yaml is valid!"
    else
        echo "⚠️  config.yaml has syntax issues - please check manually"
    fi
fi

echo ""
echo "🚀 Ready to start services:"
echo "   docker-compose -f docker-compose.prod.yml build"
echo "   docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "📋 If you still have issues:"
echo "   1. Check that all TrustLayer AI files are present: ls -la"
echo "   2. Verify Redis IP in config.yaml"
echo "   3. Check Docker is running: sudo systemctl status docker"