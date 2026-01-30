# 🚨 GCP Quota Issues - Quick Solutions

You're hitting GCP quota limits. Here are immediate solutions:

## 🎯 **Immediate Solution: Use Cloud Run**

Cloud Run has virtually no quota limits and is perfect for getting started:

### **Quick Cloud Run Deployment:**

```bash
# Set your project
export PROJECT_ID="your-project-id"

# Build and push images (if not done already)
docker build -t gcr.io/$PROJECT_ID/trustlayer-ai:latest .
docker build -t gcr.io/$PROJECT_ID/trustlayer-ai-dashboard:latest -f gcp-deployment/Dockerfile.dashboard .
docker push gcr.io/$PROJECT_ID/trustlayer-ai:latest
docker push gcr.io/$PROJECT_ID/trustlayer-ai-dashboard:latest

# Deploy proxy service
gcloud run deploy trustlayer-proxy \
  --image gcr.io/$PROJECT_ID/trustlayer-ai:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 2 \
  --port 8000

# Deploy dashboard service
gcloud run deploy trustlayer-dashboard \
  --image gcr.io/$PROJECT_ID/trustlayer-ai-dashboard:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 1 \
  --port 8501

# Get URLs
echo "Proxy URL: $(gcloud run services describe trustlayer-proxy --region us-central1 --format 'value(status.url)')"
echo "Dashboard URL: $(gcloud run services describe trustlayer-dashboard --region us-central1 --format 'value(status.url)')"
```

### **Test Your Deployment:**
```bash
# Get proxy URL
PROXY_URL=$(gcloud run services describe trustlayer-proxy --region us-central1 --format 'value(status.url)')

# Test health endpoint
curl $PROXY_URL/health

# Should return: {"status": "healthy", "service": "TrustLayer AI Proxy"}
```

## 🔧 **Long-term Solutions**

### **Option 1: Request Quota Increase**
1. Go to [GCP Quotas](https://console.cloud.google.com/iam-admin/quotas)
2. Filter by region: `us-central1`
3. Request increases for:
   - **CPUs**: 16 (currently you have ~2-4)
   - **IP addresses**: 20 (currently you have ~5-10)
   - **Persistent disk storage**: 200GB (currently you have ~50-100GB)
4. Submit request (takes 1-2 business days)

### **Option 2: Try Different Region**
Some regions have more available quota:
- `us-west1` (Oregon)
- `us-east1` (South Carolina)  
- `europe-west1` (Belgium)

### **Option 3: Ultra-Minimal GKE**
If you want to try GKE with minimal resources:
- **1 node** with `e2-micro` (2 vCPUs, 1GB RAM)
- **20GB disk**
- **Zonal** (not regional)
- **No autoscaling**
- **No private cluster**

## 💰 **Cost Comparison**

**Cloud Run (Recommended for now):**
- **Cost**: $5-20/month
- **Quota usage**: Almost none
- **Scaling**: Automatic (0 to N)
- **Perfect for**: Getting started, low traffic

**Minimal GKE:**
- **Cost**: $25-50/month  
- **Quota usage**: 2 CPUs, 20GB disk
- **Scaling**: Manual
- **Perfect for**: Learning Kubernetes

**Full GKE (after quota increase):**
- **Cost**: $150-250/month
- **Quota usage**: 8+ CPUs, 100+ GB disk
- **Scaling**: Full auto-scaling
- **Perfect for**: Production workloads

## 🎯 **Recommendation**

**Start with Cloud Run** to get TrustLayer AI working immediately, then:

1. **Request quota increases** in parallel
2. **Test and validate** your setup with Cloud Run
3. **Migrate to GKE** later when quotas are approved

Cloud Run will give you the same functionality with:
- ✅ **No quota issues**
- ✅ **Lower costs**
- ✅ **Automatic scaling**
- ✅ **Same PII protection**
- ✅ **Same monitoring**

## 🚀 **Next Steps**

1. **Deploy with Cloud Run** using the commands above
2. **Test your setup** with the health endpoint
3. **Configure DNS** to point to your Cloud Run URLs
4. **Request quota increases** for future GKE migration

Your TrustLayer AI will work perfectly on Cloud Run! 🛡️