{{
  config(
    materialized = 'incremental',
    incremental_strategy = 'insert_overwrite',
    partition_by = {
      'field': 'date_day',
      'data_type': 'date',
      'granularity': 'day'
    },
    cluster_by = ['client_id', 'platform'],
    labels = {
      'env': target.name,
      'domain': 'social',
      'layer': 'silver',
      'data_product': 'dp_social_performance',
      'managed_by': 'dbt'
    }
  )
}}

WITH unioned_staging AS (
  SELECT * FROM {{ ref('stg_meta_ads') }}
  {% if is_incremental() %}
    WHERE date_day >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  {% endif %}

  UNION ALL

  SELECT * FROM {{ ref('stg_tiktok_ads') }}
  {% if is_incremental() %}
    WHERE date_day >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  {% endif %}

  UNION ALL

  SELECT * FROM {{ ref('stg_snapchat_ads') }}
  {% if is_incremental() %}
    WHERE date_day >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  {% endif %}
),

joined_scd AS (
  SELECT
    {{ generate_surrogate_key(['u.date_day', 'u.platform', 'u.account_id', 'u.campaign_id', 'u.adset_id']) }} AS social_perf_sk,
    u.date_day,
    u.platform,
    u.client_id,
    u.account_id,
    u.account_name,
    u.campaign_id,
    COALESCE(scd.campaign_scd_sk, {{ generate_surrogate_key(['u.platform', 'u.campaign_id']) }}) AS campaign_scd_sk,
    COALESCE(scd.scd_version, 1) AS campaign_scd_version,
    u.campaign_name,
    u.campaign_objective,
    u.campaign_status,
    u.adset_id,
    u.adset_name,
    u.source_currency,
    u.spend_local,
    u.spend_eur,
    u.impressions,
    u.clicks,
    u.video_views,
    u.conversions,
    u.taxo_country,
    u.taxo_client,
    u.taxo_brand,
    u.taxo_objective,
    u.taxo_funnel,
    u.taxo_year,
    u.is_taxonomy_valid,
    (u.impressions = 0 AND u.clicks > 0) AS has_metric_anomaly,
    u._ingested_at,
    u._source_file
  FROM unioned_staging AS u
  LEFT JOIN {{ ref('dim_campaign_scd2') }} AS scd
    ON u.platform = scd.platform
    AND u.campaign_id = scd.campaign_id
    AND u.date_day >= scd.valid_from
    AND (scd.valid_to IS NULL OR u.date_day <= scd.valid_to)
)

SELECT * FROM joined_scd
