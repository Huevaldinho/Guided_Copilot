# Terraform skeleton for GCS bucket and remote state
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

# GCS bucket for LMS materials
resource "google_storage_bucket" "lms_materials" {
  name     = var.gcs_bucket_name
  location = var.gcp_region
}

# GCS bucket for Terraform remote state
resource "google_storage_bucket" "terraform_state" {
  name     = var.tf_state_bucket_name
  location = var.gcp_region
}
