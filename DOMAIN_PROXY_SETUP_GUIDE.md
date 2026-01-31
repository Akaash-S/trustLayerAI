# TrustLayer AI - Domain Proxy Setup Guide (Windows)

## Overview

Configure your Windows system to use TrustLayer AI proxy with your custom domain and SSL certificate.

**Your TrustLayer AI Proxy Configuration:**
- **HTTP Proxy**: `trustlayer.asolvitra.tech:443`
- **HTTPS Proxy**: `trustlayer.asolvitra.tech:443`
- **Dashboard**: `https://trustlayer.asolvitra.tech/dashboard`
- **Health Check**: `https://trustlayer.asolvitra.tech/health`

---

## Method 1: System-Wide Proxy (Windows Settings)

### Step 1: Open Windows Settings
1. Press `Win + I` to open Settings
2. Go to **Network & Internet**
3. Click **Proxy** in the left sidebar

### Step 2: Configure Manual Proxy
1. Under **Manual proxy setup**, turn ON **"Use a proxy server"**
2. **Address**: `trustlayer.asolvitra.tech`
3. **Port**: `443`
4. **Don't use proxy for**: `localhost;127.0.0.1;*.local`
5. Click **Save**

### Step 3: Test Configuration
Open Command Prompt and test:
```cmd
curl https://httpbin.org/ip
```
This should show your request going through the TrustLayer proxy.

---

## Method 2: Internet Options (Classic Method)

### Step 1: Open Internet Options
1. Press `Win + R`, type `inetcpl.cpl`, press Enter
2. Or go to Control Panel → Internet Options

### Step 2: Configure Proxy
1. Click the **Connections** tab
2. Click **LAN settings** button
3. Check **"Use a proxy server for your LAN"**
4. **Address**: `trustlayer.asolvitra.tech`
5. **Port**: `443`
6. Click **Advanced** button
7. In **"Do not use proxy for"**: `localhost;127.0.0.1;*.local`
8. Click **OK** on all dialogs

---

## Method 3: Browser-Specific Configuration

### Google Chrome
1. **Open Chrome Settings**
   - Click three dots menu → Settings
   - Or go to: `chrome://settings/`

2. **Navigate to System Settings**
   - Scroll down and click "Advanced"
   - Click "System" section
   - Click "Open your computer's proxy settings"

3. **Configure Proxy** (same as Method 1 above)
   - **Address**: `trustlayer.asolvitra.tech`
   - **Port**: `443`

### Firefox
1. **Open Firefox Settings**
   - Click hamburger menu → Settings
   - Or go to: `about:preferences`

2. **Network Settings**
   - Scroll down to "Network Settings"
   - Click "Settings..." button

3. **Configure Proxy**
   - Select "Manual proxy configuration"
   - **HTTP Proxy**: `trustlayer.asolvitra.tech` Port: `443`
   - **HTTPS Proxy**: `trustlayer.asolvitra.tech` Port: `443`
   - **Use this proxy server for all protocols**: ✅ Check this
   - **No proxy for**: `localhost, 127.0.0.1`
   - Click "OK"

### Microsoft Edge
1. **Open Edge Settings**
   - Click three dots menu → Settings
   - Or go to: `edge://settings/`

2. **System Settings**
   - Click "System and performance" in left sidebar
   - Click "Open your computer's proxy settings"

3. **Configure Proxy** (same as Method 1 above)

---

## Method 4: Command Line / PowerShell

### Set Proxy via PowerShell
```powershell
# Set system proxy
netsh winhttp set proxy proxy-server="trustlayer.asolvitra.tech:443" bypass-list="localhost;127.0.0.1;*.local"

# Verify settings
netsh winhttp show proxy
```

### Set Environment Variables
```cmd
# Set for current session
set HTTP_PROXY=https://trustlayer.asolvitra.tech:443
set HTTPS_PROXY=https://trustlayer.asolvitra.tech:443
set NO_PROXY=localhost,127.0.0.1,*.local

# Set permanently (requires restart)
setx HTTP_PROXY "https://trustlayer.asolvitra.tech:443"
setx HTTPS_PROXY "https://trustlayer.asolvitra.tech:443"
setx NO_PROXY "localhost,127.0.0.1,*.local"
```

---

## Testing Your Configuration

### Step 1: Test Basic Connectivity
```cmd
# Test TrustLayer AI health
curl https://trustlayer.asolvitra.tech/health

# Should return: {"status":"healthy","service":"TrustLayer AI Proxy"}
```

### Step 2: Test PII Detection
```cmd
# Test PII detection
curl -X POST https://trustlayer.asolvitra.tech/test ^
  -H "Content-Type: application/json" ^
  -d "{\"content\": \"My name is Alice Johnson, email: alice@test.com\"}"

# Should show redacted PII
```

### Step 3: Test Dashboard Access
Open your browser and go to:
```
https://trustlayer.asolvitra.tech/dashboard
```

### Step 4: Test Proxy Functionality
```cmd
# Test if requests go through proxy
curl https://httpbin.org/ip

# Should show TrustLayer proxy IP, not your real IP
```

### Step 5: Test AI API Through Proxy
```cmd
# Test OpenAI API through proxy (replace YOUR_API_KEY)
curl --proxy https://trustlayer.asolvitra.tech:443 ^
  -X POST https://api.openai.com/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_API_KEY" ^
  -d "{\"model\": \"gpt-3.5-turbo\", \"messages\": [{\"role\": \"user\", \"content\": \"My name is Bob Wilson, tell me a joke\"}]}"
```

---

## Application-Specific Configuration

### Python Applications
```python
import os
import requests

# Set proxy for requests
proxies = {
    'http': 'https://trustlayer.asolvitra.tech:443',
    'https': 'https://trustlayer.asolvitra.tech:443'
}

# Use with requests
response = requests.get('https://api.openai.com/v1/models', proxies=proxies)

# Or set environment variables
os.environ['HTTP_PROXY'] = 'https://trustlayer.asolvitra.tech:443'
os.environ['HTTPS_PROXY'] = 'https://trustlayer.asolvitra.tech:443'
```

### Node.js Applications
```javascript
// Set proxy environment variables
process.env.HTTP_PROXY = 'https://trustlayer.asolvitra.tech:443';
process.env.HTTPS_PROXY = 'https://trustlayer.asolvitra.tech:443';

// Or use with axios
const axios = require('axios');
const HttpsProxyAgent = require('https-proxy-agent');

const agent = new HttpsProxyAgent('https://trustlayer.asolvitra.tech:443');
axios.defaults.httpsAgent = agent;
```

---

## Monitoring & Dashboard

### Real-Time Monitoring
- **Dashboard URL**: `https://trustlayer.asolvitra.tech/dashboard`
- **Health Check**: `https://trustlayer.asolvitra.tech/health`
- **Metrics API**: `https://trustlayer.asolvitra.tech/metrics`

### What You'll See in Dashboard
1. **Traffic Flow**: Real-time requests going through the proxy
2. **PII Detection**: Count of detected and redacted entities
3. **Latency Metrics**: Response times for proxied requests
4. **Security Events**: Blocked domains or suspicious activities

---

## Troubleshooting

### Common Issues

#### 1. "Connection Refused" or "Timeout" Errors
```cmd
# Test if domain is reachable
ping trustlayer.asolvitra.tech

# Test if HTTPS is working
curl -I https://trustlayer.asolvitra.tech/health
```

#### 2. SSL Certificate Errors
```cmd
# Test with certificate verification disabled (for testing only)
curl -k https://trustlayer.asolvitra.tech/health
```

#### 3. Proxy Not Working in Browser
- **Clear browser cache** and restart browser
- **Check if proxy is enabled** in browser settings
- **Try incognito/private mode** to test without extensions

#### 4. Some Applications Not Using Proxy
- **Set environment variables** system-wide
- **Configure application-specific** proxy settings
- **Check firewall/antivirus** isn't blocking proxy connections

### Debug Commands
```cmd
# Check current proxy settings
netsh winhttp show proxy

# Test proxy connectivity
curl --proxy https://trustlayer.asolvitra.tech:443 https://httpbin.org/ip

# Check environment variables
echo %HTTP_PROXY%
echo %HTTPS_PROXY%
```

---

## Removing Proxy Configuration

### Windows Settings Method
1. Go to Settings → Network & Internet → Proxy
2. Turn OFF "Use a proxy server"
3. Click Save

### Internet Options Method
1. Open Internet Options → Connections → LAN settings
2. Uncheck "Use a proxy server for your LAN"
3. Click OK

### Command Line Method
```cmd
# Remove system proxy
netsh winhttp reset proxy

# Remove environment variables
set HTTP_PROXY=
set HTTPS_PROXY=
```

---

## Security Notes

⚠️ **Important Security Considerations:**

1. **SSL/TLS**: Your domain uses proper SSL certificates, ensuring secure communication
2. **PII Protection**: All sensitive data is detected and redacted before reaching AI APIs
3. **Monitoring**: All traffic is logged and monitored through the dashboard
4. **API Keys**: Your API keys pass through the proxy securely via HTTPS

---

## Next Steps

1. **Configure your system** using one of the methods above
2. **Test the configuration** with the provided test commands
3. **Visit the dashboard**: `https://trustlayer.asolvitra.tech/dashboard`
4. **Make AI API calls** through your browser or applications
5. **Monitor PII detection** in real-time through the dashboard

**Your TrustLayer AI governance proxy is now ready for production use with SSL and custom domain!** 🛡️

---

## Quick Reference

**Proxy Settings:**
- **HTTP Proxy**: `trustlayer.asolvitra.tech:443`
- **HTTPS Proxy**: `trustlayer.asolvitra.tech:443`
- **Dashboard**: `https://trustlayer.asolvitra.tech/dashboard`
- **Bypass**: `localhost;127.0.0.1;*.local`

**Test Commands:**
```cmd
curl https://trustlayer.asolvitra.tech/health
curl https://trustlayer.asolvitra.tech/dashboard
curl --proxy https://trustlayer.asolvitra.tech:443 https://httpbin.org/ip
```