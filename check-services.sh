#!/bin/bash

# TrustLayer AI - Check All Services Script
# Comprehensive check of what services are running

echo "🔍 Comprehensive Service Check"
echo "=============================="

# Check all web servers
echo ""
echo "1️⃣ Web Server Status:"
echo "----------------------"
services=("apache2" "nginx" "lighttpd" "httpd")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo "🟢 $service: RUNNING"
        echo "   Ports: $(sudo netstat -tlnp | grep "$service" | awk '{print $4}' || echo 'none')"
    elif systemctl is-enabled --quiet "$service" 2>/dev/null; then
        echo "🟡 $service: STOPPED (but enabled)"
    else
        echo "⚪ $service: NOT INSTALLED/DISABLED"
    fi
done

# Check port usage
echo ""
echo "2️⃣ Port Usage:"
echo "---------------"
echo "Port 80:"
sudo lsof -i :80 2>/dev/null || echo "   ✅ Available"
echo ""
echo "Port 443:"
sudo lsof -i :443 2>/dev/null || echo "   ✅ Available"
echo ""
echo "Port 8000 (TrustLayer Proxy):"
sudo lsof -i :8000 2>/dev/null || echo "   ❌ Not in use (TrustLayer not running?)"
echo ""
echo "Port 8501 (TrustLayer Dashboard):"
sudo lsof -i :8501 2>/dev/null || echo "   ❌ Not in use (TrustLayer not running?)"

# Check Docker containers
echo ""
echo "3️⃣ Docker Containers:"
echo "----------------------"
if command -v docker &> /dev/null; then
    if docker ps -q | grep -q .; then
        echo "🐳 Running containers:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        echo "⚪ No Docker containers running"
    fi
else
    echo "⚪ Docker not installed"
fi

# Check TrustLayer AI specifically
echo ""
echo "4️⃣ TrustLayer AI Status:"
echo "-------------------------"
if docker ps --format "{{.Names}}" | grep -q trustlayer; then
    echo "🟢 TrustLayer containers found:"
    docker ps --filter "name=trustlayer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "❌ TrustLayer containers not running"
    echo "💡 Run: ./build-and-run.sh your-project-id"
fi

# Check system resources
echo ""
echo "5️⃣ System Resources:"
echo "---------------------"
echo "Memory usage:"
free -h
echo ""
echo "Disk usage:"
df -h / | tail -1

# Check firewall
echo ""
echo "6️⃣ Firewall Status:"
echo "--------------------"
if command -v ufw &> /dev/null; then
    echo "UFW Status: $(sudo ufw status | head -1)"
    if sudo ufw status | grep -q "80"; then
        echo "Port 80: $(sudo ufw status | grep 80)"
    else
        echo "Port 80: Not specifically configured"
    fi
else
    echo "UFW not installed"
fi

# Provide recommendations
echo ""
echo "🎯 Recommendations:"
echo "==================="

# Check if TrustLayer is running
if ! docker ps --format "{{.Names}}" | grep -q trustlayer; then
    echo "1. Start TrustLayer AI containers:"
    echo "   ./build-and-run.sh your-project-id"
    echo ""
fi

# Check if any web server is blocking port 80
if sudo lsof -i :80 2>/dev/null | grep -v nginx; then
    echo "2. Stop conflicting web servers:"
    echo "   sudo systemctl stop apache2"
    echo "   sudo systemctl disable apache2"
    echo ""
fi

# Check if nginx is not running
if ! systemctl is-active --quiet nginx; then
    echo "3. Start Nginx:"
    echo "   ./fix-port-80.sh your-domain.com"
    echo ""
fi

echo "4. Test the complete setup:"
echo "   ./test-proxy.sh your-domain.com"