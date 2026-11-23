# Investigation Lineage & Qualité — « D'où vient ce chiffre ? » (Acte 4)

## Question métier posée
> *« Le CTR Snapchat de Maison Éclat a fortement chuté le 23 novembre 2026 (de 2,12 % le 22/11 à 1,47 % le 23/11, soit -30,7 %). D'où vient exactement ce chiffre, quelles tables/colonnes l'alimentent, et qu'est-ce qui explique la baisse ? »*

## 1. Lineage colonne par colonne (Gold → Silver → Bronze → GCS)

```text
gs://publicis-demo-515613-landing/adverity/snapchat_ads/2026-11-23/snapchat_ads_2026_11_23_sample.csv
  │  (col: swipes, impressions, spend_micro, currency, campaign_name, ad_squad_id)
  ▼
bronze.brz_snapchat_ads                         [Partition: report_date | Cluster: client_id, campaign_id]
  │  (845 lignes brutes dont 3 doublons le 22/11 + 2 anomalies impressions=0 le 21/11)
  ▼
silver.stg_snapchat_ads                         [dbt view]
  │  • swipes               ──► clicks
  │  • impressions          ──► impressions
  │  • spend_micro / 1e6 × ref.ref_fx_rates.rate_to_eur ──► spend_eur
  │  • parse_media_taxonomy(campaign_name) ──► taxo_brand, taxo_objective, taxo_funnel, is_taxonomy_valid
  │  • QUALIFY ROW_NUMBER() = 1 (élimine les 3 doublons bruts -> 842 lignes uniques)
  ▼
silver.fct_social_performance_daily             [dbt incremental insert_overwrite + Grain Test PASS]
  │  • Jointure temporelle sur silver.dim_campaign_scd2 (historique SCD2)
  │  • Flag has_metric_anomaly = (impressions = 0 AND clicks > 0)
  ▼
gold.dp_social_performance                      [Data Product Certifié + BigQuery RLS par client_id]
  │  • Filtre WHERE has_metric_anomaly = FALSE (écarte les 2 lignes corrompues vers dq_monitoring)
  │  • KPI canonique : CTR = SAFE_DIVIDE(SUM(clicks), SUM(impressions))
  ▼
Serving Unifié : Looker Studio  ===  Conversational Analytics (`publicis-social-gold-agent`)
```

## 2. Diagnostic Data Quality (contrôles automatisés)
- **Fraîcheur (`dbt source freshness`)** : ✅ PASS sur Meta, TikTok, Snapchat (< 24h).
- **Grain & Doublons (`unique_combination_of_columns`)** : ✅ PASS en Silver (les 3 doublons du 22/11 détectés en Bronze sont dédupliqués proprement).
- **Réconciliation financière (`assert_reconcile_bronze_silver_spend`)** : ✅ PASS (écart = `0,00 €` entre Bronze et Silver sur les 3 plateformes).
- **Anomalies tracées dans `dq_monitoring.dq_social_anomalies`** (⚠️ 2 tests WARN) :
  1. `2026-11-21` : 2 lignes avec `impressions = 0` et `swipes > 0` (`maison_eclat` + `autonova_fr`) — écartées automatiquement de Gold.
  2. `camp_snap_eclat_04` (`FR_ECLAT_TEST_NO_TAXO`) : taxonomie non conforme (4 segments au lieu de 6) → classée `UNKNOWN` en attendant correction dans Adverity.

## 3. Cause racine métier de la baisse du CTR du 23/11 (`2,12 % → 1,47 %`)
Ce n'est **pas un bug pipeline** (qualité & réconciliation OK), mais un **changement de mix média** clairement visible en Gold + SCD2 :
- Explosion du volume d'impressions upper-funnel broad sur **`camp_snap_eclat_02`** (`FR_ECLAT_PARFUM_AWR_UPPER_2026`, CTR ~0,85 %) qui a multiplié ses impressions par ×2,6 le 23/11.
- Simultanément, baisse de volume (~-55 %) sur la campagne lower-funnel à fort CTR **`camp_snap_eclat_03`** (`FR_ECLAT_SERUM_CONV_LOWER_2026`, CTR ~2,8 %).
- Historique SCD2 confirmé sur **`camp_snap_eclat_01`** qui avait basculé le 18/11 de `AWARENESS` (v1) vers `CONVERSION` (v2).
