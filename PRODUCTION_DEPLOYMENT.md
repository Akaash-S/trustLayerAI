# TrustLayer AI - Production Deployment Guide (Google Compute Engine)

## Overview

This guide covers deploying TrustLayer AI to Google Compute Engine with production-ready configurations including:

- **Compute Engine VM** with Docker containers for reliable hosting
- **Redis Memory Store** at endpoint `10.97.237.131:6379` for session management
- **Production-optimized Docker image** with pre-installed spaCy models and Gunicorn
- **Nginx reverse proxy** for SSL termination and load balancing
- **Systemd services** for automatic startup and monitoring

## Prerequisites

1. **GCP Account** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Docker** installed locally for building images
4. **Redis instance** already running at `10.97.237.131:6379`

## Quick Start

### 1. Set Environment Variables

```bash
# Windows PowerShell
$env:PROJECT_ID = "your-gcp-project-id"
$env:ZONE = "us-central1-a"

# Linux/Mac
export PROJECT_ID="your-gcp-project-id"
export ZONE="us-central1-a"
```

### 2. Deploy to Compute Engine

**Windows:**
```powershell
.\deploy-production.ps1 -ProjectId "your-gcp-project-id" -Zone "us-central1-a"
```

**Linux/Mac:**
```bash
./deploy-production.sh
```

## Architecture

### Production Components

1. **Compute Engine VM** (e2-standard-2)
   - 2 vCPUs, 8GB RAM
   - Ubuntu 22.04 LTS with Docker
   - Automatic startup and monitoring
   - External IP for public access

2. **TrustLayer AI Proxy** (Docker Container)
   - FastAPI application with PII redaction
   - Gunicorn server with Uvicorn workers
   - Connects to Redis at `10.97.237.131:6379`
   - Systemd service for auto-restart

3. **Streamlit Dashboard** (Docker Container)
   - Real-time monitoring and analytics
   - Accessible on port 8501
   - Systemd service for reliability

4. **Nginx Reverse Proxy**
   - SSL termination (Let's Encrypt)
   - Load balancing and caching
   - Security headers and rate limiting

5. **Redis Memory Store** (External)
   - Primary endpoint: `10.97.237.131:6379`
   - Session storage for PII mappings
   - Telemetry data collection

### Server Configuration

- **Production Server**: Gunicorn with Uvicorn workers
- **Reverse Proxy**: Nginx with SSL
- **Process Management**: Systemd services
- **Monitoring**: Built-in health checks
- **Auto-restart**: On failure or reboot

## VM Specifications

### Recommended Instance Types

| Workload | Instance Type | vCPUs | Memory | Disk | Cost/Month* |
|----------|---------------|-------|--------|------|-------------|
| Light | e2-standard-2 | 2 | 8GB | 20GB SSD | ~$50 |
| Medium | e2-standard-4 | 4 | 16GB | 50GB SSD | ~$100 |
| Heavy | c2-standard-4 | 4 | 16GB | 100GB SSD | ~$150 |

*Approximate costs for us-central1 region

### Network Configuration

- **Firewall Rules**: HTTP (80), HTTPS (443), SSH (22)
- **External IP**: Static IP recommended for production
- **Internal Network**: Access to Redis at `10.97.237.131:6379`

## Configuration Files

### Environment Variables

| Variable | Description | Production Value |
|----------|-------------|------------------|
| `REDIS_HOST` | Redis instance hostname | `10.97.237.131` |
| `REDIS_PORT` | Redis port | `6379` |
| `PYTHONPATH` | Python module path | `/app` |
| `PYTHONUNBUFFERED` | Python output buffering | `1` |

### Config Files

- **`config.yaml`**: Production configuration with Redis endpoint `10.97.237.131:6379`
- **`config.local.yaml`**: Local development with Docker Redis service

## Deployment Process

### Automated Deployment

The deployment script will:

1. **Create VM Instance** with Docker and required dependencies
2. **Configure Firewall Rules** for HTTP/HTTPS access
3. **Build and Push Docker Images** to Google Container Registry
4. **Deploy Containers** with docker-compose
5. **Setup Nginx** with SSL certificates
6. **Configure Systemd Services** for auto-restart
7. **Run Health Checks** to verify deployment

### Manual Steps (if needed)

```bash
# SSH into the VM
gcloud compute ssh trustlayer-ai-vm --zone=us-central1-a

# Check service status
sudo systemctl status trustlayer-proxy
sudo systemctl status trustlayer-dashboard
sudo systemctl status nginx

# View logs
sudo journalctl -u trustlayer-proxy -f
sudo journalctl -u trustlayer-dashboard -f
```

## SSL Configuration

### Automatic SSL (Recommended)

The deployment script sets up Let's Encrypt SSL certificates automatically:

```bash
# SSL certificates are automatically renewed
sudo certbot renew --dry-run
```

### Manual SSL Setup

If you need to configure SSL manually:

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring & Observability

### Health Checks

- **Proxy Health**: `https://your-domain.com/health`
- **Dashboard**: `https://your-domain.com:8501`
- **Metrics**: `https://your-domain.com/metrics`

### System Monitoring

```bash
# Check system resources
htop
df -h
free -h

# Check Docker containers
docker ps
docker stats

# Check service logs
sudo journalctl -u trustlayer-proxy --since "1 hour ago"
```

### Log Management

Logs are managed by systemd and rotated automatically:

- **Proxy Logs**: `/var/log/trustlayer/proxy.log`
- **Dashboard Logs**: `/var/log/trustlayer/dashboard.log`
- **Nginx Logs**: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`

## Testing Production Deployment

### 1. Health Check

```bash
curl -f https://your-domain.com/health
```

### 2. PII Redaction Test

```bash
curl -X POST https://your-domain.com/test \
  -H "Content-Type: application/json" \
  -d '{
    "content": "My name is John Doe and my email is john@example.com"
  }'
```

### 3. AI Provider Test (with valid API key)

```bash
curl -X POST https://your-domain.com/v1/chat/completions \
  -H "Host: api.openai.com" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello, my name is Jane Smith"}]
  }'
```

## Performance & Scaling

### Vertical Scaling

```bash
# Stop services
sudo systemctl stop trustlayer-proxy trustlayer-dashboard

# Resize VM (requires restart)
gcloud compute instances set-machine-type trustlayer-ai-vm \
  --machine-type=e2-standard-4 \
  --zone=us-central1-a

# Start VM and services
gcloud compute instances start trustlayer-ai-vm --zone=us-central1-a
```

### Horizontal Scaling

For high-traffic scenarios:

1. **Load Balancer**: Use GCP Load Balancer with multiple VMs
2. **Container Orchestration**: Consider GKE for auto-scaling
3. **Database Scaling**: Use Redis Cluster for high availability

## Security Features

### Network Security

- **Firewall Rules**: Only necessary ports (80, 443, 22) open
- **Private Redis**: Internal network access to `10.97.237.131:6379`
- **SSH Keys**: Key-based authentication only
- **Fail2ban**: Automatic IP blocking for failed attempts

### Application Security

- **Non-root Containers**: All containers run as non-root users
- **SSL/TLS**: End-to-end encryption with Let's Encrypt
- **Security Headers**: Nginx configured with security headers
- **Rate Limiting**: Built-in request rate limiting

### Data Protection

- **PII Encryption**: All PII mappings encrypted in Redis
- **Session TTL**: Automatic cleanup after 1 hour
- **Audit Logging**: All requests logged for compliance
- **Backup**: Automated daily backups of configuration

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - **Check**: Network connectivity to `10.97.237.131:6379`
   - **Solution**: Verify firewall rules and VPC configuration

2. **SSL Certificate Issues**
   - **Check**: Domain DNS pointing to VM external IP
   - **Solution**: Re-run certbot or check domain configuration

3. **Container Startup Issues**
   - **Check**: `sudo systemctl status trustlayer-proxy`
   - **Solution**: Check logs and restart services

4. **High Memory Usage**
   - **Check**: `free -h` and `docker stats`
   - **Solution**: Resize VM or optimize container resources

### Debug Commands

```bash
# Check VM status
gcloud compute instances describe trustlayer-ai-vm --zone=us-central1-a

# SSH into VM
gcloud compute ssh trustlayer-ai-vm --zone=us-central1-a

# Check all services
sudo systemctl status trustlayer-proxy trustlayer-dashboard nginx

# View container logs
docker logs trustlayer-proxy
docker logs trustlayer-dashboard

# Check Redis connectivity
redis-cli -h 10.97.237.131 -p 6379 ping

# Test internal connectivity
curl -f http://localhost:8000/health
curl -f http://localhost:8501
```

## Backup & Recovery

### Automated Backups

The deployment includes automated backup scripts:

```bash
# Configuration backup (daily)
/opt/trustlayer/backup-config.sh

# Container images backup (weekly)
/opt/trustlayer/backup-images.sh
```

### Manual Backup

```bash
# Backup configuration
sudo tar -czf trustlayer-backup-$(date +%Y%m%d).tar.gz \
  /opt/trustlayer/docker-compose.yml \
  /opt/trustlayer/config.yaml \
  /etc/nginx/sites-available/trustlayer

# Backup to Cloud Storage
gsutil cp trustlayer-backup-*.tar.gz gs://your-backup-bucket/
```

### Recovery Process

```bash
# Stop services
sudo systemctl stop trustlayer-proxy trustlayer-dashboard

# Restore configuration
sudo tar -xzf trustlayer-backup-YYYYMMDD.tar.gz -C /

# Restart services
sudo systemctl start trustlayer-proxy trustlayer-dashboard nginx
```

## Cost Optimization

### Resource Monitoring

```bash
# Check current usage
gcloud compute instances describe trustlayer-ai-vm --zone=us-central1-a \
  --format="table(machineType,status,scheduling.preemptible)"

# Monitor costs
gcloud billing budgets list
```

### Cost-Saving Options

1. **Preemptible VMs**: 60-91% cost reduction (for non-critical workloads)
2. **Committed Use Discounts**: Up to 57% savings for 1-3 year commitments
3. **Sustained Use Discounts**: Automatic discounts for long-running VMs
4. **Right-sizing**: Use smaller instances for lower traffic

## Maintenance

### Regular Maintenance Tasks

```bash
# Update system packages (monthly)
sudo apt update && sudo apt upgrade -y

# Update Docker images (as needed)
docker-compose pull && docker-compose up -d

# Clean up old Docker images
docker system prune -f

# Rotate logs (automatic via logrotate)
sudo logrotate -f /etc/logrotate.conf
```

### Security Updates

```bash
# Enable automatic security updates
sudo dpkg-reconfigure -plow unattended-upgrades

# Manual security updates
sudo apt update && sudo apt upgrade -y
```

## Support & Monitoring

### Health Monitoring

Set up monitoring alerts:

```bash
# CPU usage alert
gcloud alpha monitoring policies create --policy-from-file=cpu-alert.yaml

# Memory usage alert
gcloud alpha monitoring policies create --policy-from-file=memory-alert.yaml

# Disk usage alert
gcloud alpha monitoring policies create --policy-from-file=disk-alert.yaml
```

### Log Analysis

```bash
# Analyze access patterns
sudo tail -f /var/log/nginx/access.log | grep -E "(POST|GET) /"

# Monitor error rates
sudo tail -f /var/log/nginx/error.log

# Check application performance
curl -s https://your-domain.com/metrics | jq '.performance'
```

## Next Steps

1. **Domain Configuration**: Point your domain to the VM's external IP
2. **SSL Setup**: Configure SSL certificates for your domain
3. **Monitoring**: Set up Cloud Monitoring alerts
4. **Backup Strategy**: Configure automated backups
5. **Load Testing**: Validate performance under expected load
6. **Security Audit**: Review security configuration
7. **Documentation**: Update internal documentation with deployment details

---

**Status**: ✅ Production-ready for Google Compute Engine
**Redis Endpoint**: `10.97.237.131:6379`
**Server**: Gunicorn with Uvicorn workers on Compute Engine VM
**SSL**: Let's Encrypt automatic certificates
**Monitoring**: Systemd services with health checks
**Last Updated**: January 31, 2026