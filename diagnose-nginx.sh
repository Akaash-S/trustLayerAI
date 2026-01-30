#!/bin/bash

# TrustLayer AI - Nginx Diagnostic and Fix Script
# Diagnoses and fixes common Nginx startup issues

set -e

echo "🔍 Diagnosing Nginx startup issues..."

# Check what's using port 80
echo ""
echo "1️⃣ Checking what's using port 80..."
PORT_80_USAGE=$(sudo netstat -tlnp | grep :80 || true)
if [ -n "$PORT_80_USAGE" ]; then
    echo "⚠️  Port 80 is in use:"
    echo "$PORT_80_USAGE"
    
    # Check if it's Apache
    if echo "$PORT_80_USAGE" | grep -q apache; then
        echo "🔧 Apache is running on port 80. Stopping Apache..."
        sudo systemctl stop apache2 2>/dev/null || true
        sudo systemctl disable apache2 2>/dev/null || true
        echo "✅ Apache stopped and disabled"
    fi
    
    # Check if it's another nginx process
    if echo "$PORT_80_USAGE" | grep -q nginx; then
        echo "🔧 Another nginx process is running. Killing it..."
        sudo pkill -f nginx || true
        sleep 2
        echo "✅ Nginx processes killed"
    fi
else
    echo "✅ Port 80 is available"
fi

# Check what's using port 443
echo ""
echo "2️⃣ Checking what's using port 443..."
PORT_443_USAGE=$(sudo netstat -tlnp | grep :443 || true)
if [ -n "$PORT_443_USAGE" ]; then
    echo "⚠️  Port 443 is in use:"
    echo "$PORT_443_USAGE"
else
    echo "✅ Port 443 is available"
fi

# Check Nginx error logs
echo ""
echo "3️⃣ Checking Nginx error logs..."
if [ -f /var/log/nginx/error.log ]; then
    echo "📋 Recent Nginx errors:"
    sudo tail -10 /var/log/nginx/error.log || echo "No recent errors"
else
    echo "📋 No error log found"
fi

# Check systemd journal for nginx
echo ""
echo "4️⃣ Checking systemd journal for nginx..."
echo "📋 Recent nginx service logs:"
sudo journalctl -u nginx --no-pager --lines=10 || echo "No recent logs"

# Check nginx configuration files
echo ""
echo "5️⃣ Checking Nginx configuration..."
echo "📋 Main config test:"
sudo nginx -t

echo "📋 Enabled sites:"
ls -la /etc/nginx/sites-enabled/ || echo "No sites enabled"

# Check if nginx binary exists and permissions
echo ""
echo "6️⃣ Checking Nginx binary and permissions..."
NGINX_BIN=$(which nginx)
echo "📋 Nginx binary: $NGINX_BIN"
ls -la "$NGINX_BIN"

# Check nginx user and permissions
echo "📋 Nginx user and group:"
id www-data 2>/dev/null || echo "www-data user not found"

# Check nginx directories permissions
echo "📋 Nginx directory permissions:"
ls -la /etc/nginx/
ls -la /var/log/nginx/ 2>/dev/null || echo "Nginx log directory not found"

# Try to start nginx with more verbose output
echo ""
echo "7️⃣ Attempting to start Nginx with debugging..."
echo "📋 Starting nginx in foreground mode for debugging:"
timeout 5s sudo nginx -g "daemon off; error_log /dev/stderr debug;" 2>&1 || echo "Nginx startup attempt completed"

echo ""
echo "🔧 Attempting fixes..."

# Fix 1: Ensure nginx user exists
echo "🔧 Fix 1: Ensuring nginx user exists..."
sudo useradd -r -s /bin/false www-data 2>/dev/null || echo "www-data user already exists"

# Fix 2: Create necessary directories
echo "🔧 Fix 2: Creating necessary directories..."
sudo mkdir -p /var/log/nginx
sudo mkdir -p /var/lib/nginx
sudo mkdir -p /etc/nginx/sites-enabled
sudo mkdir -p /etc/nginx/sites-available

# Fix 3: Set proper permissions
echo "🔧 Fix 3: Setting proper permissions..."
sudo chown -R www-data:www-data /var/log/nginx
sudo chown -R www-data:www-data /var/lib/nginx
sudo chmod 755 /var/log/nginx
sudo chmod 755 /var/lib/nginx

# Fix 4: Remove any conflicting default configs
echo "🔧 Fix 4: Removing conflicting configurations..."
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/conf.d/default.conf

# Fix 5: Ensure our config is properly linked
echo "🔧 Fix 5: Ensuring TrustLayer config is properly linked..."
if [ -f /etc/nginx/sites-available/trustlayer ]; then
    sudo ln -sf /etc/nginx/sites-available/trustlayer /etc/nginx/sites-enabled/
    echo "✅ TrustLayer config linked"
else
    echo "❌ TrustLayer config not found in sites-available"
fi

# Fix 6: Test configuration again
echo "🔧 Fix 6: Testing configuration after fixes..."
if sudo nginx -t; then
    echo "✅ Configuration is valid after fixes"
else
    echo "❌ Configuration still has issues"
    exit 1
fi

# Fix 7: Try to start nginx
echo "🔧 Fix 7: Attempting to start Nginx..."
if sudo systemctl start nginx; then
    echo "✅ Nginx started successfully!"
    
    # Enable nginx to start on boot
    sudo systemctl enable nginx
    echo "✅ Nginx enabled for auto-start"
    
    # Check status
    echo "📋 Nginx status:"
    sudo systemctl status nginx --no-pager
    
else
    echo "❌ Nginx still failed to start"
    echo "📋 Final error check:"
    sudo journalctl -u nginx --no-pager --lines=5
    
    echo ""
    echo "🆘 Manual troubleshooting steps:"
    echo "   1. Check if any other web server is running:"
    echo "      sudo systemctl status apache2"
    echo "      sudo systemctl status lighttpd"
    echo "   2. Check for port conflicts:"
    echo "      sudo netstat -tlnp | grep :80"
    echo "   3. Try starting nginx manually:"
    echo "      sudo nginx -g 'daemon off;'"
    echo "   4. Check system resources:"
    echo "      df -h"
    echo "      free -h"
fi

echo ""
echo "🎯 Diagnosis complete!"