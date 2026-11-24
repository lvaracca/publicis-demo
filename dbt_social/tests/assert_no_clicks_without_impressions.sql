{{ config(severity = 'warn') }}

-- Data Quality Check: flags impossible metric rows where impressions = 0 and clicks > 0
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
