# TrustLayer AI - VPC and Networking Configuration

# Custom VPC for TrustLayer AI
resource "google_compute_network" "trustlayer_vpc" {
  name                    = "${local.name_prefix}-vpc"
  auto_create_subnetworks = false
  mtu                     = 1460
  routing_mode           = "REGIONAL"

  depends_on = [google_project_service.required_apis]

  labels = local.common_labels
}

# Proxy subnet for Internal Load Balancer
resource "google_compute_subnetwork" "proxy_subnet" {
  name          = "${local.name_prefix}-proxy-subnet"
  ip_cidr_range = local.proxy_subnet_cidr
  region        = var.region
  network       = google_compute_network.trustlayer_vpc.id
  purpose       = "INTERNAL_HTTPS_LOAD_BALANCER"
  role          = "ACTIVE"

  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# VPC Connector subnet for Cloud Run
resource "google_compute_subnetwork" "connector_subnet" {
  name          = "${local.name_prefix}-connector-subnet"
  ip_cidr_range = local.connector_subnet_cidr
  region        = var.region
  network       = google_compute_network.trustlayer_vpc.id

  private_ip_google_access = var.enable_private_google_access

  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# Private Service Connect subnet
resource "google_compute_subnetwork" "psc_subnet" {
  name          = "${local.name_prefix}-psc-subnet"
  ip_cidr_range = local.psc_subnet_cidr
  region        = var.region
  network       = google_compute_network.trustlayer_vpc.id
  purpose       = "PRIVATE_SERVICE_CONNECT"

  private_ip_google_access = true
}

# VPC Connector for Cloud Run
resource "google_vpc_access_connector" "trustlayer_connector" {
  name          = "${local.name_prefix}-connector"
  region        = var.region
  network       = google_compute_network.trustlayer_vpc.name
  ip_cidr_range = local.connector_subnet_cidr

  min_throughput = 200
  max_throughput = 1000

  depends_on = [
    google_compute_subnetwork.connector_subnet,
    google_project_service.required_apis
  ]
}

# Cloud NAT for outbound internet access
resource "google_compute_router" "trustlayer_router" {
  name    = "${local.name_prefix}-router"
  region  = var.region
  network = google_compute_network.trustlayer_vpc.id

  bgp {
    asn = 64514
  }
}

resource "google_compute_router_nat" "trustlayer_nat" {
  name                               = "${local.name_prefix}-nat"
  router                            = google_compute_router.trustlayer_router.name
  region                            = var.region
  nat_ip_allocate_option            = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Firewall Rules
resource "google_compute_firewall" "allow_internal" {
  name    = "${local.name_prefix}-allow-internal"
  network = google_compute_network.trustlayer_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "8000", "8501", "6379"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = [local.vpc_cidr]
  target_tags   = ["trustlayer-internal"]

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_firewall" "allow_health_checks" {
  name    = "${local.name_prefix}-allow-health-checks"
  network = google_compute_network.trustlayer_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "8000"]
  }

  # Google Cloud health check ranges
  source_ranges = [
    "130.211.0.0/22",
    "35.191.0.0/16"
  ]

  target_tags = ["trustlayer-service"]

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_firewall" "allow_load_balancer" {
  name    = "${local.name_prefix}-allow-lb"
  network = google_compute_network.trustlayer_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = [local.proxy_subnet_cidr]
  target_tags   = ["trustlayer-service"]

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_firewall" "deny_all_ingress" {
  name     = "${local.name_prefix}-deny-all-ingress"
  network  = google_compute_network.trustlayer_vpc.name
  priority = 65534

  deny {
    protocol = "all"
  }

  source_ranges = ["0.0.0.0/0"]

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

# Private Service Connect for AI APIs
resource "google_compute_global_address" "psc_address" {
  for_each = toset(var.allowed_domains)
  
  name         = "${local.name_prefix}-psc-${replace(each.value, ".", "-")}"
  purpose      = "PRIVATE_SERVICE_CONNECT"
  network      = google_compute_network.trustlayer_vpc.id
  address_type = "INTERNAL"
}

# Private Service Connect endpoints for AI APIs
resource "google_compute_global_forwarding_rule" "psc_endpoint" {
  for_each = toset(var.allowed_domains)
  
  name                  = "${local.name_prefix}-psc-${replace(each.value, ".", "-")}"
  target                = "https://${each.value}"
  port_range           = "443"
  load_balancing_scheme = ""
  network              = google_compute_network.trustlayer_vpc.id
  ip_address           = google_compute_global_address.psc_address[each.value].id
}