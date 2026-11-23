# Mapping Manifesto — Snapchat Ads (`bronze.brz_snapchat_ads` → Silver Core Data Model)

> Validé par humain avant génération du code dbt (`AGENTS.md`).

| Colonne Source (`brz_snapchat_ads`) | Colonne Cible Silver | Règle de transformation & nettoyage |
| :--- | :--- | :--- |
| `report_date` | `date_day` | Cast `DATE`, filtre partition `>= 2020-01-01` |
| *(constante)* | `platform` | `'snapchat'` |
| `client_id` | `client_id` | Identifiant annonceur (clé clustering & RLS Gold) |
| `account_id`, `account_name` | `account_id`, `account_name` | Direct (alimente `dim_account`) |
| `campaign_id`, `campaign_name`, `campaign_objective`, `campaign_status` | Identique | Alimente `dim_campaign_scd2` (SCD Type 2) + macro `parse_media_taxonomy(campaign_name)` |
| `ad_squad_id`, `ad_squad_name` | `adset_id`, `adset_name` | Harmonisation terminologie Social (`ad_squad` → `adset`) |
| `currency`, `spend_micro` | `source_currency`, `spend_local`, `spend_eur` | `spend_local = spend_micro / 1e6` puis `ROUND(spend_local * fx.rate_to_eur, 4)` via `ref.ref_fx_rates` |
| `impressions` | `impressions` | Cast `INT64` |
| `swipes` | `clicks` | Harmonisation KPI Social (`swipes` → `clicks`, numérateur du CTR) |
| `video_views` | `video_views` | `COALESCE(video_views, 0)` |
| `purchases` | `conversions` | `COALESCE(purchases, 0)` |
| *(déduplication)* | Grain strict | `QUALIFY ROW_NUMBER() OVER (PARTITION BY report_date, account_id, campaign_id, ad_squad_id ORDER BY _ingested_at DESC) = 1` |
