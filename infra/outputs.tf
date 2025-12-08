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

output "dns_records" {
  description = "DNS records to configure"
  value = google_cloud_run_domain_mapping.fe.status[0].resource_records
}
