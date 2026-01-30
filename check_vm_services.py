#!/usr/bin/env python3
"""
TrustLayer AI - Check VM Services
Checks what services are running on the VM via SSH
"""

import subprocess
import sys
import json

def ssh_command(external_ip, command, description=""):
    """Run command via SSH"""
    print(f"🔧 {description}")
    print(f"   Command: {command}")
    
    ssh_cmd = f'ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no {external_ip} "{command}"'
    
    try:
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"   ✅ Success")
            if result.stdout.strip():
                print(f"   Output:\n{result.stdout}")
            return True, result.stdout.strip()
        else:
            print(f"   ❌ Failed (exit code {result.returncode})")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        print(f"   ❌ Command timed out")
        return False, "Timeout"
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, str(e)

def check_vm_services(external_ip):
    """Check services on VM"""
    print(f"🐳 Checking services on VM: {external_ip}")
    print("=" * 60)
    
    # Test SSH connectivity first
    success, _ = ssh_command(external_ip, "echo 'SSH connection successful'", "Testing SSH connection")
    if not success:
        print("❌ Cannot SSH to VM. Check:")
        print("   1. VM is running")
        print("   2. SSH firewall rule exists")
        print("   3. Your SSH key is configured")
        return False
    
    # Check Docker status
    ssh_command(external_ip, "sudo systemctl status docker --no-pager", "Checking Docker service status")
    
    # Check running containers
    ssh_command(external_ip, "docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'", "Checking running containers")
    
    # Check what's listening on ports
    ssh_command(external_ip, "sudo netstat -tlnp | grep ':8000\\|:8501'", "Checking listening ports")
    
    # Check if TrustLayer directory exists
    ssh_command(external_ip, "ls -la /opt/trustlayer-ai/", "Checking TrustLayer AI directory")
    
    # Check local health endpoint
    ssh_command(external_ip, "curl -s http://localhost:8000/health || echo 'Health check failed'", "Testing local health endpoint")
    
    # Check local dashboard
    ssh_command(external_ip, "curl -s -I http://localhost:8501 | head -1 || echo 'Dashboard check failed'", "Testing local dashboard")
    
    # Check docker-compose status
    ssh_command(external_ip, "cd /opt/trustlayer-ai && docker-compose ps", "Checking docker-compose status")
    
    # Check logs if containers exist
    ssh_command(external_ip, "docker logs trustlayer-proxy --tail 10 2>/dev/null || echo 'No proxy container'", "Checking proxy logs")
    ssh_command(external_ip, "docker logs trustlayer-dashboard --tail 10 2>/dev/null || echo 'No dashboard container'", "Checking dashboard logs")
    
    return True

def fix_services(external_ip):
    """Try to fix services on VM"""
    print(f"\n🔧 Attempting to fix services on VM")
    print("=" * 60)
    
    # Navigate to TrustLayer directory and start services
    commands = [
        "cd /opt/trustlayer-ai",
        "docker-compose down",
        "docker-compose build --no-cache",
        "docker-compose up -d"
    ]
    
    combined_command = " && ".join(commands)
    ssh_command(external_ip, combined_command, "Rebuilding and starting services")
    
    # Wait a moment and check again
    print("\n⏳ Waiting 30 seconds for services to start...")
    import time
    time.sleep(30)
    
    # Check if services are now running
    ssh_command(external_ip, "docker ps", "Checking containers after restart")
    ssh_command(external_ip, "curl -s http://localhost:8000/health || echo 'Still not working'", "Testing health after restart")

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python check_vm_services.py <EXTERNAL_IP>")
        print("Example: python check_vm_services.py 34.59.4.137")
        sys.exit(1)
    
    external_ip = sys.argv[1]
    
    print("🚀 TrustLayer AI - VM Services Check")
    print("=" * 60)
    
    # Check current services
    if check_vm_services(external_ip):
        
        # Ask if user wants to try fixing
        try:
            response = input("\n🔧 Do you want to try restarting the services? (y/n): ")
            if response.lower() in ['y', 'yes']:
                fix_services(external_ip)
                
                # Test external connectivity after fix
                print(f"\n🧪 Testing external connectivity...")
                import socket
                try:
                    sock = socket.create_connection((external_ip, 8000), timeout=10)
                    sock.close()
                    print("✅ External connectivity working!")
                    print(f"\n🔧 Use this proxy configuration:")
                    print(f"   HTTP Proxy:  {external_ip}:8000")
                    print(f"   HTTPS Proxy: {external_ip}:8000")
                    print(f"   Dashboard:   http://{external_ip}:8501")
                except Exception as e:
                    print(f"❌ External connectivity still not working: {e}")
                    print("   The issue might be firewall rules, not services")
                    print(f"   Run: python fix_external_access.py")
            
        except KeyboardInterrupt:
            print("\n👋 Exiting...")

if __name__ == "__main__":
    main()