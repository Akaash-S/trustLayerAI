#!/usr/bin/env python3
"""
TrustLayer AI - Auto GCP Test
Automatically detects GCP VM external IP and tests connectivity
"""

import subprocess
import json
import sys
import os
from test_external_ip import TrustLayerExternalTester

def run_command(command):
    """Run shell command and return output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None
    except Exception:
        return None

def get_vm_external_ip(vm_name="trustlayer-ai-main", zone="us-central1-a"):
    """Get VM external IP using gcloud"""
    print(f"🔍 Looking for VM: {vm_name} in zone: {zone}")
    
    command = f'gcloud compute instances describe {vm_name} --zone={zone} --format="value(networkInterfaces[0].accessConfigs[0].natIP)"'
    external_ip = run_command(command)
    
    if external_ip:
        print(f"✅ Found VM external IP: {external_ip}")
        return external_ip
    else:
        print("❌ Could not get VM external IP")
        return None

def get_load_balancer_ip(lb_name="trustlayer-ip"):
    """Get load balancer IP using gcloud"""
    print(f"🔍 Looking for load balancer: {lb_name}")
    
    command = f'gcloud compute addresses describe {lb_name} --global --format="value(address)"'
    lb_ip = run_command(command)
    
    if lb_ip:
        print(f"✅ Found load balancer IP: {lb_ip}")
        return lb_ip
    else:
        print("⚠️  No load balancer found (this is optional)")
        return None

def check_gcloud_auth():
    """Check if gcloud is authenticated"""
    result = run_command("gcloud auth list --filter=status:ACTIVE --format='value(account)'")
    if result:
        print(f"✅ Authenticated as: {result}")
        return True
    else:
        print("❌ Not authenticated with gcloud")
        print("   Run: gcloud auth login")
        return False

def list_vms():
    """List all VMs to help user find the right one"""
    print("🔍 Available VMs:")
    result = run_command('gcloud compute instances list --format="table(name,zone,status,EXTERNAL_IP)"')
    if result:
        print(result)
    else:
        print("❌ Could not list VMs")

def main():
    """Main function"""
    print("🚀 TrustLayer AI - Auto GCP Test")
    print("=" * 50)
    
    # Check gcloud authentication
    if not check_gcloud_auth():
        sys.exit(1)
    
    # Get VM name and zone from command line or use defaults
    vm_name = sys.argv[1] if len(sys.argv) > 1 else "trustlayer-ai-main"
    zone = sys.argv[2] if len(sys.argv) > 2 else "us-central1-a"
    
    # Try to get VM external IP
    external_ip = get_vm_external_ip(vm_name, zone)
    
    if not external_ip:
        print("\n🔍 Let me show you available VMs:")
        list_vms()
        print("\nUsage: python auto_test_gcp.py [VM_NAME] [ZONE]")
        print("Example: python auto_test_gcp.py trustlayer-ai-main us-central1-a")
        sys.exit(1)
    
    # Try to get load balancer IP (optional)
    lb_ip = get_load_balancer_ip()
    
    print("\n" + "=" * 50)
    print("🧪 Starting connectivity tests...")
    print("=" * 50)
    
    # Run comprehensive tests
    tester = TrustLayerExternalTester(external_ip, lb_ip)
    tester.run_all_tests()

if __name__ == "__main__":
    main()