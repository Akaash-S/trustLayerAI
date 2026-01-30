# TrustLayer AI - Internal Load Balancer Configuration

# Health check for proxy service
resource "google_compute_health_check" "trustlayer_proxy_health" {
  name               = "${local.name_prefix}-proxy-health"
  check_interval_sec = 30
  timeout_sec        = 10
  healthy_threshold  = 2
  unhealthy_threshold = 3

  http_health_check {
    port         = 8000
    request_path = var.health_check_path
  }

  log_config {
    enable = true
  }
}

# Health check for dashboard service
resource "google_compute_health_check" "trustlayer_dashboard_health" {
  name               = "${local.name_prefix}-dashboard-health"
  check_interval_sec = 30
  timeout_sec        = 10
  healthy_threshold  = 2
  unhealthy_threshold = 3

  http_health_check {
    port         = 8501
    request_path = "/_stcore/health"
  }

  log_config {
    enable = true
  }
}

# Serverless NEG for proxy Cloud Run service
resource "google_compute_region_network_endpoint_group" "trustlayer_proxy_neg" {
  name                  = "${local.name_prefix}-proxy-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.trustlayer_proxy.name
  }
}

# Serverless NEG for dashboard Cloud Run service
resource "google_compute_region_network_endpoint_group" "trustlayer_dashboard_neg" {
  name                  = "${local.name_prefix}-dashboard-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.trustlayer_dashboard.name
  }
}

# Backend service for proxy
resource "google_compute_region_backend_service" "trustlayer_proxy_backend" {
  name                  = "${local.name_prefix}-proxy-backend"
  region                = var.region
  protocol              = "HTTP"
  load_balancing_scheme = "INTERNAL_MANAGED"
  timeout_sec           = 30

  backend {
    group = google_compute_region_network_endpoint_group.trustlayer_proxy_neg.id
  }

  health_checks = [google_compute_health_check.trustlayer_proxy_health.id]

  log_config {
    enable      = true
    sample_rate = 1.0
  }

  iap {
    oauth2_client_id     = ""
    oauth2_client_secret = ""
  }
}

# Backend service for dashboard
resource "google_compute_region_backend_service" "trustlayer_dashboard_backend" {
  name                  = "${local.name_prefix}-dashboard-backend"
  region                = var.region
  protocol              = "HTTP"
  load_balancing_scheme = "INTERNAL_MANAGED"
  timeout_sec           = 30

  backend {
    group = google_compute_region_network_endpoint_group.trustlayer_dashboard_neg.id
  }

  health_checks = [google_compute_health_check.trustlayer_dashboard_health.id]

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

# URL map for routing
resource "google_compute_region_url_map" "trustlayer_url_map" {
  name            = "${local.name_prefix}-url-map"
  region          = var.region
  default_service = google_compute_region_backend_service.trustlayer_proxy_backend.id

  host_rule {
    hosts        = ["api.${var.domain_name}"]
    path_matcher = "proxy-matcher"
  }

  host_rule {
    hosts        = ["dashboard.${var.domain_name}"]
    path_matcher = "dashboard-matcher"
  }

  path_matcher {
    name            = "proxy-matcher"
    default_service = google_compute_region_backend_service.trustlayer_proxy_backend.id

    path_rule {
      paths   = ["/health", "/metrics", "/*"]
      service = google_compute_region_backend_service.trustlayer_proxy_backend.id
    }
  }

  path_matcher {
    name            = "dashboard-matcher"
    default_service = google_compute_region_backend_service.trustlayer_dashboard_backend.id

    path_rule {
      paths   = ["/*"]
      service = google_compute_region_backend_service.trustlayer_dashboard_backend.id
    }
  }
}

# HTTP proxy for load balancer
resource "google_compute_region_target_http_proxy" "trustlayer_proxy" {
  name    = "${local.name_prefix}-http-proxy"
  region  = var.region
  url_map = google_compute_region_url_map.trustlayer_url_map.id
}

# Reserved internal IP address for load balancer
resource "google_compute_address" "trustlayer_lb_ip" {
  name         = "${local.name_prefix}-lb-ip"
  region       = var.region
  subnetwork   = google_compute_subnetwork.proxy_subnet.id
  address_type = "INTERNAL"
  purpose      = "GCE_ENDPOINT"
}

# Internal load balancer forwarding rule
resource "google_compute_forwarding_rule" "trustlayer_lb" {
  name                  = "${local.name_prefix}-lb"
  region                = var.region
  ip_protocol           = "TCP"
  load_balancing_scheme = "INTERNAL_MANAGED"
  port_range           = "80"
  target               = google_compute_region_target_http_proxy.trustlayer_proxy.id
  network              = google_compute_network.trustlayer_vpc.id
  subnetwork           = google_compute_subnetwork.proxy_subnet.id
  ip_address           = google_compute_address.trustlayer_lb_ip.address

  labels = local.common_labels
}

# SSL certificate for HTTPS (if needed)
resource "google_compute_region_ssl_certificate" "trustlayer_ssl" {
  count = var.ssl_policy != "" ? 1 : 0
  
  name_prefix = "${local.name_prefix}-ssl-"
  region      = var.region

  private_key = file("${path.module}/ssl/private.key")
  certificate = file("${path.module}/ssl/certificate.crt")

  lifecycle {
    create_before_destroy = true
  }
}

# HTTPS proxy (if SSL is enabled)
resource "google_compute_region_target_https_proxy" "trustlayer_https_proxy" {
  count = var.ssl_policy != "" ? 1 : 0
  
  name             = "${local.name_prefix}-https-proxy"
  region           = var.region
  url_map          = google_compute_region_url_map.trustlayer_url_map.id
  ssl_certificates = [google_compute_region_ssl_certificate.trustlayer_ssl[0].id]
}

# HTTPS forwarding rule (if SSL is enabled)
resource "google_compute_forwarding_rule" "trustlayer_https_lb" {
  count = var.ssl_policy != "" ? 1 : 0
  
  name                  = "${local.name_prefix}-https-lb"
  region                = var.region
  ip_protocol           = "TCP"
  load_balancing_scheme = "INTERNAL_MANAGED"
  port_range           = "443"
  target               = google_compute_region_target_https_proxy.trustlayer_https_proxy[0].id
  network              = google_compute_network.trustlayer_vpc.id
  subnetwork           = google_compute_subnetwork.proxy_subnet.id
  ip_address           = google_compute_address.trustlayer_lb_ip.address

  labels = local.common_labels
}