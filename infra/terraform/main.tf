terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

variable "project_id" {
  type    = string
  default = "publicis-demo-515613"
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "env" {
  type    = string
  default = "dev"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# GCS Landing Bucket (Adverity -> GCS) : UBLA + PAP + Lifecycle FinOps 90j -> Nearline
resource "google_storage_bucket" "landing" {
  name                        = "${var.project_id}-landing"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  soft_delete_policy {
    retention_duration_seconds = 604800 # 7 jours
  }

  lifecycle_rule {
    condition { age = 90 }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition { age = 365 }
    action { type = "Delete" }
  }

  labels = {
    env         = var.env
    domain      = "social"
    cost_center = "publicis_media_fr"
    managed_by  = "terraform"
  }
}

# Datasets BigQuery par couche Medallion
locals {
  datasets = ["ref", "bronze", "silver", "gold", "dq_monitoring"]
}

resource "google_bigquery_dataset" "layers" {
  for_each      = toset(local.datasets)
  dataset_id    = each.key
  location      = var.region
  description   = "Publicis Media France Social Platform - ${each.key} layer"

  labels = {
    env        = var.env
    domain     = "social"
    layer      = each.key
    managed_by = "terraform"
  }
}

# Keyless Least-Privilege Service Account pour l'Agent Talk-to-Data (Gold ONLY)
resource "google_service_account" "talk_to_data_gold" {
  account_id   = "sa-talk-to-data-gold"
  display_name = "Publicis Talk-to-Data Agent (Gold Semantic Layer Only)"
  description  = "Keyless SA: accès lecture seule sur gold uniquement. Aucun accès bronze/silver."
}

resource "google_project_iam_member" "talk_to_data_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.talk_to_data_gold.email}"
}

resource "google_bigquery_dataset_iam_member" "talk_to_data_gold_viewer" {
  dataset_id = google_bigquery_dataset.layers["gold"].dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.talk_to_data_gold.email}"
}
