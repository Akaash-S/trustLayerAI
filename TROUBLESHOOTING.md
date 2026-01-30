# 🔧 TrustLayer AI Troubleshooting Guide

This guide helps resolve common issues when setting up and testing TrustLayer AI locally.

## 🚨 Common Issues & Solutions

### Issue 1: "Module not found" errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
ImportError: No module named 'presidio_analyzer'
```

**Solutions:**
```bash
# Ensure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstall requirements
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# If spaCy model fails
python -m spacy download en_core_web_lg --force-reinstall
```

### Issue 2: Redis connection failed

**Symptoms:**
```
redis.exceptions.ConnectionError: Error 10061 connecting to localhost:6379
ConnectionRefusedError: [WinError 10061] No connection could be made
```

**Solutions:**
```bash
# Check if Redis container is running
docker ps

# Start Redis if not running
docker run -d --name trustlayer-redis -p 6379:6379 redis:7-alpine

# If container exists but stopped
docker start trustlayer-redis

# Test Redis connection
docker exec trustlayer-redis redis-cli ping
# Should return: PONG

# If port 6379 is busy
netstat -ano | findstr :6379
# Kill the process or use different port in config.yaml
```

### Issue 3: Port already in use

**Symptoms:**
```
OSError: [WinError 10048] Only one usage of each socket address is normally permitted
uvicorn.main:ERROR: [Errno 48] Address already in use
```

**Solutions:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID_NUMBER> /F

# Or use different port
uvicorn app.main:app --port 8001

# For Streamlit (port 8501)
streamlit run dashboard.py --server.port 8502
```

### Issue 4: Docker not running

**Symptoms:**
```
docker: error during connect: This error may indicate that the docker daemon is not running
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solutions:**
```bash
# Windows: Start Docker Desktop
# Check system tray for Docker icon

# Linux: Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Mac: Start Docker Desktop application

# Verify Docker is running
docker --version
docker ps
```

### Issue 5: spaCy model download fails

**Symptoms:**
```
OSError: [E050] Can't find model 'en_core_web_lg'
HTTP Error 404: Not Found (when downloading model)
ERROR: failed to build: process "/bin/sh -c python -m spacy download en_core_web_lg" did not complete successfully
```

**Solutions:**
```bash
# For local setup - try direct download
python -m spacy download en_core_web_lg

# If network issues, download manually
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl

# Use smaller model for testing
python -m spacy download en_core_web_sm
# Then update config.yaml to use en_core_web_sm

# For Docker builds - use the lightweight setup
python docker_setup.py

# Or build without model (downloads at runtime)
docker build -f Dockerfile.light -t trustlayer-ai .

# Verify model installation
python -c "import spacy; nlp = spacy.load('en_core_web_lg'); print('Model loaded successfully')"
```

### Issue 5a: Docker build fails with spaCy model

**Symptoms:**
```
ERROR: failed to build: failed to solve: process "/bin/sh -c python -m spacy download en_core_web_lg" did not complete successfully: exit code 1
```

**Solutions:**
```bash
# Use the Docker-specific setup script
python docker_setup.py

# Or manually build lightweight image
docker build -f Dockerfile.light -t trustlayer-ai .

# Or use docker-compose with runtime model download
docker-compose up -d

# Check container logs for model download progress
docker logs trustlayer-proxy

# If model download fails in container, exec into container
docker exec -it trustlayer-proxy bash
python -m spacy download en_core_web_sm
```

### Issue 6: Dashboard not loading

**Symptoms:**
```
ConnectionError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded
Streamlit app not accessible at localhost:8501
```

**Solutions:**
```bash
# Check if proxy is running
curl http://localhost:8000/health

# Check if Streamlit is running
netstat -ano | findstr :8501

# Restart Streamlit with verbose output
streamlit run dashboard.py --logger.level debug

# Check firewall settings
# Windows: Allow Python through Windows Firewall
# Antivirus: Add exception for Python/Streamlit

# Try different browser or incognito mode
# Clear browser cache
```

### Issue 7: Presidio/NLP errors

**Symptoms:**
```
ValueError: [E002] Can't find factory for 'sentencizer'
ModuleNotFoundError: No module named 'presidio_analyzer'
```

**Solutions:**
```bash
# Reinstall Presidio components
pip uninstall presidio-analyzer presidio-anonymizer
pip install presidio-analyzer presidio-anonymizer

# Install additional dependencies
pip install spacy transformers torch

# Download required models
python -m spacy download en_core_web_lg

# Test Presidio installation
python -c "from presidio_analyzer import AnalyzerEngine; print('Presidio working')"
```

### Issue 8: File upload tests fail

**Symptoms:**
```
ModuleNotFoundError: No module named 'reportlab'
ImportError: No module named 'openpyxl'
```

**Solutions:**
```bash
# Install missing test dependencies
pip install reportlab openpyxl

# If PDF generation fails
pip install --upgrade reportlab

# Test file creation
python -c "from reportlab.pdfgen import canvas; print('ReportLab working')"
python -c "import openpyxl; print('OpenPyXL working')"
```

### Issue 9: Permission errors (Windows)

**Symptoms:**
```
PermissionError: [WinError 5] Access is denied
FileNotFoundError: [WinError 2] The system cannot find the file specified
```

**Solutions:**
```bash
# Run Command Prompt as Administrator
# Right-click -> "Run as administrator"

# Or use PowerShell as Administrator
# Right-click PowerShell -> "Run as administrator"

# Check file permissions
# Ensure you have write access to the project directory

# Disable antivirus temporarily for testing
# Add project folder to antivirus exclusions
```

### Issue 10: Slow performance

**Symptoms:**
- Long startup times
- Slow PII detection
- High memory usage

**Solutions:**
```bash
# Use smaller spaCy model for testing
python -m spacy download en_core_web_sm

# Update config.yaml:
# Change model reference from en_core_web_lg to en_core_web_sm

# Increase Redis memory (if needed)
docker run -d --name trustlayer-redis -p 6379:6379 redis:7-alpine redis-server --maxmemory 256mb

# Monitor resource usage
docker stats trustlayer-redis
```

## 🔍 Diagnostic Commands

### Check System Status
```bash
# Python version
python --version

# Docker status
docker --version
docker ps

# Redis status
docker exec trustlayer-redis redis-cli ping

# Port usage
netstat -ano | findstr :8000
netstat -ano | findstr :8501
netstat -ano | findstr :6379

# Process list
tasklist | findstr python
tasklist | findstr streamlit
```

### Test Individual Components
```bash
# Test Python imports
python -c "import fastapi, uvicorn, redis, presidio_analyzer, spacy; print('All imports OK')"

# Test spaCy model
python -c "import spacy; nlp = spacy.load('en_core_web_lg'); print('spaCy model OK')"

# Test Redis connection
python -c "import redis; r = redis.Redis(); r.ping(); print('Redis OK')"

# Test proxy health
curl http://localhost:8000/health

# Test dashboard connectivity
curl http://localhost:8501
```

### Debug Logs
```bash
# Run proxy with debug logging
uvicorn app.main:app --log-level debug

# Run Streamlit with debug
streamlit run dashboard.py --logger.level debug

# Check Docker logs
docker logs trustlayer-redis
```

## 🆘 Getting Help

### Log Collection
When reporting issues, include:

1. **System Information:**
   ```bash
   python --version
   docker --version
   pip list | findstr -i "fastapi uvicorn redis presidio spacy streamlit"
   ```

2. **Error Messages:**
   - Full error traceback
   - Command that caused the error
   - Any relevant log output

3. **Configuration:**
   - Contents of `config.yaml`
   - Environment variables
   - Docker container status

### Reset Everything
If all else fails, complete reset:

```bash
# Stop all processes
taskkill /F /IM python.exe
taskkill /F /IM streamlit.exe

# Remove Docker containers
docker stop trustlayer-redis
docker rm trustlayer-redis

# Remove virtual environment
rmdir /s venv

# Start fresh
python setup_simple.py
```

### Performance Optimization

For better performance during testing:

1. **Use smaller models:**
   ```bash
   python -m spacy download en_core_web_sm
   # Update config to use en_core_web_sm
   ```

2. **Reduce logging:**
   ```yaml
   # In config.yaml, add:
   logging:
     level: WARNING
   ```

3. **Limit Redis memory:**
   ```bash
   docker run -d --name trustlayer-redis -p 6379:6379 redis:7-alpine redis-server --maxmemory 128mb
   ```

## 📞 Support Channels

- 🐛 **Issues**: Create GitHub issue with logs and system info
- 💬 **Discussions**: Use GitHub Discussions for questions
- 📧 **Email**: support@trustlayer.ai (if available)
- 📖 **Documentation**: Check README.md and LOCAL_TESTING_GUIDE.md

Remember: Most issues are related to environment setup. The `setup_simple.py` script handles most common problems automatically.