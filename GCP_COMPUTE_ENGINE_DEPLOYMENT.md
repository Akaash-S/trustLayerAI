# 🚀 TrustLayer AI - Google Compute Engine Manual Deployment Guide

Complete step-by-step manual guide to deploy TrustLayer AI on Google Compute Engine VMs using the GCP Console. This approach is simpler, more cost-effective, and avoids GKE quota issues.

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
- ✅ **Manual Control**: Step-by-step GUI-based setup

## 📋 **Prerequisites**

- Google Cloud account with billing enabled
- Web browser for GCP Console access
- Basic knowledge of Linux (for SSH configuration)
- Your TrustLayer AI code repository (GitHub/local)

## 🏗️ **Step 1: Create GCP Project and Setup**

### **1.1 Create New Project**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click the **project dropdown** at the top
3. Click **"New Project"**
4. Fill in:
   - **Project name**: `TrustLayer AI Production`
   - **Project ID**: `trustlayer-ai-prod` (or auto-generated)
   - **Organization**: Select your organization (if applicable)
5. Click **"Create"**
6. **Wait for project creation** (1-2 minutes)
7. **Select your new project** from the dropdown

### **1.2 Enable Billing**
1. Go to **Billing** in the left sidebar
2. Click **"Link a billing account"**
3. Select your billing account or create a new one
4. Click **"Set account"**

### **1.3 Enable Required APIs**
1. Go to **APIs & Services** → **Library**
2. Search for and enable each of these APIs (click **"Enable"** for each):
   - **Compute Engine API**
   - **Cloud DNS API** 
   - **Cloud Memorystore for Redis API**
   - **Cloud Logging API**
   - **Cloud Monitoring API**
   - **Container Registry API** (for Docker images)

**Note**: Each API takes 1-2 minutes to enable. Wait for confirmation before proceeding.

## 🌐 **Step 2: Create VPC Network**

### **2.1 Create VPC Network**
1. Go to **VPC network** → **VPC networks**
2. Click **"Create VPC Network"**
3. Configure:
   - **Name**: `trustlayer-vpc`
   - **Description**: `TrustLayer AI VPC Network`
   - **Subnet creation mode**: **Custom**
4. **Don't click Create yet** - we'll add subnets first

### **2.2 Add Subnets**
In the same VPC creation form, add these subnets:

**Subnet 1: Main VM Subnet**
1. Click **"Add subnet"**
2. Configure:
   - **Name**: `trustlayer-subnet`
   - **Region**: `us-central1`
   - **IP address range**: `10.0.1.0/24`
   - **Private Google Access**: **On**

**Subnet 2: Redis Subnet**
1. Click **"Add subnet"** again
2. Configure:
   - **Name**: `redis-subnet`
   - **Region**: `us-central1`
   - **IP address range**: `10.0.2.0/24`
   - **Private Google Access**: **On**

3. Click **"Create"** to create the VPC with both subnets

### **2.3 Create Firewall Rules**
1. Go to **VPC network** → **Firewall**
2. Click **"Create Firewall Rule"**

**Rule 1: Allow Internal Traffic**
1. Configure:
   - **Name**: `trustlayer-allow-internal`
   - **Direction**: **Ingress**
   - **Action**: **Allow**
   - **Targets**: **All instances in the network**
   - **Source IP ranges**: `10.0.0.0/16`
   - **Protocols and ports**: **Allow all**
2. Click **"Create"**

**Rule 2: Allow SSH Access**
1. Click **"Create Firewall Rule"** again
2. Configure:
   - **Name**: `trustlayer-allow-ssh`
   - **Direction**: **Ingress**
   - **Action**: **Allow**
   - **Targets**: **Specified target tags**
   - **Target tags**: `trustlayer-vm`
   - **Source IP ranges**: `0.0.0.0/0`
   - **Protocols and ports**: **TCP** → Port `22`
3. Click **"Create"**

**Rule 3: Allow Web Traffic**
1. Click **"Create Firewall Rule"** again
2. Configure:
   - **Name**: `trustlayer-allow-web`
   - **Direction**: **Ingress**
   - **Action**: **Allow**
   - **Targets**: **Specified target tags**
   - **Target tags**: `trustlayer-web`
   - **Source IP ranges**: `0.0.0.0/0`
   - **Protocols and ports**: **TCP** → Ports `80,443,8000,8501`
3. Click **"Create"**

**Rule 4: Allow Health Checks**
1. Click **"Create Firewall Rule"** again
2. Configure:
   - **Name**: `trustlayer-allow-health-check`
   - **Direction**: **Ingress**
   - **Action**: **Allow**
   - **Targets**: **Specified target tags**
   - **Target tags**: `trustlayer-web`
   - **Source IP ranges**: `130.211.0.0/22,35.191.0.0/16`
   - **Protocols and ports**: **TCP** → Port `8000`
3. Click **"Create"**
    --range=10.0.2.0/24 \
    --region=$REGION
```

### **2.2 Create Firewall Rules**
```bash
# Allow internal traffic
## 🔧 **Step 3: Create Redis Instance**

### **3.1 Create Redis Instance**
1. Go to **Memorystore** → **Redis**
2. Click **"Create Instance"**
3. Configure:
   - **Instance ID**: `trustlayer-redis`
   - **Display name**: `TrustLayer AI Redis`
   - **Tier**: **Standard**
   - **Capacity**: **1 GB**
   - **Region**: `us-central1`
   - **Zone**: `us-central1-a` (or any zone in us-central1)
   - **Network**: `trustlayer-vpc`
   - **IP range**: `10.0.3.0/29`
   - **Redis version**: **Redis 7.0**
4. Click **"Create"**
5. **Wait for creation** (5-10 minutes)
6. **Note the Redis IP address** once created (e.g., `10.0.3.2`) - you'll need this later

## 🖥️ **Step 4: Create Compute Engine VMs**

### **4.1 Prepare Your TrustLayer AI Code**
Before creating VMs, ensure you have your TrustLayer AI code ready:

**Option A: GitHub Repository**
- Make sure your code is pushed to a GitHub repository
- Note the repository URL (e.g., `https://github.com/yourusername/trustlayer-ai.git`)

**Option B: Local Files**
- Have your TrustLayer AI files ready to upload
- Include: `app/`, `dashboard.py`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`

### **4.2 Create Main TrustLayer AI VM**
1. Go to **Compute Engine** → **VM instances**
2. Click **"Create Instance"**
3. Configure:
   - **Name**: `trustlayer-ai-main`
   - **Region**: `us-central1`
   - **Zone**: `us-central1-a`
   - **Machine configuration**: **General-purpose**
   - **Machine type**: `e2-standard-2` (2 vCPU, 8 GB memory)
   - **Boot disk**: Click **"Change"**
     - **Operating system**: Ubuntu
     - **Version**: Ubuntu 22.04 LTS
     - **Boot disk type**: Standard persistent disk
     - **Size**: 50 GB
     - Click **"Select"**
   - **Identity and API access**: Use default service account
   - **Firewall**:
     - ✅ **Allow HTTP traffic**
     - ✅ **Allow HTTPS traffic**
   - **Advanced options** → **Networking**:
     - **Network**: `trustlayer-vpc`
     - **Subnet**: `trustlayer-subnet`
     - **Network tags**: `trustlayer-vm,trustlayer-web`

4. Click **"Create"**
5. **Wait for VM creation** (2-3 minutes)
### **4.3 Set Up TrustLayer AI on the VM**

1. **SSH into your VM**:
   - Go to **Compute Engine** → **VM instances**
   - Click **SSH** next to `trustlayer-ai-main`
   - A new browser window will open with SSH terminal

2. **Update the system**:
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose git curl nano
   ```

3. **Start Docker**:
   ```bash
   sudo systemctl start docker
   sudo systemctl enable docker
   sudo usermod -aG docker $USER
   ```

4. **Log out and back in** (to apply docker group):
   - Close the SSH window
   - Click **SSH** again to reconnect

5. **Create application directory**:
   ```bash
   sudo mkdir -p /opt/trustlayer-ai
   sudo chown $USER:$USER /opt/trustlayer-ai
   cd /opt/trustlayer-ai
   ```

6. **Get your TrustLayer AI code**:

   **Option A: Clone from GitHub**
   ```bash
   git clone https://github.com/yourusername/trustlayer-ai.git .
   ```

   **Option B: Upload files manually**
   - Use the **Upload file** button in the SSH window
   - Upload your TrustLayer AI files (app/, dashboard.py, requirements.txt, etc.)

7. **Create production configuration**:
   ```bash
   nano config.yaml
   ```
   
   Copy and paste this configuration (replace `REDIS_IP_HERE` with your actual Redis IP from Step 3):
   ```yaml
   proxy:
     host: "0.0.0.0"
     port: 8000
     
   allowed_domains:
     - "api.openai.com"
     - "api.anthropic.com"
     - "generativelanguage.googleapis.com"
     - "api.cohere.ai"

   redis:
     host: "REDIS_IP_HERE"  # Replace with your Redis IP (e.g., 10.0.3.2)
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
   ```
   
   Save with `Ctrl+X`, then `Y`, then `Enter`

8. **Create production docker-compose file**:
   ```bash
   nano docker-compose.prod.yml
   ```
   
   **IMPORTANT**: Copy and paste this EXACTLY (watch for proper indentation):
   ```yaml
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
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - proxy
      - dashboard
    restart: unless-stopped
   ```
   
   **Save with `Ctrl+X`, then `Y`, then `Enter`**

   **⚠️ YAML Troubleshooting:**
   If you get a YAML parsing error:
   ```bash
   # Check YAML syntax
   python3 -c "import yaml; yaml.safe_load(open('docker-compose.prod.yml'))"
   
   # If error, recreate the file:
   rm docker-compose.prod.yml
   nano docker-compose.prod.yml
   # Copy the YAML again, ensuring proper indentation (2 spaces, no tabs)
   ```

9. **Create Nginx configuration**:
   ```bash
   nano nginx.conf
   ```
   
   Copy and paste:
   ```nginx
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
   ```
   
   Save with `Ctrl+X`, then `Y`, then `Enter`

10. **Build and start the services**:

    **Option A: Simple approach (Recommended if you get exec format errors)**
    ```bash
    # Use the simplified docker-compose without custom entrypoint
    docker-compose -f docker-compose.simple.yml build
    docker-compose -f docker-compose.simple.yml up -d
    ```

    **Option B: Full production setup**
    ```bash
    docker-compose -f docker-compose.prod.yml build
    docker-compose -f docker-compose.prod.yml up -d
    ```

11. **Check if services are running**:
    ```bash
    docker ps
    ```
    
    You should see 3 containers running: `trustlayer-proxy`, `trustlayer-dashboard`, and `trustlayer-nginx`

12. **Test the health endpoint**:
    ```bash
    curl http://localhost/health
    ```
    
    Should return: `{"status": "healthy", "service": "TrustLayer AI Proxy"}`

    **If you get connection errors, try:**
    ```bash
    # Test direct proxy connection
    curl http://localhost:8000/health
    
    # Check container logs
    docker logs trustlayer-proxy
    docker logs trustlayer-dashboard
    docker logs trustlayer-nginx
    ```
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

### **5.1 Reserve Static IP Address**
1. Go to **VPC network** → **External IP addresses**
2. Click **"Reserve Static Address"**
3. Configure:
   - **Name**: `trustlayer-ip`
   - **Network Service Tier**: **Premium**
   - **IP version**: **IPv4**
   - **Type**: **Global**
4. Click **"Reserve"**
5. **Note the IP address** (e.g., `34.123.45.67`) - this will be your load balancer IP

### **5.2 Create Instance Group**
1. Go to **Compute Engine** → **Instance groups**
2. Click **"Create Instance Group"**
3. Configure:
   - **Name**: `trustlayer-ig-main`
   - **Location**: **Single zone**
   - **Region**: `us-central1`
   - **Zone**: `us-central1-a`
   - **Network**: `trustlayer-vpc`
   - **Subnet**: `trustlayer-subnet`
4. Click **"Create"**

### **5.3 Add VM to Instance Group**
1. In the instance group details page, click **"Add instances"**
2. Select `trustlayer-ai-main`
3. Click **"Add"**

### **5.4 Set Named Ports**
1. In the instance group details, click **"Edit"**
2. Under **Port mapping**, click **"Add port"**
3. Configure:
   - **Port name**: `http`
   - **Port numbers**: `80`
4. Click **"Save"**

### **5.5 Create Health Check**
1. Go to **Compute Engine** → **Health checks**
2. Click **"Create Health Check"**
3. Configure:
   - **Name**: `trustlayer-health-check`
   - **Protocol**: **HTTP**
   - **Port**: `80`
   - **Request path**: `/health`
   - **Check interval**: `30` seconds
   - **Timeout**: `10` seconds
   - **Healthy threshold**: `2`
   - **Unhealthy threshold**: `3`
4. Click **"Create"**

### **5.6 Create Backend Service**
1. Go to **Network services** → **Load balancing**
2. Click **"Create Load Balancer"**
3. Choose **"HTTP(S) Load Balancing"**
4. Choose **"From Internet to my VMs or serverless services"**
5. Click **"Continue"**

**Backend Configuration:**
1. Click **"Backend services"** → **"Create a backend service"**
2. Configure:
   - **Name**: `trustlayer-backend-service`
   - **Backend type**: **Instance group**
   - **Protocol**: **HTTP**
   - **Named port**: `http`
   - **Timeout**: `30` seconds
3. Click **"Add backend"**
4. Configure backend:
   - **Instance group**: `trustlayer-ig-main`
   - **Port numbers**: `80`
   - **Balancing mode**: **Rate**
   - **Maximum RPS**: `1000`
5. Under **Health check**, select `trustlayer-health-check`
6. Click **"Create"**

**Frontend Configuration:**
1. Click **"Frontend configuration"**
2. Configure:
   - **Name**: `trustlayer-frontend`
   - **Protocol**: **HTTP**
   - **IP version**: **IPv4**
   - **IP address**: Select `trustlayer-ip` (your reserved IP)
   - **Port**: `80`
3. Click **"Done"**

**Review and Create:**
1. Click **"Review and finalize"**
2. Review all settings
3. Click **"Create"**
4. **Wait for load balancer creation** (5-10 minutes)
    --target-http-proxy=trustlayer-http-proxy \
    --ports=80
```

## 🌐 **Step 6: Set Up DNS Forwarder**

### **6.1 Create DNS Forwarder VM**
1. Go to **Compute Engine** → **VM instances**
2. Click **"Create Instance"**
3. Configure:
   - **Name**: `trustlayer-dns`
   - **Region**: `us-central1`
   - **Zone**: `us-central1-a`
   - **Machine type**: `e2-micro` (smallest option)
   - **Boot disk**: 
     - **Operating system**: Ubuntu
     - **Version**: Ubuntu 22.04 LTS
     - **Size**: 20 GB
   - **Firewall**: 
     - ✅ **Allow HTTP traffic**
     - ✅ **Allow HTTPS traffic**
   - **Advanced options** → **Networking**:
     - **Network**: `trustlayer-vpc`
     - **Subnet**: `trustlayer-subnet`
     - **Network tags**: `trustlayer-vm,dns-server`
4. Click **"Create"**
5. **Note the External IP** of the DNS VM (e.g., `35.123.45.68`)

### **6.2 Configure DNS Forwarder**
1. **SSH into the DNS VM**:
   - Click **SSH** next to `trustlayer-dns`

2. **Install BIND9**:
   ```bash
   sudo apt update
   sudo apt install -y bind9 bind9utils
   ```

3. **Configure BIND9 zones**:
   ```bash
   sudo nano /etc/bind/named.conf.local
   ```
   
   Add this configuration (replace `YOUR_LOAD_BALANCER_IP` with your actual load balancer IP):
   ```
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
   ```
   
   Save with `Ctrl+X`, then `Y`, then `Enter`

4. **Create zone files for each AI API**:

   **OpenAI zone file**:
   ```bash
   sudo nano /etc/bind/db.api.openai.com
   ```
   
   Add (replace `YOUR_LOAD_BALANCER_IP`):
   ```
   $TTL    604800
   @       IN      SOA     api.openai.com. root.api.openai.com. (
                                 2         ; Serial
                            604800         ; Refresh
                             86400         ; Retry
                           2419200         ; Expire
                            604800 )       ; Negative Cache TTL
   ;
   @       IN      NS      api.openai.com.
   @       IN      A       YOUR_LOAD_BALANCER_IP
   ```

   **Anthropic zone file**:
   ```bash
   sudo nano /etc/bind/db.api.anthropic.com
   ```
   
   Add (replace `YOUR_LOAD_BALANCER_IP`):
   ```
   $TTL    604800
   @       IN      SOA     api.anthropic.com. root.api.anthropic.com. (
                                 2         ; Serial
                            604800         ; Refresh
                             86400         ; Retry
                           2419200         ; Expire
                            604800 )       ; Negative Cache TTL
   ;
   @       IN      NS      api.anthropic.com.
   @       IN      A       YOUR_LOAD_BALANCER_IP
   ```

   **Google AI zone file**:
   ```bash
   sudo nano /etc/bind/db.generativelanguage.googleapis.com
   ```
   
   Add (replace `YOUR_LOAD_BALANCER_IP`):
   ```
   $TTL    604800
   @       IN      SOA     generativelanguage.googleapis.com. root.generativelanguage.googleapis.com. (
                                 2         ; Serial
                            604800         ; Refresh
                             86400         ; Retry
                           2419200         ; Expire
                            604800 )       ; Negative Cache TTL
   ;
   @       IN      NS      generativelanguage.googleapis.com.
   @       IN      A       YOUR_LOAD_BALANCER_IP
   ```

   **Cohere zone file**:
   ```bash
   sudo nano /etc/bind/db.api.cohere.ai
   ```
   
   Add (replace `YOUR_LOAD_BALANCER_IP`):
   ```
   $TTL    604800
   @       IN      SOA     api.cohere.ai. root.api.cohere.ai. (
                                 2         ; Serial
                            604800         ; Refresh
                             86400         ; Retry
                           2419200         ; Expire
                            604800 )       ; Negative Cache TTL
   ;
   @       IN      NS      api.cohere.ai.
   @       IN      A       YOUR_LOAD_BALANCER_IP
   ```

5. **Configure BIND9 options**:
   ```bash
   sudo nano /etc/bind/named.conf.options
   ```
   
   Replace the content with:
   ```
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
   ```

6. **Restart BIND9**:
   ```bash
   sudo systemctl restart bind9
   sudo systemctl enable bind9
   ```

7. **Test DNS resolution**:
   ```bash
   nslookup api.openai.com localhost
   ```
   
   Should return your load balancer IP

### **6.3 Create DNS Firewall Rule**
1. Go to **VPC network** → **Firewall**
2. Click **"Create Firewall Rule"**
3. Configure:
   - **Name**: `trustlayer-allow-dns`
   - **Direction**: **Ingress**
   - **Action**: **Allow**
   - **Targets**: **Specified target tags**
   - **Target tags**: `dns-server`
   - **Source IP ranges**: `0.0.0.0/0`
   - **Protocols and ports**: **TCP and UDP** → Port `53`
4. Click **"Create"**

## 🧪 **Step 7: Test Your Deployment**

### **7.1 Test Load Balancer Health**
1. Open a web browser
2. Go to `http://YOUR_LOAD_BALANCER_IP/health` (replace with your actual load balancer IP)
3. Should see: `{"status": "healthy", "service": "TrustLayer AI Proxy"}`

### **7.2 Test Dashboard**
1. Go to `http://YOUR_LOAD_BALANCER_IP/dashboard`
2. Should see the TrustLayer AI dashboard with metrics

### **7.3 Test DNS Resolution**
From your DNS VM, test:
```bash
nslookup api.openai.com localhost
# Should return your load balancer IP

nslookup api.anthropic.com localhost  
# Should return your load balancer IP
```

## 🖥️ **Step 8: Configure Your Local System**

### **8.1 Update Local DNS Settings**

**Windows:**
1. Go to **Settings** → **Network & Internet** → **Change adapter options**
2. Right-click your network connection → **Properties**
3. Select **Internet Protocol Version 4 (TCP/IPv4)** → **Properties**
4. Choose **"Use the following DNS server addresses"**
5. **Preferred DNS server**: `YOUR_DNS_VM_IP` (e.g., `35.123.45.68`)
6. **Alternate DNS server**: `8.8.8.8`
7. Click **OK** and restart your network connection

**macOS:**
1. Go to **System Preferences** → **Network**
2. Select your network connection → **Advanced**
3. Go to **DNS** tab
4. Click **+** and add: `YOUR_DNS_VM_IP`
5. Click **OK** → **Apply**

**Linux:**
```bash
# Edit resolv.conf
sudo nano /etc/resolv.conf

# Add at the top:
nameserver YOUR_DNS_VM_IP
nameserver 8.8.8.8
```

### **8.2 Test Local DNS Resolution**
Open terminal/command prompt and test:
```bash
nslookup api.openai.com
# Should return your load balancer IP

nslookup api.anthropic.com
# Should return your load balancer IP
```

## 🎯 **Step 9: Test End-to-End PII Detection**

### **9.1 Test with curl**
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

### **9.2 Expected Behavior**
- Request should be intercepted by your proxy
- PII should be detected and redacted
- You'll get a 401/502 error (expected without API keys)
- Check dashboard for PII detection metrics

## 📊 **Step 10: Monitor Your System**

### **10.1 Access Points**
- **Load Balancer IP**: `YOUR_LOAD_BALANCER_IP`
- **Dashboard**: `http://YOUR_LOAD_BALANCER_IP/dashboard`
- **Health Check**: `http://YOUR_LOAD_BALANCER_IP/health`
- **Metrics**: `http://YOUR_LOAD_BALANCER_IP/metrics`
- **DNS Server**: `YOUR_DNS_VM_IP`

### **10.2 Check System Status**
1. **VMs Status**: Go to **Compute Engine** → **VM instances**
2. **Load Balancer**: Go to **Network services** → **Load balancing**
3. **Redis**: Go to **Memorystore** → **Redis**
4. **Firewall**: Go to **VPC network** → **Firewall**

### **10.3 View Logs**
SSH into your main VM and check logs:
```bash
cd /opt/trustlayer-ai
docker-compose -f docker-compose.prod.yml logs -f proxy
docker-compose -f docker-compose.prod.yml logs -f dashboard
```

## 💰 **Cost Breakdown**

**Monthly Costs (Estimated):**
- **Main VM (e2-standard-2)**: ~$25
- **DNS VM (e2-micro)**: ~$5
- **Redis (1GB)**: ~$15
- **Load Balancer**: ~$18
- **Storage & Network**: ~$5
- **Total**: ~$68/month

## 🔧 **Troubleshooting**

### **YAML Configuration Errors**

**Error**: `yaml.parser.ParserError: while parsing a block mapping`

**Solution**:
1. **Check indentation** - YAML uses spaces, not tabs
2. **Recreate the file**:
   ```bash
   cd /opt/trustlayer-ai
   rm docker-compose.prod.yml
   nano docker-compose.prod.yml
   ```
3. **Copy from the repository**:
   ```bash
   # Download the correct file
   curl -o docker-compose.prod.yml https://raw.githubusercontent.com/yourusername/trustlayer-ai/main/docker-compose.prod.yml
   ```
4. **Validate YAML syntax**:
   ```bash
   python3 -c "import yaml; print('YAML is valid!' if yaml.safe_load(open('docker-compose.prod.yml')) else 'YAML is invalid!')"
   ```

### **Docker Exec Format Error**

**Error**: `exec /app/entrypoint.sh: exec format error`

**This is a common issue with line endings or missing files. Here's how to fix it:**

**Solution 1: Rebuild without cache**
```bash
cd /opt/trustlayer-ai
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

**Solution 2: Check if entrypoint.sh exists**
```bash
# Make sure entrypoint.sh exists in your project
ls -la entrypoint.sh

# If missing, create it:
cat > entrypoint.sh << 'EOF'
#!/bin/bash
set -e

echo "🛡️ Starting TrustLayer AI..."

# Function to check and setup spaCy model
setup_spacy_model() {
    echo "📦 Checking spaCy model availability..."
    
    # Check if small model exists
    if python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
        echo "✅ spaCy model (en_core_web_sm) is available"
        return 0
    fi
    
    echo "⚠️  Could not find spaCy model"
    echo "   TrustLayer will use basic regex patterns for PII detection"
    return 1
}

# Setup spaCy model (don't fail if it doesn't work)
setup_spacy_model || true

echo "🚀 Starting application..."
exec "$@"
EOF

# Make it executable
chmod +x entrypoint.sh
```

**Solution 3: Use simplified docker-compose (without entrypoint)**
```bash
# Create a simplified version without custom entrypoint
cat > docker-compose.simple.yml << 'EOF'
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
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

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
EOF

# Use the simplified version
docker-compose -f docker-compose.simple.yml up -d
```

### **Common Issues:**

**1. Health Check Failing**
- SSH into VM: `docker ps` to check containers
- Check logs: `docker logs trustlayer-proxy`
- Test locally: `curl http://localhost/health`

**2. DNS Not Working**
- SSH into DNS VM: `sudo systemctl status bind9`
- Check zone files: `sudo named-checkzone api.openai.com /etc/bind/db.api.openai.com`
- Test DNS: `nslookup api.openai.com localhost`

**3. Load Balancer Issues**
- Check backend health in GCP Console
- Verify firewall rules allow traffic
- Check instance group has VMs

**4. Dashboard Not Loading**
- Check if dashboard container is running: `docker ps`
- Check dashboard logs: `docker logs trustlayer-dashboard`
- Test direct access: `http://VM_IP:8501`

**5. Docker Build Failures**
- Check if all files are present: `ls -la`
- Verify Dockerfile exists: `cat Dockerfile`
- Check Docker logs: `docker-compose -f docker-compose.prod.yml logs`

**6. Permission Issues**
- Fix ownership: `sudo chown -R $USER:$USER /opt/trustlayer-ai`
- Fix permissions: `chmod +x /opt/trustlayer-ai`

## 🎉 **Success! Your TrustLayer AI is Running**

Your TrustLayer AI system is now deployed on Google Compute Engine! Here's what you have:

### **✅ What's Working:**
- **Load Balancer**: Routes traffic to your proxy
- **TrustLayer AI Proxy**: Detects and redacts PII
- **Dashboard**: Real-time monitoring and metrics
- **DNS Forwarder**: Routes AI API calls through your proxy
- **Redis**: Session management and PII tokenization
- **Auto-restart**: Services restart automatically

### **🔗 Quick Reference:**
```
Load Balancer IP: YOUR_LOAD_BALANCER_IP
Dashboard: http://YOUR_LOAD_BALANCER_IP/dashboard
Health Check: http://YOUR_LOAD_BALANCER_IP/health
DNS Server: YOUR_DNS_VM_IP
```

### **🧪 Test Your Setup:**
All AI API calls from your system will now:
✅ **Route through your proxy** automatically  
✅ **Have PII detected and redacted** before reaching AI APIs  
✅ **Get PII restored** in responses  
✅ **Be monitored and logged** in your dashboard  

**Your AI interactions are now secure and compliant!** 🛡️

## 📚 **Next Steps**

1. **Add API Keys**: Configure your actual AI API keys
2. **Enable HTTPS**: Set up SSL certificates
3. **Set Up Monitoring**: Configure alerts and dashboards
4. **Scale**: Add more VMs or enable auto-scaling
5. **Backup**: Set up automated backups

**Your TrustLayer AI proxy is ready for production use!** 🚀