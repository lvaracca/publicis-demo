{{ config(severity = 'warn') }}

-- Contrôle Data Quality : détecte les campagnes ne respectant pas la taxonomie Publicis (6 segments)
SELECT DISTINCT
  platform,
  client_id,
  campaign_id,
  campaign_name
FROM {{ ref('fct_social_performance_daily') }}
WHERE is_taxonomy_valid = FALSE
