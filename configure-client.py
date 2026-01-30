#!/usr/bin/env python3
"""
TrustLayer AI - Client Configuration Helper
Helps configure your applications to use TrustLayer AI proxy
"""

import json
import os
import sys

def generate_openai_config(domain, api_key="your-openai-api-key"):
    """Generate OpenAI client configuration"""
    return f"""
# OpenAI Configuration for TrustLayer AI
import openai

client = openai.OpenAI(
    api_key="{api_key}",
    base_url="https://{domain}/v1"
)

# For requests that need Host header routing
import httpx
client._client = httpx.Client(
    headers={{"Host": "api.openai.com"}}
)

# Example usage
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {{"role": "user", "content": "My name is John Doe and email is john@example.com"}}
    ]
)
print(response.choices[0].message.content)
"""

def generate_anthropic_config(domain, api_key="your-anthropic-api-key"):
    """Generate Anthropic client configuration"""
    return f"""
# Anthropic Configuration for TrustLayer AI
import anthropic

client = anthropic.Anthropic(
    api_key="{api_key}",
    base_url="https://{domain}"
)

# Set Host header for routing
client._client.headers.update({{"Host": "api.anthropic.com"}})

# Example usage
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=100,
    messages=[
        {{"role": "user", "content": "My SSN is 123-45-6789. Please help me."}}
    ]
)
print(response.content[0].text)
"""

def generate_curl_examples(domain):
    """Generate curl examples"""
    return f"""
# Curl Examples for TrustLayer AI

# Test PII Detection
curl -X POST https://{domain}/test \\
  -H "Content-Type: application/json" \\
  -d '{{"content": "My name is John Doe, email john@example.com"}}'

# OpenAI API Call
curl -X POST https://{domain}/v1/chat/completions \\
  -H "Host: api.openai.com" \\
  -H "Authorization: Bearer your-openai-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "model": "gpt-3.5-turbo",
    "messages": [
      {{"role": "user", "content": "My credit card is 4532-1234-5678-9012"}}
    ]
  }}'

# Anthropic API Call
curl -X POST https://{domain}/v1/messages \\
  -H "Host: api.anthropic.com" \\
  -H "Authorization: Bearer your-anthropic-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 100,
    "messages": [
      {{"role": "user", "content": "My phone number is 555-123-4567"}}
    ]
  }}'

# Health Check
curl https://{domain}/health

# Metrics
curl https://{domain}/metrics
"""

def generate_env_vars(domain):
    """Generate environment variables"""
    return f"""
# Environment Variables for TrustLayer AI
export TRUSTLAYER_PROXY="https://{domain}"
export OPENAI_BASE_URL="$TRUSTLAYER_PROXY/v1"
export ANTHROPIC_BASE_URL="$TRUSTLAYER_PROXY"

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export TRUSTLAYER_PROXY="https://{domain}"' >> ~/.bashrc
echo 'export OPENAI_BASE_URL="$TRUSTLAYER_PROXY/v1"' >> ~/.bashrc
echo 'export ANTHROPIC_BASE_URL="$TRUSTLAYER_PROXY"' >> ~/.bashrc
"""

def generate_hosts_file(domain, vm_ip):
    """Generate hosts file entries for DNS override"""
    return f"""
# DNS Override Method (Advanced)
# Add these lines to your hosts file:

# Linux/Mac: /etc/hosts
# Windows: C:\\Windows\\System32\\drivers\\etc\\hosts

{vm_ip} api.openai.com
{vm_ip} api.anthropic.com
{vm_ip} generativelanguage.googleapis.com

# This will redirect all AI API calls through TrustLayer AI
# Your applications will work without code changes!
"""

def main():
    if len(sys.argv) < 2:
        print("❌ Please provide your domain name")
        print("Usage: python3 configure-client.py your-domain.com [vm-ip]")
        print("Example: python3 configure-client.py trustlayer.example.com 34.123.45.67")
        sys.exit(1)
    
    domain = sys.argv[1]
    vm_ip = sys.argv[2] if len(sys.argv) > 2 else "YOUR_VM_IP"
    
    print(f"🔧 Generating TrustLayer AI client configurations for: {domain}")
    print()
    
    # Create output directory
    os.makedirs("client-configs", exist_ok=True)
    
    # Generate configurations
    configs = {
        "openai_config.py": generate_openai_config(domain),
        "anthropic_config.py": generate_anthropic_config(domain),
        "curl_examples.sh": generate_curl_examples(domain),
        "environment_vars.sh": generate_env_vars(domain),
        "hosts_file_entries.txt": generate_hosts_file(domain, vm_ip)
    }
    
    # Write configuration files
    for filename, content in configs.items():
        filepath = os.path.join("client-configs", filename)
        with open(filepath, "w") as f:
            f.write(content.strip() + "\n")
        print(f"✅ Created: {filepath}")
    
    print()
    print("🎉 Client configurations generated!")
    print()
    print("📋 Next steps:")
    print("   1. Review the generated files in ./client-configs/")
    print("   2. Update API keys in the Python files")
    print("   3. Choose your integration method:")
    print("      • Code changes: Use openai_config.py or anthropic_config.py")
    print("      • Environment variables: Source environment_vars.sh")
    print("      • DNS override: Add hosts_file_entries.txt to your hosts file")
    print("   4. Test with: chmod +x test-proxy.sh && ./test-proxy.sh")
    print()
    print("🔗 Useful links:")
    print(f"   • Health: https://{domain}/health")
    print(f"   • Dashboard: https://{domain}/dashboard")
    print(f"   • Metrics: https://{domain}/metrics")

if __name__ == "__main__":
    main()