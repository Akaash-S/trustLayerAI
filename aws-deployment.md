# AWS VPC Deployment Guide

## Architecture Overview

```
Internet Gateway
       |
   Route 53 Private Zone
       |
   Client VPN Endpoint
       |
   Private Subnet (TrustLayer Proxy)
       |
   NAT Gateway → Internet (AI APIs)
```

## Step 1: VPC Setup

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=TrustLayer-VPC}]'

# Create Private Subnet
aws ec2 create-subnet --vpc-id vpc-xxxxxxxxx --cidr-block 10.0.1.0/24 --availability-zone us-east-1a

# Create Internet Gateway
aws ec2 create-internet-gateway --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=TrustLayer-IGW}]'

# Attach IGW to VPC
aws ec2 attach-internet-gateway --internet-gateway-id igw-xxxxxxxxx --vpc-id vpc-xxxxxxxxx
```

## Step 2: Route 53 Private Hosted Zone

```bash
# Create private hosted zone
aws route53 create-hosted-zone \
  --name trustlayer.internal \
  --vpc VPCRegion=us-east-1,VPCId=vpc-xxxxxxxxx \
  --caller-reference $(date +%s)

# Create DNS records to redirect AI traffic
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.openai.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "10.0.1.100"}]
      }
    }]
  }'
```

## Step 3: Client VPN Endpoint

```bash
# Create Client VPN Endpoint
aws ec2 create-client-vpn-endpoint \
  --client-cidr-block 10.1.0.0/16 \
  --server-certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012 \
  --authentication-options Type=certificate-authentication,MutualAuthentication={ClientRootCertificateChainArn=arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012} \
  --connection-log-options Enabled=true,CloudwatchLogGroup=TrustLayer-VPN-Logs

# Associate with subnet
aws ec2 associate-client-vpn-target-network \
  --client-vpn-endpoint-id cvpn-endpoint-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx
```

## Step 4: Deploy TrustLayer Proxy

### EC2 Instance Setup

```bash
# Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --count 1 \
  --instance-type t3.medium \
  --key-name my-key-pair \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx \
  --private-ip-address 10.0.1.100 \
  --user-data file://user-data.sh
```

### User Data Script (user-data.sh)

```bash
#!/bin/bash
yum update -y
yum install -y docker git

# Start Docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone TrustLayer AI
cd /home/ec2-user
git clone https://github.com/your-org/trustlayer-ai.git
cd trustlayer-ai

# Start services
docker-compose up -d

# Setup log rotation
cat > /etc/logrotate.d/trustlayer << EOF
/home/ec2-user/trustlayer-ai/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ec2-user ec2-user
}
EOF
```

## Step 5: Security Groups

```bash
# Create security group for proxy
aws ec2 create-security-group \
  --group-name TrustLayer-Proxy-SG \
  --description "Security group for TrustLayer AI Proxy" \
  --vpc-id vpc-xxxxxxxxx

# Allow inbound traffic from VPN clients
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 8000 \
  --cidr 10.1.0.0/16

# Allow outbound HTTPS to AI APIs
aws ec2 authorize-security-group-egress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

## Step 6: Monitoring & Logging

### CloudWatch Setup

```bash
# Create log group
aws logs create-log-group --log-group-name /aws/trustlayer/proxy

# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name TrustLayer-AI \
  --dashboard-body file://dashboard.json
```

### Dashboard Configuration (dashboard.json)

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/EC2", "CPUUtilization", "InstanceId", "i-xxxxxxxxx"],
          ["AWS/EC2", "NetworkIn", "InstanceId", "i-xxxxxxxxx"],
          ["AWS/EC2", "NetworkOut", "InstanceId", "i-xxxxxxxxx"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "TrustLayer Proxy Metrics"
      }
    }
  ]
}
```

## Step 7: Client Configuration

### Windows Client Setup

```powershell
# Download VPN client configuration
aws ec2 export-client-vpn-client-configuration \
  --client-vpn-endpoint-id cvpn-endpoint-xxxxxxxxx \
  --output text > trustlayer-vpn.ovpn

# Import into OpenVPN client
# Configure DNS to use 10.0.1.100 for AI domains
```

### macOS/Linux Client Setup

```bash
# Install OpenVPN
sudo apt-get install openvpn  # Ubuntu/Debian
brew install openvpn         # macOS

# Connect to VPN
sudo openvpn --config trustlayer-vpn.ovpn

# Update /etc/hosts or DNS settings
echo "10.0.1.100 api.openai.com" >> /etc/hosts
echo "10.0.1.100 api.anthropic.com" >> /etc/hosts
```

## Step 8: Testing & Validation

```bash
# Test proxy connectivity
curl -H "Host: api.openai.com" http://10.0.1.100:8000/v1/models

# Test PII redaction
curl -X POST -H "Host: api.openai.com" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"My name is John Doe and my email is john@example.com"}]}' \
  http://10.0.1.100:8000/v1/chat/completions

# Check dashboard
curl http://10.0.1.100:8501
```

## Step 9: Production Hardening

### SSL/TLS Configuration

```bash
# Generate SSL certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Update docker-compose.yml to use HTTPS
# Add nginx reverse proxy for SSL termination
```

### Backup & Recovery

```bash
# Setup automated Redis backups
aws s3 mb s3://trustlayer-backups
echo "0 2 * * * docker exec trustlayer-redis redis-cli BGSAVE && aws s3 cp /data/dump.rdb s3://trustlayer-backups/redis-$(date +%Y%m%d).rdb" | crontab -
```

## Compliance & Auditing

- All traffic is logged to CloudWatch
- PII redaction events are tracked
- Compliance dashboard shows DPDP Act 2026 status
- Regular security audits via AWS Config
- Automated vulnerability scanning with Inspector

## Cost Optimization

- Use Spot Instances for non-critical environments
- Implement auto-scaling based on traffic
- Use Reserved Instances for production
- Monitor costs with AWS Cost Explorer

## Troubleshooting

### Common Issues

1. **DNS Resolution**: Ensure Route 53 records point to proxy
2. **VPN Connectivity**: Check security groups and routing tables
3. **Proxy Errors**: Check CloudWatch logs and Redis connectivity
4. **Performance**: Monitor latency and scale horizontally if needed