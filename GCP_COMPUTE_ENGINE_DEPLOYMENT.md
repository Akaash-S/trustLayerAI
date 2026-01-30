# 🚀 TrustLayer AI - Google Compute Engine Deployment Guide

Complete step-by-step guide to deploy TrustLayer AI on Google Compute Engine VMs. This approach is simpler, more cost-effective, and avoids GKE quota issues.

## 🎯 **Architecture Overview**

```
Your Local System → Custom DNS → GCP Load Balancer → Compute Engine VMs → AI APIs
                                        ↓
                                  TrustLayer AI Proxy
                                  Redis Instance
                                  Dashboard
```

**Benefits of Compute Engine vs GKE:**
- ✅ **Lower Cost**: ~$30-50/month vs $150+/month for GKE
- ✅ **No Quota Issues**: Standard VM quotas are much higher
- ✅ **Simpler Setup**: Direct VM management, no Kubernetes complexity
- ✅ **Better Control**: Full access to underlying infrastructure
- ✅ **Easier Debugging**: Direct SSH access to VMs

## 📋 **Prerequisites**

- Google Cloud account with billing enabled
- Local machine with `gcloud` CLI installed
- Basic knowledge of Linux and Docker
- Domain name (optional, for custom DNS)

## 🏗️ **Step 1: Create GCP Project and Setup**

### **1.1 Create Project**
```bash
# Set project variables
export PROJECT_ID="trustlayer-ai-suite"
export REGION="us-central1"
export ZONE="us-central1-a"

# Create project
gcloud projects create $PROJECT_ID --name="TrustLayer AI"
gcloud config set project $PROJECT_ID

# Enable billing (replace BILLING_ACCOUNT_ID with your billing account)
# Get billing account: gcloud billing accounts list
gcloud billing projects link $PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

### **1.2 Enable Required APIs**
```bash
# Enable all required APIs
gcloud services enable compute.googleapis.com
gcloud services enable dns.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### **1.3 Set Default Region/Zone**
```bash
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE
```

## 🌐 **Step 2: Create VPC Network**

### **2.1 Create VPC and Subnets**
```bash
# Create VPC
gcloud compute networks create trustlayer-vpc --subnet-mode=custom

# Create main subnet for VMs
gcloud compute networks subnets create trustlayer-subnet \
    --network=trustlayer-vpc \
    --range=10.0.1.0/24 \
    --region=$REGION

# Create subnet for Redis
gcloud compute networks subnets create redis-subnet \
    --network=trustlayer-vpc \
    --range=10.0.2.0/24 \
    --region=$REGION
```

### **2.2 Create Firewall Rules**
```bash
# Allow internal traffic
gcloud compute firewall-rules create trustlayer-allow-internal \
    --network=trustlayer-vpc \
    --allow=tcp,udp,icmp \
    --source-ranges=10.0.0.0/16

# Allow SSH
gcloud compute firewall-rules create trustlayer-allow-ssh \
    --network=trustlayer-vpc \
    --allow=tcp:22 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=trustlayer-vm

# Allow HTTP/HTTPS and custom ports
gcloud compute firewall-rules create trustlayer-allow-web \
    --network=trustlayer-vpc \
    --allow=tcp:80,tcp:443,tcp:8000,tcp:8501 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=trustlayer-web

# Allow health checks
gcloud compute firewall-rules create trustlayer-allow-health-check \
    --network=trustlayer-vpc \
    --allow=tcp:8000 \
    --source-ranges=130.211.0.0/22,35.191.0.0/16 \
    --target-tags=trustlayer-web
```

## 🔧 **Step 3: Create Redis Instance**

```bash
# Create Redis instance
gcloud redis instances create trustlayer-redis \
    --size=1 \
    --region=$REGION \
    --network=trustlayer-vpc \
    --redis-version=redis_7_0

# Get Redis IP (save this for later)
export REDIS_IP=$(gcloud redis instances describe trustlayer-redis --region=$REGION --format="value(host)")
echo "Redis IP: $REDIS_IP"
```

## 🖥️ **Step 4: Create Compute Engine VMs**

### **4.1 Create Startup Script**
```bash
# Create startup script for TrustLayer AI
cat > startup-script.sh << 'EOF'
#!/bin/bash

# Update system
apt-get update
apt-get install -y docker.io docker-compose git curl

# Start Docker
systemctl start docker
systemctl enable docker

# Add user to docker group
usermod -aG docker $USER

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create app directory
mkdir -p /opt/trustlayer-ai
cd /opt/trustlayer-ai

# Clone repository (replace with your repo)
git clone https://github.com/your-org/trustlayer-ai.git .

# Create production config
cat > config.yaml << 'YAML_EOF'
proxy:
  host: "0.0.0.0"
  port: 8000
  
allowed_domains:
  - "api.openai.com"
  - "api.anthropic.com"
  - "generativelanguage.googleapis.com"
  - "api.cohere.ai"

redis:
  host: "REDIS_IP_PLACEHOLDER"
  port: 6379
  db: 0
  session_ttl: 3600

presidio:
  entities:
    - "PERSON"
    - "EMAIL_ADDRESS"
    - "PHONE_NUMBER"
    - "CREDIT_CARD"
    - "IBAN_CODE"
    - "IP_ADDRESS"
    - "LOCATION"
    - "ORGANIZATION"
    - "DATE_TIME"
    - "MEDICAL_LICENSE"
    - "US_SSN"
    - "IN_PAN"
    - "IN_AADHAAR"

security:
  prompt_injection_patterns:
    - "ignore previous instructions"
    - "forget everything"
    - "act as"
    - "pretend to be"
    - "roleplay"
    - "system prompt"
    - "override"

dashboard:
  host: "0.0.0.0"
  port: 8501
YAML_EOF

# Replace Redis IP placeholder
sed -i "s/REDIS_IP_PLACEHOLDER/$REDIS_IP/g" config.yaml

# Create production docker-compose
cat > docker-compose.prod.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  # TrustLayer AI Proxy
  proxy:
    build: .
    container_name: trustlayer-proxy
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
    environment:
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 90s

  # Streamlit Dashboard
  dashboard:
    build: .
    container_name: trustlayer-dashboard
    ports:
      - "8501:8501"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./dashboard.py:/app/dashboard.py:ro
    environment:
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
    depends_on:
      - proxy
    restart: unless-stopped
    command: streamlit run dashboard.py --server.address 0.0.0.0 --server.port 8501 --server.headless true

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: trustlayer-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - proxy
      - dashboard
    restart: unless-stopped
COMPOSE_EOF

# Create Nginx config
cat > nginx.conf << 'NGINX_EOF'
events {
    worker_connections 1024;
}

http {
    upstream proxy_backend {
        server proxy:8000;
    }
    
    upstream dashboard_backend {
        server dashboard:8501;
    }

    # Proxy service
    server {
        listen 80;
        server_name _;
        
        # Health check endpoint
        location /health {
            proxy_pass http://proxy_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        # Metrics endpoint
        location /metrics {
            proxy_pass http://proxy_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        # Dashboard
        location /dashboard {
            proxy_pass http://dashboard_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support for Streamlit
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        
        # Main proxy (catch-all)
        location / {
            proxy_pass http://proxy_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
NGINX_EOF

# Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Create systemd service for auto-start
cat > /etc/systemd/system/trustlayer-ai.service << 'SERVICE_EOF'
[Unit]
Description=TrustLayer AI Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/trustlayer-ai
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl enable trustlayer-ai.service
systemctl start trustlayer-ai.service

# Log startup completion
echo "TrustLayer AI startup completed at $(date)" >> /var/log/trustlayer-startup.log
EOF

# Replace Redis IP in startup script
sed -i "s/\$REDIS_IP/$REDIS_IP/g" startup-script.sh
```

### **4.2 Create Primary VM**
```bash
# Create main TrustLayer AI VM
gcloud compute instances create trustlayer-ai-main \
    --zone=$ZONE \
    --machine-type=e2-standard-2 \
    --network-interface=network-tier=PREMIUM,subnet=trustlayer-subnet \
    --metadata-from-file startup-script=startup-script.sh \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --tags=trustlayer-vm,trustlayer-web \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=50GB \
    --boot-disk-type=pd-standard \
    --boot-disk-device-name=trustlayer-ai-main

# Get VM IP
export VM_IP=$(gcloud compute instances describe trustlayer-ai-main --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
echo "VM IP: $VM_IP"
```

### **4.3 Create Backup VM (Optional)**
```bash
# Create backup VM for high availability
gcloud compute instances create trustlayer-ai-backup \
    --zone=us-central1-b \
    --machine-type=e2-standard-2 \
    --network-interface=network-tier=PREMIUM,subnet=trustlayer-subnet \
    --metadata-from-file startup-script=startup-script.sh \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --tags=trustlayer-vm,trustlayer-web \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=50GB \
    --boot-disk-type=pd-standard \
    --boot-disk-device-name=trustlayer-ai-backup
```

## ⚖️ **Step 5: Create Load Balancer**

### **5.1 Create Instance Groups**
```bash
# Create instance group for main VM
gcloud compute instance-groups unmanaged create trustlayer-ig-main \
    --zone=$ZONE

gcloud compute instance-groups unmanaged add-instances trustlayer-ig-main \
    --instances=trustlayer-ai-main \
    --zone=$ZONE

# Set named port for health checks
gcloud compute instance-groups unmanaged set-named-ports trustlayer-ig-main \
    --named-ports=http:8000 \
    --zone=$ZONE

# Create instance group for backup VM (if created)
# gcloud compute instance-groups unmanaged create trustlayer-ig-backup \
#     --zone=us-central1-b
# gcloud compute instance-groups unmanaged add-instances trustlayer-ig-backup \
#     --instances=trustlayer-ai-backup \
#     --zone=us-central1-b
```

### **5.2 Create Health Check**
```bash
# Create health check
gcloud compute health-checks create http trustlayer-health-check \
    --port=8000 \
    --request-path=/health \
    --check-interval=30s \
    --timeout=10s \
    --healthy-threshold=2 \
    --unhealthy-threshold=3
```

### **5.3 Create Backend Service**
```bash
# Create backend service
gcloud compute backend-services create trustlayer-backend-service \
    --protocol=HTTP \
    --port-name=http \
    --health-checks=trustlayer-health-check \
    --global

# Add instance group to backend service
gcloud compute backend-services add-backend trustlayer-backend-service \
    --instance-group=trustlayer-ig-main \
    --instance-group-zone=$ZONE \
    --global
```

### **5.4 Create URL Map and Proxy**
```bash
# Create URL map
gcloud compute url-maps create trustlayer-url-map \
    --default-service=trustlayer-backend-service

# Create HTTP proxy
gcloud compute target-http-proxies create trustlayer-http-proxy \
    --url-map=trustlayer-url-map
```

### **5.5 Create Global Forwarding Rule**
```bash
# Reserve static IP
gcloud compute addresses create trustlayer-ip --global

# Get the reserved IP
export LOAD_BALANCER_IP=$(gcloud compute addresses describe trustlayer-ip --global --format="value(address)")
echo "Load Balancer IP: $LOAD_BALANCER_IP"

# Create forwarding rule
gcloud compute forwarding-rules create trustlayer-forwarding-rule \
    --address=trustlayer-ip \
    --global \
    --target-http-proxy=trustlayer-http-proxy \
    --ports=80
```

## 🌐 **Step 6: Set Up DNS**

### **6.1 Option A: Using Google Cloud DNS**
```bash
# Create DNS zone
gcloud dns managed-zones create trustlayer-zone \
    --description="TrustLayer AI DNS Zone" \
    --dns-name=trustlayer.local \
    --visibility=private \
    --networks=trustlayer-vpc

# Add DNS records for AI APIs
gcloud dns record-sets transaction start --zone=trustlayer-zone

# Add A records pointing to load balancer
gcloud dns record-sets transaction add $LOAD_BALANCER_IP \
    --name=api.openai.com.trustlayer.local. \
    --ttl=300 \
    --type=A \
    --zone=trustlayer-zone

gcloud dns record-sets transaction add $LOAD_BALANCER_IP \
    --name=api.anthropic.com.trustlayer.local. \
    --ttl=300 \
    --type=A \
    --zone=trustlayer-zone

gcloud dns record-sets transaction add $LOAD_BALANCER_IP \
    --name=generativelanguage.googleapis.com.trustlayer.local. \
    --ttl=300 \
    --type=A \
    --zone=trustlayer-zone

gcloud dns record-sets transaction execute --zone=trustlayer-zone
```

### **6.2 Option B: Create DNS Forwarder VM**
```bash
# Create DNS forwarder startup script
cat > dns-startup-script.sh << 'EOF'
#!/bin/bash

# Update system
apt-get update
apt-get install -y bind9 bind9utils

# Configure BIND9 for DNS forwarding
cat > /etc/bind/named.conf.local << 'BIND_EOF'
zone "api.openai.com" {
    type master;
    file "/etc/bind/db.api.openai.com";
};

zone "api.anthropic.com" {
    type master;
    file "/etc/bind/db.api.anthropic.com";
};

zone "generativelanguage.googleapis.com" {
    type master;
    file "/etc/bind/db.generativelanguage.googleapis.com";
};

zone "api.cohere.ai" {
    type master;
    file "/etc/bind/db.api.cohere.ai";
};
BIND_EOF

# Create zone files
cat > /etc/bind/db.api.openai.com << 'ZONE_EOF'
$TTL    604800
@       IN      SOA     api.openai.com. root.api.openai.com. (
                              2         ; Serial
                         604800         ; Refresh
                          86400         ; Retry
                        2419200         ; Expire
                         604800 )       ; Negative Cache TTL
;
@       IN      NS      api.openai.com.
@       IN      A       LOAD_BALANCER_IP_PLACEHOLDER
ZONE_EOF

# Copy zone file template for other domains
cp /etc/bind/db.api.openai.com /etc/bind/db.api.anthropic.com
cp /etc/bind/db.api.openai.com /etc/bind/db.generativelanguage.googleapis.com
cp /etc/bind/db.api.openai.com /etc/bind/db.api.cohere.ai

# Replace domain names in zone files
sed -i 's/api.openai.com/api.anthropic.com/g' /etc/bind/db.api.anthropic.com
sed -i 's/api.openai.com/generativelanguage.googleapis.com/g' /etc/bind/db.generativelanguage.googleapis.com
sed -i 's/api.openai.com/api.cohere.ai/g' /etc/bind/db.api.cohere.ai

# Replace IP placeholder in all zone files
sed -i "s/LOAD_BALANCER_IP_PLACEHOLDER/$LOAD_BALANCER_IP/g" /etc/bind/db.*

# Configure BIND9 options
cat > /etc/bind/named.conf.options << 'OPTIONS_EOF'
options {
    directory "/var/cache/bind";
    recursion yes;
    allow-query { any; };
    forwarders {
        8.8.8.8;
        8.8.4.4;
    };
    dnssec-validation auto;
    listen-on-v6 { any; };
};
OPTIONS_EOF

# Restart and enable BIND9
systemctl restart bind9
systemctl enable bind9

# Test DNS resolution
nslookup api.openai.com localhost
EOF

# Replace load balancer IP in DNS startup script
sed -i "s/\$LOAD_BALANCER_IP/$LOAD_BALANCER_IP/g" dns-startup-script.sh

# Create DNS forwarder VM
gcloud compute instances create trustlayer-dns \
    --zone=$ZONE \
    --machine-type=e2-micro \
    --network-interface=network-tier=PREMIUM,subnet=trustlayer-subnet \
    --metadata-from-file startup-script=dns-startup-script.sh \
    --maintenance-policy=MIGRATE \
    --tags=trustlayer-vm,dns-server \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-standard

# Get DNS VM IP
export DNS_IP=$(gcloud compute instances describe trustlayer-dns --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
echo "DNS Server IP: $DNS_IP"

# Create firewall rule for DNS
gcloud compute firewall-rules create trustlayer-allow-dns \
    --network=trustlayer-vpc \
    --allow=tcp:53,udp:53 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=dns-server
```

## 🧪 **Step 7: Test Your Deployment**

### **7.1 Wait for Services to Start**
```bash
# Wait for VMs to complete startup (5-10 minutes)
echo "Waiting for services to start..."
sleep 300

# Check VM status
gcloud compute instances list --filter="name:trustlayer-ai-main"

# Check if services are running
gcloud compute ssh trustlayer-ai-main --zone=$ZONE --command="docker ps"
```

### **7.2 Test Health Endpoints**
```bash
# Test direct VM health
curl http://$VM_IP:8000/health

# Test load balancer health
curl http://$LOAD_BALANCER_IP/health

# Test dashboard
curl -I http://$VM_IP:8501
```

### **7.3 Test DNS Resolution**
```bash
# If using DNS forwarder VM
nslookup api.openai.com $DNS_IP

# Should return your load balancer IP
```

### **7.4 Test PII Detection**
```bash
# Test PII redaction through load balancer
curl -X POST http://$LOAD_BALANCER_IP/v1/chat/completions \
  -H "Host: api.openai.com" \
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

## 🖥️ **Step 8: Configure Your Local System**

### **8.1 Update Local DNS Settings**

**Windows:**
1. Open **Network Settings** → **Change adapter options**
2. Right-click your connection → **Properties**
3. Select **Internet Protocol Version 4 (TCP/IPv4)** → **Properties**
4. Choose **"Use the following DNS server addresses"**
5. **Preferred DNS server**: `$DNS_IP` (your DNS forwarder IP)
6. **Alternate DNS server**: `8.8.8.8`

**macOS:**
```bash
# Add DNS server
sudo networksetup -setdnsservers Wi-Fi $DNS_IP 8.8.8.8

# Or edit manually in System Preferences → Network → Advanced → DNS
```

**Linux:**
```bash
# Edit resolv.conf
sudo tee /etc/resolv.conf << EOF
nameserver $DNS_IP
nameserver 8.8.8.8
EOF
```

### **8.2 Test Local DNS Resolution**
```bash
# Test that AI domains resolve to your load balancer
nslookup api.openai.com
# Should return: $LOAD_BALANCER_IP

nslookup api.anthropic.com  
# Should return: $LOAD_BALANCER_IP
```

## 📊 **Step 9: Access Dashboard and Monitor**

### **9.1 Access Dashboard**
```bash
# Get dashboard URL
echo "Dashboard URL: http://$LOAD_BALANCER_IP/dashboard"
echo "Direct VM Dashboard: http://$VM_IP:8501"

# Open in browser
# Windows: start http://$LOAD_BALANCER_IP/dashboard
# macOS: open http://$LOAD_BALANCER_IP/dashboard
# Linux: xdg-open http://$LOAD_BALANCER_IP/dashboard
```

### **9.2 Monitor System Health**
```bash
# Check all VMs
gcloud compute instances list --filter="name:trustlayer-*"

# Check load balancer backend health
gcloud compute backend-services get-health trustlayer-backend-service --global

# Check Redis status
gcloud redis instances list --region=$REGION

# SSH into main VM to check logs
gcloud compute ssh trustlayer-ai-main --zone=$ZONE --command="docker-compose -f /opt/trustlayer-ai/docker-compose.prod.yml logs -f"
```

## 🔧 **Step 10: Production Optimizations**

### **10.1 Enable HTTPS**
```bash
# Create SSL certificate
gcloud compute ssl-certificates create trustlayer-ssl-cert \
    --domains=$LOAD_BALANCER_IP

# Create HTTPS proxy
gcloud compute target-https-proxies create trustlayer-https-proxy \
    --url-map=trustlayer-url-map \
    --ssl-certificates=trustlayer-ssl-cert

# Create HTTPS forwarding rule
gcloud compute forwarding-rules create trustlayer-https-forwarding-rule \
    --address=trustlayer-ip \
    --global \
    --target-https-proxy=trustlayer-https-proxy \
    --ports=443
```

### **10.2 Set Up Monitoring**
```bash
# Install monitoring agent on VMs
gcloud compute ssh trustlayer-ai-main --zone=$ZONE --command="
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install
"
```

### **10.3 Create Backup Scripts**
```bash
# Create backup script
cat > backup-script.sh << 'EOF'
#!/bin/bash

# Backup configuration
gcloud compute instances create-machine-image trustlayer-ai-main \
    --source-instance=trustlayer-ai-main \
    --source-instance-zone=$ZONE \
    --machine-image-name=trustlayer-backup-$(date +%Y%m%d-%H%M%S)

# Backup Redis data
gcloud redis instances export trustlayer-redis \
    --destination=gs://trustlayer-backups/redis-backup-$(date +%Y%m%d-%H%M%S).rdb \
    --region=$REGION
EOF

# Create storage bucket for backups
gsutil mb gs://trustlayer-backups-$PROJECT_ID

# Set up cron job for daily backups
gcloud compute ssh trustlayer-ai-main --zone=$ZONE --command="
echo '0 2 * * * /opt/trustlayer-ai/backup-script.sh' | crontab -
"
```

## 💰 **Cost Optimization**

### **Current Setup Cost Estimate:**
- **Main VM (e2-standard-2)**: ~$25/month
- **Backup VM (e2-standard-2)**: ~$25/month (optional)
- **DNS VM (e2-micro)**: ~$5/month
- **Redis (1GB)**: ~$15/month
- **Load Balancer**: ~$18/month
- **Storage & Network**: ~$5/month
- **Total**: ~$68-93/month

### **Cost Reduction Options:**

**Option 1: Single VM Setup**
```bash
# Skip backup VM creation
# Use e2-medium instead of e2-standard-2
# Total cost: ~$45/month
```

**Option 2: Preemptible Instances**
```bash
# Add --preemptible flag to VM creation
# Reduces cost by 60-91%
# Total cost: ~$20-30/month
```

**Option 3: Spot Instances**
```bash
# Use spot instances for non-critical components
gcloud compute instances create trustlayer-ai-spot \
    --provisioning-model=SPOT \
    --instance-termination-action=STOP
```

## 🚨 **Troubleshooting**

### **Common Issues:**

**1. VM Startup Script Failed**
```bash
# Check startup script logs
gcloud compute ssh trustlayer-ai-main --zone=$ZONE --command="sudo journalctl -u google-startup-scripts.service"

# Check custom logs
gcloud compute ssh trustlayer-ai-main --zone=$ZONE --command="cat /var/log/trustlayer-startup.log"
```

**2. Docker Services Not Starting**
```bash
# SSH into VM and check
gcloud compute ssh trustlayer-ai-main --zone=$ZONE

# Check Docker status
sudo systemctl status docker

# Check containers
docker ps -a

# Restart services
cd /opt/trustlayer-ai
sudo docker-compose -f docker-compose.prod.yml restart
```

**3. Load Balancer Health Check Failing**
```bash
# Check backend health
gcloud compute backend-services get-health trustlayer-backend-service --global

# Check firewall rules
gcloud compute firewall-rules list --filter="name:trustlayer-*"

# Test health endpoint directly
curl http://$VM_IP:8000/health
```

**4. DNS Resolution Not Working**
```bash
# Check DNS VM status
gcloud compute ssh trustlayer-dns --zone=$ZONE --command="sudo systemctl status bind9"

# Test DNS locally on VM
gcloud compute ssh trustlayer-dns --zone=$ZONE --command="nslookup api.openai.com localhost"

# Check DNS logs
gcloud compute ssh trustlayer-dns --zone=$ZONE --command="sudo journalctl -u bind9"
```

**5. Redis Connection Issues**
```bash
# Check Redis status
gcloud redis instances describe trustlayer-redis --region=$REGION

# Test Redis connection from VM
gcloud compute ssh trustlayer-ai-main --zone=$ZONE --command="
docker run --rm redis:7-alpine redis-cli -h $REDIS_IP ping
"
```

## 🔄 **Scaling and High Availability**

### **Horizontal Scaling**
```bash
# Create additional VMs
for i in {2..3}; do
  gcloud compute instances create trustlayer-ai-vm$i \
    --zone=$ZONE \
    --machine-type=e2-standard-2 \
    --network-interface=subnet=trustlayer-subnet \
    --metadata-from-file startup-script=startup-script.sh \
    --tags=trustlayer-vm,trustlayer-web \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud
    
  # Add to instance group
  gcloud compute instance-groups unmanaged add-instances trustlayer-ig-main \
    --instances=trustlayer-ai-vm$i \
    --zone=$ZONE
done
```

### **Auto-Scaling Setup**
```bash
# Convert to managed instance group
gcloud compute instance-templates create trustlayer-template \
    --machine-type=e2-standard-2 \
    --network-interface=subnet=trustlayer-subnet \
    --metadata-from-file startup-script=startup-script.sh \
    --tags=trustlayer-vm,trustlayer-web \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud

# Create managed instance group
gcloud compute instance-groups managed create trustlayer-mig \
    --template=trustlayer-template \
    --size=2 \
    --zone=$ZONE

# Set up auto-scaling
gcloud compute instance-groups managed set-autoscaling trustlayer-mig \
    --max-num-replicas=5 \
    --min-num-replicas=2 \
    --target-cpu-utilization=0.7 \
    --zone=$ZONE
```

## 🎉 **Success! Your TrustLayer AI is Running**

Your TrustLayer AI system is now deployed on Google Compute Engine! Here's what you have:

### **✅ What's Working:**
- **Load Balancer**: `http://$LOAD_BALANCER_IP`
- **Dashboard**: `http://$LOAD_BALANCER_IP/dashboard`
- **Health Check**: `http://$LOAD_BALANCER_IP/health`
- **DNS Forwarder**: Routes AI API calls through your proxy
- **Redis**: Session management and PII tokenization
- **Auto-restart**: Services automatically restart on VM reboot

### **🔗 Access Points:**
```bash
echo "=== TrustLayer AI Access Points ==="
echo "Load Balancer IP: $LOAD_BALANCER_IP"
echo "Main VM IP: $VM_IP"
echo "DNS Server IP: $DNS_IP"
echo "Redis IP: $REDIS_IP"
echo ""
echo "Dashboard: http://$LOAD_BALANCER_IP/dashboard"
echo "Health Check: http://$LOAD_BALANCER_IP/health"
echo "Metrics: http://$LOAD_BALANCER_IP/metrics"
```

### **🧪 Test Your Setup:**
```bash
# Test PII detection
curl -X POST http://$LOAD_BALANCER_IP/v1/chat/completions \
  -H "Host: api.openai.com" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"My name is Alice and email is alice@test.com"}]}'
```

### **📊 Monitor Your System:**
- **GCP Console**: Monitor VM health, load balancer status
- **Dashboard**: Real-time PII blocking and traffic metrics
- **Logs**: `gcloud compute ssh trustlayer-ai-main --command="docker logs trustlayer-proxy"`

Your AI interactions are now secure, compliant, and transparent! 🛡️

## 📚 **Next Steps**

1. **Add API Keys**: Configure your actual AI API keys in the environment
2. **Set Up HTTPS**: Enable SSL certificates for production
3. **Configure Monitoring**: Set up alerts and dashboards
4. **Test Thoroughly**: Run comprehensive PII detection tests
5. **Scale as Needed**: Add more VMs or enable auto-scaling

**Your TrustLayer AI proxy is ready for production use!** 🚀