# Publicis Media France — Social Data Platform (Paved Road Rules)

> **Publicis Media France Agentification Principle**:
> *Agents propose, templates write the code, a human validates via Pull Request.*
> *Business agents ("Talk to Data") read ONLY the Gold semantic layer — never technical Bronze or Silver tables.*

---

## 1. Target GCP Environment
- **Project ID**: `publicis-demo-515613`
- **Region**: `europe-west1` (co-located GCS + BigQuery = zero inter-region egress)
- **Landing Bucket (Adverity → GCS)**: `gs://publicis-demo-515613-landing`
- **BigQuery Datasets**:
  - `ref`: canonical reference tables (`ref_fx_rates`, `ref_media_taxonomy`, `ref_clients_rls`)
  - `bronze`: raw source-aligned tables (`brz_<source>`)
  - `silver`: unified dbt canonical model (`stg_<source>`, `dim_*_scd2`, `fct_*`)
  - `gold`: certified Data Products with Row-Level Security (`dp_<product>`)
  - `dq_monitoring`: data quality checks and anomaly tracking

---

## 2. Mandatory Naming Conventions
- **Data Contracts**: `contracts/<source>.contract.yaml` (ODCS v3 format, based on `templates/data_contract.odcs.yaml`)
- **Bronze Terraform**: `infra/terraform/bronze_<source>.tf` (based on `templates/bronze_table.tf.tmpl`)
- **Ingestion SQL**: `sql/ingestion/load_brz_<source>.sql` (idempotent `MERGE` or partition overwrite, with `_ingested_at` and `_source_file`)
- **dbt Staging**: `dbt_social/models/staging/<source>/stg_<source>.sql` (materialized as `view`)
- **dbt SCD2 Snapshots**: `dbt_social/snapshots/snp_campaign_scd2.sql`
- **dbt Silver Facts**: `dbt_social/models/silver/fct_social_performance_daily.sql` (materialized as `incremental`, `insert_overwrite`)
- **dbt Gold Data Products**: `dbt_social/models/gold/dp_social_performance.sql`

---

## 3. Silver Core Data Model Standards (Social)
1. **Strict Grain**: `(date_day, platform, account_id, campaign_id, adset_id)` — **mandatory grain test** (`unique_combination_of_columns`) on every Silver fact table.
2. **Surrogate Key**: `social_perf_sk` generated via `{{ generate_surrogate_key(['date_day', 'platform', 'account_id', 'campaign_id', 'adset_id']) }}`.
3. **EUR Currency Normalization**: all media spend is converted to EUR by joining `ref.ref_fx_rates` (`spend_local * rate_to_eur`). Watch out for micro-currency platforms (e.g., Snapchat `spend_micro / 1e6`).
4. **Canonical Media Taxonomy**: every `campaign_name` must be parsed via `{{ parse_media_taxonomy('campaign_name') }}` (convention `{COUNTRY}_{CLIENT}_{BRAND}_{OBJECTIVE}_{FUNNEL}_{YEAR}`). On parse failure, fallback to `UNKNOWN` and surface in data quality monitoring.
5. **SCD Type 2**: any change to campaign attributes (name, objective, status) must be historized in `dim_campaign_scd2`.
6. **Deduplication**: every staging model deduplicates on its natural key (`QUALIFY ROW_NUMBER() OVER (...) = 1`) before entering Silver.

---

## 4. BigQuery FinOps & Performance Standards (Built-In by Design)
- **Partitioning**: every Bronze/Silver/Gold fact table is partitioned by day (`report_date` or `date_day`).
- **Clustering**: `CLUSTER BY client_id, platform` (or `client_id, campaign_id` in Bronze).
- **Scan Guardrail**: `require_partition_filter = true` on large Bronze tables.
- **Incremental Processing**: `materialized='incremental'`, `incremental_strategy='insert_overwrite'` on Silver fact tables.
- **Mandatory Labels** on every Terraform resource, dbt model, and BigQuery job:
  - `env`: `dev` | `stg` | `prod`
  - `domain`: `social`
  - `data_product`: `dp_social_performance` (or `ingestion_<source>`)
  - `managed_by`: `terraform` | `dbt`
- **GCS Lifecycle**: automatic transition to `NEARLINE` after 90 days, deletion after 365 days.

---

## 5. Security, Governance & Agentification
- **Keyless Only**: zero Service Account JSON keys in the repository or CI/CD (ADC / Workload Identity only).
- **Least Privilege & Client Isolation**:
  - `gold.dp_social_performance` enforces a **Row Access Policy (RLS)** driven by `ref.ref_clients_rls`.
  - Onboarding a new client is pure **configuration** (1 row in `ref_clients_rls`), never pipeline copy-paste.
- **Single-Definition KPIs (Semantic Layer)**:
  - `CTR = SAFE_DIVIDE(SUM(clicks), SUM(impressions))` — **NEVER** `AVG(ctr)`.
  - `CPM = SAFE_DIVIDE(SUM(spend_eur), SUM(impressions)) * 1000`.
  - `CPC = SAFE_DIVIDE(SUM(spend_eur), SUM(clicks))`.
- **Mandatory PR Workflow**: every creation or change goes through a Git branch (`feat/...`), automated validation (`terraform validate` / `dbt compile` / `dbt test`), and human Pull Request review.
