# TrustLayer AI - VM Deployment Guide

## Quick Start

Since you already have your VM created, just run these simple commands to build and start the containers:

### Linux/Mac:
```bash
# Make script executable
chmod +x build-and-run.sh

# Build and run (replace with your actual project ID)
./build-and-run.sh your-gcp-project-id
```

### Windows:
```powershell
# Build and run (replace with your actual project ID)
.\build-and-run.ps1 -ProjectId "your-gcp-project-id"
```

## What the script does:

1. **Stops** any existing containers
2. **Builds** the Docker image locally with all dependencies
3. **Creates** docker-compose.yml from the production template
4. **Starts** both proxy and dashboard containers
5. **Tests** health endpoints
6. **Shows** status and management commands

## Services:

- **Proxy**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **Dashboard**: http://localhost:8501
- **Redis**: 10.97.237.131:6379 (your existing Redis instance)

## Management Commands:

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Check status
docker-compose ps

# Update and restart
./build-and-run.sh your-project-id
```

## Configuration:

- **Redis Endpoint**: 10.97.237.131:6379 (configured in config.yaml)
- **Server**: Gunicorn with 2 Uvicorn workers
- **Timeout**: 120 seconds
- **Auto-restart**: Unless stopped manually

## Troubleshooting:

If containers fail to start:

```bash
# Check logs
docker-compose logs proxy
docker-compose logs dashboard

# Test Redis connectivity
redis-cli -h 10.97.237.131 -p 6379 ping

# Rebuild image
docker build -t trustlayer-ai:latest .
docker-compose up -d
```

That's it! Simple and straightforward deployment for your existing VM.