#!/bin/bash

# TrustLayer AI - Fix Port 80 Conflict Script
# Finds and resolves what's using port 80

set -e

echo "🔍 Finding what's using port 80..."

# Check what's using port 80
echo "📋 Checking port 80 usage:"
PORT_80_PROCESSES=$(sudo lsof -i :80 2>/dev/null || true)

if [ -n "$PORT_80_PROCESSES" ]; then
    echo "⚠️  Port 80 is in use:"
    echo "$PORT_80_PROCESSES"
    echo ""
    
    # Extract process names and PIDs
    PIDS=$(echo "$PORT_80_PROCESSES" | awk 'NR>1 {print $2}' | sort -u)
    PROCESSES=$(echo "$PORT_80_PROCESSES" | awk 'NR>1 {print $1}' | sort -u)
    
    echo "🔧 Processes using port 80: $PROCESSES"
    echo "🔧 PIDs: $PIDS"
    echo ""
    
    # Check for common web servers
    if echo "$PROCESSES" | grep -q apache; then
        echo "🛑 Stopping Apache..."
        sudo systemctl stop apache2 2>/dev/null || true
        sudo systemctl disable apache2 2>/dev/null || true
        echo "✅ Apache stopped and disabled"
    fi
    
    if echo "$PROCESSES" | grep -q nginx; then
        echo "🛑 Stopping existing Nginx processes..."
        sudo systemctl stop nginx 2>/dev/null || true
        sudo pkill -f nginx 2>/dev/null || true
        sleep 3
        echo "✅ Nginx processes stopped"
    fi
    
    if echo "$PROCESSES" | grep -q lighttpd; then
        echo "🛑 Stopping Lighttpd..."
        sudo systemctl stop lighttpd 2>/dev/null || true
        sudo systemctl disable lighttpd 2>/dev/null || true
        echo "✅ Lighttpd stopped and disabled"
    fi
    
    # Check for Docker containers using port 80
    if command -v docker &> /dev/null; then
        echo "🐳 Checking Docker containers using port 80..."
        DOCKER_CONTAINERS=$(docker ps --format "table {{.Names}}\t{{.Ports}}" | grep ":80" || true)
        if [ -n "$DOCKER_CONTAINERS" ]; then
            echo "⚠️  Docker containers using port 80:"
            echo "$DOCKER_CONTAINERS"
            echo "💡 You may need to stop these containers manually"
        fi
    fi
    
    # Kill any remaining processes on port 80
    echo "🔪 Killing remaining processes on port 80..."
    for pid in $PIDS; do
        if [ -n "$pid" ] && [ "$pid" != "PID" ]; then
            echo "Killing process $pid..."
            sudo kill -9 "$pid" 2>/dev/null || true
        fi
    done
    
    sleep 2
    
else
    echo "✅ Port 80 is available"
fi

# Double-check port 80 is now free
echo ""
echo "🔍 Double-checking port 80..."
PORT_80_CHECK=$(sudo lsof -i :80 2>/dev/null || true)
if [ -n "$PORT_80_CHECK" ]; then
    echo "❌ Port 80 is still in use:"
    echo "$PORT_80_CHECK"
    echo ""
    echo "🆘 Manual intervention required:"
    echo "   1. Identify the process: sudo lsof -i :80"
    echo "   2. Stop the service: sudo systemctl stop <service-name>"
    echo "   3. Or kill the process: sudo kill -9 <pid>"
    exit 1
else
    echo "✅ Port 80 is now free"
fi

# Check port 443 as well
echo ""
echo "🔍 Checking port 443..."
PORT_443_CHECK=$(sudo lsof -i :443 2>/dev/null || true)
if [ -n "$PORT_443_CHECK" ]; then
    echo "⚠️  Port 443 is in use (this is usually OK for SSL):"
    echo "$PORT_443_CHECK"
else
    echo "✅ Port 443 is available"
fi

# Now try to start Nginx
echo ""
echo "🚀 Attempting to start Nginx..."

# Create a simple test configuration first
DOMAIN=${1:-"localhost"}
echo "📝 Creating simple Nginx configuration for $DOMAIN..."

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

# Enable the site
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

# Start Nginx
echo "🚀 Starting Nginx..."
if sudo systemctl start nginx; then
    echo "✅ Nginx started successfully!"
    sudo systemctl enable nginx
    echo "✅ Nginx enabled for auto-start"
    
    # Check status
    echo ""
    echo "📋 Nginx status:"
    sudo systemctl status nginx --no-pager -l
    
    # Test the proxy
    echo ""
    echo "🧪 Testing the proxy..."
    sleep 2
    
    if curl -f "http://localhost/health" 2>/dev/null; then
        echo "✅ Proxy is working through Nginx!"
    else
        echo "⚠️  Proxy test failed - make sure TrustLayer AI containers are running"
        echo "💡 Run: ./build-and-run.sh your-project-id"
    fi
    
else
    echo "❌ Nginx failed to start"
    echo "📋 Error details:"
    sudo journalctl -u nginx --no-pager --lines=10
    
    echo ""
    echo "🔍 Final port check:"
    sudo lsof -i :80 || echo "No processes found on port 80"
    
    exit 1
fi

echo ""
echo "🎉 Port 80 conflict resolved and Nginx is running!"
echo ""
echo "🔗 Test URLs:"
echo "   • Health: http://$DOMAIN/health"
echo "   • Dashboard: http://$DOMAIN/dashboard"
echo ""
echo "🔒 Next steps for SSL:"
echo "   1. Make sure your domain points to this server"
echo "   2. Run: sudo certbot --nginx -d $DOMAIN"