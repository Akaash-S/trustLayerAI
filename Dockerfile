FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal for production)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-install spaCy model during build (production-ready)
# Using direct download URL for reliability
RUN python -c "import spacy; spacy.cli.download('en_core_web_sm')" || \
    pip install --no-cache-dir https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl || \
    echo "Warning: spaCy model installation failed, will use basic PII detection"

# Copy application code
COPY app/ ./app/
COPY config.yaml ./
COPY dashboard.py ./

# Create non-root user for security
RUN useradd -m -u 1000 trustlayer && \
    chown -R trustlayer:trustlayer /app
USER trustlayer

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command using Gunicorn (not uvicorn)
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "1", "--timeout", "120", "--keep-alive", "2"]