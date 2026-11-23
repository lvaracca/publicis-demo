{{
  config(
    materialized = 'table',
    labels = {
      'env': target.name,
      'domain': 'social',
      'layer': 'silver',
      'managed_by': 'dbt'
    }
  )
}}

WITH unioned AS (
  SELECT platform, client_id, account_id, account_name, MAX(date_day) AS last_seen_date
  FROM {{ ref('stg_meta_ads') }}
  GROUP BY 1, 2, 3, 4

  UNION ALL

  SELECT platform, client_id, account_id, account_name, MAX(date_day) AS last_seen_date
  FROM {{ ref('stg_tiktok_ads') }}
  GROUP BY 1, 2, 3, 4

  UNION ALL

  SELECT platform, client_id, account_id, account_name, MAX(date_day) AS last_seen_date
  FROM {{ ref('stg_snapchat_ads') }}
  GROUP BY 1, 2, 3, 4
)

SELECT
  {{ generate_surrogate_key(['platform', 'account_id']) }} AS account_sk,
  platform,
  client_id,
  account_id,
  account_name,
  last_seen_date
FROM unioned
QUALIFY ROW_NUMBER() OVER (PARTITION BY platform, account_id ORDER BY last_seen_date DESC) = 1
