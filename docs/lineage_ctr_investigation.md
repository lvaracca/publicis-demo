# Lineage & Data Quality Investigation — "Where Does This Number Come From?" (Act 4)

## Business Question
> *"Maison Éclat's Snapchat CTR dropped sharply on November 23, 2026 (from 2.12% on Nov 22 to 1.47% on Nov 23, a -30.7% relative drop). Where exactly does this number come from, which tables/columns feed it, and what caused the drop?"*

## 1. Column-Level Lineage (Gold → Silver → Bronze → GCS)

```text
gs://publicis-demo-515613-landing/adverity/snapchat_ads/2026-11-23/snapchat_ads_2026_11_23_sample.csv
  │  (cols: swipes, impressions, spend_micro, currency, campaign_name, ad_squad_id)
  ▼
bronze.brz_snapchat_ads                         [Partition: report_date | Cluster: client_id, campaign_id]
  │  (845 raw rows including 3 duplicates on Nov 22 + 2 impressions=0 anomalies on Nov 21)
  ▼
silver.stg_snapchat_ads                         [dbt view]
  │  • swipes               ──► clicks
  │  • impressions          ──► impressions
  │  • spend_micro / 1e6 × ref.ref_fx_rates.rate_to_eur ──► spend_eur
  │  • parse_media_taxonomy(campaign_name) ──► taxo_brand, taxo_objective, taxo_funnel, is_taxonomy_valid
  │  • QUALIFY ROW_NUMBER() = 1 (removes 3 raw duplicates -> 842 unique rows)
  ▼
silver.fct_social_performance_daily             [dbt incremental insert_overwrite + Grain Test PASS]
  │  • Point-in-time join on silver.dim_campaign_scd2 (SCD Type 2 history)
  │  • Flag has_metric_anomaly = (impressions = 0 AND clicks > 0)
  ▼
gold.dp_social_performance                      [Certified Data Product + BigQuery RLS by client_id]
  │  • Filter WHERE has_metric_anomaly = FALSE (routes 2 corrupted rows to dq_monitoring)
  │  • Canonical KPI: CTR = SAFE_DIVIDE(SUM(clicks), SUM(impressions))
  ▼
Unified Serving: Looker Studio  ===  Conversational Analytics (`publicis-social-gold-agent`)
```

## 2. Data Quality Diagnosis (Automated Checks)
- **Freshness (`dbt source freshness`)**: ✅ PASS across Meta, TikTok, Snapchat (< 24h).
- **Grain & Duplicates (`unique_combination_of_columns`)**: ✅ PASS in Silver (3 raw duplicates on Nov 22 cleanly deduplicated in staging).
- **Financial Reconciliation (`assert_reconcile_bronze_silver_spend`)**: ✅ PASS (`0.00 EUR` variance between Bronze and Silver across all 3 platforms).
- **Anomalies Logged in `dq_monitoring.dq_social_anomalies`** (⚠️ 2 WARN tests):
  1. `2026-11-21`: 2 rows with `impressions = 0` and `swipes > 0` (`maison_eclat` + `autonova_fr`) — automatically excluded from Gold.
  2. `camp_snap_eclat_04` (`FR_ECLAT_TEST_NO_TAXO`): malformed taxonomy (4 tokens instead of 6) → classified as `UNKNOWN` pending correction in Adverity.

## 3. Business Root Cause of the Nov 23 CTR Drop (`2.12% → 1.47%`)
This is **not a pipeline bug** (data quality and spend reconciliation are green), but a **media mix shift** clearly visible in Gold + SCD2:
- Surge (×2.6) in broad upper-funnel awareness impressions on **`camp_snap_eclat_02`** (`FR_ECLAT_PARFUM_AWR_UPPER_2026`, low CTR ~0.85%) on Nov 23.
- Simultaneous ~55% volume drop on high-CTR lower-funnel campaign **`camp_snap_eclat_03`** (`FR_ECLAT_SERUM_CONV_LOWER_2026`, CTR ~2.8%).
- SCD2 history confirmed on **`camp_snap_eclat_01`**, which transitioned on Nov 18 from `AWARENESS` (v1) to `CONVERSION` (v2).
