# TrustLayer AI - Cloud Run Services Configuration

# Service Account for Cloud Run
resource "google_service_account" "trustlayer_sa" {
  account_id   = "${local.name_prefix}-sa"
  display_name = "TrustLayer AI Service Account"
  description  = "Service account for TrustLayer AI Cloud Run services"
}

# IAM bindings for service account
resource "google_project_iam_member" "trustlayer_sa_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/redis.editor"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.trustlayer_sa.email}"
}

# Cloud Run service for TrustLayer AI Proxy
resource "google_cloud_run_v2_service" "trustlayer_proxy" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.trustlayer_sa.email
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    vpc_access {
      connector = google_vpc_access_connector.trustlayer_connector.id
      egress    = "ALL_TRAFFIC"
    }

    containers {
      image = replace(var.container_image, "PROJECT_ID", var.project_id)
      
      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
        cpu_idle = true
      }

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "REGION"
        value = var.region
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "REDIS_HOST"
        value = google_redis_instance.trustlayer_redis.host
      }

      env {
        name  = "REDIS_PORT"
        value = tostring(google_redis_instance.trustlayer_redis.port)
      }

      env {
        name  = "LOG_LEVEL"
        value = var.log_level
      }

      env {
        name  = "SESSION_TTL"
        value = tostring(var.session_ttl)
      }

      env {
        name = "ALLOWED_DOMAINS"
        value = join(",", var.allowed_domains)
      }

      startup_probe {
        initial_delay_seconds = 10
        timeout_seconds      = 5
        period_seconds       = 10
        failure_threshold    = 3
        
        http_get {
          path = var.health_check_path
          port = 8000
        }
      }

      liveness_probe {
        initial_delay_seconds = 30
        timeout_seconds      = 5
        period_seconds       = 30
        failure_threshold    = 3
        
        http_get {
          path = var.health_check_path
          port = 8000
        }
      }
    }

    labels = merge(local.common_labels, {
      service = "proxy"
    })
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    google_project_service.required_apis,
    google_vpc_access_connector.trustlayer_connector,
    google_redis_instance.trustlayer_redis
  ]

  labels = local.common_labels
}

# Cloud Run service for TrustLayer AI Dashboard
resource "google_cloud_run_v2_service" "trustlayer_dashboard" {
  name     = var.dashboard_service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.trustlayer_sa.email
    
    scaling {
      min_instance_count = 1
      max_instance_count = 3
    }

    vpc_access {
      connector = google_vpc_access_connector.trustlayer_connector.id
      egress    = "ALL_TRAFFIC"
    }

    containers {
      image = replace(var.dashboard_image, "PROJECT_ID", var.project_id)
      
      ports {
        container_port = 8501
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
        cpu_idle = true
      }

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "PROXY_URL"
        value = "http://${google_cloud_run_v2_service.trustlayer_proxy.uri}"
      }

      env {
        name  = "PYTHONPATH"
        value = "/app"
      }

      env {
        name  = "STREAMLIT_SERVER_ADDRESS"
        value = "0.0.0.0"
      }

      env {
        name  = "STREAMLIT_SERVER_PORT"
        value = "8501"
      }

      startup_probe {
        initial_delay_seconds = 15
        timeout_seconds      = 10
        period_seconds       = 10
        failure_threshold    = 5
        
        http_get {
          path = "/_stcore/health"
          port = 8501
        }
      }

      liveness_probe {
        initial_delay_seconds = 30
        timeout_seconds      = 10
        period_seconds       = 30
        failure_threshold    = 3
        
        http_get {
          path = "/_stcore/health"
          port = 8501
        }
      }
    }

    labels = merge(local.common_labels, {
      service = "dashboard"
    })
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    google_project_service.required_apis,
    google_vpc_access_connector.trustlayer_connector,
    google_cloud_run_v2_service.trustlayer_proxy
  ]

  labels = local.common_labels
}

# IAM policy for Cloud Run services (internal access only)
resource "google_cloud_run_service_iam_member" "proxy_invoker" {
  service  = google_cloud_run_v2_service.trustlayer_proxy.name
  location = google_cloud_run_v2_service.trustlayer_proxy.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service_iam_member" "dashboard_invoker" {
  service  = google_cloud_run_v2_service.trustlayer_dashboard.name
  location = google_cloud_run_v2_service.trustlayer_dashboard.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}