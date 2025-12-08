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

resource "google_project_service" "run" {
  service = "run.googleapis.com"
}

resource "google_project_service" "artifactregistry" {
  service = "artifactregistry.googleapis.com"
 }

resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = var.app_name
  format        = "DOCKER"
  depends_on = [google_project_service.artifactregistry]
}

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

resource "google_cloud_run_v2_service_iam_member" "fe_public" {
  name     = google_cloud_run_v2_service.fe.name
  location = google_cloud_run_v2_service.fe.location
  role     = "roles/run.invoker"
  member   = "allUsers"
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

