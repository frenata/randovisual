resource "google_project_service" "secretmanager" {
  service = "secretmanager.googleapis.com"
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
