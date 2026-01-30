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

# Download spaCy model with fallback options
RUN python -m spacy download en_core_web_lg || \
    python -m spacy download en_core_web_sm || \
    (echo "Warning: Could not download spaCy model, will download at runtime" && \
     mkdir -p /app/models && \
     echo "en_core_web_sm" > /app/models/fallback_model.txt)

# Copy application code
COPY . .

# Create startup script that handles model download at runtime
RUN echo '#!/bin/bash\n\
# Check if spaCy model is available\n\
python -c "import spacy; spacy.load(\"en_core_web_lg\")" 2>/dev/null || \\\n\
python -c "import spacy; spacy.load(\"en_core_web_sm\")" 2>/dev/null || \\\n\
{\n\
    echo "Downloading spaCy model at runtime..."\n\
    python -m spacy download en_core_web_sm || echo "Failed to download model, using basic NLP"\n\
}\n\
\n\
# Start the application\n\
exec "$@"\n' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 trustlayer && chown -R trustlayer:trustlayer /app
USER trustlayer

# Expose ports
EXPOSE 8000 8501

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]