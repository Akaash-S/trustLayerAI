#!/usr/bin/env python3
"""
TrustLayer AI - Fix External Access
Diagnoses and fixes external access issues for GCP Compute Engine
Specifically handles cases where IP works inside GCP but not outside
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
            network = vm_info['networkInterfaces'][0]['network'].split('/')[-1]
            
            print(f"   ✅ VM Status: {status}")
            print(f"   ✅ External IP: {external_ip}")
            print(f"   ✅ Internal IP: {internal_ip}")
            print(f"   ✅ Network: {network}")
            print(f"   ✅ Network Tags: {tags}")
            
            return {
                'external_ip': external_ip,
                'internal_ip': internal_ip,
                'status': status,
                'tags': tags,
                'zone': zone,
                'name': vm_name,
                'network': network
            }
        except Exception as e:
            print(f"   ❌ Error parsing VM info: {e}")
            return None
    else:
        return None

def check_existing_firewall_rules(network="default"):
    """Check all firewall rules that might affect external access"""
    print(f"\n🔥 Checking firewall rules for network: {network}")
    
    # Check all firewall rules for the network
    command = f'gcloud compute firewall-rules list --filter="network~{network}" --format="table(name,allowed,sourceRanges,targetTags,direction)" --sort-by=name'
    success, output = run_command(command, "Listing all firewall rules for network")
    
    if success:
        print("   Current firewall rules:")
        print(f"   {output}")
        
        # Check specifically for rules that allow ports 8000 and 8501
        command2 = f'gcloud compute firewall-rules list --filter="network~{network} AND allowed.ports:(8000 OR 8501)" --format="table(name,allowed,sourceRanges,targetTags)"'
        success2, output2 = run_command(command2, "Checking rules for ports 8000/8501")
        
        if success2 and output2.strip():
            print("   ✅ Found rules for TrustLayer ports:")
            print(f"   {output2}")
            return True
        else:
            print("   ❌ No rules found for ports 8000/8501")
            return False
    
    return False

def delete_conflicting_rules():
    """Delete any conflicting firewall rules"""
    print(f"\n🗑️  Checking for conflicting firewall rules")
    
    # Check for any deny rules that might block our traffic
    command = 'gcloud compute firewall-rules list --filter="action=DENY" --format="table(name,allowed,denied,sourceRanges,targetTags)"'
    success, output = run_command(command, "Checking for DENY rules")
    
    if success and "DENY" in output:
        print("   ⚠️  Found DENY rules that might conflict:")
        print(f"   {output}")
        print("   You may need to review these manually")
    else:
        print("   ✅ No conflicting DENY rules found")

def create_comprehensive_firewall_rules(network="default"):
    """Create comprehensive firewall rules for external access"""
    print(f"\n🔥 Creating comprehensive firewall rules")
    
    # Delete existing TrustLayer rules first to avoid conflicts
    print("   🗑️  Removing any existing TrustLayer rules...")
    existing_rules = ["trustlayer-allow-external", "trustlayer-allow-web", "trustlayer-allow-proxy"]
    
    for rule in existing_rules:
        command = f'gcloud compute firewall-rules delete {rule} --quiet'
        run_command(command, f"Deleting existing rule: {rule}")
    
    # Rule 1: Allow external access to TrustLayer ports (MOST IMPORTANT)
    command1 = f'''gcloud compute firewall-rules create trustlayer-allow-external \
    --network {network} \
    --action ALLOW \
    --rules tcp:8000,tcp:8501,tcp:80,tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --target-tags trustlayer-web \
    --description "Allow external access to TrustLayer AI from anywhere" \
    --priority 1000'''
    
    success1, _ = run_command(command1, "Creating external access rule (HIGH PRIORITY)")
    
    # Rule 2: Allow SSH access
    command2 = f'''gcloud compute firewall-rules create trustlayer-allow-ssh \
    --network {network} \
    --action ALLOW \
    --rules tcp:22 \
    --source-ranges 0.0.0.0/0 \
    --target-tags trustlayer-vm \
    --description "Allow SSH access to TrustLayer VMs" \
    --priority 1000'''
    
    success2, _ = run_command(command2, "Creating SSH access rule")
    
    # Rule 3: Allow internal communication
    command3 = f'''gcloud compute firewall-rules create trustlayer-allow-internal \
    --network {network} \
    --action ALLOW \
    --rules tcp,udp,icmp \
    --source-ranges 10.0.0.0/8 \
    --description "Allow internal communication for TrustLayer" \
    --priority 1000'''
    
    success3, _ = run_command(command3, "Creating internal communication rule")
    
    return success1 and success2 and success3

def add_network_tags_comprehensive(vm_info):
    """Add network tags to VM with comprehensive approach"""
    print(f"\n🏷️  Adding network tags to VM")
    
    vm_name = vm_info['name']
    zone = vm_info['zone']
    existing_tags = vm_info['tags']
    
    # Tags we need
    required_tags = ['trustlayer-web', 'trustlayer-vm', 'http-server', 'https-server']
    
    # Check if tags already exist
    missing_tags = [tag for tag in required_tags if tag not in existing_tags]
    
    if not missing_tags:
        print("   ✅ All required tags already present")
        return True
    
    # Add missing tags (keep existing ones)
    all_tags = list(set(existing_tags + missing_tags))  # Remove duplicates
    tags_str = ','.join(all_tags)
    
    command = f'gcloud compute instances set-tags {vm_name} --tags {tags_str} --zone {zone}'
    success, _ = run_command(command, f"Setting tags: {all_tags}")
    
    return success

def verify_external_access_step_by_step(external_ip):
    """Verify external access step by step"""
    print(f"\n🧪 Verifying external access step by step")
    
    # Step 1: Test from Google Cloud Shell (should work)
    print("   📋 To test from Google Cloud Shell (should work):")
    print(f"   gcloud cloud-shell ssh --command='curl -s http://{external_ip}:8000/health'")
    
    # Step 2: Test basic TCP connectivity
    print(f"\n   🔌 Testing TCP connectivity to {external_ip}:8000...")
    import socket
    try:
        sock = socket.create_connection((external_ip, 8000), timeout=15)
        sock.close()
        print("   ✅ TCP connection successful")
        
        # Step 3: Test HTTP
        print(f"   🌐 Testing HTTP connectivity...")
        import requests
        try:
            response = requests.get(f"http://{external_ip}:8000/health", timeout=15)
            if response.status_code == 200:
                print("   ✅ HTTP connection successful")
                print(f"   ✅ Response: {response.json()}")
                return True
            else:
                print(f"   ⚠️  HTTP returned status {response.status_code}")
        except Exception as e:
            print(f"   ❌ HTTP error: {e}")
            
    except Exception as e:
        print(f"   ❌ TCP connection failed: {e}")
        print("   This confirms the firewall is still blocking external access")
    
    return False

def check_network_connectivity_issues():
    """Check for common network connectivity issues"""
    print(f"\n🌐 Checking for network connectivity issues")
    
    # Check if we're behind a corporate firewall
    print("   🏢 Checking if you're behind a corporate firewall...")
    try:
        import requests
        response = requests.get("http://httpbin.org/ip", timeout=10)
        if response.status_code == 200:
            your_ip = response.json().get('origin', 'unknown')
            print(f"   ✅ Your public IP: {your_ip}")
            
            # Check if it's a corporate/restricted IP range
            if any(your_ip.startswith(prefix) for prefix in ['10.', '172.', '192.168.']):
                print("   ⚠️  You appear to be behind a NAT/corporate firewall")
                print("   This might be blocking outbound connections to GCP")
            else:
                print("   ✅ You have a public IP address")
        else:
            print("   ⚠️  Could not determine your public IP")
    except Exception as e:
        print(f"   ❌ Network connectivity test failed: {e}")

def provide_alternative_solutions(vm_info):
    """Provide alternative solutions if direct access doesn't work"""
    external_ip = vm_info['external_ip']
    
    print(f"\n🔧 ALTERNATIVE SOLUTIONS:")
    print("=" * 60)
    
    print("1. 🚇 SSH Tunnel (Immediate solution):")
    print(f"   ssh -L 8000:localhost:8000 -L 8501:localhost:8501 {external_ip}")
    print("   Then use proxy: 127.0.0.1:8000")
    print("   Dashboard: http://localhost:8501")
    
    print("\n2. 🌐 Use Google Cloud Shell:")
    print("   - Go to Google Cloud Console")
    print("   - Click the Cloud Shell icon (>_)")
    print(f"   - Run: curl http://{external_ip}:8000/health")
    print("   - This should work from inside GCP")
    
    print("\n3. ⚖️  Set up Load Balancer (Recommended for production):")
    print("   - Follow the GCP deployment guide")
    print("   - Create a load balancer with external IP")
    print("   - Use load balancer IP instead of VM IP")
    
    print("\n4. 🔒 VPN Solution:")
    print("   - Set up Cloud VPN or use a VPN service")
    print("   - Connect through VPN to access GCP resources")
    
    print("\n5. 🌍 Test from different network:")
    print("   - Try from mobile hotspot")
    print("   - Try from different location/ISP")
    print("   - This helps identify if it's your network blocking GCP")

def main():
    """Main function"""
    print("🚀 TrustLayer AI - Fix External Access (GCP Firewall Issue)")
    print("=" * 70)
    print("🎯 Specifically fixing: IP works inside GCP but not outside")
    print("=" * 70)
    
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
    
    external_ip = vm_info['external_ip']
    network = vm_info['network']
    
    print(f"\n🎯 Target: {external_ip} (VM: {vm_name}, Network: {network})")
    
    # Check existing firewall rules
    has_proper_rules = check_existing_firewall_rules(network)
    
    # Check for conflicting rules
    delete_conflicting_rules()
    
    # Create comprehensive firewall rules
    print("\n🔧 Creating comprehensive firewall rules...")
    if not create_comprehensive_firewall_rules(network):
        print("❌ Failed to create firewall rules")
        sys.exit(1)
    
    # Add network tags to VM
    if not add_network_tags_comprehensive(vm_info):
        print("❌ Failed to add network tags")
        sys.exit(1)
    
    # Wait for rules to propagate
    print("\n⏳ Waiting 60 seconds for firewall rules to propagate...")
    time.sleep(60)
    
    # Verify external access
    if verify_external_access_step_by_step(external_ip):
        print("\n🎉 SUCCESS! External access is now working!")
        print(f"\n🔧 Use this proxy configuration:")
        print(f"   HTTP Proxy:  {external_ip}:8000")
        print(f"   HTTPS Proxy: {external_ip}:8000")
        print(f"   Dashboard:   http://{external_ip}:8501")
        
        # Test with the original test script
        print(f"\n🧪 Run this to verify:")
        print(f"   python test_external_ip.py {external_ip}")
        
    else:
        print("\n⚠️  External access still not working after firewall fixes")
        print("   This suggests the issue might be:")
        print("   1. Your local network/ISP blocking GCP IPs")
        print("   2. Corporate firewall blocking outbound connections")
        print("   3. Services not running properly on the VM")
        
        # Check network connectivity issues
        check_network_connectivity_issues()
        
        # Provide alternative solutions
        provide_alternative_solutions(vm_info)
        
        print(f"\n📋 Next steps:")
        print(f"   1. Try SSH tunnel: ssh -L 8000:localhost:8000 {external_ip}")
        print(f"   2. Test from Google Cloud Shell")
        print(f"   3. Check VM services: python check_vm_services.py {external_ip}")

if __name__ == "__main__":
    main()