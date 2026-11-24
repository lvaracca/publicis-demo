# Publicis Media France — Semantic Context Set (Social Data Product)

This folder defines the **Semantic Context Set** (Open Knowledge Format / Dataplex Knowledge Catalog style) attached to the certified Data Product `publicis-demo-515613.gold.dp_social_performance`.

It serves as the **single source of truth** for KPI definitions shared across:
1. **Looker Studio** (BI serving layer)
2. **Conversational Analytics** (`publicis-social-gold-agent`, Talk-to-Data layer)
3. **Antigravity / Data Agent Kit** (column-level lineage and quality investigations)

## Governance Rules
- **Owner**: `team-data-engineering@publicismedia.fr`
- **Data Steward**: `paid-social-ops@publicismedia.fr`
- **Freshness SLA**: daily by 07:00 CET (max 24 hours)
- **Security / Client Isolation**: BigQuery Row-Level Security (`rls_client_isolation`) driven by `ref.ref_clients_rls`.
- **Agentification Rule**: business agents query `gold.dp_social_performance` **exclusively** and have zero IAM permissions on `bronze.*` or `silver.*`.

## Canonical KPI Glossary (Defined Once, Served Everywhere)

| KPI | Canonical BigQuery SQL Formula | Forbidden Anti-Pattern | Unit |
| :--- | :--- | :--- | :--- |
| **CTR** (Click-Through Rate) | `SAFE_DIVIDE(SUM(clicks), SUM(impressions))` | ❌ NEVER `AVG(ctr)` | Ratio (`%`, e.g., `2.05%`) |
| **Spend EUR** (Media Spend) | `SUM(spend_eur)` | Do not mix `spend_local` | EUR (`€`) |
| **CPM EUR** (Cost per Mille) | `SAFE_DIVIDE(SUM(spend_eur), SUM(impressions)) * 1000` | ❌ NEVER `AVG(cpm)` | EUR (`€`) |
| **CPC EUR** (Cost per Click) | `SAFE_DIVIDE(SUM(spend_eur), SUM(clicks))` | ❌ NEVER `AVG(cpc)` | EUR (`€`) |
| **CVR** (Conversion Rate) | `SAFE_DIVIDE(SUM(conversions), SUM(clicks))` | ❌ NEVER `AVG(cvr)` | Ratio (`%`) |
| **CPA EUR** (Cost per Acquisition) | `SAFE_DIVIDE(SUM(spend_eur), SUM(conversions))` | ❌ NEVER `AVG(cpa)` | EUR (`€`) |

## Business Interpretation Rules
- **Platforms**: `meta` (Meta Ads: Facebook/Instagram), `tiktok` (TikTok Ads), `snapchat` (Snapchat Ads, where `clicks` maps to normalized `swipes`).
- **Pilot Clients**:
  - `maison_eclat` ("Maison Éclat", brands: `SERUM`, `PARFUM`)
  - `autonova_fr` ("AutoNova France", brands: `HYBRID`, `SUVEV`)
- **Campaign History (SCD2)**: a single `campaign_id` can change objective (`AWARENESS` → `CONVERSION`) over time; `campaign_scd_version` tracks the active version on each `date_day`.
- **Anomalies Excluded from Gold**: impossible metric rows (`impressions = 0 AND clicks > 0`) are filtered out of `gold.dp_social_performance` and logged in `dq_monitoring.dq_social_anomalies`.
