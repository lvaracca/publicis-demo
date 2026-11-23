# Généré depuis contracts/snapchat_ads.contract.yaml (v1.0.0) via templates/bronze_table.tf.tmpl

resource "google_bigquery_table" "brz_snapchat_ads" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.layers["bronze"].dataset_id
  table_id   = "brz_snapchat_ads"

  description = "Snapchat Ads raw daily social performance ingested from Adverity GCS landing."

  time_partitioning {
    type          = "DAY"
    field         = "report_date"
    expiration_ms = 63072000000 # 730 jours
  }

  require_partition_filter = true
  clustering               = ["client_id", "campaign_id"]

  labels = {
    env          = var.env
    domain       = "social"
    source       = "snapchat_ads"
    data_product = "ingestion_snapchat_ads"
    managed_by   = "terraform"
  }

  schema = jsonencode([
    { name = "report_date", type = "DATE", mode = "REQUIRED" },
    { name = "client_id", type = "STRING", mode = "REQUIRED" },
    { name = "account_id", type = "STRING", mode = "REQUIRED" },
    { name = "account_name", type = "STRING", mode = "REQUIRED" },
    { name = "campaign_id", type = "STRING", mode = "REQUIRED" },
    { name = "campaign_name", type = "STRING", mode = "REQUIRED" },
    { name = "campaign_objective", type = "STRING", mode = "REQUIRED" },
    { name = "campaign_status", type = "STRING", mode = "REQUIRED" },
    { name = "ad_squad_id", type = "STRING", mode = "REQUIRED" },
    { name = "ad_squad_name", type = "STRING", mode = "REQUIRED" },
    { name = "currency", type = "STRING", mode = "REQUIRED" },
    { name = "spend_micro", type = "INT64", mode = "REQUIRED" },
    { name = "impressions", type = "INT64", mode = "REQUIRED" },
    { name = "swipes", type = "INT64", mode = "REQUIRED" },
    { name = "video_views", type = "INT64", mode = "NULLABLE" },
    { name = "purchases", type = "INT64", mode = "NULLABLE" },
    { name = "view_through_conversions", type = "INT64", mode = "NULLABLE" },
    { name = "_ingested_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "_source_file", type = "STRING", mode = "REQUIRED" }
  ])
}
