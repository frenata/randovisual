terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP Project ID"
  default = "randovisual"
}

variable "region" {
  default = "us-west1"
}

variable "app_name" {
  default = "randovisual"
}

# Enable required APIs
resource "google_project_service" "run" {
  service = "run.googleapis.com"
}

resource "google_project_service" "storage" {
  service = "storage.googleapis.com"
}

resource "google_project_service" "secretmanager" {
  service = "secretmanager.googleapis.com"
}

# Cloud Storage bucket for PMTiles
resource "google_storage_bucket" "tiles" {
  name          = "${var.app_name}-tiles"
  location      = "US"
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
  
  website {
    main_page_suffix = "index.html"
  }
}

# Make bucket publicly readable
resource "google_storage_bucket_iam_member" "public_read" {
  bucket = google_storage_bucket.tiles.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# Backend bucket for CDN
resource "google_compute_backend_bucket" "tiles_backend" {
  name        = "${var.app_name}-tiles-backend"
  bucket_name = google_storage_bucket.tiles.name
  enable_cdn  = true
  
  cdn_policy {
    cache_mode        = "CACHE_ALL_STATIC"
    default_ttl       = 2592000  # 30 days
    max_ttl           = 2592000
    client_ttl        = 2592000
    negative_caching  = true
    
    signed_url_cache_max_age_sec = 3600
  }
}

# Secret Manager secrets
resource "google_secret_manager_secret" "rwgps_api_token" {
  secret_id = "${var.app_name}-rwgps-api-token"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret" "rwgps_api_key" {
  secret_id = "${var.app_name}-rwgps-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "${var.app_name}-database-url"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

# Service Account for Cloud Run
resource "google_service_account" "cloudrun" {
  account_id   = "${var.app_name}-cloudrun"
  display_name = "Cloud Run Service Account"
}

resource "google_secret_manager_secret_iam_member" "rwgps_token_access" {
  secret_id = google_secret_manager_secret.rwgps_api_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_secret_manager_secret_iam_member" "rwgps_key_access" {
  secret_id = google_secret_manager_secret.rwgps_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_secret_manager_secret_iam_member" "database_access" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_project_service" "artifactregistry" {
  service = "artifactregistry.googleapis.com"
 }
# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = var.app_name
  format        = "DOCKER"
  depends_on = [google_project_service.artifactregistry]
}


# Cloud Run: API
resource "google_cloud_run_v2_service" "api" {
  name     = "${var.app_name}-api"
  location = var.region

  template {
    service_account = google_service_account.cloudrun.email

    scaling {
      min_instance_count = 0
      max_instance_count = 4
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}/api:latest"

      ports {
        container_port = 8000
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "RWGPS_API_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.rwgps_api_token.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "RWGPS_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.rwgps_api_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }
    }
  }

  depends_on = [google_project_service.run]
}

# Cloud Run: Frontend
resource "google_cloud_run_v2_service" "fe" {
  name     = "${var.app_name}-fe"
  location = var.region

  template {
    service_account = google_service_account.cloudrun.email

    scaling {
      min_instance_count = 0
      max_instance_count = 4
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}/fe:latest"

      ports {
        container_port = 80
      }

      env {
        name  = "TILER_URL"
        value = "https://storage.googleapis.com/${google_storage_bucket.tiles.name}/routes.pmtiles"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }
    }
  }

  lifecycle {
    ignore_changes = [
      client,
      client_version
    ]
  }
  depends_on = [google_project_service.run]
}

# Make frontend publicly accessible
resource "google_cloud_run_v2_service_iam_member" "fe_public" {
  name     = google_cloud_run_v2_service.fe.name
  location = google_cloud_run_v2_service.fe.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "tiles_bucket" {
  description = "Cloud Storage bucket for PMTiles"
  value       = google_storage_bucket.tiles.name
}

output "tiles_url" {
  description = "Direct URL to PMTiles file"
  value       = "https://storage.googleapis.com/${google_storage_bucket.tiles.name}/routes.pmtiles"
}

output "fe_url" {
  description = "Frontend service URL"
  value       = google_cloud_run_v2_service.fe.uri
}

output "api_url" {
  description = "API service URL"
  value       = google_cloud_run_v2_service.api.uri
}

output "upload_command" {
  description = "Command to upload PMTiles"
  value       = "gsutil cp data/routes.pmtiles gs://${google_storage_bucket.tiles.name}/"
}

output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown"
  value = <<-EOT
    Storage (2GB): ~$0.04/month
    Egress (with CDN): ~$0.17/GB after cache
    Cloud Run (low traffic): ~$0-2/month
    Total: ~$1-5/month
  EOT
}

resource "google_cloud_run_domain_mapping" "fe" {
  location = var.region
  name     = "randovisual.frenata.net"

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.fe.name
  }
}

output "dns_records" {
  description = "DNS records to configure"
  value = google_cloud_run_domain_mapping.fe.status[0].resource_records
}
