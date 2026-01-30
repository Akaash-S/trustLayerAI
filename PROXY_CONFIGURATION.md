# TrustLayer AI - System Proxy Configuration Guide

## 1. SSL Certificate Setup

First, set up SSL certificates on your VM:

```bash
# Make script executable
chmod +x setup-ssl.sh

# Run SSL setup (replace with your domain)
./setup-ssl.sh your-domain.com admin@your-domain.com
```

**What this does:**
- Installs Nginx and Certbot
- Creates Nginx reverse proxy configuration
- Obtains Let's Encrypt SSL certificate
- Sets up automatic certificate renewal
- Configures security headers and rate limiting

## 2. DNS Configuration

Point your domain to your VM's external IP:

```bash
# Get your VM's external IP
gcloud compute instances describe trustlayer-ai-vm --zone=us-central1-a --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
```

Create DNS A record:
```
Type: A
Name: your-domain.com (or subdomain like trustlayer.your-domain.com)
Value: YOUR_VM_EXTERNAL_IP
TTL: 300 (5 minutes)
```

## 3. Application Configuration

### For OpenAI API calls:

**Before (Direct):**
```python
import openai

client = openai.OpenAI(
    api_key="your-api-key",
    base_url="https://api.openai.com/v1"  # Direct to OpenAI
)
```

**After (Through TrustLayer AI):**
```python
import openai

client = openai.OpenAI(
    api_key="your-api-key",
    base_url="https://your-domain.com/v1"  # Through TrustLayer AI
)

# Add Host header to route to OpenAI
import httpx
client._client = httpx.Client(
    headers={"Host": "api.openai.com"}
)
```

### For Anthropic API calls:

**Before (Direct):**
```python
import anthropic

client = anthropic.Anthropic(
    api_key="your-api-key"
)
```

**After (Through TrustLayer AI):**
```python
import anthropic

client = anthropic.Anthropic(
    api_key="your-api-key",
    base_url="https://your-domain.com"
)

# Set custom headers
client._client.headers.update({"Host": "api.anthropic.com"})
```

### For curl/HTTP requests:

**Before (Direct):**
```bash
curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}'
```

**After (Through TrustLayer AI):**
```bash
curl -X POST https://your-domain.com/v1/chat/completions \
  -H "Host: api.openai.com" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "My name is John Doe and email is john@example.com"}]}'
```

## 4. Environment Variables

Set up environment variables for easy configuration:

```bash
# Add to ~/.bashrc or ~/.zshrc
export TRUSTLAYER_PROXY="https://your-domain.com"
export OPENAI_BASE_URL="$TRUSTLAYER_PROXY/v1"
export ANTHROPIC_BASE_URL="$TRUSTLAYER_PROXY"
```

## 5. Network-Level Configuration (Advanced)

### Option A: DNS Override (Recommended)

Create local DNS overrides to redirect AI API calls:

**On Linux/Mac:**
```bash
# Edit /etc/hosts (requires sudo)
sudo nano /etc/hosts

# Add these lines:
YOUR_VM_IP api.openai.com
YOUR_VM_IP api.anthropic.com
YOUR_VM_IP generativelanguage.googleapis.com
```

**On Windows:**
```cmd
# Edit C:\Windows\System32\drivers\etc\hosts (as Administrator)
# Add these lines:
YOUR_VM_IP api.openai.com
YOUR_VM_IP api.anthropic.com
YOUR_VM_IP generativelanguage.googleapis.com
```

### Option B: Corporate Proxy Configuration

If you're in a corporate environment, configure TrustLayer AI as your HTTP proxy:

```bash
# Set proxy environment variables
export HTTP_PROXY="https://your-domain.com:443"
export HTTPS_PROXY="https://your-domain.com:443"
export NO_PROXY="localhost,127.0.0.1,.local"
```

## 6. Testing Your Configuration

### Test PII Redaction:
```bash
curl -X POST https://your-domain.com/test \
  -H "Content-Type: application/json" \
  -d '{"content": "My name is John Doe, email john@example.com, phone 555-123-4567"}'
```

### Test OpenAI Integration:
```bash
curl -X POST https://your-domain.com/v1/chat/completions \
  -H "Host: api.openai.com" \
  -H "Authorization: Bearer your-openai-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello, my name is Jane Smith and my email is jane@company.com"}
    ]
  }'
```

### Test Health and Metrics:
```bash
# Health check
curl https://your-domain.com/health

# Metrics
curl https://your-domain.com/metrics

# Dashboard
open https://your-domain.com/dashboard
```

## 7. Application Integration Examples

### Python with requests:
```python
import requests

# Configure session to use TrustLayer AI
session = requests.Session()
session.headers.update({
    'Host': 'api.openai.com',
    'Authorization': 'Bearer your-api-key'
})

response = session.post(
    'https://your-domain.com/v1/chat/completions',
    json={
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'user', 'content': 'My SSN is 123-45-6789'}]
    }
)
```

### Node.js with axios:
```javascript
const axios = require('axios');

const client = axios.create({
  baseURL: 'https://your-domain.com',
  headers: {
    'Host': 'api.openai.com',
    'Authorization': 'Bearer your-api-key'
  }
});

const response = await client.post('/v1/chat/completions', {
  model: 'gpt-3.5-turbo',
  messages: [{
    role: 'user', 
    content: 'My credit card number is 4532-1234-5678-9012'
  }]
});
```

### Java with OkHttp:
```java
OkHttpClient client = new OkHttpClient.Builder()
    .addInterceptor(chain -> {
        Request original = chain.request();
        Request request = original.newBuilder()
            .header("Host", "api.openai.com")
            .header("Authorization", "Bearer your-api-key")
            .build();
        return chain.proceed(request);
    })
    .build();

Request request = new Request.Builder()
    .url("https://your-domain.com/v1/chat/completions")
    .post(RequestBody.create(jsonPayload, MediaType.parse("application/json")))
    .build();
```

## 8. Monitoring and Maintenance

### Check SSL Certificate Status:
```bash
sudo certbot certificates
```

### View Access Logs:
```bash
sudo tail -f /var/log/nginx/access.log
```

### Monitor TrustLayer AI:
```bash
# Container status
docker-compose ps

# Application logs
docker-compose logs -f proxy

# System resources
htop
```

### Update TrustLayer AI:
```bash
# Pull latest code and rebuild
git pull
./build-and-run.sh your-project-id
```

## 9. Security Considerations

1. **Firewall Configuration:**
```bash
# Only allow necessary ports
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

2. **Regular Updates:**
```bash
# System updates
sudo apt update && sudo apt upgrade -y

# SSL certificate renewal (automatic)
sudo certbot renew
```

3. **Access Control:**
- Use strong SSH keys
- Disable password authentication
- Consider IP whitelisting for admin access
- Monitor access logs regularly

## 10. Troubleshooting

### SSL Issues:
```bash
# Check certificate
sudo certbot certificates

# Test SSL
openssl s_client -connect your-domain.com:443

# Renew certificate
sudo certbot renew --force-renewal
```

### Proxy Issues:
```bash
# Check Nginx status
sudo systemctl status nginx

# Test Nginx config
sudo nginx -t

# Check TrustLayer AI health
curl https://your-domain.com/health
```

### DNS Issues:
```bash
# Check DNS resolution
nslookup your-domain.com
dig your-domain.com

# Test connectivity
ping your-domain.com
```

---

**🎉 You're all set!** Your TrustLayer AI proxy is now secured with SSL and ready to protect your AI API calls with PII redaction.