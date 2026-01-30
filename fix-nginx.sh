#!/bin/bash

# TrustLayer AI - Fix Nginx Configuration Script
# Run this if you're getting nginx configuration errors

set -e

DOMAIN=${1:-""}

if [ -z "$DOMAIN" ]; then
    echo "❌ Please provide your domain name"
    echo "Usage: $0 your-domain.com"
    exit 1
fi

echo "🔧 Fixing Nginx configuration for domain: $DOMAIN"

# Stop nginx to avoid conflicts
sudo systemctl stop nginx 2>/dev/null || true

# Backup existing configuration
echo "💾 Backing up existing configuration..."
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
sudo cp /etc/nginx/sites-available/trustlayer /etc/nginx/sites-available/trustlayer.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Remove any existing rate limit zones from nginx.conf to avoid duplicates
echo "🧹 Cleaning up existing configuration..."
sudo sed -i '/# TrustLayer AI Rate Limiting Configuration/,/limit_req_zone.*dashboard/d' /etc/nginx/nginx.conf 2>/dev/null || true

# Add rate limiting zones to the http block in nginx.conf
echo "📝 Adding rate limiting configuration to nginx.conf..."
sudo sed -i '/http {/a\\n\t# TrustLayer AI Rate Limiting Configuration\n\tlimit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;\n\tlimit_req_zone $binary_remote_addr zone=dashboard:10m rate=5r/s;\n' /etc/nginx/nginx.conf

# Create clean site configuration
echo "📝 Creating clean site configuration..."
sudo tee /etc/nginx/sites-available/trustlayer > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Apply rate limiting
    limit_req zone=api burst=20 nodelay;

    # Proxy to TrustLayer AI
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Handle large requests (for file uploads)
        client_max_body_size 100M;
        
        # Buffer settings for better performance
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Dashboard location (separate rate limit)
    location /dashboard {
        limit_req zone=dashboard burst=10 nodelay;
        
        proxy_pass http://localhost:8501;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Streamlit specific settings
        proxy_read_timeout 86400;
    }

    # Health check endpoint (no rate limiting for monitoring)
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
        
        # Quick health check settings
        proxy_connect_timeout 5s;
        proxy_send_timeout 5s;
        proxy_read_timeout 5s;
    }

    # Metrics endpoint (limited access)
    location /metrics {
        limit_req zone=api burst=5 nodelay;
        proxy_pass http://localhost:8000/metrics;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/trustlayer /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
echo "🧪 Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration test failed"
    echo "📋 Restoring backup..."
    sudo cp /etc/nginx/nginx.conf.backup.* /etc/nginx/nginx.conf 2>/dev/null || true
    sudo cp /etc/nginx/sites-available/trustlayer.backup.* /etc/nginx/sites-available/trustlayer 2>/dev/null || true
    exit 1
fi

# Start nginx
echo "🚀 Starting Nginx..."
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running successfully"
else
    echo "❌ Nginx failed to start"
    echo "📋 Checking logs..."
    sudo journalctl -u nginx --no-pager --lines=10
    exit 1
fi

echo ""
echo "🎉 Nginx configuration fixed successfully!"
echo "🔗 Test your site: http://$DOMAIN/health"
echo ""
echo "🔒 Next steps:"
echo "   1. Test the configuration: curl http://$DOMAIN/health"
echo "   2. Set up SSL: sudo certbot --nginx -d $DOMAIN"
echo "   3. Test HTTPS: curl https://$DOMAIN/health"
echo ""
echo "📊 Useful commands:"
echo "   • Check status: sudo systemctl status nginx"
echo "   • View logs: sudo tail -f /var/log/nginx/error.log"
echo "   • Test config: sudo nginx -t"
echo "   • Reload: sudo systemctl reload nginx"