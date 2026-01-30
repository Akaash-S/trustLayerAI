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
    
    # Check if large model exists
    if python -c "import spacy; spacy.load('en_core_web_lg')" 2>/dev/null; then
        echo "✅ spaCy model (en_core_web_lg) is available"
        return 0
    fi
    
    # Try to download small model
    echo "📥 Attempting to download spaCy model..."
    if python -m spacy download en_core_web_sm 2>/dev/null; then
        echo "✅ Successfully downloaded en_core_web_sm"
        return 0
    fi
    
    # Try alternative download method
    echo "📥 Trying alternative download method..."
    if pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl 2>/dev/null; then
        echo "✅ Successfully installed model via direct download"
        return 0
    fi
    
    echo "⚠️  Could not download spaCy model"
    echo "   TrustLayer will use basic regex patterns for PII detection"
    echo "   This provides ~70-80% accuracy vs ~95% with spaCy models"
    return 1
}

# Setup spaCy model (don't fail if it doesn't work)
setup_spacy_model || true

echo "🚀 Starting application..."
exec "$@"