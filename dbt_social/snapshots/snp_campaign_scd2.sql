{% snapshot snp_campaign_scd2 %}

{{
  config(
    target_schema = 'silver',
    unique_key = 'campaign_natural_key',
    strategy = 'check',
    check_cols = ['campaign_name', 'campaign_objective', 'campaign_status']
  )
}}

SELECT
  CONCAT(platform, '|', campaign_id) AS campaign_natural_key,
  platform,
  client_id,
  account_id,
  campaign_id,
  campaign_name,
  campaign_objective,
  campaign_status,
  valid_from AS last_changed_date
FROM {{ ref('dim_campaign_scd2') }}
WHERE is_current = TRUE

{% endsnapshot %}
