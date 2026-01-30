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
sudo tee /etc/nginx/sites-available/trustlayer > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
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
    }

    # Dashboard location (optional - separate subdomain recommended)
    location /dashboard {
        proxy_pass http://localhost:8501;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
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
sudo tee -a /etc/nginx/sites-available/trustlayer > /dev/null << 'EOF'

# HTTPS server block (added by certbot)
server {
    listen 443 ssl http2;
    server_name DOMAIN_PLACEHOLDER;

    # Additional security headers for HTTPS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # The rest of the configuration will be added by certbot
}
EOF

# Replace placeholder with actual domain
sudo sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /etc/nginx/sites-available/trustlayer

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