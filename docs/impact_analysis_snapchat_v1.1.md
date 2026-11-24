# Schema Drift Impact Analysis — Snapchat Ads (`v1.0.0` → `v1.1.0`)

## Detected Drift (CI/CD Data Contract Check)
- **Source File**: `gs://publicis-demo-515613-landing/adverity/snapchat_ads/2026-11-24/snapchat_ads_2026_11_24_v2_drift.csv`
- **Reference Contract**: `contracts/snapchat_ads.contract.yaml` (`v1.0.0`)
- **Classification**: `NON_BREAKING_ADDITIVE` (new nullable column `view_through_conversions: INT64`)
- **Primary Key Impacted?**: No (`[report_date, account_id, campaign_id, ad_squad_id]` intact)

## End-to-End Impact Matrix (Pre-Execution)

| Layer | Impacted Asset | Nature of Impact | Required Action |
| :--- | :--- | :--- | :--- |
| **Data Contract** | `contracts/snapchat_ads.contract.yaml` | Minor version bump `1.0.0 → 1.1.0` | Add `view_through_conversions` (NULLABLE) via PR |
| **Terraform / Bronze** | `bronze.brz_snapchat_ads` | Backward-compatible nullable column addition | `ALTER TABLE ADD COLUMN IF NOT EXISTS` / `terraform apply` |
| **Silver (dbt)** | `stg_snapchat_ads`, `fct_social_performance_daily` | **Zero breakage risk** (explicit column pruning in `stg_snapchat_ads`, never `SELECT *`) | Optional: expose in Silver backlog if requested by business |
| **Gold / BI / Agent** | `gold.dp_social_performance`, Looker Studio, Conversational Analytics | **Zero impact** on CTR or RLS policies | No immediate action required |

> **Breaking Variant (`snapchat_ads_2026_11_24_v2_breaking.csv`)**: if Adverity renames `swipes → swipe_ups`, `check_schema_drift.py` exits with `exit code 1` (`BREAKING`), blocks ingestion before Bronze, and alerts the Data Steward before `stg_snapchat_ads` and the Gold `CTR` KPI break in production.
