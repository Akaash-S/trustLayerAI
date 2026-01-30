#!/bin/bash

# TrustLayer AI - Build and Run Script for Compute Engine VM
# This script builds the Docker image and runs the containers

set -e

PROJECT_ID=${1:-"your-gcp-project-id"}

if [ "$PROJECT_ID" = "your-gcp-project-id" ]; then
    echo "❌ Please provide your GCP project ID as an argument"
    echo "Usage: $0 your-project-id"
    exit 1
fi

echo "🚀 Building and running TrustLayer AI containers"
echo "Project: $PROJECT_ID"
echo "Redis Endpoint: 10.97.237.131:6379"

# Stop existing containers if running
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t trustlayer-ai:latest .

# Tag for GCR (optional, for future pushes)
docker tag trustlayer-ai:latest gcr.io/$PROJECT_ID/trustlayer-ai:latest

# Update docker-compose with project ID
echo "📝 Updating docker-compose configuration..."
sed "s/PROJECT_ID/$PROJECT_ID/g" gcp-deployment/docker-compose.production.yml > docker-compose.yml

# Start the containers
echo "🚀 Starting containers..."
docker-compose up -d

# Wait for containers to start
echo "⏳ Waiting for containers to start..."
sleep 30

# Check container status
echo "📊 Container status:"
docker-compose ps

# Test health endpoints
echo "🧪 Testing health endpoints..."
sleep 10

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Proxy health check passed"
else
    echo "❌ Proxy health check failed"
    echo "📋 Proxy logs:"
    docker-compose logs proxy --tail=10
fi

if curl -f http://localhost:8501 > /dev/null 2>&1; then
    echo "✅ Dashboard is accessible"
else
    echo "❌ Dashboard is not accessible"
    echo "📋 Dashboard logs:"
    docker-compose logs dashboard --tail=10
fi

echo ""
echo "🎉 TrustLayer AI is now running!"
echo "📋 Services:"
echo "   • Proxy: http://localhost:8000"
echo "   • Health: http://localhost:8000/health"
echo "   • Metrics: http://localhost:8000/metrics"
echo "   • Dashboard: http://localhost:8501"
echo "   • Redis: 10.97.237.131:6379"

echo ""
echo "📊 Management commands:"
echo "   • View logs: docker-compose logs -f"
echo "   • Restart: docker-compose restart"
echo "   • Stop: docker-compose down"
echo "   • Update: $0 $PROJECT_ID"