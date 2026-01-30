# 🚀 TrustLayer AI - Manual GKE Deployment Guide

Complete step-by-step guide to manually deploy TrustLayer AI on Google Kubernetes Engine with VPC DNS integration for routing all AI traffic through your proxy.

## 🎯 **Architecture Overview**

```
Your Local System → Custom DNS → GCP VPC → GKE Cluster → TrustLayer AI Proxy → AI APIs
                                    ↓
                              Load Balancer ← Dashboard
```

**Flow:**
1. Your system uses custom DNS pointing to GCP
2. AI API requests (api.openai.com, etc.) resolve to your GCP Load Balancer
3. Load Balancer forwards to TrustLayer AI proxy in GKE
4. Proxy sanitizes PII and forwards to real AI APIs
5. Response comes back through proxy with PII restored

## 📋 **Prerequisites**

- Google Cloud account with billing enabled
- Local machine with `gcloud` CLI and `kubectl` installed
- Docker installed locally
- Basic knowledge of Kubernetes

## 🏗️ **Step 1: Create GCP Project and Enable APIs**

### **1.1 Create Project**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **"Select a project"** → **"New Project"**
3. Enter:
   - **Project name**: `trustlayer-ai-gke`
   - **Project ID**: `trustlayer-ai-gke-[random]` (note this ID)
4. Click **"Create"**

### **1.2 Enable Required APIs**
1. Go to **APIs & Services** → **Library**
2. Enable these APIs (search and click "Enable" for each):
   - Kubernetes Engine API
   - Compute Engine API
   - Container Registry API
   - Cloud DNS API
   - Cloud Memorystore for Redis API
   - Cloud Logging API
   - Cloud Monitoring API

### **1.3 Set Up Billing**
1. Go to **Billing** → Link your project to a billing account

## 🌐 **Step 2: Create VPC Network**

### **2.1 Create VPC**
1. Go to **VPC network** → **VPC networks**
2. Click **"Create VPC Network"**
3. Configure:
   - **Name**: `trustlayer-vpc`
   - **Subnet creation mode**: Custom
   
### **2.2 Create Subnets**
Add these subnets:

**GKE Subnet:**
- **Name**: `gke-subnet`
- **Region**: `us-central1`
- **IP address range**: `10.0.1.0/24`
- **Secondary IP ranges**:
  - **Range name**: `gke-pods`, **IP range**: `10.1.0.0/16`
  - **Range name**: `gke-services`, **IP range**: `10.2.0.0/16`

**DNS Resolver Subnet:**
- **Name**: `dns-resolver-subnet`
- **Region**: `us-central1`
- **IP address range**: `10.0.2.0/24`

4. Click **"Create"**

### **2.3 Create Firewall Rules**
1. Go to **VPC network** → **Firewall**
2. Click **"Create Firewall Rule"**

**Rule 1: Allow Internal Traffic**
- **Name**: `trustlayer-allow-internal`
- **Direction**: Ingress
- **Targets**: All instances in the network
- **Source IP ranges**: `10.0.0.0/16`
- **Protocols and ports**: Allow all

**Rule 2: Allow External Access**
- **Name**: `trustlayer-allow-external`
- **Direction**: Ingress
- **Targets**: Specified target tags
- **Target tags**: `trustlayer-external`
- **Source IP ranges**: `0.0.0.0/0`
- **Protocols and ports**: TCP ports 80, 443, 8000, 8501

**Rule 3: Allow DNS**
- **Name**: `trustlayer-allow-dns`
- **Direction**: Ingress
- **Targets**: Specified target tags
- **Target tags**: `dns-forwarder`
- **Source IP ranges**: `0.0.0.0/0`
- **Protocols and ports**: TCP and UDP port 53

## 🔧 **Step 3: Create Redis Instance**

1. Go to **Memorystore** → **Redis**
2. Click **"Create Instance"**
3. Configure:
   - **Instance ID**: `trustlayer-redis`
   - **Display name**: `TrustLayer AI Redis`
   - **Tier**: Standard
   - **Capacity**: 1 GB
   - **Region**: `us-central1`
   - **Zone**: `us-central1-a`
   - **Network**: `trustlayer-vpc`
   - **IP range**: `10.0.3.0/29`
4. Click **"Create"**
5. **Note the Redis IP address** once created (e.g., `10.0.3.2`)

## ⚙️ **Step 4: Create GKE Cluster (Quota-Friendly)**

### **4.1 Check Your Current Quotas**
1. Go to **IAM & Admin** → **Quotas**
2. Check these quotas in your region:
   - **CPUs**: Should have at least 8 CPUs available
   - **IP addresses**: Should have at least 10 available
   - **Persistent disk storage**: Should have at least 100GB available

### **4.2 Create Minimal Cluster (Low Resource)**
1. Go to **Kubernetes Engine** → **Clusters**
2. Click **"Create"** → **"GKE Standard"**
3. Configure for **minimal resource usage**:

**Cluster Basics:**
- **Name**: `trustlayer-cluster`
- **Location type**: Zonal (uses fewer resources than regional)
- **Zone**: `us-central1-a`

**Networking:**
- **Network**: `trustlayer-vpc`
- **Node subnet**: `gke-subnet`
- **Pod address range**: `gke-pods`
- **Service address range**: `gke-services`
- **Enable private cluster**: No (to save IP quota)
- **Enable network policy**: No (to save resources)

**Security:**
- **Enable Workload Identity**: No (to save resources initially)
- **Enable Shielded nodes**: No (to save resources)

### **4.3 Configure Minimal Node Pool**
1. In the cluster creation, configure the default node pool:
   - **Machine type**: `e2-micro` (smallest available)
   - **Number of nodes**: 1 (minimum)
   - **Boot disk size**: 20GB (minimum)
   - **Boot disk type**: Standard persistent disk
   - **Enable autoscaling**: No (start with fixed size)
   - **Enable auto-upgrade**: No (to avoid disruptions)
   - **Enable auto-repair**: No (to avoid disruptions)

2. Click **"Create"**

**Expected Resource Usage:**
- CPUs: 2 (1 node × 2 vCPUs)
- Memory: 1GB
- Disk: 20GB
- IP addresses: ~5

### **4.4 Alternative: Use Cloud Run Instead**

If you still hit quota limits, use Cloud Run (serverless) instead:

1. Go to **Cloud Run**
2. Click **"Create Service"**
3. Configure:
   - **Service name**: `trustlayer-proxy`
   - **Region**: `us-central1`
   - **Container image URL**: `gcr.io/PROJECT_ID/trustlayer-ai:latest`
   - **CPU allocation**: 1 vCPU
   - **Memory**: 1GiB
   - **Maximum instances**: 2
   - **Ingress**: Allow all traffic

This uses almost no quota when idle!

## 🐳 **Step 5: Build and Push Container Images**

### **5.1 Set Up Local Environment**
```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Authenticate Docker
gcloud auth configure-docker

# Get cluster credentials
gcloud container clusters get-credentials trustlayer-cluster --region us-central1
```

### **5.2 Build Images**
```bash
# Build proxy image
docker build -t gcr.io/$PROJECT_ID/trustlayer-ai:latest .

# Build dashboard image
docker build -t gcr.io/$PROJECT_ID/trustlayer-ai-dashboard:latest -f gcp-deployment/Dockerfile.dashboard .

# Push images
docker push gcr.io/$PROJECT_ID/trustlayer-ai:latest
docker push gcr.io/$PROJECT_ID/trustlayer-ai-dashboard:latest
```

## 📦 **Step 6: Deploy to Kubernetes**

### **6.1 Update Kubernetes Manifests**
Update the image references in your Kubernetes files:

```bash
# Replace PROJECT_ID in all Kubernetes manifests
sed -i "s/PROJECT_ID/$PROJECT_ID/g" gcp-deployment/kubernetes/*.yaml
```

### **6.2 Create Namespace and RBAC**
```bash
kubectl apply -f gcp-deployment/kubernetes/namespace.yaml
kubectl apply -f gcp-deployment/kubernetes/rbac.yaml
```

### **6.3 Create ConfigMap with Redis IP**
Edit `gcp-deployment/kubernetes/configmap.yaml` and update the Redis host:
```yaml
redis:
  host: "10.0.3.2"  # Use your actual Redis IP
  port: 6379
```

Then apply:
```bash
kubectl apply -f gcp-deployment/kubernetes/configmap.yaml
```

### **6.4 Deploy Services**
```bash
# Deploy Redis (if not using Memorystore)
kubectl apply -f gcp-deployment/kubernetes/redis.yaml

# Deploy proxy service
kubectl apply -f gcp-deployment/kubernetes/proxy.yaml

# Deploy dashboard
kubectl apply -f gcp-deployment/kubernetes/dashboard.yaml

# Deploy ingress
kubectl apply -f gcp-deployment/kubernetes/ingress.yaml
```

### **6.5 Verify Deployment**
```bash
# Check pods
kubectl get pods -n trustlayer-ai

# Check services
kubectl get services -n trustlayer-ai

# Check ingress
kubectl get ingress -n trustlayer-ai
```

## 🌐 **Step 7: Create External Load Balancer**

### **7.1 Create External IP**
1. Go to **VPC network** → **External IP addresses**
2. Click **"Reserve Static Address"**
3. Configure:
   - **Name**: `trustlayer-external-ip`
   - **Network Service Tier**: Premium
   - **IP version**: IPv4
   - **Type**: Regional
   - **Region**: `us-central1`
4. Click **"Reserve"**
5. **Note the IP address** (e.g., `34.123.45.67`)

### **7.2 Create Load Balancer**
1. Go to **Network services** → **Load balancing**
2. Click **"Create Load Balancer"**
3. Choose **"HTTP(S) Load Balancing"** → **"Start configuration"**
4. Choose **"From Internet to my VMs or serverless services"**

**Backend Configuration:**
1. Click **"Backend services"** → **"Create a backend service"**
2. Configure:
   - **Name**: `trustlayer-backend`
   - **Backend type**: Network endpoint group
   - **Protocol**: HTTP
   - **Port**: 80
3. Click **"Create & add backends"**
4. Select your GKE ingress NEG
5. Click **"Done"**

**Frontend Configuration:**
1. Click **"Frontend configuration"**
2. Configure:
   - **Name**: `trustlayer-frontend`
   - **Protocol**: HTTP
   - **IP address**: Select your reserved IP
   - **Port**: 80
3. Click **"Done"**

**Review and Create:**
1. Click **"Review and finalize"**
2. Click **"Create"**

Wait 5-10 minutes for load balancer setup.

## 🔍 **Step 8: Set Up DNS Forwarder**

### **8.1 Create DNS Forwarder VM**
1. Go to **Compute Engine** → **VM instances**
2. Click **"Create Instance"**
3. Configure:
   - **Name**: `dns-forwarder`
   - **Region**: `us-central1`
   - **Zone**: `us-central1-a`
   - **Machine type**: `e2-micro`
   - **Boot disk**: Ubuntu 22.04 LTS
   - **Network**: `trustlayer-vpc`
   - **Subnet**: `dns-resolver-subnet`
   - **External IP**: Create IP address
   - **Network tags**: `dns-forwarder`

### **8.2 Configure DNS Forwarder**
SSH into the VM and run:

```bash
# Update system
sudo apt update && sudo apt install -y bind9 bind9utils

# Configure BIND9
sudo tee /etc/bind/named.conf.local <<EOF
zone "api.openai.com" {
    type forward;
    forwarders { 34.123.45.67; };  # Your load balancer IP
};

zone "api.anthropic.com" {
    type forward;
    forwarders { 34.123.45.67; };
};

zone "generativelanguage.googleapis.com" {
    type forward;
    forwarders { 34.123.45.67; };
};

zone "api.cohere.ai" {
    type forward;
    forwarders { 34.123.45.67; };
};
EOF

# Configure BIND9 options
sudo tee /etc/bind/named.conf.options <<EOF
options {
    directory "/var/cache/bind";
    recursion yes;
    allow-query { any; };
    forwarders {
        8.8.8.8;
        8.8.4.4;
    };
    forward only;
    dnssec-validation auto;
    listen-on-v6 { any; };
};
EOF

# Restart BIND9
sudo systemctl restart bind9
sudo systemctl enable bind9

# Test DNS
nslookup api.openai.com localhost
```

### **8.3 Note DNS Forwarder IP**
Get the external IP of your DNS forwarder VM (e.g., `35.123.45.68`)

## 🖥️ **Step 9: Configure Your Local System**

### **9.1 Update DNS Settings**

**Windows:**
1. Go to **Network Settings** → **Change adapter options**
2. Right-click your network connection → **Properties**
3. Select **Internet Protocol Version 4 (TCP/IPv4)** → **Properties**
4. Choose **"Use the following DNS server addresses"**
5. **Preferred DNS server**: `35.123.45.68` (your DNS forwarder IP)
6. **Alternate DNS server**: `8.8.8.8`
7. Click **OK**

**macOS:**
1. Go to **System Preferences** → **Network**
2. Select your network connection → **Advanced**
3. Go to **DNS** tab
4. Add DNS server: `35.123.45.68`
5. Click **OK** → **Apply**

**Linux:**
```bash
# Edit resolv.conf
sudo tee /etc/resolv.conf <<EOF
nameserver 35.123.45.68
nameserver 8.8.8.8
EOF
```

### **9.2 Test DNS Resolution**
```bash
# Test that AI API domains resolve to your load balancer
nslookup api.openai.com
# Should return your load balancer IP: 34.123.45.67

nslookup api.anthropic.com
# Should return your load balancer IP: 34.123.45.67
```

## 🧪 **Step 10: Test Your Setup**

### **10.1 Test Health Endpoint**
```bash
curl http://api.openai.com/health
# Should return: {"status": "healthy", "service": "TrustLayer AI Proxy"}
```

### **10.2 Test PII Detection**
```bash
curl -X POST http://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
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

### **10.3 Access Dashboard**
Open browser and go to: `http://34.123.45.67:8501`

You should see the TrustLayer AI dashboard showing:
- Real-time traffic metrics
- PII detection statistics
- System health status

## 📊 **Step 11: Monitor Your Deployment**

### **11.1 Check Kubernetes Status**
```bash
# Check all resources
kubectl get all -n trustlayer-ai

# Check logs
kubectl logs -f deployment/trustlayer-proxy -n trustlayer-ai
kubectl logs -f deployment/trustlayer-dashboard -n trustlayer-ai
```

### **11.2 Monitor in Google Cloud Console**
1. **GKE**: Monitor cluster health and node status
2. **Load Balancing**: Check traffic and backend health
3. **Memorystore**: Monitor Redis performance
4. **Logging**: View application logs
5. **Monitoring**: Set up alerts and dashboards

## � **Quota Issues? Here are Solutions**

### **Option A: Request Quota Increase**
1. Go to **IAM & Admin** → **Quotas**
2. Filter by your region (e.g., `us-central1`)
3. Find and select these quotas:
   - **CPUs** (increase to 16)
   - **IP addresses** (increase to 20)
   - **Persistent disk storage** (increase to 200GB)
4. Click **"Edit Quotas"** → **"Submit Request"**
5. **Wait 1-2 business days** for approval

### **Option B: Use Different Region**
Try regions with more available quota:
- `us-west1` (Oregon)
- `us-east1` (South Carolina)
- `europe-west1` (Belgium)

### **Option C: Ultra-Minimal Setup**
If still having issues, use this minimal configuration:

**Single e2-micro Node:**
- Machine type: `e2-micro`
- Nodes: 1
- Disk: 20GB
- No autoscaling
- No private cluster
- Zonal (not regional)

**Resource Usage:**
- CPUs: 2 vCPUs
- Memory: 1GB
- Disk: 20GB
- Cost: ~$5/month

### **Option D: Cloud Run Alternative (Recommended for Quota Issues)**

Instead of GKE, use Cloud Run which has virtually no quota limits:

1. **Skip GKE cluster creation**
2. **Use Cloud Run services** instead
3. **Follow Cloud Run deployment** (see Step 4.4 above)
4. **Much lower resource usage**
5. **Pay-per-use pricing**

## 🔄 **Continue with Cloud Run Path**

If you chose Cloud Run due to quota issues, follow these modified steps:

### **12.1 Add AI API Keys**
1. Go to **Security** → **Secret Manager**
2. Create secrets for your API keys:
   - `openai-api-key`
   - `anthropic-api-key`
   - `google-ai-api-key`

3. Update your Kubernetes deployment to use these secrets:
```yaml
env:
- name: OPENAI_API_KEY
  valueFrom:
    secretKeyRef:
      name: openai-api-key
      key: key
```

### **12.2 Set Up HTTPS**
1. Get SSL certificates for your domains
2. Update load balancer to use HTTPS
3. Configure certificate management

### **12.3 Scale for Production**
```bash
# Scale proxy deployment
kubectl scale deployment trustlayer-proxy --replicas=3 -n trustlayer-ai

# Enable cluster autoscaling
gcloud container clusters update trustlayer-cluster \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10 \
  --region=us-central1
```

## 🎯 **How It Works**

1. **Your application makes API call** to `api.openai.com`
2. **DNS resolves** to your GCP Load Balancer IP (`34.123.45.67`)
3. **Load Balancer forwards** to TrustLayer AI proxy in GKE
4. **Proxy detects and redacts PII** from your request
5. **Proxy forwards sanitized request** to real OpenAI API
6. **OpenAI responds** with sanitized data
7. **Proxy restores PII** in the response
8. **Your application receives** the complete response

### **Cloud Run Deployment Steps (Alternative to GKE):**

If you chose Cloud Run due to quota issues, follow these steps instead of Steps 5-11:

**Step 5-CR: Deploy to Cloud Run**
```bash
# Set your project
export PROJECT_ID="your-project-id"

# Deploy proxy service
gcloud run deploy trustlayer-proxy \
  --image gcr.io/$PROJECT_ID/trustlayer-ai:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 2 \
  --port 8000 \
  --set-env-vars REDIS_HOST=10.0.3.2,REDIS_PORT=6379

# Deploy dashboard service  
gcloud run deploy trustlayer-dashboard \
  --image gcr.io/$PROJECT_ID/trustlayer-ai-dashboard:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 1 \
  --port 8501
```

**Step 6-CR: Get Service URLs**
```bash
# Get proxy URL
PROXY_URL=$(gcloud run services describe trustlayer-proxy --region us-central1 --format 'value(status.url)')

# Get dashboard URL  
DASHBOARD_URL=$(gcloud run services describe trustlayer-dashboard --region us-central1 --format 'value(status.url)')

echo "Proxy URL: $PROXY_URL"
echo "Dashboard URL: $DASHBOARD_URL"

# Extract IP from URL for DNS configuration
PROXY_IP=$(nslookup $(echo $PROXY_URL | sed 's|https://||' | sed 's|http://||') | grep Address | tail -1 | awk '{print $2}')
echo "Proxy IP for DNS: $PROXY_IP"
```

**Step 7-CR: Test Cloud Run Deployment**
```bash
# Test proxy health
curl $PROXY_URL/health

# Test dashboard
curl -I $DASHBOARD_URL
```

**Step 8-CR: Configure DNS for Cloud Run**
Use the proxy IP in your DNS forwarder configuration instead of a load balancer IP.

## 💰 **Cost Comparison**

**GKE Cluster (if you have quota):**
- Cost: ~$148-228/month
- Resources: Always running
- Better for high traffic

**Cloud Run (quota-friendly):**
- Cost: ~$10-30/month
- Resources: Pay-per-use
- Perfect for getting started

## 🔧 **Production Configuration**

## 🚨 **Troubleshooting**

### **DNS Not Working**
```bash
# Check DNS forwarder
ssh dns-forwarder
sudo systemctl status bind9
sudo journalctl -u bind9

# Test local DNS
nslookup api.openai.com
```

### **Pods Not Starting**
```bash
# Check pod status
kubectl describe pod <pod-name> -n trustlayer-ai

# Check logs
kubectl logs <pod-name> -n trustlayer-ai
```

### **Load Balancer Issues**
1. Check backend health in Google Cloud Console
2. Verify firewall rules allow traffic
3. Check ingress configuration

## 🎉 **Success!**

Your TrustLayer AI system is now running on GKE with DNS integration! All AI API calls from your system will now:

✅ **Route through your proxy** automatically  
✅ **Have PII detected and redacted** before reaching AI APIs  
✅ **Get PII restored** in responses  
✅ **Be monitored and logged** in your dashboard  
✅ **Scale automatically** based on demand  

Your AI interactions are now secure and compliant! 🛡️