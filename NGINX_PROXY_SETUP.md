# Nginx Proxy Setup for TrustLayer AI

## Overview

Since port 80 is accessible externally but ports 8000/8501 are blocked, we'll configure Nginx to proxy TrustLayer AI through port 80.

**Result**: Use `34.59.4.137:80` as your proxy instead of `34.59.4.137:8000`

## Manual Setup Steps

### Step 1: SSH into Your VM

1. Go to **Google Cloud Console** → **Compute Engine** → **VM instances**
2. Click **SSH** button next to your `trustlayer-ai-main` VM
3. Or use: `gcloud compute ssh trustlayer-ai-main --zone=us-central1-a`

### Step 2: Check TrustLayer AI Services

```bash
# Check if TrustLayer AI is running locally
curl http://localhost:8000/health

# If not working, start the services
cd /opt/trustlayer-ai  # or wherever you deployed TrustLayer
docker-compose up -d

# Check Docker containers
docker ps

# Test again
curl http://localhost:8000/health
# Should return: {"status": "healthy", "service": "TrustLayer AI Proxy"}
```

### Step 3: Backup Existing Nginx Config

```bash
# Create backup
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup
```

### Step 4: Create New Nginx Configuration

```bash
# Edit the Nginx default site
sudo nano /etc/nginx/sites-available/default
```

**Replace the entire content with:**

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name _;
    
    # TrustLayer AI Proxy - Main proxy functionality
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Handle timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Handle large requests
        client_max_body_size 10M;
    }
    
    # Dashboard access via /dashboard path
    location /dashboard {
        rewrite ^/dashboard(.*) /$1 break;
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Metrics endpoint
    location /metrics {
        proxy_pass http://localhost:8000/metrics;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Test endpoint
    location /test {
        proxy_pass http://localhost:8000/test;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Save and exit**: `Ctrl+X`, then `Y`, then `Enter`

### Step 5: Test and Reload Nginx

```bash
# Test Nginx configuration
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx

# Check Nginx status
sudo systemctl status nginx
```

### Step 6: Test the Proxy

```bash
# Test from within the VM
curl http://localhost:80/health
curl http://localhost:80/metrics
curl -I http://localhost:80/dashboard

# All should work now
```

### Step 7: Test External Access

From your local machine:

```bash
# Test health endpoint
curl http://34.59.4.137/health

# Test dashboard
curl -I http://34.59.4.137/dashboard

# Test metrics
curl http://34.59.4.137/metrics
```

## New Proxy Configuration

After setup, use these settings:

**Browser/System Proxy:**
- **HTTP Proxy**: `34.59.4.137:80`
- **HTTPS Proxy**: `34.59.4.137:80`

**Access URLs:**
- **Dashboard**: `http://34.59.4.137/dashboard`
- **Health Check**: `http://34.59.4.137/health`
- **Metrics**: `http://34.59.4.137/metrics`

## Testing Your Setup

### 1. Basic Connectivity
```bash
curl http://34.59.4.137/health
# Should return: {"status": "healthy", "service": "TrustLayer AI Proxy"}
```

### 2. PII Detection Test
```bash
curl -X POST http://34.59.4.137/test \
  -H "Content-Type: application/json" \
  -d '{"content": "My name is John Smith, email: john@test.com"}'
```

### 3. Dashboard Access
Open in browser: `http://34.59.4.137/dashboard`

### 4. Proxy Test with AI API
```bash
# Test through proxy (replace YOUR_API_KEY)
curl --proxy http://34.59.4.137:80 \
  -X POST https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "My name is Alice Johnson, tell me a joke"}
    ]
  }'
```

## Troubleshooting

### If Health Check Still Returns 404

1. **Check TrustLayer AI is running**:
   ```bash
   docker ps
   curl http://localhost:8000/health
   ```

2. **Check Nginx logs**:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   sudo tail -f /var/log/nginx/access.log
   ```

3. **Restart services**:
   ```bash
   # Restart TrustLayer AI
   cd /opt/trustlayer-ai
   docker-compose restart
   
   # Restart Nginx
   sudo systemctl restart nginx
   ```

### If Dashboard Doesn't Load

1. **Check Streamlit is running**:
   ```bash
   docker logs trustlayer-dashboard
   curl -I http://localhost:8501
   ```

2. **Check WebSocket connections** in browser developer tools

### Restore Original Config

If something goes wrong:

```bash
# Restore backup
sudo cp /etc/nginx/sites-available/default.backup /etc/nginx/sites-available/default
sudo systemctl reload nginx
```

## Security Notes

- This setup proxies all traffic through port 80
- For production, add SSL/TLS certificates
- Consider adding authentication for the dashboard
- Monitor Nginx access logs for security

## Next Steps

1. **Configure your browser** to use `34.59.4.137:80` as proxy
2. **Test with real AI API calls** to see PII detection in action
3. **Monitor the dashboard** at `http://34.59.4.137/dashboard`
4. **Set up SSL certificates** for production use

Your TrustLayer AI is now accessible through port 80! 🎉