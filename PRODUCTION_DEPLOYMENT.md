# TrustLayer AI - Production Deployment Guide

## Overview

This guide covers deploying TrustLayer AI to Google Cloud Platform (GCP) with production-ready configurations including:

- **Cloud Run** for serverless container hosting with Gunicorn + Uvicorn workers
- **Redis Memory Store** at endpoint `10.97.237.131:6379` for session management
- **Production-optimized Docker image** with pre-installed spaCy models
- **Auto-scaling** from 1-10 instances based on traffic

## Prerequisites

1. **GCP Account** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Docker** installed locally
4. **Redis instance** already running at `10.97.237.131:6379`

## Quick Start

### 1. Set Environment Variables

```bash
# Windows PowerShell
$env:PROJECT_ID = "your-gcp-project-id"

# Linux/Mac
export PROJECT_ID="your-gcp-project-id"
```

### 2. Deploy to Production

**Windows:**
```powershell
.\deploy-production.ps1 -ProjectId "your-gcp-project-id"
```

**Linux/Mac:**
```bash
./deploy-production.sh
```

## Architecture

### Production Components

1. **TrustLayer AI Proxy** (Cloud Run)
   - FastAPI application with PII redaction
   - Gunicorn server with Uvicorn workers for production performance
   - Connects to Redis at `10.97.237.131:6379`
   - Auto-scaling based on traffic (1-10 instances)

2. **Redis Memory Store** (External)
   - Primary endpoint: `10.97.237.131:6379`
   - Session storage for PII mappings
   - Telemetry data collection

3. **Production Optimizations**
   - Pre-installed spaCy models during build
   - No runtime pip installations
   - Non-root container user
   - Health checks and monitoring

### Server Configuration

- **Production Server**: Gunicorn with Uvicorn workers
- **Development Server**: Uvicorn with reload
- **Worker Class**: `uvicorn.workers.UvicornWorker`
- **Timeout**: 120 seconds
- **Keep-alive**: 2 seconds

## Configuration

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

## Docker Configuration

### Single Dockerfile

The codebase now uses a single `Dockerfile` optimized for production:

```dockerfile
FROM python:3.11-slim

# Install dependencies and spaCy model during build
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import spacy; spacy.cli.download('en_core_web_sm')" || \
    pip install --no-cache-dir https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# Production command with Gunicorn
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "1", "--timeout", "120", "--keep-alive", "2"]
```

### Local Development

For local development with Docker Compose:

```bash
docker compose up
```

This uses the local Redis container and development configuration.

## Monitoring & Observability

### Health Checks

- **Endpoint**: `/health`
- **Expected Response**: `{"status": "healthy", "service": "TrustLayer AI Proxy"}`
- **Timeout**: 10 seconds

### Metrics

- **Endpoint**: `/metrics`
- **Data**: Request counts, PII blocking stats, latency percentiles
- **Format**: JSON

### Logging

```bash
# View Cloud Run logs
gcloud run services logs read trustlayer-ai-proxy --region=us-central1

# Follow logs in real-time
gcloud run services logs tail trustlayer-ai-proxy --region=us-central1
```

## Testing Production Deployment

### 1. Health Check

```bash
curl -f https://your-service-url/health
```

### 2. PII Redaction Test

```bash
curl -X POST https://your-service-url/test \
  -H "Content-Type: application/json" \
  -d '{
    "content": "My name is John Doe and my email is john@example.com"
  }'
```

### 3. AI Provider Test (with valid API key)

```bash
curl -X POST https://your-service-url/v1/chat/completions \
  -H "Host: api.openai.com" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello, my name is Jane Smith"}]
  }'
```

## Performance & Scaling

### Auto-scaling Configuration

- **Min instances**: 1 (always warm)
- **Max instances**: 10 (adjust based on load)
- **Concurrency**: 100 requests per instance
- **CPU**: 1000m (1 vCPU)
- **Memory**: 2Gi

### Gunicorn Benefits

- **Production-grade WSGI server**
- **Better resource management**
- **Graceful worker restarts**
- **Process monitoring**
- **Signal handling**

## Security Features

### Network Security

- **Internal Load Balancer**: Cloud Run with internal ingress
- **Redis Connection**: Direct IP connection to `10.97.237.131:6379`
- **Non-root Container**: Security hardened with dedicated user

### Data Protection

- **PII Encryption**: All PII mappings encrypted in Redis
- **Session TTL**: Automatic cleanup after 1 hour
- **Audit Logging**: All requests logged for compliance

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - **Check**: Redis instance at `10.97.237.131:6379` is accessible
   - **Solution**: Verify network connectivity and firewall rules

2. **spaCy Model Missing**
   - **Fixed**: Production image pre-installs models during build
   - **Fallback**: Basic regex patterns if models unavailable

3. **Gunicorn Worker Issues**
   - **Check**: Worker timeout settings (120s)
   - **Solution**: Adjust timeout or worker count based on load

### Debug Commands

```bash
# Check Cloud Run service status
gcloud run services describe trustlayer-ai-proxy --region=us-central1

# Test Redis connectivity
redis-cli -h 10.97.237.131 -p 6379 ping

# Check container logs
gcloud run services logs read trustlayer-ai-proxy --region=us-central1 --limit=50
```

## File Structure

After cleanup, the codebase now has a clean structure:

```
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── redactor.py          # PII redaction engine
│   ├── telemetry.py         # Metrics collection
│   └── extractors.py        # File processing
├── gcp-deployment/
│   └── cloud-run-production.yaml
├── Dockerfile               # Single production Dockerfile
├── docker-compose.yml       # Local development
├── config.yaml              # Production config (Redis: 10.97.237.131:6379)
├── config.local.yaml        # Local development config
├── dashboard.py             # Streamlit dashboard
├── requirements.txt         # Dependencies (includes Gunicorn)
├── deploy-production.ps1    # Windows deployment
├── deploy-production.sh     # Linux/Mac deployment
└── README.md
```

## Next Steps

1. **Test Deployment**: Run health checks and PII redaction tests
2. **Monitor Performance**: Check metrics and logs
3. **Scale Testing**: Validate auto-scaling behavior
4. **Security Audit**: Review network and data security
5. **Backup Strategy**: Implement Redis backup if needed

---

**Status**: ✅ Production-ready with Gunicorn, Redis endpoint, and optimized Docker image
**Redis Endpoint**: `10.97.237.131:6379`
**Server**: Gunicorn + Uvicorn workers
**Last Updated**: January 31, 2026