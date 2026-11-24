# Mapping Manifesto — Snapchat Ads (`bronze.brz_snapchat_ads` → Silver Core Data Model)

> Human-reviewed before dbt code generation (`AGENTS.md`).

| Source Column (`brz_snapchat_ads`) | Target Silver Column | Transformation & Cleaning Rule |
| :--- | :--- | :--- |
| `report_date` | `date_day` | Cast to `DATE`, partition filter `>= 2020-01-01` |
| *(constant)* | `platform` | `'snapchat'` |
| `client_id` | `client_id` | Advertiser identifier (clustering & Gold RLS key) |
| `account_id`, `account_name` | `account_id`, `account_name` | Direct mapping (feeds `dim_account`) |
| `campaign_id`, `campaign_name`, `campaign_objective`, `campaign_status` | Identical | Feeds `dim_campaign_scd2` (SCD Type 2) + `parse_media_taxonomy(campaign_name)` macro |
| `ad_squad_id`, `ad_squad_name` | `adset_id`, `adset_name` | Social terminology harmonization (`ad_squad` → `adset`) |
| `currency`, `spend_micro` | `source_currency`, `spend_local`, `spend_eur` | `spend_local = spend_micro / 1e6`, then `ROUND(spend_local * fx.rate_to_eur, 4)` via `ref.ref_fx_rates` |
| `impressions` | `impressions` | Cast to `INT64` |
| `swipes` | `clicks` | Social KPI harmonization (`swipes` → `clicks`, CTR numerator) |
| `video_views` | `video_views` | `COALESCE(video_views, 0)` |
| `purchases` | `conversions` | `COALESCE(purchases, 0)` |
| *(deduplication)* | Strict grain | `QUALIFY ROW_NUMBER() OVER (PARTITION BY report_date, account_id, campaign_id, ad_squad_id ORDER BY _ingested_at DESC) = 1` |
