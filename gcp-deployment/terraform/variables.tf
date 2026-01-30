# TrustLayer AI - Terraform Variables

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for deployment"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone for deployment"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Internal domain name for the service"
  type        = string
  default     = "trustlayer.internal"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "trustlayer-ai-proxy"
}

variable "dashboard_service_name" {
  description = "Name of the dashboard Cloud Run service"
  type        = string
  default     = "trustlayer-ai-dashboard"
}

variable "container_image" {
  description = "Container image for the proxy service"
  type        = string
  default     = "gcr.io/PROJECT_ID/trustlayer-ai:latest"
}

variable "dashboard_image" {
  description = "Container image for the dashboard service"
  type        = string
  default     = "gcr.io/PROJECT_ID/trustlayer-ai-dashboard:latest"
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "cpu_limit" {
  description = "CPU limit for Cloud Run instances"
  type        = string
  default     = "2"
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run instances"
  type        = string
  default     = "4Gi"
}

variable "redis_memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

variable "redis_tier" {
  description = "Redis service tier"
  type        = string
  default     = "STANDARD_HA"
}

variable "allowed_domains" {
  description = "List of allowed AI API domains"
  type        = list(string)
  default = [
    "api.openai.com",
    "api.anthropic.com",
    "generativelanguage.googleapis.com",
    "api.cohere.ai"
  ]
}

variable "enable_monitoring" {
  description = "Enable Cloud Monitoring and Logging"
  type        = bool
  default     = true
}

variable "enable_cloud_armor" {
  description = "Enable Cloud Armor security policies"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain Redis backups"
  type        = number
  default     = 7
}

variable "ssl_policy" {
  description = "SSL policy for load balancer"
  type        = string
  default     = "MODERN"
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
}

variable "session_ttl" {
  description = "Session TTL in seconds"
  type        = number
  default     = 3600
}

variable "health_check_path" {
  description = "Health check endpoint path"
  type        = string
  default     = "/health"
}

variable "metrics_path" {
  description = "Metrics endpoint path"
  type        = string
  default     = "/metrics"
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC flow logs for security monitoring"
  type        = bool
  default     = true
}

variable "enable_private_google_access" {
  description = "Enable Private Google Access for subnets"
  type        = bool
  default     = true
}

variable "notification_email" {
  description = "Email for monitoring notifications"
  type        = string
  default     = ""
}

variable "budget_amount" {
  description = "Monthly budget amount in USD"
  type        = number
  default     = 100
}