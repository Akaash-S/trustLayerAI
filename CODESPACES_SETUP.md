# 🚀 TrustLayer AI - GitHub Codespaces Setup

Complete guide for developing and deploying TrustLayer AI using GitHub Codespaces with GCP deployment.

## 🎯 **Why Codespaces?**

✅ **No local setup needed** - Everything runs in the cloud  
✅ **Pre-configured environment** - Docker, gcloud, Python ready  
✅ **No network issues** - Direct cloud-to-cloud connectivity  
✅ **Easy GCP deployment** - Built-in gcloud CLI  
✅ **Port forwarding** - Test locally, deploy globally  

## 🏗️ **Step 1: Set Up Codespaces**

### **1.1 Create Codespace**
1. Go to your GitHub repository
2. Click **"Code"** → **"Codespaces"** → **"Create codespace on main"**
3. Wait 2-3 minutes for setup

### **1.2 Verify Environment**
```bash
# Check Python
python --version

# Check Docker
docker --version

# Check gcloud
gcloud --version

# Install dependencies
pip install -r requirements.txt
```

## 🔧 **Step 2: Fix SSL Issues**

The SSL error is fixed in the code. The proxy now uses:
- **Disabled SSL verification** for development
- **Better error handling** for network issues
- **Retry logic** for failed connections

### **2.1 Test Local Setup**
```bash
# Start Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Start the proxy
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, start dashboard
streamlit run dashboard.py --server.address 0.0.0.0 --server.port 8501
```

### **2.2 Test Endpoints**
```bash
# Test health (should work)
curl http://localhost:8000/health

# Test with mock data (won't call real APIs)
curl -X POST http://localhost:8000/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## ☁️ **Step 3: Set Up GCP from Codespaces**

### **3.1 Authenticate with GCP**
```bash
# Login to GCP
gcloud auth login

# Set your project
export PROJECT_ID="trustlayer-ai-suite"  # Your project ID
gcloud config set project $PROJECT_ID

# Verify authentication
gcloud auth list
gcloud config get-value project
```

### **3.2 Enable Required APIs**
```bash
# Enable APIs
gcloud services enable \
  run.googleapis.com \
  compute.googleapis.com \
  redis.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

## 🐳 **Step 4: Build and Deploy with Cloud Build**

### **4.1 Use Cloud Build (Recommended)**
```bash
# Build in the cloud (avoids local network issues)
gcloud builds submit --tag gcr.io/$PROJECT_ID/trustlayer-ai .

# Build dashboard
gcloud builds submit --tag gcr.io/$PROJECT_ID/trustlayer-ai-dashboard -f gcp-deployment/Dockerfile.dashboard .
```

### **4.2 Alternative: Use Artifact Registry**
```bash
# Create Artifact Registry repository
gcloud artifacts repositories create trustlayer-repo \
    --repository-format=docker \
    --location=us-central1

# Configure Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build and push
docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/trustlayer-repo/trustlayer-ai:latest .
docker push us-central1-docker.pkg.dev/$PROJECT_ID/trustlayer-repo/trustlayer-ai:latest
```

## 🚀 **Step 5: Deploy to Cloud Run**

### **5.1 Create Redis Instance**
```bash
# Create Redis instance
gcloud redis instances create trustlayer-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_7_0

# Get Redis IP
REDIS_IP=$(gcloud redis instances describe trustlayer-redis --region=us-central1 --format="value(host)")
echo "Redis IP: $REDIS_IP"
```

### **5.2 Deploy Services**
```bash
# Deploy proxy service
gcloud run deploy trustlayer-proxy \
  --image gcr.io/$PROJECT_ID/trustlayer-ai:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 5 \
  --port 8000 \
  --set-env-vars REDIS_HOST=$REDIS_IP,REDIS_PORT=6379,LOG_LEVEL=INFO

# Deploy dashboard
gcloud run deploy trustlayer-dashboard \
  --image gcr.io/$PROJECT_ID/trustlayer-ai-dashboard:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 2 \
  --port 8501 \
  --set-env-vars PROXY_URL=https://trustlayer-proxy-[hash]-uc.a.run.app
```

### **5.3 Get Service URLs**
```bash
# Get URLs
PROXY_URL=$(gcloud run services describe trustlayer-proxy --region us-central1 --format 'value(status.url)')
DASHBOARD_URL=$(gcloud run services describe trustlayer-dashboard --region us-central1 --format 'value(status.url)')

echo "🎯 Your TrustLayer AI is deployed!"
echo "Proxy URL: $PROXY_URL"
echo "Dashboard URL: $DASHBOARD_URL"
```

## 🧪 **Step 6: Test Your Deployment**

### **6.1 Test Health Endpoint**
```bash
curl $PROXY_URL/health
# Expected: {"status": "healthy", "service": "TrustLayer AI Proxy"}
```

### **6.2 Test PII Detection**
```bash
curl -X POST $PROXY_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-openai-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "My name is John Doe and my email is john@example.com"
      }
    ]
  }'
```

### **6.3 Access Dashboard**
Open your browser and go to the Dashboard URL. You should see:
- Real-time traffic metrics
- PII detection statistics
- System health status

## 🔧 **Step 7: Configure DNS (Optional)**

### **7.1 Create DNS Forwarder VM**
```bash
# Create VM for DNS forwarding
gcloud compute instances create dns-forwarder \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --tags=dns-forwarder

# Get external IP
FORWARDER_IP=$(gcloud compute instances describe dns-forwarder --zone=us-central1-a --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
echo "DNS Forwarder IP: $FORWARDER_IP"
```

### **7.2 Configure DNS Forwarder**
```bash
# SSH into the VM
gcloud compute ssh dns-forwarder --zone=us-central1-a

# Install and configure BIND9
sudo apt update && sudo apt install -y bind9

# Configure to forward AI API domains to your proxy
sudo tee /etc/bind/named.conf.local <<EOF
zone "api.openai.com" {
    type forward;
    forwarders { $(echo $PROXY_URL | sed 's|https://||' | sed 's|http://||'); };
};
EOF

# Restart BIND9
sudo systemctl restart bind9
```

## 🎯 **Step 8: Use Your AI Proxy**

### **8.1 Update Your Applications**
Instead of calling `https://api.openai.com` directly, your applications will now call your proxy URL:

```python
# Before
openai.api_base = "https://api.openai.com/v1"

# After  
openai.api_base = f"{PROXY_URL}/v1"
```

### **8.2 Monitor Usage**
- **Dashboard**: Monitor all AI interactions in real-time
- **Logs**: Check Cloud Run logs for detailed request information
- **Metrics**: View performance metrics in Google Cloud Console

## 💰 **Costs**

**Codespaces Development:**
- Free tier: 60 hours/month
- Paid: ~$0.18/hour

**GCP Deployment:**
- Cloud Run: $5-30/month (pay-per-use)
- Redis: $45/month (1GB instance)
- DNS Forwarder VM: $5/month
- **Total**: ~$55-80/month

## 🚨 **Troubleshooting**

### **SSL Errors Fixed**
The code now handles SSL issues by:
- Disabling SSL verification for development
- Better error handling and retries
- Proper certificate handling in production

### **Network Issues**
If you still get network errors:
```bash
# Check if services are running
gcloud run services list

# Check logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# Test connectivity
curl -v $PROXY_URL/health
```

### **Redis Connection Issues**
```bash
# Check Redis status
gcloud redis instances list

# Test Redis connectivity from Cloud Run
gcloud run services update trustlayer-proxy \
  --set-env-vars REDIS_HOST=$REDIS_IP,REDIS_PORT=6379
```

## 🎉 **Success!**

You now have TrustLayer AI running in GitHub Codespaces and deployed to GCP Cloud Run with:

✅ **No SSL issues** - Fixed with proper HTTP client configuration  
✅ **Cloud-based development** - No local setup needed  
✅ **Scalable deployment** - Auto-scaling Cloud Run services  
✅ **Real-time monitoring** - Dashboard and logging  
✅ **PII protection** - Automatic detection and redaction  
✅ **Cost-effective** - Pay-per-use pricing  

Your AI interactions are now secure and monitored! 🛡️