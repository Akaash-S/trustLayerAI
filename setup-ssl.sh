#!/bin/bash

# TrustLayer AI - SSL Certificate Setup Script
# Run this on your VM to set up SSL certificates and Nginx reverse proxy

set -e

DOMAIN=${1:-"trustlayer.asolvitra.tech"}
EMAIL=${2:-"akaashofficial21@gmail.com"}

if [ -z "$DOMAIN" ]; then
    echo "❌ Please provide your domain name"
    echo "Usage: $0 your-domain.com [email@domain.com]"
    echo "Example: $0 trustlayer.example.com admin@example.com"
    exit 1
fi

echo "🔒 Setting up SSL certificate for domain: $DOMAIN"
echo "📧 Email: $EMAIL"

# Update system
echo "📦 Updating system packages..."
sudo apt update

# Install Nginx and Certbot
echo "🔧 Installing Nginx and Certbot..."
sudo apt install -y nginx certbot python3-certbot-nginx

# Create Nginx configuration for TrustLayer AI
echo "📝 Creating Nginx configuration..."

# First, add rate limiting to the main nginx.conf http block
sudo tee -a /etc/nginx/nginx.conf > /dev/null << 'EOF'

# TrustLayer AI Rate Limiting Configuration
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=dashboard:10m rate=5r/s;
EOF

# Create the site configuration
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
        
        # Optional: Restrict to specific IPs
        # allow 192.168.1.0/24;
        # deny all;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/trustlayer /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

# Start and enable Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Get SSL certificate from Let's Encrypt
echo "📜 Obtaining SSL certificate from Let's Encrypt..."
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL

# Test SSL renewal
echo "🔄 Testing SSL certificate renewal..."
sudo certbot renew --dry-run

# Set up automatic renewal
echo "⏰ Setting up automatic SSL renewal..."
(sudo crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | sudo crontab -

# Update Nginx config to add HTTPS security headers
echo "🔒 Adding HTTPS security configuration..."
sudo tee /etc/nginx/conf.d/trustlayer-ssl.conf > /dev/null << 'EOF'
# TrustLayer AI SSL Security Configuration
# This file contains SSL-specific settings that will be applied after certbot setup

# SSL Security Headers (will be included in HTTPS server block)
map $scheme $hsts_header {
    https "max-age=31536000; includeSubDomains; preload";
}

# Content Security Policy for TrustLayer AI
map $uri $csp_header {
    default "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' wss: ws:;";
    ~^/dashboard "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.plot.ly; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' wss: ws:;";
}
EOF

# Reload Nginx
sudo systemctl reload nginx

echo "✅ SSL setup completed successfully!"
echo "🌐 Your site is now available at: https://$DOMAIN"
echo "🔗 Health check: https://$DOMAIN/health"
echo "📊 Dashboard: https://$DOMAIN/dashboard"

# Test HTTPS
echo "🧪 Testing HTTPS connection..."
sleep 5
if curl -f "https://$DOMAIN/health" > /dev/null 2>&1; then
    echo "✅ HTTPS health check passed"
else
    echo "⚠️  HTTPS health check failed - please check configuration"
    echo "📋 Nginx status:"
    sudo systemctl status nginx --no-pager
    echo "📋 Nginx error log:"
    sudo tail -10 /var/log/nginx/error.log
fi

echo ""
echo "🎉 TrustLayer AI is now secured with SSL!"
echo "📋 Next steps:"
echo "   1. Update your DNS to point $DOMAIN to this server's IP"
echo "   2. Configure your applications to use https://$DOMAIN as proxy"
echo "   3. Test PII redaction with your applications"
echo ""
echo "🔧 Management commands:"
echo "   • Check SSL status: sudo certbot certificates"
echo "   • Renew SSL: sudo certbot renew"
echo "   • Nginx reload: sudo systemctl reload nginx"
echo "   • View logs: sudo tail -f /var/log/nginx/access.log"