# TrustLayer AI - Private DNS Configuration

# Private DNS zone for internal domain
resource "google_dns_managed_zone" "trustlayer_internal" {
  name        = "${local.name_prefix}-internal-zone"
  dns_name    = "${var.domain_name}."
  description = "Private DNS zone for TrustLayer AI internal services"
  visibility  = "private"

  private_visibility_config {
    networks {
      network_url = google_compute_network.trustlayer_vpc.id
    }
  }

  labels = local.common_labels

  depends_on = [google_project_service.required_apis]
}

# A record for API service pointing to load balancer
resource "google_dns_record_set" "api_record" {
  name = "api.${google_dns_managed_zone.trustlayer_internal.dns_name}"
  type = "A"
  ttl  = 300

  managed_zone = google_dns_managed_zone.trustlayer_internal.name

  rrdatas = [google_compute_address.trustlayer_lb_ip.address]
}

# A record for dashboard service pointing to load balancer
resource "google_dns_record_set" "dashboard_record" {
  name = "dashboard.${google_dns_managed_zone.trustlayer_internal.dns_name}"
  type = "A"
  ttl  = 300

  managed_zone = google_dns_managed_zone.trustlayer_internal.name

  rrdatas = [google_compute_address.trustlayer_lb_ip.address]
}

# CNAME record for main domain pointing to API
resource "google_dns_record_set" "main_record" {
  name = google_dns_managed_zone.trustlayer_internal.dns_name
  type = "CNAME"
  ttl  = 300

  managed_zone = google_dns_managed_zone.trustlayer_internal.name

  rrdatas = ["api.${google_dns_managed_zone.trustlayer_internal.dns_name}"]
}

# TXT record for service discovery and verification
resource "google_dns_record_set" "service_discovery" {
  name = "_trustlayer._tcp.${google_dns_managed_zone.trustlayer_internal.dns_name}"
  type = "TXT"
  ttl  = 300

  managed_zone = google_dns_managed_zone.trustlayer_internal.name

  rrdatas = [
    "\"service=trustlayer-ai\"",
    "\"version=1.0\"",
    "\"environment=${var.environment}\"",
    "\"region=${var.region}\""
  ]
}

# SRV record for service discovery
resource "google_dns_record_set" "service_srv" {
  name = "_trustlayer._tcp.${google_dns_managed_zone.trustlayer_internal.dns_name}"
  type = "SRV"
  ttl  = 300

  managed_zone = google_dns_managed_zone.trustlayer_internal.name

  rrdatas = [
    "10 5 80 api.${google_dns_managed_zone.trustlayer_internal.dns_name}",
    "10 5 8501 dashboard.${google_dns_managed_zone.trustlayer_internal.dns_name}"
  ]
}

# Health check record for monitoring
resource "google_dns_record_set" "health_record" {
  name = "health.${google_dns_managed_zone.trustlayer_internal.dns_name}"
  type = "CNAME"
  ttl  = 60

  managed_zone = google_dns_managed_zone.trustlayer_internal.name

  rrdatas = ["api.${google_dns_managed_zone.trustlayer_internal.dns_name}"]
}

# Metrics endpoint record
resource "google_dns_record_set" "metrics_record" {
  name = "metrics.${google_dns_managed_zone.trustlayer_internal.dns_name}"
  type = "CNAME"
  ttl  = 60

  managed_zone = google_dns_managed_zone.trustlayer_internal.name

  rrdatas = ["api.${google_dns_managed_zone.trustlayer_internal.dns_name}"]
}

# Private DNS forwarding for AI API domains
resource "google_dns_managed_zone" "ai_apis_zone" {
  for_each = toset(var.allowed_domains)
  
  name        = "${local.name_prefix}-${replace(each.value, ".", "-")}-zone"
  dns_name    = "${each.value}."
  description = "Private DNS zone for ${each.value} AI API"
  visibility  = "private"

  private_visibility_config {
    networks {
      network_url = google_compute_network.trustlayer_vpc.id
    }
  }

  labels = merge(local.common_labels, {
    ai_provider = replace(each.value, ".", "-")
  })
}

# A records for AI API domains pointing to PSC endpoints
resource "google_dns_record_set" "ai_api_records" {
  for_each = toset(var.allowed_domains)
  
  name = google_dns_managed_zone.ai_apis_zone[each.value].dns_name
  type = "A"
  ttl  = 300

  managed_zone = google_dns_managed_zone.ai_apis_zone[each.value].name

  rrdatas = [google_compute_global_address.psc_address[each.value].address]
}

# DNS policy for query logging and security
resource "google_dns_policy" "trustlayer_dns_policy" {
  name                      = "${local.name_prefix}-dns-policy"
  enable_inbound_forwarding = false
  enable_logging            = true

  networks {
    network_url = google_compute_network.trustlayer_vpc.id
  }

  alternative_name_server_config {
    target_name_servers {
      ipv4_address    = "8.8.8.8"
      forwarding_path = "default"
    }
    target_name_servers {
      ipv4_address    = "8.8.4.4"
      forwarding_path = "default"
    }
  }
}