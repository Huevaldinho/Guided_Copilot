output "lms_materials_bucket" {
  value       = google_storage_bucket.lms_materials.name
  description = "GCS bucket name for LMS materials"
}

output "terraform_state_bucket" {
  value       = google_storage_bucket.terraform_state.name
  description = "GCS bucket name for Terraform state"
}
