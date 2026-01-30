#!/usr/bin/env python3
"""
TrustLayer AI - Fix External Access
Diagnoses and fixes external access issues for GCP Compute Engine
"""

import subprocess
import sys
import json
import time

def run_command(command, description=""):
    """Run shell command and return result"""
    print(f"🔧 {description}")
    print(f"   Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Success")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True, result.stdout.strip()
        else:
            print(f"   ❌ Failed: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, str(e)

def check_gcloud_auth():
    """Check if gcloud is authenticated"""
    success, output = run_command("gcloud auth list --filter=status:ACTIVE --format='value(account)'", "Checking gcloud authentication")
    if success and output:
        print(f"   ✅ Authenticated as: {output}")
        return True
    else:
        print("   ❌ Not authenticated with gcloud")
        print("   Run: gcloud auth login")
        return False

def get_vm_info(vm_name="trustlayer-ai-main", zone="us-central1-a"):
    """Get VM information"""
    print(f"\n🔍 Getting VM information for {vm_name} in {zone}")
    
    command = f'gcloud compute instances describe {vm_name} --zone={zone} --format=json'
    success, output = run_command(command, f"Getting VM details")
    
    if success:
        try:
            vm_info = json.loads(output)
            external_ip = vm_info['networkInterfaces'][0]['accessConfigs'][0]['natIP']
            internal_ip = vm_info['networkInterfaces'][0]['networkIP']
            status = vm_info['status']
            tags = vm_info.get('tags', {}).get('items', [])
            
            print(f"   ✅ VM Status: {status}")
            print(f"   ✅ External IP: {external_ip}")
            print(f"   ✅ Internal IP: {internal_ip}")
            print(f"   ✅ Network Tags: {tags}")
            
            return {
                'external_ip': external_ip,
                'internal_ip': internal_ip,
                'status': status,
                'tags': tags,
                'zone': zone,
                'name': vm_name
            }
        except Exception as e:
            print(f"   ❌ Error parsing VM info: {e}")
            return None
    else:
        return None

def check_firewall_rules():
    """Check existing firewall rules"""
    print(f"\n🔥 Checking firewall rules")
    
    command = 'gcloud compute firewall-rules list --filter="name~trustlayer" --format="table(name,allowed,sourceRanges,targetTags)"'
    success, output = run_command(command, "Listing TrustLayer firewall rules")
    
    if success:
        if "trustlayer" in output:
            print("   ✅ Found existing TrustLayer firewall rules:")
            print(f"   {output}")
            return True
        else:
            print("   ⚠️  No TrustLayer firewall rules found")
            return False
    return False

def create_firewall_rules():
    """Create necessary firewall rules"""
    print(f"\n🔥 Creating firewall rules")
    
    # Rule 1: Allow external access to proxy and dashboard
    command1 = '''gcloud compute firewall-rules create trustlayer-allow-external \
    --allow tcp:8000,tcp:8501,tcp:80,tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --target-tags trustlayer-web \
    --description "Allow external access to TrustLayer AI proxy and dashboard"'''
    
    success1, _ = run_command(command1, "Creating external access rule")
    
    # Rule 2: Allow SSH
    command2 = '''gcloud compute firewall-rules create trustlayer-allow-ssh \
    --allow tcp:22 \
    --source-ranges 0.0.0.0/0 \
    --target-tags trustlayer-vm \
    --description "Allow SSH access to TrustLayer AI VMs"'''
    
    success2, _ = run_command(command2, "Creating SSH access rule")
    
    return success1 and success2

def add_network_tags(vm_info):
    """Add network tags to VM"""
    print(f"\n🏷️  Adding network tags to VM")
    
    vm_name = vm_info['name']
    zone = vm_info['zone']
    existing_tags = vm_info['tags']
    
    # Tags we need
    required_tags = ['trustlayer-web', 'trustlayer-vm']
    
    # Check if tags already exist
    missing_tags = [tag for tag in required_tags if tag not in existing_tags]
    
    if not missing_tags:
        print("   ✅ All required tags already present")
        return True
    
    # Add missing tags
    all_tags = existing_tags + missing_tags
    tags_str = ','.join(all_tags)
    
    command = f'gcloud compute instances add-tags {vm_name} --tags {tags_str} --zone {zone}'
    success, _ = run_command(command, f"Adding tags: {missing_tags}")
    
    return success

def check_vm_services(vm_info):
    """Check if services are running on VM"""
    print(f"\n🐳 Checking services on VM")
    
    external_ip = vm_info['external_ip']
    
    # Try to SSH and check services
    commands = [
        "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'",
        "sudo netstat -tlnp | grep ':8000\\|:8501'",
        "curl -s http://localhost:8000/health || echo 'Health check failed'",
        "curl -s -I http://localhost:8501 || echo 'Dashboard check failed'"
    ]
    
    print(f"   📋 To check services manually, SSH into your VM:")
    print(f"   ssh {external_ip}")
    print(f"   Then run these commands:")
    for cmd in commands:
        print(f"   {cmd}")
    
    return True

def test_connectivity_after_fix(external_ip):
    """Test connectivity after applying fixes"""
    print(f"\n🧪 Testing connectivity after fixes")
    
    import socket
    import requests
    
    # Wait a moment for rules to propagate
    print("   ⏳ Waiting 30 seconds for firewall rules to propagate...")
    time.sleep(30)
    
    # Test TCP connection
    try:
        sock = socket.create_connection((external_ip, 8000), timeout=10)
        sock.close()
        print("   ✅ TCP connection to port 8000 successful")
        
        # Test health endpoint
        try:
            response = requests.get(f"http://{external_ip}:8000/health", timeout=10)
            if response.status_code == 200:
                print("   ✅ Health endpoint accessible")
                return True
            else:
                print(f"   ⚠️  Health endpoint returned HTTP {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Health endpoint error: {e}")
            
    except Exception as e:
        print(f"   ❌ TCP connection still failing: {e}")
        return False
    
    return False

def print_next_steps(vm_info):
    """Print next steps for user"""
    external_ip = vm_info['external_ip']
    
    print(f"\n📋 NEXT STEPS:")
    print("=" * 60)
    print("1. Wait 2-3 minutes for firewall rules to fully propagate")
    print("2. SSH into your VM to check services:")
    print(f"   ssh {external_ip}")
    print("3. Check if Docker containers are running:")
    print("   docker ps")
    print("4. Check if services are listening on all interfaces:")
    print("   sudo netstat -tlnp | grep ':8000\\|:8501'")
    print("5. Test health endpoint locally on VM:")
    print("   curl http://localhost:8000/health")
    print("6. If services aren't running, start them:")
    print("   cd /opt/trustlayer-ai")
    print("   docker-compose up -d")
    print("7. Test external access again:")
    print(f"   python test_external_ip.py {external_ip}")
    
    print(f"\n🔧 If external access still doesn't work:")
    print("1. Use SSH tunnel as temporary solution:")
    print(f"   ssh -L 8000:localhost:8000 -L 8501:localhost:8501 {external_ip}")
    print("   Then use proxy: 127.0.0.1:8000")
    print("2. Check if your local network/ISP blocks the ports")
    print("3. Consider using the load balancer approach from the deployment guide")

def main():
    """Main function"""
    print("🚀 TrustLayer AI - Fix External Access")
    print("=" * 60)
    
    # Get VM name and zone from command line or use defaults
    vm_name = sys.argv[1] if len(sys.argv) > 1 else "trustlayer-ai-main"
    zone = sys.argv[2] if len(sys.argv) > 2 else "us-central1-a"
    
    # Check gcloud authentication
    if not check_gcloud_auth():
        sys.exit(1)
    
    # Get VM information
    vm_info = get_vm_info(vm_name, zone)
    if not vm_info:
        print("❌ Could not get VM information")
        sys.exit(1)
    
    if vm_info['status'] != 'RUNNING':
        print(f"❌ VM is not running (status: {vm_info['status']})")
        print("   Start your VM first:")
        print(f"   gcloud compute instances start {vm_name} --zone {zone}")
        sys.exit(1)
    
    # Check existing firewall rules
    has_firewall = check_firewall_rules()
    
    # Create firewall rules if needed
    if not has_firewall:
        print("🔧 Creating missing firewall rules...")
        if not create_firewall_rules():
            print("❌ Failed to create firewall rules")
            sys.exit(1)
    else:
        print("✅ Firewall rules already exist")
    
    # Add network tags to VM
    if not add_network_tags(vm_info):
        print("❌ Failed to add network tags")
        sys.exit(1)
    
    # Check VM services
    check_vm_services(vm_info)
    
    # Test connectivity
    external_ip = vm_info['external_ip']
    if test_connectivity_after_fix(external_ip):
        print("\n🎉 SUCCESS! External access is now working!")
        print(f"\n🔧 Use this proxy configuration:")
        print(f"   HTTP Proxy:  {external_ip}:8000")
        print(f"   HTTPS Proxy: {external_ip}:8000")
        print(f"   Dashboard:   http://{external_ip}:8501")
    else:
        print("\n⚠️  Firewall rules created but connectivity still not working")
        print("   This usually means services aren't running on the VM")
        print_next_steps(vm_info)

if __name__ == "__main__":
    main()