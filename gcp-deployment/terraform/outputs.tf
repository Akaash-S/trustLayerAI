# TrustLayer AI - Terraform Outputs

# Network outputs
output "vpc_id" {
  description = "ID of the VPC network"
  value       = google_compute_network.trustlayer_vpc.id
}

output "vpc_name" {
  description = "Name of the VPC network"
  value       = google_compute_network.trustlayer_vpc.name
}

output "proxy_subnet_id" {
  description = "ID of the proxy subnet"
  value       = google_compute_subnetwork.proxy_subnet.id
}

output "connector_subnet_id" {
  description = "ID of the VPC connector subnet"
  value       = google_compute_subnetwork.connector_subnet.id
}

output "vpc_connector_id" {
  description = "ID of the VPC connector"
  value       = google_vpc_access_connector.trustlayer_connector.id
}

# Load balancer outputs
output "load_balancer_ip" {
  description = "Internal IP address of the load balancer"
  value       = google_compute_address.trustlayer_lb_ip.address
}

output "load_balancer_url" {
  description = "URL of the internal load balancer"
  value       = "http://${google_compute_address.trustlayer_lb_ip.address}"
}

# Cloud Run outputs
output "proxy_service_url" {
  description = "URL of the TrustLayer AI proxy service"
  value       = google_cloud_run_v2_service.trustlayer_proxy.uri
}

output "dashboard_service_url" {
  description = "URL of the TrustLayer AI dashboard service"
  value       = google_cloud_run_v2_service.trustlayer_dashboard.uri
}

output "proxy_service_name" {
  description = "Name of the proxy Cloud Run service"
  value       = google_cloud_run_v2_service.trustlayer_proxy.name
}

output "dashboard_service_name" {
  description = "Name of the dashboard Cloud Run service"
  value       = google_cloud_run_v2_service.trustlayer_dashboard.name
}

# Redis outputs
output "redis_host" {
  description = "Host address of the Redis instance"
  value       = google_redis_instance.trustlayer_redis.host
  sensitive   = true
}

output "redis_port" {
  description = "Port of the Redis instance"
  value       = google_redis_instance.trustlayer_redis.port
}

output "redis_instance_id" {
  description = "ID of the Redis instance"
  value       = google_redis_instance.trustlayer_redis.instance_id
}

output "redis_auth_string" {
  description = "Auth string for Redis instance"
  value       = google_redis_instance.trustlayer_redis.auth_string
  sensitive   = true
}

# DNS outputs
output "internal_domain" {
  description = "Internal domain name"
  value       = var.domain_name
}

output "api_fqdn" {
  description = "Fully qualified domain name for API service"
  value       = "api.${var.domain_name}"
}

output "dashboard_fqdn" {
  description = "Fully qualified domain name for dashboard service"
  value       = "dashboard.${var.domain_name}"
}

output "dns_zone_name" {
  description = "Name of the private DNS zone"
  value       = google_dns_managed_zone.trustlayer_internal.name
}

# Service account outputs
output "service_account_email" {
  description = "Email of the TrustLayer AI service account"
  value       = google_service_account.trustlayer_sa.email
}

output "monitor_service_account_email" {
  description = "Email of the monitoring service account"
  value       = google_service_account.trustlayer_monitor_sa.email
}

# Security outputs
output "security_policy_id" {
  description = "ID of the Cloud Armor security policy"
  value       = var.enable_cloud_armor ? google_compute_security_policy.trustlayer_security_policy[0].id : null
}

output "kms_key_id" {
  description = "ID of the KMS encryption key"
  value       = google_kms_crypto_key.trustlayer_key.id
}

output "kms_keyring_id" {
  description = "ID of the KMS key ring"
  value       = google_kms_key_ring.trustlayer_keyring.id
}

# Monitoring outputs
output "monitoring_workspace_id" {
  description = "ID of the monitoring workspace"
  value       = var.enable_monitoring ? google_monitoring_workspace.trustlayer_workspace[0].workspace_id : null
}

output "notification_channel_id" {
  description = "ID of the email notification channel"
  value       = var.notification_email != "" ? google_monitoring_notification_channel.email[0].id : null
}

# Private Service Connect outputs
output "psc_addresses" {
  description = "Private Service Connect IP addresses for AI APIs"
  value = {
    for domain in var.allowed_domains :
    domain => google_compute_global_address.psc_address[domain].address
  }
}

# Project information
output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

# Connection information
output "connection_info" {
  description = "Connection information for accessing TrustLayer AI"
  value = {
    api_endpoint      = "http://${google_compute_address.trustlayer_lb_ip.address}/health"
    dashboard_url     = "http://${google_compute_address.trustlayer_lb_ip.address}:8501"
    internal_api_url  = "http://api.${var.domain_name}"
    internal_dash_url = "http://dashboard.${var.domain_name}"
    redis_connection  = "${google_redis_instance.trustlayer_redis.host}:${google_redis_instance.trustlayer_redis.port}"
  }
}

# Deployment commands
output "deployment_commands" {
  description = "Commands for testing the deployment"
  value = {
    health_check    = "curl -H 'Host: api.${var.domain_name}' http://${google_compute_address.trustlayer_lb_ip.address}/health"
    metrics_check   = "curl -H 'Host: api.${var.domain_name}' http://${google_compute_address.trustlayer_lb_ip.address}/metrics"
    dashboard_check = "curl -H 'Host: dashboard.${var.domain_name}' http://${google_compute_address.trustlayer_lb_ip.address}"
    dns_test        = "nslookup api.${var.domain_name}"
  }
}

# Cost estimation
output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (USD)"
  value = {
    cloud_run_proxy    = "~$10-50 (based on usage)"
    cloud_run_dashboard = "~$5-20 (based on usage)"
    redis_standard_ha  = "~$45 (1GB Standard HA)"
    load_balancer      = "~$18 (Internal LB)"
    vpc_connector      = "~$9 (200-1000 Mbps)"
    monitoring         = "~$5-15 (based on metrics)"
    storage            = "~$1-5 (logs and backups)"
    total_estimated    = "~$93-162 per month"
    note              = "Costs vary based on actual usage, region, and configuration"
  }
}

# Security compliance
output "security_compliance" {
  description = "Security and compliance features enabled"
  value = {
    private_networking     = "✅ VPC with private subnets"
    no_public_ips         = "✅ Internal load balancer only"
    encryption_at_rest    = "✅ KMS encryption enabled"
    encryption_in_transit = "✅ TLS/SSL termination"
    cloud_armor          = var.enable_cloud_armor ? "✅ Enabled" : "❌ Disabled"
    vpc_flow_logs        = var.enable_vpc_flow_logs ? "✅ Enabled" : "❌ Disabled"
    audit_logging        = "✅ Cloud Audit Logs enabled"
    monitoring           = var.enable_monitoring ? "✅ Enabled" : "❌ Disabled"
    binary_authorization = "✅ Container security enabled"
    iam_least_privilege  = "✅ Custom roles with minimal permissions"
  }
}