#!/bin/bash

# TrustLayer AI - Simple Nginx Start Script
# A simple approach to get Nginx running

set -e

DOMAIN=${1:-"localhost"}

echo "🚀 Simple Nginx setup for TrustLayer AI"
echo "Domain: $DOMAIN"

# Stop any existing web servers
echo "🛑 Stopping conflicting services..."
sudo systemctl stop apache2 2>/dev/null || echo "Apache not running"
sudo systemctl stop nginx 2>/dev/null || echo "Nginx not running"
sudo pkill -f nginx 2>/dev/null || echo "No nginx processes to kill"

# Install nginx if not installed
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing Nginx..."
    sudo apt update
    sudo apt install -y nginx
fi

# Create a minimal working configuration
echo "📝 Creating minimal Nginx configuration..."
sudo tee /etc/nginx/sites-available/trustlayer > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        client_max_body_size 100M;
    }

    location /dashboard {
        proxy_pass http://localhost:8501;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
EOF

# Remove default site and enable ours
echo "🔧 Configuring sites..."
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-enabled/trustlayer
sudo ln -s /etc/nginx/sites-available/trustlayer /etc/nginx/sites-enabled/

# Test configuration
echo "🧪 Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Configuration is valid"
else
    echo "❌ Configuration test failed"
    exit 1
fi

# Start nginx
echo "🚀 Starting Nginx..."
if sudo systemctl start nginx; then
    echo "✅ Nginx started successfully"
    sudo systemctl enable nginx
    echo "✅ Nginx enabled for auto-start"
else
    echo "❌ Failed to start Nginx"
    echo "📋 Checking logs..."
    sudo journalctl -u nginx --no-pager --lines=10
    exit 1
fi

# Test the setup
echo "🧪 Testing the setup..."
sleep 2

if curl -f "http://localhost/health" 2>/dev/null; then
    echo "✅ Proxy is working through Nginx"
else
    echo "⚠️  Proxy test failed - make sure TrustLayer AI containers are running"
    echo "💡 Run: ./build-and-run.sh your-project-id"
fi

echo ""
echo "🎉 Nginx setup complete!"
echo "📋 Status:"
sudo systemctl status nginx --no-pager

echo ""
echo "🔗 Test URLs:"
echo "   • Health: http://$DOMAIN/health"
echo "   • Dashboard: http://$DOMAIN/dashboard"
echo "   • Proxy: http://$DOMAIN/"

echo ""
echo "🔒 Next steps for SSL:"
echo "   1. Make sure your domain points to this server"
echo "   2. Run: sudo certbot --nginx -d $DOMAIN"
echo "   3. Test HTTPS: curl https://$DOMAIN/health"