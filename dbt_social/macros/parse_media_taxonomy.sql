{% macro parse_media_taxonomy(campaign_name_col) -%}
    CASE
      WHEN ARRAY_LENGTH(SPLIT({{ campaign_name_col }}, '_')) = 6 THEN SPLIT({{ campaign_name_col }}, '_')[SAFE_OFFSET(0)]
      ELSE 'UNKNOWN'
    END AS taxo_country,
    CASE
      WHEN ARRAY_LENGTH(SPLIT({{ campaign_name_col }}, '_')) = 6 THEN SPLIT({{ campaign_name_col }}, '_')[SAFE_OFFSET(1)]
      ELSE 'UNKNOWN'
    END AS taxo_client,
    CASE
      WHEN ARRAY_LENGTH(SPLIT({{ campaign_name_col }}, '_')) = 6 THEN SPLIT({{ campaign_name_col }}, '_')[SAFE_OFFSET(2)]
      ELSE 'UNKNOWN'
    END AS taxo_brand,
    CASE
      WHEN ARRAY_LENGTH(SPLIT({{ campaign_name_col }}, '_')) = 6 THEN SPLIT({{ campaign_name_col }}, '_')[SAFE_OFFSET(3)]
      ELSE 'UNKNOWN'
    END AS taxo_objective,
    CASE
      WHEN ARRAY_LENGTH(SPLIT({{ campaign_name_col }}, '_')) = 6 THEN SPLIT({{ campaign_name_col }}, '_')[SAFE_OFFSET(4)]
      ELSE 'UNKNOWN'
    END AS taxo_funnel,
    CASE
      WHEN ARRAY_LENGTH(SPLIT({{ campaign_name_col }}, '_')) = 6 THEN SPLIT({{ campaign_name_col }}, '_')[SAFE_OFFSET(5)]
      ELSE 'UNKNOWN'
    END AS taxo_year,
    (ARRAY_LENGTH(SPLIT({{ campaign_name_col }}, '_')) = 6) AS is_taxonomy_valid
{%- endmacro %}
