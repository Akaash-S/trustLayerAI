#!/bin/bash

echo "🔧 TrustLayer AI - Quick Fix for Docker Issues"
echo "=============================================="

cd /opt/trustlayer-ai

echo "🛑 Stopping any running containers..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker-compose -f docker-compose.simple.yml down 2>/dev/null || true

echo "🧹 Cleaning up Docker..."
docker system prune -f

echo "📝 Creating simplified docker-compose.yml..."
cat > docker-compose.simple.yml << 'EOF'
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
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

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

echo "🔨 Building containers (this may take a few minutes)..."
docker-compose -f docker-compose.simple.yml build --no-cache

echo "🚀 Starting services..."
docker-compose -f docker-compose.simple.yml up -d

echo "⏳ Waiting for services to start..."
sleep 30

echo "🧪 Testing services..."
echo ""

# Test proxy
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Proxy is running: http://localhost:8000"
else
    echo "❌ Proxy is not responding"
fi

# Test dashboard
if curl -s -I http://localhost:8501 > /dev/null; then
    echo "✅ Dashboard is running: http://localhost:8501"
else
    echo "❌ Dashboard is not responding"
fi

# Test nginx
if curl -s http://localhost/health > /dev/null; then
    echo "✅ Load balancer is running: http://localhost"
else
    echo "❌ Load balancer is not responding"
fi

echo ""
echo "📊 Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🎉 Quick fix completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Test health: curl http://localhost/health"
echo "   2. View dashboard: http://localhost:8501"
echo "   3. Check logs: docker-compose -f docker-compose.simple.yml logs -f"
echo ""
echo "🔧 If issues persist:"
echo "   docker-compose -f docker-compose.simple.yml logs proxy"
echo "   docker-compose -f docker-compose.simple.yml logs dashboard"