resource "google_bigquery_table" "brz_meta_ads" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.layers["bronze"].dataset_id
  table_id   = "brz_meta_ads"

  description = "Meta Ads raw daily social performance ingested from Adverity GCS landing."

  time_partitioning {
    type          = "DAY"
    field         = "report_date"
    expiration_ms = 63072000000 # 730 days
  }

  require_partition_filter = true
  clustering               = ["client_id", "campaign_id"]

  labels = {
    env          = var.env
    domain       = "social"
    source       = "meta_ads"
    data_product = "ingestion_meta_ads"
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
    { name = "adset_id", type = "STRING", mode = "REQUIRED" },
    { name = "adset_name", type = "STRING", mode = "REQUIRED" },
    { name = "currency", type = "STRING", mode = "REQUIRED" },
    { name = "spend", type = "FLOAT64", mode = "REQUIRED" },
    { name = "impressions", type = "INT64", mode = "REQUIRED" },
    { name = "link_clicks", type = "INT64", mode = "REQUIRED" },
    { name = "video_views", type = "INT64", mode = "NULLABLE" },
    { name = "conversions", type = "INT64", mode = "NULLABLE" },
    { name = "_ingested_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "_source_file", type = "STRING", mode = "REQUIRED" }
  ])
}
