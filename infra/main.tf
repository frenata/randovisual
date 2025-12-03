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

resource "google_project_service" "artifactregistry" {
  service = "artifactregistry.googleapis.com"
}

resource "google_project_service" "secretmanager" {
  service = "secretmanager.googleapis.com"
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = var.app_name
  format        = "DOCKER"

  depends_on = [google_project_service.artifactregistry]
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

# Service Account for Cloud Run services
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

# Cloud Run: Tiler (pg_tileserv)
resource "google_cloud_run_v2_service" "tiler" {
  name     = "${var.app_name}-tiler"
  location = var.region

  template {
    service_account = google_service_account.cloudrun.email

    scaling {
      min_instance_count = 0
      max_instance_count = 4
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}/tiler:latest"

      ports {
        container_port = 7800
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
        value = google_cloud_run_v2_service.tiler.uri
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

# IAM to allow public access
resource "google_cloud_run_v2_service_iam_member" "tiler_public" {
  name     = google_cloud_run_v2_service.tiler.name
  location = google_cloud_run_v2_service.tiler.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# API is not publicly accessible - requires authentication

resource "google_cloud_run_v2_service_iam_member" "fe_public" {
  name     = google_cloud_run_v2_service.fe.name
  location = google_cloud_run_v2_service.fe.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "tiler_url" {
  description = "Tiler service URL"
  value       = google_cloud_run_v2_service.tiler.uri
}

output "api_url" {
  description = "API service URL"
  value       = google_cloud_run_v2_service.api.uri
}

output "fe_url" {
  description = "Frontend service URL"
  value       = google_cloud_run_v2_service.fe.uri
}

output "artifact_registry" {
  description = "Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}"
}

output "secrets_to_populate" {
  description = "Secrets that need values set"
  value = {
    rwgps_api_token = google_secret_manager_secret.rwgps_api_token.secret_id
    rwgps_api_key   = google_secret_manager_secret.rwgps_api_key.secret_id
    database_url    = google_secret_manager_secret.database_url.secret_id
  }
}
