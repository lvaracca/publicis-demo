# Automatic Client Isolation in Gold (Row-Level Security driven by ref.ref_clients_rls)
# Adding a new client is pure configuration in ref.ref_clients_rls (zero copy-paste).

resource "google_bigquery_job" "apply_gold_rls" {
  job_id   = "apply_gold_rls_policy_v1"
  location = var.region

  query {
    use_legacy_sql = false
    query          = <<-SQL
      CREATE OR REPLACE ROW ACCESS POLICY rls_client_isolation
      ON `${var.project_id}.gold.dp_social_performance`
      GRANT TO (
        "user:admin@lvaracca.altostrat.com",
        "user:lvaracca@gcp.altostrat.com",
        "serviceAccount:sa-talk-to-data-gold@${var.project_id}.iam.gserviceaccount.com"
      )
      FILTER USING (
        client_id IN (
          SELECT client_id
          FROM `${var.project_id}.ref.ref_clients_rls`
          WHERE user_principal = SESSION_USER()
            AND is_active = TRUE
        )
      );
    SQL
  }

  labels = {
    env          = var.env
    domain       = "social"
    data_product = "dp_social_performance"
    managed_by   = "terraform"
  }
}
