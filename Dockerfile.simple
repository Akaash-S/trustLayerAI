FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download spaCy model during build with proper error handling
RUN python -m spacy download en_core_web_sm || \
    pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl || \
    echo "Warning: spaCy model installation failed, will use basic PII detection"

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 trustlayer && chown -R trustlayer:trustlayer /app
USER trustlayer

# Expose ports
EXPOSE 8000 8501

# Default command (will be overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]