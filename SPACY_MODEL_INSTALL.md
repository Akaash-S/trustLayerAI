# 🧠 spaCy Model Installation Guide

If the automatic spaCy model download fails, here are manual installation methods:

## Method 1: Direct pip install (Recommended)

```bash
# Activate your virtual environment first
venv\Scripts\activate

# Install the large English model directly
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl
```

## Method 2: Use smaller model (Faster, less accurate)

```bash
# Install smaller model if large one fails
python -m spacy download en_core_web_sm
```

Then update `config.yaml` to use the smaller model:
```yaml
presidio:
  model: "en_core_web_sm"  # Add this line
  entities:
    - "PERSON"
    # ... rest of entities
```

## Method 3: Download and install manually

1. Download the model file:
   - Go to: https://github.com/explosion/spacy-models/releases
   - Find `en_core_web_lg-3.7.1` 
   - Download the `.whl` file

2. Install locally:
```bash
pip install path/to/downloaded/en_core_web_lg-3.7.1-py3-none-any.whl
```

## Method 4: Alternative model versions

Try different versions if the latest doesn't work:

```bash
# Try version 3.6.0
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.6.0/en_core_web_lg-3.6.0-py3-none-any.whl

# Try version 3.5.0  
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.5.0/en_core_web_lg-3.5.0-py3-none-any.whl
```

## Verify Installation

Test if the model is installed correctly:

```python
import spacy

# Test large model
try:
    nlp = spacy.load("en_core_web_lg")
    print("✅ en_core_web_lg loaded successfully")
except OSError:
    print("❌ en_core_web_lg not found")

# Test small model (fallback)
try:
    nlp = spacy.load("en_core_web_sm") 
    print("✅ en_core_web_sm loaded successfully")
except OSError:
    print("❌ en_core_web_sm not found")
```

## Troubleshooting

### Issue: "Can't find model"
```bash
# Link the model manually
python -m spacy link en_core_web_lg en
```

### Issue: "No module named 'en_core_web_lg'"
```bash
# Reinstall spacy first
pip uninstall spacy
pip install spacy==3.7.2
# Then install model again
```

### Issue: Network/firewall blocking download
1. Download the `.whl` file manually from GitHub releases
2. Transfer to your machine
3. Install with `pip install filename.whl`

## Model Comparison

| Model | Size | Accuracy | Speed | Use Case |
|-------|------|----------|-------|----------|
| en_core_web_lg | ~750MB | High | Slower | Production |
| en_core_web_md | ~50MB | Medium | Medium | Development |
| en_core_web_sm | ~15MB | Lower | Fast | Testing |

For TrustLayer AI, we recommend `en_core_web_lg` for best PII detection accuracy in production.