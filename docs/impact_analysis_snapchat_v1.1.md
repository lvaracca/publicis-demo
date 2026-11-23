# Analyse d'impact Schema Drift — Snapchat Ads (`v1.0.0` → `v1.1.0`)

## Écart détecté (CI/CD Data Contract Check)
- **Fichier source** : `gs://publicis-demo-515613-landing/adverity/snapchat_ads/2026-11-24/snapchat_ads_2026_11_24_v2_drift.csv`
- **Contrat de référence** : `contracts/snapchat_ads.contract.yaml` (`v1.0.0`)
- **Classification** : `NON_BREAKING_ADDITIVE` (ajout d'une colonne nullable `view_through_conversions: INT64`)
- **Clé primaire impactée ?** : Non (`[report_date, account_id, campaign_id, ad_squad_id]` intacte)

## Matrice d'impact de bout en bout (avant exécution)

| Couche | Asset impacté | Nature de l'impact | Action requise |
| :--- | :--- | :--- | :--- |
| **Data Contract** | `contracts/snapchat_ads.contract.yaml` | Évolution mineure `1.0.0 → 1.1.0` | Ajouter `view_through_conversions` (NULLABLE) via PR |
| **Terraform / Bronze** | `bronze.brz_snapchat_ads` | Ajout de colonne nullable rétrocompatible | `ALTER TABLE ADD COLUMN IF NOT EXISTS` / `terraform apply` |
| **Silver (dbt)** | `stg_snapchat_ads`, `fct_social_performance_daily` | **Aucun risque de casse** (column pruning explicite dans `stg_snapchat_ads`, jamais de `SELECT *`) | Optionnel : exposer en backlog Silver si demandé par les métiers |
| **Gold / BI / Agent** | `gold.dp_social_performance`, Looker Studio, Conversational Analytics | **Zéro impact** sur le CTR ni sur la RLS | Aucune action immédiate |

> **Variante Breaking (`snapchat_ads_2026_11_24_v2_breaking.csv`)** : si Adverity renommait `swipes → swipe_ups`, le contrôle `check_schema_drift.py` retourne un `exit code 1` (`BREAKING`), bloque le chargement avant Bronze, et alerte le Data Steward avant que `stg_snapchat_ads` et le KPI `CTR` ne cassent en production.
