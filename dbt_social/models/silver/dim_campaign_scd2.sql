{{
  config(
    materialized = 'table',
    cluster_by = ['client_id', 'platform'],
    labels = {
      'env': target.name,
      'domain': 'social',
      'layer': 'silver',
      'managed_by': 'dbt'
    }
  )
}}

/*
  Conformed Campaign Dimension in SCD Type 2 (Slowly Changing Dimension).
  Automatically historizes any change in campaign name, objective, or status.
*/

WITH daily_campaigns AS (
  SELECT DISTINCT
    date_day, platform, client_id, account_id, campaign_id,
    campaign_name, campaign_objective, campaign_status,
    taxo_brand, taxo_objective, taxo_funnel, is_taxonomy_valid
  FROM {{ ref('stg_meta_ads') }}

  UNION ALL

  SELECT DISTINCT
    date_day, platform, client_id, account_id, campaign_id,
    campaign_name, campaign_objective, campaign_status,
    taxo_brand, taxo_objective, taxo_funnel, is_taxonomy_valid
  FROM {{ ref('stg_tiktok_ads') }}

  UNION ALL

  SELECT DISTINCT
    date_day, platform, client_id, account_id, campaign_id,
    campaign_name, campaign_objective, campaign_status,
    taxo_brand, taxo_objective, taxo_funnel, is_taxonomy_valid
  FROM {{ ref('stg_snapchat_ads') }}
),

with_changes AS (
  SELECT
    *,
    LAG(CONCAT(campaign_name, '|', campaign_objective, '|', campaign_status)) OVER (
      PARTITION BY platform, campaign_id
      ORDER BY date_day
    ) AS prev_signature,
    CONCAT(campaign_name, '|', campaign_objective, '|', campaign_status) AS curr_signature
  FROM daily_campaigns
),

versioned AS (
  SELECT
    *,
    SUM(CASE WHEN prev_signature IS NULL OR prev_signature != curr_signature THEN 1 ELSE 0 END) OVER (
      PARTITION BY platform, campaign_id
      ORDER BY date_day
    ) AS scd_version
  FROM with_changes
),

scd_ranges AS (
  SELECT
    platform,
    client_id,
    account_id,
    campaign_id,
    scd_version,
    ANY_VALUE(campaign_name) AS campaign_name,
    ANY_VALUE(campaign_objective) AS campaign_objective,
    ANY_VALUE(campaign_status) AS campaign_status,
    ANY_VALUE(taxo_brand) AS taxo_brand,
    ANY_VALUE(taxo_objective) AS taxo_objective,
    ANY_VALUE(taxo_funnel) AS taxo_funnel,
    ANY_VALUE(is_taxonomy_valid) AS is_taxonomy_valid,
    MIN(date_day) AS valid_from,
    MAX(date_day) AS last_observed_date
  FROM versioned
  GROUP BY 1, 2, 3, 4, 5
)

SELECT
  {{ generate_surrogate_key(['platform', 'campaign_id', 'scd_version']) }} AS campaign_scd_sk,
  platform,
  client_id,
  account_id,
  campaign_id,
  scd_version,
  campaign_name,
  campaign_objective,
  campaign_status,
  taxo_brand,
  taxo_objective,
  taxo_funnel,
  is_taxonomy_valid,
  valid_from,
  LEAD(DATE_SUB(valid_from, INTERVAL 1 DAY)) OVER (
    PARTITION BY platform, campaign_id
    ORDER BY scd_version
  ) AS valid_to,
  (LEAD(valid_from) OVER (PARTITION BY platform, campaign_id ORDER BY scd_version) IS NULL) AS is_current
FROM scd_ranges
