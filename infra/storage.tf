resource "google_project_service" "storage" {
  service = "storage.googleapis.com"
}

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
