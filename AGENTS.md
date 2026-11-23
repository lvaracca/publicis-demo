# Publicis Media France — Social Data Platform (Paved Road Rules)

> **Principe d'Agentification Publicis Media France** :
> *Les agents proposent, les templates écrivent le code, un humain valide via Pull Request.*
> *Les agents métier (« Talk to Data ») lisent uniquement la couche sémantique Gold, jamais les tables techniques Bronze ou Silver.*

---

## 1. Environnement GCP cible
- **Project ID** : `publicis-demo-515613`
- **Region** : `europe-west1` (co-localisation GCS + BigQuery = 0 egress inter-régions)
- **Landing Bucket (Adverity → GCS)** : `gs://publicis-demo-515613-landing`
- **Datasets BigQuery** :
  - `ref` : référentiels canoniques (`ref_fx_rates`, `ref_media_taxonomy`, `ref_clients_rls`)
  - `bronze` : données brutes ingérées par source (`brz_<source>`)
  - `silver` : modèle canonique unifié dbt (`stg_<source>`, `dim_*_scd2`, `fct_*`)
  - `gold` : Data Products certifiés avec RLS (`dp_<product>`)
  - `dq_monitoring` : résultats des contrôles qualité et anomalies

---

## 2. Conventions de nommage obligatoires
- **Contrats** : `contracts/<source>.contract.yaml` (format ODCS v3, basé sur `templates/data_contract.odcs.yaml`)
- **Terraform Bronze** : `infra/terraform/bronze_<source>.tf` (basé sur `templates/bronze_table.tf.tmpl`)
- **SQL d'ingestion** : `sql/ingestion/load_brz_<source>.sql` (idempotent, `MERGE` ou partition overwrite, avec `_ingested_at` et `_source_file`)
- **dbt Staging** : `dbt_social/models/staging/<source>/stg_<source>.sql` (matérialisé en `view`)
- **dbt Snapshots SCD2** : `dbt_social/snapshots/snp_campaign_scd2.sql`
- **dbt Silver Facts** : `dbt_social/models/silver/fct_social_performance_daily.sql` (matérialisé en `incremental`, `insert_overwrite`)
- **dbt Gold Data Products** : `dbt_social/models/gold/dp_social_performance.sql`

---

## 3. Standards Silver Core Data Model (Social)
1. **Grain strict** : `(date_day, platform, account_id, campaign_id, adset_id)` — **test de grain obligatoire** (`unique_combination_of_columns`) sur toute table de faits Silver.
2. **Clé de substitution** : `social_perf_sk` générée par `{{ generate_surrogate_key(['date_day', 'platform', 'account_id', 'campaign_id', 'adset_id']) }}`.
3. **Normalisation monétaire EUR** : toutes les dépenses sont converties en EUR via jointure sur `ref.ref_fx_rates` (`spend_local * rate_to_eur`). Attention aux plateformes en micro-devises (ex. Snapchat `spend_micro / 1e6`).
4. **Taxonomie Média canonique** : tout `campaign_name` doit être parsé via la macro `{{ parse_media_taxonomy('campaign_name') }}` (convention `{COUNTRY}_{CLIENT}_{BRAND}_{OBJECTIVE}_{FUNNEL}_{YEAR}`). En cas d'échec de parsing, fallback `UNKNOWN` + remontée en contrôle qualité.
5. **SCD Type 2** : tout changement d'attribut campagne (nom, objectif, statut) doit être historisé dans `dim_campaign_scd2`.
6. **Déduplication** : toute couche staging déduplique sur la clé naturelle (`QUALIFY ROW_NUMBER() OVER (...) = 1`) avant Silver.

---

## 4. Standards FinOps & Performance BigQuery (obligatoires dès le design)
- **Partitionnement** : toute table Bronze/Silver/Gold de faits est partitionnée par jour (`report_date` ou `date_day`).
- **Clustering** : `CLUSTER BY client_id, platform` (ou `client_id, campaign_id` en Bronze).
- **Garde-fou scan** : `require_partition_filter = true` sur les tables Bronze volumineuses.
- **Incrémental** : `materialized='incremental'`, `incremental_strategy='insert_overwrite'` sur les faits Silver.
- **Labels obligatoires** sur chaque ressource Terraform, modèle dbt et job BigQuery :
  - `env`: `dev` | `stg` | `prod`
  - `domain`: `social`
  - `data_product`: `dp_social_performance` (ou `ingestion_<source>`)
  - `managed_by`: `terraform` | `dbt`
- **Cycle de vie GCS** : passage automatique en `NEARLINE` après 90 jours, suppression après 365 jours.

---

## 5. Sécurité, Gouvernance & Agentification
- **Keyless only** : aucune clé JSON de Service Account dans le repo ni en CI/CD (ADC / Workload Identity uniquement).
- **Moindre privilège & Isolation Client** :
  - `gold.dp_social_performance` applique une **Row Access Policy (RLS)** pilotée par `ref.ref_clients_rls`.
  - Un nouveau client s'ajoute **par configuration** (ligne dans `ref_clients_rls`), jamais par copier-coller de pipeline.
- **KPI uniques (Couche Sémantique)** :
  - `CTR = SAFE_DIVIDE(SUM(clicks), SUM(impressions))` — **JAMAIS** `AVG(ctr)`.
  - `CPM = SAFE_DIVIDE(SUM(spend_eur), SUM(impressions)) * 1000`.
  - `CPC = SAFE_DIVIDE(SUM(spend_eur), SUM(clicks))`.
- **Workflow obligatoire** : toute création ou modification passe par une branche Git (`feat/...`), validation (`terraform validate` / `dbt compile` / `dbt test`), et Pull Request revue par un humain.
