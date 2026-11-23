# Publicis Media France — Context Set Sémantique (Social Data Product)

Ce dossier formalise le **Context Set** (inspiré Open Knowledge Format / Dataplex Knowledge Catalog) associé au Data Product certifié `publicis-demo-515613.gold.dp_social_performance`.

Il constitue la **source de vérité unique** pour les définitions KPI partagées entre :
1. **Looker Studio** (couche BI)
2. **Conversational Analytics** (`publicis-social-gold-agent`, couche Talk-to-Data)
3. **Antigravity / Data Agent Kit** (lineage et investigations qualité)

## Règles de Gouvernance
- **Owner** : `team-data-engineering@publicismedia.fr`
- **Data Steward** : `paid-social-ops@publicismedia.fr`
- **SLA de fraîcheur** : quotidien avant 07h00 CET (max 24h)
- **Sécurité / Isolation** : Row-Level Security BigQuery active (`rls_client_isolation`) pilotée par `ref.ref_clients_rls`.
- **Règle d'Agentification** : les agents métier lisent **exclusivement** `gold.dp_social_performance` et n'ont aucun droit IAM sur `bronze.*` ni `silver.*`.

## Glossaire des KPI Canoniques (Définis une seule fois)

| KPI | Formule SQL BigQuery (Canonique) | Erreur interdite | Unité |
| :--- | :--- | :--- | :--- |
| **CTR** (Taux de clic) | `SAFE_DIVIDE(SUM(clicks), SUM(impressions))` | ❌ JAMAIS `AVG(ctr)` | Ratio (`%`, ex. `1,84 %`) |
| **Spend EUR** (Investissement) | `SUM(spend_eur)` | Ne pas mélanger `spend_local` | EUR (`€`) |
| **CPM EUR** (Coût pour mille) | `SAFE_DIVIDE(SUM(spend_eur), SUM(impressions)) * 1000` | ❌ JAMAIS `AVG(cpm)` | EUR (`€`) |
| **CPC EUR** (Coût par clic) | `SAFE_DIVIDE(SUM(spend_eur), SUM(clicks))` | ❌ JAMAIS `AVG(cpc)` | EUR (`€`) |
| **CVR** (Taux de conversion) | `SAFE_DIVIDE(SUM(conversions), SUM(clicks))` | ❌ JAMAIS `AVG(cvr)` | Ratio (`%`) |
| **CPA EUR** (Coût par acquisition) | `SAFE_DIVIDE(SUM(spend_eur), SUM(conversions))` | ❌ JAMAIS `AVG(cpa)` | EUR (`€`) |

## Règles d'interprétation métier
- **Plateformes** : `meta` (Meta Ads : Facebook/Instagram), `tiktok` (TikTok Ads), `snapchat` (Snapchat Ads, où `clicks` correspond aux `swipes` normalisés).
- **Clients pilotes** :
  - `maison_eclat` (« Maison Éclat », marques : `SERUM`, `PARFUM`)
  - `autonova_fr` (« AutoNova France », marques : `HYBRID`, `SUVEV`)
- **Historique Campagne (SCD2)** : une même `campaign_id` peut changer d'objectif (`AWARENESS` → `CONVERSION`) au fil du temps ; la colonne `campaign_scd_version` trace la version active à chaque `date_day`.
- **Anomalies exclues de Gold** : les lignes incohérentes (`impressions = 0 AND clicks > 0`) sont écartées de `gold.dp_social_performance` et tracées dans `dq_monitoring.dq_social_anomalies`.
