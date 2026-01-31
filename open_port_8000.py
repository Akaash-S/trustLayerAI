#!/usr/bin/env python3
"""
Open Port 8000 for External Access
Creates firewall rule to allow external access to TrustLayer AI on port 8000
"""

import subprocess
import sys

def run_command(command, description=""):
    """Run shell command and return result"""
    print(f"🔧 {description}")
    print(f"   Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Success")
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n')[:3]:
                    print(f"      {line}")
            return True, result.stdout.strip()
        else:
            print(f"   ❌ Failed: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, str(e)

def open_port_8000():
    """Open port 8000 for external access"""
    print("🚀 Opening Port 8000 for External Access")
    print("=" * 50)
    
    # Step 1: Create firewall rule for port 8000
    print("\n1️⃣ Creating firewall rule for port 8000...")
    command = '''gcloud compute firewall-rules create trustlayer-port-8000 \
    --network vpc-trustlayer \
    --action ALLOW \
    --rules tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --target-tags trustlayer-web \
    --description "Allow external access to TrustLayer AI port 8000" \
    --priority 1000'''
    
    success, output = run_command(command, "Creating firewall rule for port 8000")
    
    if not success and "already exists" in output:
        print("   ✅ Rule already exists - that's fine")
        success = True
    
    # Step 2: Create firewall rule for port 8501 (dashboard)
    print("\n2️⃣ Creating firewall rule for port 8501...")
    command2 = '''gcloud compute firewall-rules create trustlayer-port-8501 \
    --network vpc-trustlayer \
    --action ALLOW \
    --rules tcp:8501 \
    --source-ranges 0.0.0.0/0 \
    --target-tags trustlayer-web \
    --description "Allow external access to TrustLayer AI dashboard port 8501" \
    --priority 1000'''
    
    success2, output2 = run_command(command2, "Creating firewall rule for port 8501")
    
    if not success2 and "already exists" in output2:
        print("   ✅ Rule already exists - that's fine")
        success2 = True
    
    # Step 3: Verify VM has the correct network tags
    print("\n3️⃣ Checking VM network tags...")
    vm_command = 'gcloud compute instances describe trustlayer-ai-main --zone=us-central1-a --format="value(tags.items)"'
    success3, tags = run_command(vm_command, "Getting VM network tags")
    
    if success3:
        if "trustlayer-web" in tags:
            print("   ✅ VM has trustlayer-web tag")
        else:
            print("   ⚠️  VM missing trustlayer-web tag - adding it...")
            add_tag_command = 'gcloud compute instances add-tags trustlayer-ai-main --tags trustlayer-web --zone us-central1-a'
            run_command(add_tag_command, "Adding trustlayer-web tag to VM")
    
    # Step 4: List all TrustLayer firewall rules
    print("\n4️⃣ Listing all TrustLayer firewall rules...")
    list_command = 'gcloud compute firewall-rules list --filter="name~trustlayer" --format="table(name,allowed,sourceRanges,targetTags)"'
    run_command(list_command, "Listing TrustLayer firewall rules")
    
    print("\n" + "=" * 50)
    print("🎉 PORT 8000 SHOULD NOW BE ACCESSIBLE!")
    print("=" * 50)
    
    print("\n🔧 NEW PROXY CONFIGURATION:")
    print("   HTTP Proxy:  34.59.4.137:8000")
    print("   HTTPS Proxy: 34.59.4.137:8000")
    print("   Dashboard:   http://34.59.4.137:8501")
    print("   Health:      http://34.59.4.137:8000/health")
    print("   Metrics:     http://34.59.4.137:8000/metrics")
    
    print("\n📋 TEST COMMANDS:")
    print("   curl http://34.59.4.137:8000/health")
    print("   curl http://34.59.4.137:8000/metrics")
    print("   curl -I http://34.59.4.137:8501")
    
    print("\n⏳ Wait 1-2 minutes for firewall rules to propagate, then test!")
    
    return success and success2

if __name__ == "__main__":
    success = open_port_8000()
    
    if success:
        print("\n✅ Firewall rules created successfully!")
        print("Test external access in 1-2 minutes")
    else:
        print("\n❌ Failed to create firewall rules")
        print("You may need to run this from Google Cloud Shell")
        print("Or create the rules manually in GCP Console")