{{
  config(
    materialized = 'table',
    labels = {
      'env': target.name,
      'domain': 'social',
      'layer': 'dq_monitoring',
      'managed_by': 'dbt'
    }
  )
}}

/*
  Centralized Data Quality observability table (dq_monitoring.dq_social_anomalies).
  Automatically surfaces anomalies detected between Bronze and Silver:
  - Impossible metric rows (impressions = 0 and clicks > 0)
  - Malformed campaign taxonomy names
*/

SELECT
  CURRENT_TIMESTAMP() AS detected_at,
  'METRIC_IMPOSSIBLE_CLICKS_WITHOUT_IMPRESSIONS' AS anomaly_type,
  'WARN' AS severity,
  platform,
  client_id,
  date_day,
  campaign_id,
  campaign_name,
  adset_id,
  CONCAT('impressions=0 but clicks=', CAST(clicks AS STRING)) AS details
FROM {{ ref('fct_social_performance_daily') }}
WHERE has_metric_anomaly = TRUE

UNION ALL

SELECT
  CURRENT_TIMESTAMP() AS detected_at,
  'TAXONOMY_MALFORMED_CAMPAIGN_NAME' AS anomaly_type,
  'WARN' AS severity,
  platform,
  client_id,
  MAX(date_day) AS date_day,
  campaign_id,
  campaign_name,
  'ALL_ADSETS' AS adset_id,
  CONCAT('Non-compliant campaign name (expected 6 underscore-delimited tokens): ', campaign_name) AS details
FROM {{ ref('fct_social_performance_daily') }}
WHERE is_taxonomy_valid = FALSE
GROUP BY 1, 2, 3, 4, 5, 7, 8, 9
