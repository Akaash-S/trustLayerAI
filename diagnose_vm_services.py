#!/usr/bin/env python3
"""
Diagnose VM Services - Check what's running on the TrustLayer AI VM
Run this script from Google Cloud Shell or a machine with gcloud CLI
"""

import subprocess
import sys
import json

def run_ssh_command(vm_ip, command, description=""):
    """Run command via SSH on the VM"""
    print(f"🔍 {description}")
    print(f"   Command: {command}")
    
    ssh_command = f'ssh -o StrictHostKeyChecking=no {vm_ip} "{command}"'
    
    try:
        result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"   ✅ Success:")
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    print(f"      {line}")
            return True, result.stdout.strip()
        else:
            print(f"   ❌ Failed:")
            for line in result.stderr.strip().split('\n'):
                if line.strip():
                    print(f"      {line}")
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        print(f"   ❌ Command timed out")
        return False, "Timeout"
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, str(e)

def diagnose_vm(vm_ip):
    """Diagnose what's running on the VM"""
    print(f"🚀 Diagnosing TrustLayer AI VM: {vm_ip}")
    print("=" * 60)
    
    # Check 1: What processes are listening on ports
    run_ssh_command(vm_ip, "sudo netstat -tlnp | grep -E ':(80|8000|8501)\\s'", 
                   "Checking what's listening on ports 80, 8000, 8501")
    
    print()
    
    # Check 2: Docker containers
    run_ssh_command(vm_ip, "docker ps", 
                   "Checking Docker containers")
    
    print()
    
    # Check 3: Docker compose status
    run_ssh_command(vm_ip, "cd /opt/trustlayer-ai && docker-compose ps", 
                   "Checking docker-compose status")
    
    print()
    
    # Check 4: Test local connectivity
    run_ssh_command(vm_ip, "curl -s http://localhost:8000/health", 
                   "Testing TrustLayer AI health locally")
    
    print()
    
    # Check 5: Test dashboard locally
    run_ssh_command(vm_ip, "curl -I http://localhost:8501", 
                   "Testing dashboard locally")
    
    print()
    
    # Check 6: Nginx status
    run_ssh_command(vm_ip, "sudo systemctl status nginx --no-pager -l", 
                   "Checking Nginx status")
    
    print()
    
    # Check 7: Check if TrustLayer directory exists
    run_ssh_command(vm_ip, "ls -la /opt/trustlayer-ai/", 
                   "Checking TrustLayer AI directory")
    
    print()
    
    # Check 8: Check firewall on VM
    run_ssh_command(vm_ip, "sudo ufw status", 
                   "Checking local firewall (ufw)")
    
    print("=" * 60)
    print("🔧 DIAGNOSIS COMPLETE")
    print("=" * 60)
    
    print("\n📋 NEXT STEPS BASED ON RESULTS:")
    print("1. If Docker containers are not running:")
    print("   ssh into VM and run: cd /opt/trustlayer-ai && docker-compose up -d")
    print("\n2. If ports 8000/8501 show 127.0.0.1 instead of 0.0.0.0:")
    print("   Services are only listening locally - need to fix binding")
    print("\n3. If Nginx is proxying but TrustLayer isn't running:")
    print("   Start TrustLayer services first")
    print("\n4. If local tests work but external doesn't:")
    print("   Firewall issue - check GCP firewall rules and VM network tags")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python diagnose_vm_services.py <VM_EXTERNAL_IP>")
        print("Example: python diagnose_vm_services.py 34.59.4.137")
        print("\nNote: This script uses SSH, so make sure you can SSH to the VM")
        sys.exit(1)
    
    vm_ip = sys.argv[1]
    diagnose_vm(vm_ip)