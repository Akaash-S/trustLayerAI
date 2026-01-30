# TrustLayer AI - GCP Sovereign AI Deployment
# Terraform configuration for production-ready deployment

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "compute.googleapis.com",
    "dns.googleapis.com",
    "vpcaccess.googleapis.com",
    "redis.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudtrace.googleapis.com"
  ])

  service = each.key
  project = var.project_id

  disable_dependent_services = true
  disable_on_destroy         = false
}

# Data sources
data "google_project" "project" {
  project_id = var.project_id
}

# Random suffix for unique resource names
resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  # Common labels for all resources
  common_labels = {
    project     = "trustlayer-ai"
    environment = var.environment
    managed_by  = "terraform"
    team        = "security"
  }

  # Naming convention
  name_prefix = "trustlayer-${var.environment}"
  
  # Network configuration
  vpc_cidr             = "10.0.0.0/16"
  proxy_subnet_cidr    = "10.0.1.0/24"
  connector_subnet_cidr = "10.0.2.0/28"
  psc_subnet_cidr      = "10.0.3.0/24"
}