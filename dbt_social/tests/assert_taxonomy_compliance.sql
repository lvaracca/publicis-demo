{{ config(severity = 'warn') }}

-- Data Quality Check: flags campaigns violating the Publicis canonical taxonomy (6 tokens)
SELECT DISTINCT
  platform,
  client_id,
  campaign_id,
  campaign_name
FROM {{ ref('fct_social_performance_daily') }}
WHERE is_taxonomy_valid = FALSE
