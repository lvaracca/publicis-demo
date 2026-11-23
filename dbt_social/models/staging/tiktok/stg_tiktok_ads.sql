{{
  config(
    materialized = 'view',
    labels = {
      'env': target.name,
      'domain': 'social',
      'source': 'tiktok_ads',
      'managed_by': 'dbt'
    }
  )
}}

WITH source_raw AS (
  SELECT
    report_date,
    client_id,
    account_id,
    account_name,
    campaign_id,
    campaign_name,
    objective_type AS campaign_objective,
    campaign_status,
    adgroup_id AS adset_id,
    adgroup_name AS adset_name,
    currency,
    CAST(spend AS FLOAT64) AS spend_local,
    CAST(impressions AS INT64) AS impressions,
    CAST(clicks AS INT64) AS clicks,
    CAST(COALESCE(video_play_actions, 0) AS INT64) AS video_views,
    CAST(COALESCE(conversions, 0) AS INT64) AS conversions,
    _ingested_at,
    _source_file
  FROM {{ source('bronze', 'brz_tiktok_ads') }}
  WHERE report_date >= DATE('2020-01-01')
),

deduplicated AS (
  SELECT *
  FROM source_raw
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY report_date, account_id, campaign_id, adset_id
    ORDER BY _ingested_at DESC
  ) = 1
)

SELECT
  d.report_date AS date_day,
  'tiktok' AS platform,
  d.client_id,
  d.account_id,
  d.account_name,
  d.campaign_id,
  d.campaign_name,
  d.campaign_objective,
  d.campaign_status,
  d.adset_id,
  d.adset_name,
  d.currency AS source_currency,
  d.spend_local,
  ROUND(d.spend_local * COALESCE(fx.rate_to_eur, 1.0), 4) AS spend_eur,
  d.impressions,
  d.clicks,
  d.video_views,
  d.conversions,
  {{ parse_media_taxonomy('d.campaign_name') }},
  d._ingested_at,
  d._source_file
FROM deduplicated AS d
LEFT JOIN {{ source('ref', 'ref_fx_rates') }} AS fx
  ON d.report_date = fx.rate_date
  AND d.currency = fx.currency_code
