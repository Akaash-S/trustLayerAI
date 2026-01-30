# TrustLayer AI - Security Configuration

# Cloud Armor security policy
resource "google_compute_security_policy" "trustlayer_security_policy" {
  count = var.enable_cloud_armor ? 1 : 0
  
  name        = "${local.name_prefix}-security-policy"
  description = "Security policy for TrustLayer AI services"

  # Default rule - allow all traffic (will be overridden by specific rules)
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow rule"
  }

  # Block known malicious IPs
  rule {
    action   = "deny(403)"
    priority = "1000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = [
          "192.0.2.0/24",    # TEST-NET-1 (example)
          "198.51.100.0/24", # TEST-NET-2 (example)
          "203.0.113.0/24"   # TEST-NET-3 (example)
        ]
      }
    }
    description = "Block known malicious IP ranges"
  }

  # Rate limiting rule
  rule {
    action   = "rate_based_ban"
    priority = "2000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }
      ban_duration_sec = 300
    }
    description = "Rate limiting: 100 requests per minute per IP"
  }

  # SQL injection protection
  rule {
    action   = "deny(403)"
    priority = "3000"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-stable')"
      }
    }
    description = "Block SQL injection attempts"
  }

  # XSS protection
  rule {
    action   = "deny(403)"
    priority = "3100"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-stable')"
      }
    }
    description = "Block XSS attempts"
  }

  # Local file inclusion protection
  rule {
    action   = "deny(403)"
    priority = "3200"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('lfi-stable')"
      }
    }
    description = "Block local file inclusion attempts"
  }

  # Remote code execution protection
  rule {
    action   = "deny(403)"
    priority = "3300"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('rce-stable')"
      }
    }
    description = "Block remote code execution attempts"
  }

  # Scanner detection
  rule {
    action   = "deny(403)"
    priority = "3400"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('scannerdetection-stable')"
      }
    }
    description = "Block security scanners"
  }

  # Protocol attack protection
  rule {
    action   = "deny(403)"
    priority = "3500"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('protocolattack-stable')"
      }
    }
    description = "Block protocol attacks"
  }

  # Session fixation protection
  rule {
    action   = "deny(403)"
    priority = "3600"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sessionfixation-stable')"
      }
    }
    description = "Block session fixation attempts"
  }

  adaptive_protection_config {
    layer_7_ddos_defense_config {
      enable          = true
      rule_visibility = "STANDARD"
    }
  }
}

# Attach security policy to backend service
resource "google_compute_region_backend_service" "trustlayer_proxy_backend_with_security" {
  count = var.enable_cloud_armor ? 1 : 0
  
  name                  = "${local.name_prefix}-proxy-backend-secure"
  region                = var.region
  protocol              = "HTTP"
  load_balancing_scheme = "INTERNAL_MANAGED"
  timeout_sec           = 30

  backend {
    group = google_compute_region_network_endpoint_group.trustlayer_proxy_neg.id
  }

  health_checks = [google_compute_health_check.trustlayer_proxy_health.id]
  security_policy = google_compute_security_policy.trustlayer_security_policy[0].id

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

# IAM custom role for TrustLayer AI operations
resource "google_project_iam_custom_role" "trustlayer_operator" {
  role_id     = "trustlayerOperator"
  title       = "TrustLayer AI Operator"
  description = "Custom role for TrustLayer AI operations"
  
  permissions = [
    "run.services.get",
    "run.services.list",
    "run.revisions.get",
    "run.revisions.list",
    "redis.instances.get",
    "redis.instances.list",
    "monitoring.timeSeries.list",
    "logging.entries.list",
    "compute.healthChecks.get",
    "compute.backendServices.get"
  ]
}

# Service account for monitoring and operations
resource "google_service_account" "trustlayer_monitor_sa" {
  account_id   = "${local.name_prefix}-monitor-sa"
  display_name = "TrustLayer AI Monitoring Service Account"
  description  = "Service account for monitoring and alerting"
}

# IAM bindings for monitoring service account
resource "google_project_iam_member" "monitor_sa_roles" {
  for_each = toset([
    "roles/monitoring.viewer",
    "roles/logging.viewer",
    "roles/cloudtrace.user",
    google_project_iam_custom_role.trustlayer_operator.id
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.trustlayer_monitor_sa.email}"
}

# Binary Authorization policy for container security
resource "google_binary_authorization_policy" "trustlayer_policy" {
  admission_whitelist_patterns {
    name_pattern = "gcr.io/${var.project_id}/*"
  }

  default_admission_rule {
    evaluation_mode  = "REQUIRE_ATTESTATION"
    enforcement_mode = "ENFORCED_BLOCK_AND_AUDIT_LOG"
    
    require_attestations_by = [
      google_binary_authorization_attestor.trustlayer_attestor.name
    ]
  }

  cluster_admission_rules {
    cluster                = "projects/${var.project_id}/locations/${var.region}/clusters/*"
    evaluation_mode        = "REQUIRE_ATTESTATION"
    enforcement_mode       = "ENFORCED_BLOCK_AND_AUDIT_LOG"
    
    require_attestations_by = [
      google_binary_authorization_attestor.trustlayer_attestor.name
    ]
  }
}

# Binary Authorization attestor
resource "google_binary_authorization_attestor" "trustlayer_attestor" {
  name = "${local.name_prefix}-attestor"
  
  attestation_authority_note {
    note_reference = google_container_analysis_note.trustlayer_note.name
    
    public_keys {
      id = "trustlayer-key"
      ascii_armored_pgp_public_key = file("${path.module}/keys/trustlayer-public.pgp")
    }
  }
}

# Container Analysis note for attestations
resource "google_container_analysis_note" "trustlayer_note" {
  name = "${local.name_prefix}-attestation-note"
  
  attestation_authority {
    hint {
      human_readable_name = "TrustLayer AI Attestor"
    }
  }
}

# VPC Flow Logs configuration
resource "google_compute_subnetwork" "proxy_subnet_with_flow_logs" {
  count = var.enable_vpc_flow_logs ? 1 : 0
  
  name          = "${local.name_prefix}-proxy-subnet-logged"
  ip_cidr_range = local.proxy_subnet_cidr
  region        = var.region
  network       = google_compute_network.trustlayer_vpc.id
  purpose       = "INTERNAL_HTTPS_LOAD_BALANCER"
  role          = "ACTIVE"

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 1.0
    metadata             = "INCLUDE_ALL_METADATA"
    metadata_fields = [
      "src_instance",
      "dst_instance",
      "src_vpc",
      "dst_vpc",
      "src_location",
      "dst_location"
    ]
  }

  private_ip_google_access = var.enable_private_google_access
}

# Security Command Center notification
resource "google_scc_notification_config" "trustlayer_scc_notification" {
  count = var.notification_email != "" ? 1 : 0
  
  config_id    = "${local.name_prefix}-scc-notification"
  organization = data.google_project.project.org_id
  description  = "Security Command Center notifications for TrustLayer AI"
  
  pubsub_topic = google_pubsub_topic.security_notifications[0].id
  
  streaming_config {
    filter = "state=\"ACTIVE\" AND category=\"MALWARE\" OR category=\"VULNERABILITY\""
  }
}

# Pub/Sub topic for security notifications
resource "google_pubsub_topic" "security_notifications" {
  count = var.notification_email != "" ? 1 : 0
  
  name = "${local.name_prefix}-security-notifications"
  
  labels = local.common_labels
}

# Pub/Sub subscription for email notifications
resource "google_pubsub_subscription" "security_email_subscription" {
  count = var.notification_email != "" ? 1 : 0
  
  name  = "${local.name_prefix}-security-email-sub"
  topic = google_pubsub_topic.security_notifications[0].name
  
  push_config {
    push_endpoint = "https://pubsub.googleapis.com/v1/projects/${var.project_id}/topics/${google_pubsub_topic.security_notifications[0].name}"
  }
  
  labels = local.common_labels
}

# Cloud KMS key ring for encryption
resource "google_kms_key_ring" "trustlayer_keyring" {
  name     = "${local.name_prefix}-keyring"
  location = var.region
}

# Cloud KMS crypto key for application data encryption
resource "google_kms_crypto_key" "trustlayer_key" {
  name     = "${local.name_prefix}-crypto-key"
  key_ring = google_kms_key_ring.trustlayer_keyring.id
  
  rotation_period = "7776000s" # 90 days
  
  lifecycle {
    prevent_destroy = true
  }
  
  labels = local.common_labels
}

# IAM binding for KMS key usage
resource "google_kms_crypto_key_iam_member" "trustlayer_key_user" {
  crypto_key_id = google_kms_crypto_key.trustlayer_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_service_account.trustlayer_sa.email}"
}