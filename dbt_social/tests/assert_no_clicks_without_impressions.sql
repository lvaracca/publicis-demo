{{ config(severity = 'warn') }}

-- Contrôle Data Quality : détecte les lignes incohérentes avec impressions = 0 et clicks > 0
SELECT
  date_day,
  platform,
  client_id,
  campaign_id,
  adset_id,
  impressions,
  clicks
FROM {{ ref('fct_social_performance_daily') }}
WHERE has_metric_anomaly = TRUE
