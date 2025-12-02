variable "gcp_project" {
  type        = string
  description = "GCP Project ID"
}

variable "gcp_region" {
  type        = string
  description = "GCP region"
  default     = "us-central1"
}

variable "gcs_bucket_name" {
  type        = string
  description = "GCS bucket name for LMS materials"
}

variable "tf_state_bucket_name" {
  type        = string
  description = "GCS bucket name for Terraform state"
}
