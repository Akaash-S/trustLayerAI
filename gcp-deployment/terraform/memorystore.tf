# TrustLayer AI - Cloud Memorystore (Redis) Configuration

# Redis instance for session storage and telemetry
resource "google_redis_instance" "trustlayer_redis" {
  name           = "${local.name_prefix}-redis"
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size_gb
  region         = var.region

  location_id             = var.zone
  alternative_location_id = "${substr(var.region, 0, length(var.region)-1)}b"

  authorized_network = google_compute_network.trustlayer_vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_version     = "REDIS_7_0"
  display_name      = "TrustLayer AI Redis Instance"
  reserved_ip_range = "10.0.4.0/29"

  # High availability configuration
  replica_count = var.redis_tier == "STANDARD_HA" ? 1 : 0
  read_replicas_mode = var.redis_tier == "STANDARD_HA" ? "READ_REPLICAS_ENABLED" : "READ_REPLICAS_DISABLED"

  # Redis configuration
  redis_configs = {
    maxmemory-policy = "allkeys-lru"
    notify-keyspace-events = "Ex"
    timeout = "300"
    tcp-keepalive = "60"
  }

  # Maintenance policy
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 2
        minutes = 0
        seconds = 0
        nanos   = 0
      }
    }
  }

  # Persistence configuration
  persistence_config {
    persistence_mode    = "RDB"
    rdb_snapshot_period = "TWELVE_HOURS"
    rdb_snapshot_start_time = "02:00"
  }

  # Backup configuration
  backup_configuration {
    enabled = true
    start_time = "03:00"
  }

  # Transit encryption
  transit_encryption_mode = "SERVER_AUTHENTICATION"
  auth_enabled           = true

  labels = merge(local.common_labels, {
    service = "redis"
    tier    = lower(var.redis_tier)
  })

  depends_on = [
    google_project_service.required_apis,
    google_compute_network.trustlayer_vpc
  ]
}

# Private service connection for Redis
resource "google_service_networking_connection" "redis_private_vpc_connection" {
  network                 = google_compute_network.trustlayer_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.redis_private_ip_range.name]

  depends_on = [google_project_service.required_apis]
}

# Reserved IP range for Redis private service connection
resource "google_compute_global_address" "redis_private_ip_range" {
  name          = "${local.name_prefix}-redis-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.trustlayer_vpc.id
}

# Redis backup schedule (additional backups)
resource "google_redis_instance" "trustlayer_redis_backup" {
  count = var.backup_retention_days > 0 ? 1 : 0
  
  name           = "${local.name_prefix}-redis-backup"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region

  location_id = var.zone

  authorized_network = google_compute_network.trustlayer_vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_version = "REDIS_7_0"
  display_name  = "TrustLayer AI Redis Backup Instance"

  # Backup-specific configuration
  redis_configs = {
    maxmemory-policy = "noeviction"
    save = "900 1 300 10 60 10000"
  }

  labels = merge(local.common_labels, {
    service = "redis-backup"
    purpose = "backup"
  })

  depends_on = [
    google_service_networking_connection.redis_private_vpc_connection
  ]
}

# Cloud Scheduler job for Redis backup automation
resource "google_cloud_scheduler_job" "redis_backup_job" {
  count = var.backup_retention_days > 0 ? 1 : 0
  
  name             = "${local.name_prefix}-redis-backup-job"
  description      = "Automated Redis backup for TrustLayer AI"
  schedule         = "0 2 * * *"  # Daily at 2 AM
  time_zone        = "UTC"
  attempt_deadline = "320s"

  retry_config {
    retry_count = 3
  }

  http_target {
    http_method = "POST"
    uri         = "https://redis.googleapis.com/v1/projects/${var.project_id}/locations/${var.region}/instances/${google_redis_instance.trustlayer_redis.name}:export"
    
    headers = {
      "Content-Type" = "application/json"
    }

    body = base64encode(jsonencode({
      outputConfig = {
        gcsDestination = {
          uri = "gs://${google_storage_bucket.redis_backups[0].name}/redis-backup-${formatdate("YYYY-MM-DD", timestamp())}.rdb"
        }
      }
    }))

    oauth_token {
      service_account_email = google_service_account.trustlayer_sa.email
    }
  }

  depends_on = [
    google_project_service.required_apis,
    google_redis_instance.trustlayer_redis
  ]
}

# Storage bucket for Redis backups
resource "google_storage_bucket" "redis_backups" {
  count = var.backup_retention_days > 0 ? 1 : 0
  
  name          = "${var.project_id}-${local.name_prefix}-redis-backups"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = var.backup_retention_days
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 5
    }
    action {
      type = "Delete"
    }
  }

  labels = merge(local.common_labels, {
    service = "redis-backup"
    purpose = "backup-storage"
  })
}

# IAM binding for Redis backup service account
resource "google_storage_bucket_iam_member" "redis_backup_writer" {
  count = var.backup_retention_days > 0 ? 1 : 0
  
  bucket = google_storage_bucket.redis_backups[0].name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.trustlayer_sa.email}"
}