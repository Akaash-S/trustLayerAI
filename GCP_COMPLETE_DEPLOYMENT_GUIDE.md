# 🚀 TrustLayer AI - Complete GCP Deployment Guide (From Scratch)

This guide will take you from zero to a fully deployed TrustLayer AI system on Google Cloud Platform in about 30-45 minutes.

## 📋 **Prerequisites Checklist**

Before starting, ensure you have:

- [ ] **Google Cloud Account** with billing enabled
- [ ] **Local machine** with internet access (Windows/Mac/Linux)
- [ ] **Admin access** to install software on your machine
- [ ] **Credit card** for GCP billing (free tier available)

## 🛠️ **Step 1: Set Up Your Local Environment**

### **1.1 Install Required Tools**

#### **Install Google Cloud CLI**
```bash
# Windows (PowerShell as Administrator)
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe

# macOS
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

#### **Install Terraform**
```bash
# Windows (PowerShell as Administrator)
choco install terraform

# macOS
brew install terraform

# Linux (Ubuntu/Debian)
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

#### **Install Docker**
```bash
# Windows: Download Docker Desktop from https://www.docker.com/products/docker-desktop
# macOS: Download Docker Desktop from https://www.docker.com/products/docker-desktop
# Linux (Ubuntu):
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
```

#### **Install Git**
```bash
# Windows: Download from https://git-scm.com/download/win
# macOS: 
brew install git
# Linux:
sudo apt install git
```

### **1.2 Verify Installations**
```bash
# Check all tools are installed
gcloud version
terraform version
docker --version
git --version
```

## 🏗️ **Step 2: Set Up Google Cloud Project**

### **2.1 Create a New GCP Project**

1. **Go to Google Cloud Console**: https://console.cloud.google.com
2. **Click "Select a project"** → **"New Project"**
3. **Enter project details**:
   - Project name: `trustlayer-ai-suite`
   - Project ID: `trustlayer-ai-[random-id]` (must be globally unique)
   - Organization: Select your organization (if applicable)
4. **Click "Create"**

### **2.2 Enable Billing**

1. **Go to Billing**: https://console.cloud.google.com/billing
2. **Link your project** to a billing account
3. **Verify billing is enabled** for your project

### **2.3 Set Up Local Authentication**

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set your project ID (replace with your actual project ID)
export PROJECT_ID="trustlayer-ai-your-unique-id"
gcloud config set project $PROJECT_ID

# Verify authentication
gcloud auth list
gcloud config get-value project
```

## 📦 **Step 3: Get the TrustLayer AI Code**

### **3.1 Clone or Download the Repository**

If you have the code in a repository:
```bash
git clone https://github.com/your-username/trustlayer-ai.git
cd trustlayer-ai
```

If you're starting fresh, create the project structure:
```bash
mkdir trustlayer-ai
cd trustlayer-ai

# Create the basic structure
mkdir -p app gcp-deployment/terraform gcp-deployment/kubernetes
```

### **3.2 Verify Project Structure**

Your project should look like this:
```
trustlayer-ai/
├── app/
│   ├── main.py
│   ├── redactor.py
│   ├── telemetry.py
│   └── extractors.py
├── gcp-deployment/
│   ├── terraform/
│   ├── kubernetes/
│   ├── cloudbuild.yaml
│   ├── deploy.sh
│   └── Dockerfile.dashboard
├── dashboard.py
├── config.yaml
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## ⚙️ **Step 4: Configure the Deployment**

### **4.1 Set Environment Variables**

```bash
# Set your configuration
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export ZONE="us-central1-a"
export ENVIRONMENT="prod"
export NOTIFICATION_EMAIL="your-email@company.com"

# Verify variables
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Email: $NOTIFICATION_EMAIL"
```

### **4.2 Enable Required Google Cloud APIs**

```bash
# Enable all required APIs (this may take 2-3 minutes)
gcloud services enable \
  run.googleapis.com \
  compute.googleapis.com \
  dns.googleapis.com \
  vpcaccess.googleapis.com \
  redis.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  binaryauthorization.googleapis.com \
  containeranalysis.googleapis.com \
  cloudkms.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled --filter="name:run.googleapis.com OR name:compute.googleapis.com"
```

## 🐳 **Step 5: Build and Push Container Images**

### **5.1 Configure Docker for Google Container Registry**

```bash
# Configure Docker authentication
gcloud auth configure-docker

# Verify Docker is working
docker run hello-world
```

### **5.2 Build the Main Application Container**

```bash
# Build the TrustLayer AI proxy container
docker build -t gcr.io/$PROJECT_ID/trustlayer-ai:latest .

# Verify the build
docker images | grep trustlayer-ai
```

### **5.3 Build the Dashboard Container**

```bash
# Build the dashboard container
docker build -t gcr.io/$PROJECT_ID/trustlayer-ai-dashboard:latest -f gcp-deployment/Dockerfile.dashboard .

# Verify both images
docker images | grep gcr.io/$PROJECT_ID
```

### **5.4 Push Images to Google Container Registry**

```bash
# Push both images (this may take 5-10 minutes depending on your internet speed)
docker push gcr.io/$PROJECT_ID/trustlayer-ai:latest
docker push gcr.io/$PROJECT_ID/trustlayer-ai-dashboard:latest

# Verify images in registry
gcloud container images list --repository=gcr.io/$PROJECT_ID
```

## 🏗️ **Step 6: Deploy Infrastructure with Terraform**

### **6.1 Initialize Terraform**

```bash
# Navigate to Terraform directory
cd gcp-deployment/terraform

# Initialize Terraform (downloads providers)
terraform init

# Verify initialization
ls -la .terraform/
```

### **6.2 Create Terraform Variables File**

```bash
# Create terraform.tfvars file with your configuration
cat > terraform.tfvars <<EOF
project_id = "$PROJECT_ID"
region = "$REGION"
zone = "$ZONE"
environment = "$ENVIRONMENT"
domain_name = "trustlayer.internal"
container_image = "gcr.io/$PROJECT_ID/trustlayer-ai:latest"
dashboard_image = "gcr.io/$PROJECT_ID/trustlayer-ai-dashboard:latest"
enable_monitoring = true
enable_cloud_armor = true
notification_email = "$NOTIFICATION_EMAIL"
min_instances = 1
max_instances = 5
cpu_limit = "2"
memory_limit = "4Gi"
redis_memory_size_gb = 1
EOF

# Verify the file
cat terraform.tfvars
```

### **6.3 Plan the Deployment**

```bash
# Create deployment plan
terraform plan -var-file=terraform.tfvars

# Review the plan - you should see ~30-40 resources to be created
```

### **6.4 Deploy the Infrastructure**

```bash
# Apply the Terraform configuration (this takes 10-15 minutes)
terraform apply -var-file=terraform.tfvars -auto-approve

# Wait for completion and note the outputs
```

### **6.5 Get Deployment Information**

```bash
# Get important outputs
export LOAD_BALANCER_IP=$(terraform output -raw load_balancer_ip)
export VPC_CONNECTOR=$(terraform output -raw vpc_connector_id)
export SERVICE_ACCOUNT=$(terraform output -raw service_account_email)

echo "Load Balancer IP: $LOAD_BALANCER_IP"
echo "VPC Connector: $VPC_CONNECTOR"
echo "Service Account: $SERVICE_ACCOUNT"
```

## 🚀 **Step 7: Deploy Applications with Cloud Build**

### **7.1 Update Cloud Build Configuration**

```bash
# Go back to project root
cd ../..

# Update the cloudbuild.yaml substitutions with your values
sed -i "s/PROJECT_ID/$PROJECT_ID/g" gcp-deployment/cloudbuild.yaml
sed -i "s/us-central1/$REGION/g" gcp-deployment/cloudbuild.yaml
sed -i "s/us-central1-a/$ZONE/g" gcp-deployment/cloudbuild.yaml
```

### **7.2 Run Cloud Build Pipeline**

```bash
# Submit the build (this takes 15-20 minutes)
gcloud builds submit \
  --config=gcp-deployment/cloudbuild.yaml \
  --substitutions=_REGION="$REGION",_ZONE="$ZONE",_ENVIRONMENT="$ENVIRONMENT",_DOMAIN_NAME="trustlayer.internal",_VPC_CONNECTOR="$VPC_CONNECTOR",_SERVICE_ACCOUNT="$SERVICE_ACCOUNT",_LOAD_BALANCER_IP="$LOAD_BALANCER_IP" \
  .

# Monitor the build progress
gcloud builds list --limit=5
```

## 🧪 **Step 8: Test Your Deployment**

### **8.1 Wait for Services to Start**

```bash
# Wait for services to be ready (2-3 minutes)
echo "Waiting for services to start..."
sleep 180
```

### **8.2 Test Health Endpoints**

```bash
# Test the proxy health endpoint
echo "Testing proxy health..."
curl -H "Host: api.trustlayer.internal" http://$LOAD_BALANCER_IP/health

# Expected response: {"status": "healthy", "service": "TrustLayer AI Proxy"}
```

### **8.3 Test Metrics Endpoint**

```bash
# Test the metrics endpoint
echo "Testing metrics..."
curl -H "Host: api.trustlayer.internal" http://$LOAD_BALANCER_IP/metrics

# Expected response: JSON with telemetry data
```

### **8.4 Test Dashboard**

```bash
# Test dashboard accessibility
echo "Testing dashboard..."
curl -I -H "Host: dashboard.trustlayer.internal" http://$LOAD_BALANCER_IP

# Expected response: HTTP 200 OK
```

### **8.5 Test PII Detection (Optional)**

```bash
# Test PII detection with sample data
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Host: api.trustlayer.internal" \
  -d '{
    "messages": [
      {
        "role": "user", 
        "content": "My name is John Doe and my email is john.doe@example.com. My phone number is 555-123-4567."
      }
    ]
  }' \
  http://$LOAD_BALANCER_IP/v1/chat/completions

# This should show PII redaction in action
```

## 🎯 **Step 9: Access Your Deployment**

### **9.1 Get Access Information**

```bash
# Display connection information
echo "🎉 TrustLayer AI Deployment Complete!"
echo "======================================"
echo ""
echo "📍 Access Information:"
echo "Load Balancer IP: $LOAD_BALANCER_IP"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""
echo "🔗 Service URLs:"
echo "API Health: http://$LOAD_BALANCER_IP/health"
echo "API Metrics: http://$LOAD_BALANCER_IP/metrics"
echo "Dashboard: http://$LOAD_BALANCER_IP:8501"
echo ""
echo "🌐 Internal URLs (from within GCP):"
echo "API: http://api.trustlayer.internal"
echo "Dashboard: http://dashboard.trustlayer.internal"
```

### **9.2 Access the Dashboard**

1. **Open your browser** and go to: `http://LOAD_BALANCER_IP:8501`
2. **You should see** the TrustLayer AI Dashboard
3. **The dashboard will show**:
   - Real-time traffic metrics
   - PII detection statistics
   - System health status
   - Compliance scores

### **9.3 Set Up DNS (Optional)**

If you want to access via custom domain:

```bash
# Create a DNS record pointing to your load balancer IP
# This depends on your DNS provider (Cloudflare, Route53, etc.)
# Example for Google Cloud DNS:

gcloud dns record-sets transaction start --zone=your-zone
gcloud dns record-sets transaction add $LOAD_BALANCER_IP --name=trustlayer.yourdomain.com. --ttl=300 --type=A --zone=your-zone
gcloud dns record-sets transaction execute --zone=your-zone
```

## 📊 **Step 10: Monitor Your Deployment**

### **10.1 Access Google Cloud Console**

1. **Go to**: https://console.cloud.google.com
2. **Select your project**: `trustlayer-ai-[your-id]`
3. **Navigate to**:
   - **Cloud Run**: See your running services
   - **Monitoring**: View metrics and alerts
   - **Logging**: Check application logs

### **10.2 Set Up Monitoring Alerts**

```bash
# Create a simple uptime alert
gcloud alpha monitoring policies create --policy-from-file=- <<EOF
{
  "displayName": "TrustLayer AI Uptime Alert",
  "conditions": [
    {
      "displayName": "API Health Check",
      "conditionThreshold": {
        "filter": "resource.type=\"uptime_url\"",
        "comparison": "COMPARISON_EQUAL",
        "thresholdValue": 0,
        "duration": "300s"
      }
    }
  ],
  "notificationChannels": [],
  "alertStrategy": {
    "autoClose": "1800s"
  }
}
EOF
```

## 💰 **Step 11: Understand Your Costs**

### **11.1 Current Cost Breakdown**

Your deployment will cost approximately:

- **Cloud Run (Proxy)**: $10-50/month (based on usage)
- **Cloud Run (Dashboard)**: $5-20/month (based on usage)
- **Cloud Memorystore (Redis)**: ~$45/month (1GB Standard HA)
- **Internal Load Balancer**: ~$18/month
- **VPC Connector**: ~$9/month
- **Monitoring & Logging**: $5-15/month
- **Storage & Networking**: $1-5/month

**Total Estimated Cost**: $93-162/month

### **11.2 Set Up Budget Alerts**

```bash
# Create a budget alert
gcloud billing budgets create \
  --billing-account=$(gcloud billing accounts list --format="value(name)" --limit=1) \
  --display-name="TrustLayer AI Budget" \
  --budget-amount=200 \
  --threshold-percent=50,90 \
  --threshold-percent=100
```

## 🔧 **Step 12: Configure for Production Use**

### **12.1 Add Your AI API Keys**

1. **Go to Google Secret Manager**: https://console.cloud.google.com/security/secret-manager
2. **Create secrets** for your AI API keys:
   - `openai-api-key`
   - `anthropic-api-key`
   - `google-ai-api-key`

3. **Update your Cloud Run services** to use these secrets:

```bash
# Update the proxy service with API keys
gcloud run services update trustlayer-ai-proxy \
  --region=$REGION \
  --set-secrets=OPENAI_API_KEY=openai-api-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest
```

### **12.2 Configure Custom Domains (Optional)**

If you have a custom domain:

```bash
# Map your domain to Cloud Run
gcloud run domain-mappings create \
  --service=trustlayer-ai-proxy \
  --domain=api.yourdomain.com \
  --region=$REGION
```

### **12.3 Set Up SSL Certificates**

```bash
# Create managed SSL certificate
gcloud compute ssl-certificates create trustlayer-ssl-cert \
  --domains=api.yourdomain.com,dashboard.yourdomain.com \
  --global
```

## 🛡️ **Step 13: Security Hardening**

### **13.1 Review IAM Permissions**

```bash
# List current IAM bindings
gcloud projects get-iam-policy $PROJECT_ID

# Remove any unnecessary permissions
# Add specific users/groups as needed
```

### **13.2 Enable Additional Security Features**

```bash
# Enable Security Command Center (if available)
gcloud services enable securitycenter.googleapis.com

# Enable Binary Authorization
gcloud container binauthz policy import policy.yaml
```

### **13.3 Set Up VPC Firewall Rules**

```bash
# Review current firewall rules
gcloud compute firewall-rules list

# The Terraform deployment already created secure rules
# Verify no unnecessary ports are open
```

## 🚨 **Troubleshooting Common Issues**

### **Issue 1: Build Failures**

```bash
# Check build logs
gcloud builds log $(gcloud builds list --limit=1 --format="value(id)")

# Common fixes:
# - Verify Docker images were pushed successfully
# - Check API quotas and limits
# - Ensure billing is enabled
```

### **Issue 2: Service Not Starting**

```bash
# Check Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trustlayer-ai-proxy" --limit=50

# Common fixes:
# - Check environment variables
# - Verify Redis connectivity
# - Check resource limits
```

### **Issue 3: Network Connectivity**

```bash
# Test internal connectivity
gcloud compute ssh test-vm --zone=$ZONE --command="curl -H 'Host: api.trustlayer.internal' http://$LOAD_BALANCER_IP/health"

# Common fixes:
# - Verify VPC connector is working
# - Check firewall rules
# - Ensure DNS resolution is working
```

### **Issue 4: High Costs**

```bash
# Check current usage
gcloud billing budgets list
gcloud monitoring metrics list

# Cost optimization:
# - Reduce min_instances to 0 for development
# - Use smaller Redis instance
# - Enable request-based scaling
```

## 🎉 **Congratulations!**

You have successfully deployed TrustLayer AI on Google Cloud Platform! Your system now provides:

✅ **Enterprise-grade AI governance** with automatic PII detection and redaction  
✅ **Scalable serverless architecture** that handles traffic spikes automatically  
✅ **Complete security** with private networking and Cloud Armor protection  
✅ **Real-time monitoring** with comprehensive dashboards and alerting  
✅ **Cost optimization** with pay-per-use pricing and auto-scaling  

## 📞 **Next Steps**

1. **Start using your AI proxy** by pointing your applications to `http://api.trustlayer.internal`
2. **Monitor the dashboard** at `http://LOAD_BALANCER_IP:8501`
3. **Set up your AI API keys** in Google Secret Manager
4. **Configure custom domains** if needed
5. **Set up additional monitoring** and alerting as required

## 📚 **Additional Resources**

- **Google Cloud Documentation**: https://cloud.google.com/docs
- **Terraform GCP Provider**: https://registry.terraform.io/providers/hashicorp/google/latest/docs
- **Cloud Run Documentation**: https://cloud.google.com/run/docs
- **Monitoring Documentation**: https://cloud.google.com/monitoring/docs

---

**Your TrustLayer AI system is now live and protecting your AI interactions with enterprise-grade security!** 🛡️🚀