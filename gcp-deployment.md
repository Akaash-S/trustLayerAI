# 🏗️ TrustLayer AI - GCP "Sovereign AI" Deployment

A production-ready Google Cloud Platform deployment using Private Service Connect, Internal Load Balancers, and Cloud Run for complete data sovereignty.

## 🏛️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Corporate Network                             │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │ Developer   │───▶│ VPN Gateway  │───▶│ Private DNS     │    │
│  │ Workstation │    │              │    │ trustlayer.     │    │
│  └─────────────┘    └──────────────┘    │ internal        │    │
└─────────────────────────────────────────┼─────────────────┼────┘
                                          │                 │
┌─────────────────────────────────────────┼─────────────────┼────┐
│                    GCP VPC              │                 │    │
│                                         ▼                 ▼    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Private Service Connect                    │   │
│  │          api.trustlayer.internal → 10.1.0.100         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                         │                      │
│  ┌─────────────────────────────────────┼─────────────────┐    │
│  │        Internal Load Balancer       │                 │    │
│  │     ┌─────────────┐  ┌─────────────┐│                 │    │
│  │     │ Cloud Armor │  │ Serverless  ││                 │    │
│  │     │ Security    │  │ NEG         ││                 │    │
│  │     └─────────────┘  └─────────────┘│                 │    │
│  └─────────────────────────────────────┼─────────────────┘    │
│                                         │                      │
│  ┌─────────────────────────────────────┼─────────────────┐    │
│  │              Cloud Run              │                 │    │
│  │  ┌─────────────────────────────────┐│                 │    │
│  │  │      TrustLayer AI Proxy        ││                 │    │
│  │  │  ┌─────────────┐ ┌─────────────┐││                 │    │
│  │  │  │ FastAPI     │ │ Presidio    │││                 │    │
│  │  │  │ Proxy       │ │ PII Engine  │││                 │    │
│  │  │  └─────────────┘ └─────────────┘││                 │    │
│  │  └─────────────────────────────────┘│                 │    │
│  └─────────────────────────────────────┼─────────────────┘    │
│                                         │                      │
│  ┌─────────────────────────────────────┼─────────────────┐    │
│  │            Cloud Memorystore        │                 │    │
│  │         (Redis for Sessions)        │                 │    │
│  └─────────────────────────────────────┼─────────────────┘    │
└─────────────────────────────────────────┼─────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External AI APIs                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐     │
│  │ OpenAI API  │  │ Anthropic   │  │ Google Gemini       │     │
│  │ (Sanitized) │  │ (Sanitized) │  │ (Sanitized)         │     │
│  └─────────────┘  └─────────────┘  └─────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Prerequisites

1. **GCP Project** with billing enabled
2. **Terraform** installed locally
3. **gcloud CLI** configured
4. **Docker** for building container images
5. **Required APIs** enabled:
   - Cloud Run API
   - Compute Engine API
   - Cloud DNS API
   - VPC Access API
   - Cloud Memorystore API

## 📁 Project Structure

```
gcp-deployment/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── vpc.tf
│   ├── cloud-run.tf
│   ├── load-balancer.tf
│   ├── dns.tf
│   ├── memorystore.tf
│   └── security.tf
├── cloudbuild.yaml
├── Dockerfile.gcp
└── deploy.sh
```

## 🚀 Quick Deployment

```bash
# 1. Clone and setup
git clone <your-repo>
cd trustlayer-ai

# 2. Set GCP project
export PROJECT_ID="your-project-id"
export REGION="us-central1"

# 3. Enable required APIs
gcloud services enable run.googleapis.com compute.googleapis.com dns.googleapis.com vpcaccess.googleapis.com redis.googleapis.com

# 4. Deploy infrastructure
cd gcp-deployment/terraform
terraform init
terraform plan -var="project_id=${PROJECT_ID}" -var="region=${REGION}"
terraform apply

# 5. Build and deploy container
gcloud builds submit --config=../cloudbuild.yaml ../..

# 6. Test deployment
curl -H "Host: api.trustlayer.internal" http://10.1.0.100/health
```

## 🏗️ Infrastructure Components

### 1. VPC and Networking
- **Custom VPC** with private subnets
- **Proxy-only subnet** for Internal Load Balancer
- **Private Service Connect** for internal access
- **Cloud NAT** for outbound internet access

### 2. Compute (Cloud Run)
- **Serverless** auto-scaling container
- **Internal ingress only** (no public access)
- **VPC Connector** for private networking
- **Environment variables** for configuration

### 3. Load Balancing
- **Internal Application Load Balancer**
- **Serverless NEG** pointing to Cloud Run
- **Health checks** for service monitoring
- **SSL termination** with managed certificates

### 4. Security
- **Cloud Armor** security policies
- **IAM roles** with least privilege
- **Private Google Access** enabled
- **VPC firewall rules** for traffic control

### 5. Data Storage
- **Cloud Memorystore** (Redis) for session data
- **Private IP** connectivity only
- **Automatic backups** enabled
- **High availability** configuration

### 6. DNS and Discovery
- **Private DNS Zone** (trustlayer.internal)
- **A record** pointing to load balancer
- **Internal resolution** only

## 🔐 Security Features

### Data Sovereignty
- ✅ **No public internet exposure** - All traffic stays within GCP
- ✅ **Private Service Connect** - Direct private connectivity
- ✅ **VPC-native networking** - No external IPs required
- ✅ **Regional data residency** - Data stays in specified region

### Access Control
- ✅ **IAM-based access** - Role-based permissions
- ✅ **VPC firewall rules** - Network-level security
- ✅ **Cloud Armor policies** - Application-level protection
- ✅ **Private endpoints** - No public API exposure

### Compliance
- ✅ **Audit logging** - All API calls logged
- ✅ **Data encryption** - At rest and in transit
- ✅ **Network isolation** - Complete traffic segregation
- ✅ **GDPR/CCPA ready** - Privacy by design

## 📊 Monitoring and Observability

### Cloud Monitoring
- **Custom metrics** for PII detection rates
- **SLI/SLO dashboards** for reliability
- **Alerting policies** for incidents
- **Log-based metrics** for compliance

### Cloud Logging
- **Structured logging** for all components
- **PII redaction events** tracking
- **Security event monitoring**
- **Compliance audit trails**

### Cloud Trace
- **Request tracing** across services
- **Latency analysis** for optimization
- **Performance monitoring**
- **Bottleneck identification**

## 💰 Cost Optimization

### Serverless Benefits
- **Pay-per-request** pricing model
- **Auto-scaling to zero** when idle
- **No infrastructure management**
- **Automatic resource optimization**

### Resource Efficiency
- **Shared VPC** across environments
- **Regional deployment** to minimize egress
- **Committed use discounts** for predictable workloads
- **Preemptible instances** for batch processing

## 🔄 CI/CD Pipeline

### Cloud Build Integration
```yaml
# cloudbuild.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/trustlayer-ai', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/trustlayer-ai']
- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 'trustlayer-ai', '--image', 'gcr.io/$PROJECT_ID/trustlayer-ai', '--region', 'us-central1']
```

### Automated Testing
- **Unit tests** in build pipeline
- **Integration tests** against staging
- **Security scans** with Container Analysis
- **Performance tests** with load testing

## 🌍 Multi-Region Deployment

### Global Load Balancing
```hcl
# Global load balancer for multi-region
resource "google_compute_global_forwarding_rule" "trustlayer_global" {
  name       = "trustlayer-global-lb"
  target     = google_compute_target_http_proxy.trustlayer_global.id
  port_range = "80"
}
```

### Cross-Region Replication
- **Cloud Memorystore** cross-region replication
- **Multi-region Cloud Run** deployments
- **Global load balancing** for failover
- **Data synchronization** strategies

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] GCP project created and billing enabled
- [ ] Required APIs enabled
- [ ] Service accounts created with proper IAM roles
- [ ] VPC and subnets planned
- [ ] DNS zones configured

### Deployment
- [ ] Terraform infrastructure deployed
- [ ] Container image built and pushed
- [ ] Cloud Run service deployed
- [ ] Load balancer configured
- [ ] DNS records created

### Post-Deployment
- [ ] Health checks passing
- [ ] Monitoring dashboards configured
- [ ] Alerting policies set up
- [ ] Security policies applied
- [ ] Documentation updated

### Testing
- [ ] Internal connectivity verified
- [ ] PII redaction working
- [ ] Load balancer health checks passing
- [ ] DNS resolution working
- [ ] Security policies enforced

## 🆘 Troubleshooting

### Common Issues
1. **VPC Connector timeout** - Check subnet CIDR ranges
2. **DNS resolution fails** - Verify private zone configuration
3. **Load balancer 502 errors** - Check Cloud Run health endpoint
4. **Redis connection issues** - Verify VPC peering and firewall rules

### Debug Commands
```bash
# Check Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# Test internal connectivity
gcloud compute ssh test-vm --command="curl -H 'Host: api.trustlayer.internal' http://10.1.0.100/health"

# Verify DNS resolution
gcloud compute ssh test-vm --command="nslookup api.trustlayer.internal"

# Check load balancer status
gcloud compute backend-services describe trustlayer-backend --global
```

## 📞 Support and Maintenance

### Regular Maintenance
- **Security patches** - Automated container updates
- **Dependency updates** - Scheduled vulnerability scans
- **Performance tuning** - Monthly optimization reviews
- **Cost optimization** - Quarterly cost analysis

### Incident Response
- **24/7 monitoring** - Automated alerting
- **Runbook procedures** - Documented response steps
- **Escalation paths** - Clear responsibility matrix
- **Post-incident reviews** - Continuous improvement

---

**Next Steps:** Choose your deployment method and follow the detailed Terraform configurations in the following sections.