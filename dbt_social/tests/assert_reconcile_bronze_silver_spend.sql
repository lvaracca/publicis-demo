-- Test de réconciliation financière Bronze <-> Silver (tolérance 0.05 EUR par plateforme)
-- Garantit qu'aucun euro n'est perdu ou dupliqué lors de la transformation Silver.

WITH bronze_meta AS (
  SELECT
    'meta' AS platform,
    ROUND(SUM(d.spend * COALESCE(fx.rate_to_eur, 1.0)), 2) AS bronze_spend_eur
  FROM (
    SELECT report_date, account_id, campaign_id, adset_id, currency, spend
    FROM {{ source('bronze', 'brz_meta_ads') }}
    WHERE report_date >= DATE('2020-01-01')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY report_date, account_id, campaign_id, adset_id ORDER BY _ingested_at DESC) = 1
  ) AS d
  LEFT JOIN {{ source('ref', 'ref_fx_rates') }} AS fx
    ON d.report_date = fx.rate_date AND d.currency = fx.currency_code
),

bronze_tiktok AS (
  SELECT
    'tiktok' AS platform,
    ROUND(SUM(d.spend * COALESCE(fx.rate_to_eur, 1.0)), 2) AS bronze_spend_eur
  FROM (
    SELECT report_date, account_id, campaign_id, adgroup_id, currency, spend
    FROM {{ source('bronze', 'brz_tiktok_ads') }}
    WHERE report_date >= DATE('2020-01-01')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY report_date, account_id, campaign_id, adgroup_id ORDER BY _ingested_at DESC) = 1
  ) AS d
  LEFT JOIN {{ source('ref', 'ref_fx_rates') }} AS fx
    ON d.report_date = fx.rate_date AND d.currency = fx.currency_code
),

bronze_totals AS (
  SELECT * FROM bronze_meta
  UNION ALL
  SELECT * FROM bronze_tiktok
),

silver_totals AS (
  SELECT
    platform,
    ROUND(SUM(spend_eur), 2) AS silver_spend_eur
  FROM {{ ref('fct_social_performance_daily') }}
  GROUP BY 1
)

SELECT
  b.platform,
  b.bronze_spend_eur,
  s.silver_spend_eur,
  ABS(b.bronze_spend_eur - s.silver_spend_eur) AS diff_eur
FROM bronze_totals AS b
FULL OUTER JOIN silver_totals AS s
  ON b.platform = s.platform
WHERE ABS(COALESCE(b.bronze_spend_eur, 0) - COALESCE(s.silver_spend_eur, 0)) > 0.05
