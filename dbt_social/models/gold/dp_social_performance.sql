{{
  config(
    materialized = 'table',
    partition_by = {
      'field': 'date_day',
      'data_type': 'date',
      'granularity': 'day'
    },
    cluster_by = ['client_id', 'platform'],
    labels = {
      'env': target.name,
      'domain': 'social',
      'layer': 'gold',
      'data_product': 'dp_social_performance',
      'certified': 'true',
      'managed_by': 'dbt'
    },
    post_hook = [
      "CREATE OR REPLACE ROW ACCESS POLICY rls_client_isolation ON {{ this }} GRANT TO ('user:admin@lvaracca.altostrat.com', 'user:lvaracca@gcp.altostrat.com', 'user:nicolas@lvaracca.altostrat.com', 'serviceAccount:sa-talk-to-data-gold@publicis-demo-515613.iam.gserviceaccount.com') FILTER USING (client_id IN (SELECT client_id FROM `publicis-demo-515613.ref.ref_clients_rls` WHERE user_principal = SESSION_USER() AND is_active = TRUE))"
    ]
  )
}}

/*
  Certified Gold Data Product: dp_social_performance
  - Single serving table for BI (Looker Studio / Power BI) and AI Agents (Conversational Analytics).
  - Automatic client isolation via Row-Level Security (ref.ref_clients_rls).
  - Canonical KPI semantic rules:
      * CTR = SAFE_DIVIDE(SUM(clicks), SUM(impressions))  -- NEVER AVG(ctr)
      * CPM = SAFE_DIVIDE(SUM(spend_eur), SUM(impressions)) * 1000
      * CPC = SAFE_DIVIDE(SUM(spend_eur), SUM(clicks))
*/

SELECT
  f.date_day,
  f.client_id,
  CASE f.client_id
    WHEN 'maison_eclat' THEN 'Maison Éclat'
    WHEN 'autonova_fr' THEN 'AutoNova France'
    ELSE f.client_id
  END AS client_name,
  f.platform,
  f.account_id,
  f.account_name,
  f.campaign_id,
  f.campaign_name,
  f.campaign_objective,
  f.campaign_scd_version,
  f.adset_id,
  f.adset_name,
  f.taxo_brand AS brand_code,
  COALESCE(tb.label, f.taxo_brand) AS brand_name,
  f.taxo_objective AS taxonomy_objective,
  f.taxo_funnel AS funnel_stage,
  f.is_taxonomy_valid,
  f.spend_eur,
  f.impressions,
  f.clicks,
  f.video_views,
  f.conversions
FROM {{ ref('fct_social_performance_daily') }} AS f
LEFT JOIN {{ source('ref', 'ref_media_taxonomy') }} AS tb
  ON tb.taxonomy_type = 'BRAND'
  AND tb.code = f.taxo_brand
WHERE f.has_metric_anomaly = FALSE
