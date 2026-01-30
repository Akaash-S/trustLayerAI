# TrustLayer AI - Monitoring and Observability Configuration

# Monitoring workspace (if not exists)
resource "google_monitoring_workspace" "trustlayer_workspace" {
  count = var.enable_monitoring ? 1 : 0
  
  provider         = google-beta
  workspace_id     = var.project_id
  initial_project  = var.project_id
}

# Custom metrics for PII detection
resource "google_logging_metric" "pii_detection_rate" {
  count = var.enable_monitoring ? 1 : 0
  
  name   = "trustlayer_pii_detection_rate"
  filter = "resource.type=\"cloud_run_revision\" AND jsonPayload.message=~\"PII entities blocked\""
  
  metric_descriptor {
    metric_kind = "GAUGE"
    value_type  = "INT64"
    display_name = "PII Detection Rate"
  }
  
  value_extractor = "EXTRACT(jsonPayload.entities_count)"
  
  label_extractors = {
    "service_name" = "EXTRACT(resource.labels.service_name)"
    "revision_name" = "EXTRACT(resource.labels.revision_name)"
  }
}

# Custom metrics for request latency
resource "google_logging_metric" "request_latency" {
  count = var.enable_monitoring ? 1 : 0
  
  name   = "trustlayer_request_latency"
  filter = "resource.type=\"cloud_run_revision\" AND jsonPayload.latency_ms"
  
  metric_descriptor {
    metric_kind = "GAUGE"
    value_type  = "DOUBLE"
    display_name = "Request Latency (ms)"
  }
  
  value_extractor = "EXTRACT(jsonPayload.latency_ms)"
  
  label_extractors = {
    "service_name" = "EXTRACT(resource.labels.service_name)"
    "method" = "EXTRACT(jsonPayload.method)"
  }
}

# Alert policy for high error rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  count = var.enable_monitoring ? 1 : 0
  
  display_name = "TrustLayer AI - High Error Rate"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Cloud Run error rate > 5%"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 0.05
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_MEAN"
        group_by_fields = ["resource.labels.service_name"]
      }
    }
  }
  
  notification_channels = var.notification_email != "" ? [google_monitoring_notification_channel.email[0].id] : []
  
  alert_strategy {
    auto_close = "1800s"
  }
}

# Alert policy for high latency
resource "google_monitoring_alert_policy" "high_latency" {
  count = var.enable_monitoring ? 1 : 0
  
  display_name = "TrustLayer AI - High Latency"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Request latency > 5 seconds"
    
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/trustlayer_request_latency\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 5000
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
        cross_series_reducer = "REDUCE_MEAN"
        group_by_fields = ["metric.labels.service_name"]
      }
    }
  }
  
  notification_channels = var.notification_email != "" ? [google_monitoring_notification_channel.email[0].id] : []
}

# Alert policy for Redis connection issues
resource "google_monitoring_alert_policy" "redis_connection_issues" {
  count = var.enable_monitoring ? 1 : 0
  
  display_name = "TrustLayer AI - Redis Connection Issues"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Redis connection failures"
    
    condition_threshold {
      filter          = "resource.type=\"redis_instance\" AND resource.labels.instance_id=\"${google_redis_instance.trustlayer_redis.instance_id}\""
      duration        = "300s"
      comparison      = "COMPARISON_LESS_THAN"
      threshold_value = 0.95
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }
  
  notification_channels = var.notification_email != "" ? [google_monitoring_notification_channel.email[0].id] : []
}

# Alert policy for PII detection anomalies
resource "google_monitoring_alert_policy" "pii_detection_anomaly" {
  count = var.enable_monitoring ? 1 : 0
  
  display_name = "TrustLayer AI - PII Detection Anomaly"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Unusual PII detection patterns"
    
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/trustlayer_pii_detection_rate\""
      duration        = "600s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 100
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
  
  notification_channels = var.notification_email != "" ? [google_monitoring_notification_channel.email[0].id] : []
}

# Notification channel for email alerts
resource "google_monitoring_notification_channel" "email" {
  count = var.notification_email != "" ? 1 : 0
  
  display_name = "TrustLayer AI Email Notifications"
  type         = "email"
  
  labels = {
    email_address = var.notification_email
  }
  
  enabled = true
}

# Uptime check for API endpoint
resource "google_monitoring_uptime_check_config" "api_uptime_check" {
  count = var.enable_monitoring ? 1 : 0
  
  display_name = "TrustLayer AI API Uptime Check"
  timeout      = "10s"
  period       = "300s"
  
  http_check {
    path         = var.health_check_path
    port         = "80"
    request_method = "GET"
    
    accepted_response_status_codes {
      status_class = "STATUS_CLASS_2XX"
    }
  }
  
  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = "api.${var.domain_name}"
    }
  }
  
  content_matchers {
    content = "healthy"
    matcher = "CONTAINS_STRING"
  }
}

# Dashboard for TrustLayer AI metrics
resource "google_monitoring_dashboard" "trustlayer_dashboard" {
  count = var.enable_monitoring ? 1 : 0
  
  dashboard_json = jsonencode({
    displayName = "TrustLayer AI - Operational Dashboard"
    
    mosaicLayout = {
      tiles = [
        {
          width = 6
          height = 4
          widget = {
            title = "Request Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}\""
                    aggregation = {
                      alignmentPeriod = "60s"
                      perSeriesAligner = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "LINE"
              }]
              yAxis = {
                label = "Requests/sec"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width = 6
          height = 4
          xPos = 6
          widget = {
            title = "Error Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}\" AND metric.labels.response_code_class!=\"2xx\""
                    aggregation = {
                      alignmentPeriod = "60s"
                      perSeriesAligner = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "LINE"
              }]
              yAxis = {
                label = "Errors/sec"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width = 6
          height = 4
          yPos = 4
          widget = {
            title = "PII Detection Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"logging.googleapis.com/user/trustlayer_pii_detection_rate\""
                    aggregation = {
                      alignmentPeriod = "300s"
                      perSeriesAligner = "ALIGN_MEAN"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "STACKED_BAR"
              }]
              yAxis = {
                label = "PII Entities Detected"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width = 6
          height = 4
          xPos = 6
          yPos = 4
          widget = {
            title = "Redis Memory Usage"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"redis_instance\" AND resource.labels.instance_id=\"${google_redis_instance.trustlayer_redis.instance_id}\" AND metric.type=\"redis.googleapis.com/stats/memory/usage_ratio\""
                    aggregation = {
                      alignmentPeriod = "60s"
                      perSeriesAligner = "ALIGN_MEAN"
                    }
                  }
                }
                plotType = "LINE"
              }]
              yAxis = {
                label = "Memory Usage %"
                scale = "LINEAR"
              }
            }
          }
        }
      ]
    }
  })
}

# Log sink for security events
resource "google_logging_project_sink" "security_sink" {
  count = var.enable_monitoring ? 1 : 0
  
  name        = "${local.name_prefix}-security-sink"
  destination = "storage.googleapis.com/${google_storage_bucket.security_logs[0].name}"
  
  filter = "protoPayload.serviceName=\"cloudresourcemanager.googleapis.com\" OR protoPayload.serviceName=\"iam.googleapis.com\" OR severity>=ERROR"
  
  unique_writer_identity = true
}

# Storage bucket for security logs
resource "google_storage_bucket" "security_logs" {
  count = var.enable_monitoring ? 1 : 0
  
  name          = "${var.project_id}-${local.name_prefix}-security-logs"
  location      = var.region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
  
  labels = merge(local.common_labels, {
    purpose = "security-logs"
  })
}

# IAM binding for log sink
resource "google_storage_bucket_iam_member" "security_logs_writer" {
  count = var.enable_monitoring ? 1 : 0
  
  bucket = google_storage_bucket.security_logs[0].name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.security_sink[0].writer_identity
}