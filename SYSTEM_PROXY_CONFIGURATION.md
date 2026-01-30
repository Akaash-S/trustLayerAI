# 🔧 System Proxy Configuration for TrustLayer AI

Complete guide to configure your system to route all AI API traffic through TrustLayer AI proxy with HTTPS/SSL support.

## 🎯 **Architecture Overview**

```
Your Applications → System Proxy → TrustLayer AI (GCP) → Real AI APIs
                                        ↓
                                   PII Detection
                                   & Redaction
```

**Flow:**
1. Your apps make normal API calls (e.g., `https://api.openai.com`)
2. System proxy intercepts and routes to TrustLayer AI
3. TrustLayer AI detects/redacts PII and forwards to real APIs
4. Response comes back with PII restored

## 🚀 **Step 1: Deploy TrustLayer AI with HTTPS**

### **1.1 Deploy to Cloud Run with Custom Domain**
```bash
# Deploy your proxy
gcloud run deploy trustlayer-proxy \
  --image gcr.io/$PROJECT_ID/trustlayer-ai:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --port 8000

# Get the Cloud Run URL
PROXY_URL=$(gcloud run services describe trustlayer-proxy --region us-central1 --format 'value(status.url)')
echo "Proxy URL: $PROXY_URL"
```

### **1.2 Set Up Custom Domain (Optional but Recommended)**
```bash
# Map custom domain for easier configuration
gcloud run domain-mappings create \
  --service trustlayer-proxy \
  --domain proxy.yourdomain.com \
  --region us-central1

# This gives you: https://proxy.yourdomain.com
```

## 🔧 **Step 2: Configure System Proxy**

### **Option A: Windows Configuration**

#### **Method 1: Windows Proxy Settings (Recommended)**
1. **Open Settings** → **Network & Internet** → **Proxy**
2. **Enable "Use a proxy server"**
3. **Configure:**
   - **Address**: Your TrustLayer AI URL (without https://)
   - **Port**: 443 (for HTTPS) or 80 (for HTTP)
   - **Bypass proxy for local addresses**: Check this
4. **Save settings**

#### **Method 2: Windows Registry (Advanced)**
```powershell
# Run as Administrator
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer /t REG_SZ /d "your-proxy-url:443"
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyOverride /t REG_SZ /d "localhost;127.*;10.*;192.168.*"
```

#### **Method 3: Application-Specific (Python)**
```python
import os
import requests

# Set proxy for your Python applications
os.environ['HTTPS_PROXY'] = 'https://your-trustlayer-url'
os.environ['HTTP_PROXY'] = 'https://your-trustlayer-url'

# Test
response = requests.get('https://api.openai.com/v1/models')
```

### **Option B: macOS Configuration**

#### **Method 1: System Preferences**
1. **Apple Menu** → **System Preferences** → **Network**
2. **Select your network** → **Advanced** → **Proxies**
3. **Check "Web Proxy (HTTP)" and "Secure Web Proxy (HTTPS)"**
4. **Configure:**
   - **Web Proxy Server**: your-trustlayer-url
   - **Port**: 443
5. **Click OK** → **Apply**

#### **Method 2: Command Line**
```bash
# Set system proxy
sudo networksetup -setwebproxy "Wi-Fi" your-trustlayer-url 443
sudo networksetup -setsecurewebproxy "Wi-Fi" your-trustlayer-url 443

# Verify
networksetup -getwebproxy "Wi-Fi"
```

### **Option C: Linux Configuration**

#### **Method 1: Environment Variables**
```bash
# Add to ~/.bashrc or ~/.zshrc
export HTTP_PROXY="https://your-trustlayer-url"
export HTTPS_PROXY="https://your-trustlayer-url"
export NO_PROXY="localhost,127.0.0.1,10.*,192.168.*"

# Reload
source ~/.bashrc
```

#### **Method 2: System-wide Configuration**
```bash
# Edit /etc/environment
sudo tee -a /etc/environment <<EOF
HTTP_PROXY="https://your-trustlayer-url"
HTTPS_PROXY="https://your-trustlayer-url"
NO_PROXY="localhost,127.0.0.1,10.*,192.168.*"
EOF
```

## 🔐 **Step 3: Configure HTTPS/SSL Support**

### **3.1 Update TrustLayer AI for SSL Termination**

Update your `app/main.py` to handle SSL properly:

```python
# Add this to handle SSL termination
@app.middleware("http")
async def force_https_redirect(request: Request, call_next):
    # Handle SSL termination from load balancer
    if request.headers.get("x-forwarded-proto") == "http":
        url = request.url.replace(scheme="https")
        return RedirectResponse(url=url, status_code=301)
    
    response = await call_next(request)
    return response
```

### **3.2 Configure Reverse Proxy (Nginx)**

Create an Nginx configuration for SSL termination:

```nginx
server {
    listen 443 ssl;
    server_name proxy.yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://your-cloud-run-url;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🧪 **Step 4: Test Your Configuration**

### **4.1 Test Basic Connectivity**
```bash
# Test health endpoint through proxy
curl -x your-trustlayer-url:443 https://api.openai.com/health

# Should return TrustLayer AI health response
```

### **4.2 Test PII Detection**
```python
import openai
import os

# Configure OpenAI to use your proxy
openai.api_base = "https://your-trustlayer-url/v1"
openai.api_key = "your-openai-api-key"

# Test with PII
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "user", 
            "content": "My name is John Doe and my email is john@example.com. Help me write an email."
        }
    ]
)

print(response)
```

### **4.3 Monitor Traffic**
Check your TrustLayer AI dashboard to see:
- Intercepted requests
- PII detection events
- Response times

## 🔧 **Step 5: Application-Specific Configuration**

### **5.1 Python Applications**
```python
# Method 1: Environment variables
import os
os.environ['HTTPS_PROXY'] = 'https://your-trustlayer-url'

# Method 2: Requests library
import requests
proxies = {
    'http': 'https://your-trustlayer-url',
    'https': 'https://your-trustlayer-url'
}
response = requests.get('https://api.openai.com/v1/models', proxies=proxies)

# Method 3: OpenAI library
import openai
openai.api_base = "https://your-trustlayer-url/v1"
```

### **5.2 Node.js Applications**
```javascript
// Method 1: Environment variables
process.env.HTTPS_PROXY = 'https://your-trustlayer-url';

// Method 2: Axios configuration
const axios = require('axios');
const agent = new require('https-proxy-agent')('https://your-trustlayer-url');

const client = axios.create({
  httpsAgent: agent
});

// Method 3: OpenAI library
const { Configuration, OpenAIApi } = require("openai");
const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
  basePath: "https://your-trustlayer-url/v1"
});
```

### **5.3 cURL Commands**
```bash
# Use proxy with cURL
curl --proxy https://your-trustlayer-url \
     -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

## 🔍 **Step 6: Advanced Configuration**

### **6.1 Domain-Specific Routing**

Configure your proxy to only intercept AI API domains:

```bash
# Windows: Add to proxy bypass list
# Bypass everything except AI APIs
ProxyOverride: "*;!api.openai.com;!api.anthropic.com;!generativelanguage.googleapis.com"

# Linux: Use PAC file
function FindProxyForURL(url, host) {
    if (shExpMatch(host, "api.openai.com") ||
        shExpMatch(host, "api.anthropic.com") ||
        shExpMatch(host, "generativelanguage.googleapis.com")) {
        return "PROXY your-trustlayer-url:443";
    }
    return "DIRECT";
}
```

### **6.2 Load Balancing**

Deploy multiple TrustLayer AI instances:

```bash
# Deploy to multiple regions
gcloud run deploy trustlayer-proxy-us \
  --image gcr.io/$PROJECT_ID/trustlayer-ai:latest \
  --region us-central1

gcloud run deploy trustlayer-proxy-eu \
  --image gcr.io/$PROJECT_ID/trustlayer-ai:latest \
  --region europe-west1

# Use load balancer or round-robin DNS
```

## 📊 **Step 7: Monitoring and Validation**

### **7.1 Verify Traffic Routing**
```bash
# Check if traffic is going through proxy
curl -v https://api.openai.com/v1/models

# Look for TrustLayer AI headers in response
# Should see custom headers indicating proxy processing
```

### **7.2 Monitor Dashboard**
Access your TrustLayer AI dashboard to verify:
- ✅ **Requests being intercepted**
- ✅ **PII detection working**
- ✅ **Response times acceptable**
- ✅ **No errors in logs**

### **7.3 Test PII Protection**
```python
# Send request with PII
import requests

response = requests.post('https://api.openai.com/v1/chat/completions', 
    headers={'Authorization': 'Bearer your-key'},
    json={
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                'role': 'user',
                'content': 'My SSN is 123-45-6789 and my email is test@example.com'
            }
        ]
    }
)

# Check dashboard - should show PII detection event
```

## 🚨 **Troubleshooting**

### **Common Issues:**

#### **1. SSL Certificate Errors**
```bash
# Disable SSL verification for testing
export PYTHONHTTPSVERIFY=0
# Or add your certificate to system trust store
```

#### **2. Proxy Not Working**
```bash
# Test direct connection
curl https://your-trustlayer-url/health

# Test proxy connection
curl --proxy https://your-trustlayer-url https://httpbin.org/ip
```

#### **3. Application Not Using Proxy**
```python
# Force proxy usage
import requests
session = requests.Session()
session.proxies = {
    'http': 'https://your-trustlayer-url',
    'https': 'https://your-trustlayer-url'
}
```

## 💰 **Cost Considerations**

**Additional Costs for HTTPS/SSL:**
- **SSL Certificate**: $0-100/year (Let's Encrypt is free)
- **Load Balancer**: $18/month (if using Google Cloud Load Balancer)
- **Custom Domain**: $12/year (optional)

**Total Additional Cost**: $18-30/month for production HTTPS setup

## 🎉 **Success Validation**

Your system proxy is working correctly when you see:

✅ **All AI API calls** going through TrustLayer AI  
✅ **PII detection events** in the dashboard  
✅ **Response times** under 200ms additional latency  
✅ **No application changes** needed  
✅ **HTTPS/SSL** working properly  
✅ **Monitoring data** showing intercepted traffic  

## 🔐 **Security Best Practices**

1. **Use HTTPS everywhere** - Never send API keys over HTTP
2. **Rotate certificates** regularly
3. **Monitor proxy logs** for suspicious activity
4. **Set up alerts** for proxy failures
5. **Use strong authentication** for proxy access
6. **Regular security audits** of proxy configuration

Your TrustLayer AI proxy is now transparently protecting all your AI interactions! 🛡️