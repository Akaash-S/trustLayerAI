FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model for NLP
RUN python -m spacy download en_core_web_lg

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 trustlayer && chown -R trustlayer:trustlayer /app
USER trustlayer

# Expose ports
EXPOSE 8000 8501

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]