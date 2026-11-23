-- Ingestion as Code — Snapchat Ads (GCS Adverity Landing -> BigQuery Bronze)
-- Généré depuis contracts/snapchat_ads.contract.yaml (v1.0.0)
-- Idempotent : crée la table partitionnée/clusterisée avec labels FinOps puis charge l'échantillon.

DECLARE min_dt DATE;
DECLARE max_dt DATE;

CREATE TABLE IF NOT EXISTS `publicis-demo-515613.bronze.brz_snapchat_ads` (
  report_date DATE NOT NULL OPTIONS(description="Date de diffusion quotidienne"),
  client_id STRING NOT NULL OPTIONS(description="Identifiant annonceur Publicis"),
  account_id STRING NOT NULL OPTIONS(description="ID compte publicitaire Snapchat"),
  account_name STRING NOT NULL OPTIONS(description="Nom du compte Snapchat"),
  campaign_id STRING NOT NULL OPTIONS(description="ID campagne Snapchat"),
  campaign_name STRING NOT NULL OPTIONS(description="Nom campagne (taxonomie Publicis)"),
  campaign_objective STRING NOT NULL OPTIONS(description="Objectif campagne"),
  campaign_status STRING NOT NULL OPTIONS(description="Statut campagne"),
  ad_squad_id STRING NOT NULL OPTIONS(description="ID Ad Squad"),
  ad_squad_name STRING NOT NULL OPTIONS(description="Nom Ad Squad"),
  currency STRING NOT NULL OPTIONS(description="Devise source (USD)"),
  spend_micro INT64 NOT NULL OPTIONS(description="Dépense en micro-devises (diviser par 1e6)"),
  impressions INT64 NOT NULL OPTIONS(description="Nombre d'impressions"),
  swipes INT64 NOT NULL OPTIONS(description="Nombre de swipes (clics)"),
  video_views INT64 OPTIONS(description="Nombre de vues vidéo"),
  purchases INT64 OPTIONS(description="Nombre d'achats"),
  _ingested_at TIMESTAMP NOT NULL OPTIONS(description="Horodatage technique d'ingestion"),
  _source_file STRING NOT NULL OPTIONS(description="URI GCS du fichier Adverity")
)
PARTITION BY report_date
CLUSTER BY client_id, campaign_id
OPTIONS(
  description="Snapchat Ads raw daily social performance ingested from Adverity GCS landing.",
  require_partition_filter=true,
  partition_expiration_days=730,
  labels=[("env", "dev"), ("domain", "social"), ("source", "snapchat_ads"), ("data_product", "ingestion_snapchat_ads"), ("managed_by", "terraform")]
);

-- Chargement de staging depuis le fichier CSV GCS (Adverity)
LOAD DATA OVERWRITE `publicis-demo-515613.bronze._stg_load_snapchat_ads` (
  report_date DATE,
  client_id STRING,
  account_id STRING,
  account_name STRING,
  campaign_id STRING,
  campaign_name STRING,
  campaign_objective STRING,
  campaign_status STRING,
  ad_squad_id STRING,
  ad_squad_name STRING,
  currency STRING,
  spend_micro INT64,
  impressions INT64,
  swipes INT64,
  video_views INT64,
  purchases INT64
)
FROM FILES (
  format = 'CSV',
  skip_leading_rows = 1,
  uris = ['gs://publicis-demo-515613-landing/adverity/snapchat_ads/2026-11-23/snapchat_ads_2026_11_23_sample.csv']
);

-- Insertion idempotente avec variables de partition (respecte require_partition_filter = true / FinOps)
SET (min_dt, max_dt) = (
  SELECT AS STRUCT MIN(report_date), MAX(report_date)
  FROM `publicis-demo-515613.bronze._stg_load_snapchat_ads`
);

DELETE FROM `publicis-demo-515613.bronze.brz_snapchat_ads`
WHERE report_date BETWEEN min_dt AND max_dt;

INSERT INTO `publicis-demo-515613.bronze.brz_snapchat_ads`
SELECT
  report_date,
  client_id,
  account_id,
  account_name,
  campaign_id,
  campaign_name,
  campaign_objective,
  campaign_status,
  ad_squad_id,
  ad_squad_name,
  currency,
  spend_micro,
  impressions,
  swipes,
  video_views,
  purchases,
  CURRENT_TIMESTAMP() AS _ingested_at,
  'gs://publicis-demo-515613-landing/adverity/snapchat_ads/2026-11-23/snapchat_ads_2026_11_23_sample.csv' AS _source_file
FROM `publicis-demo-515613.bronze._stg_load_snapchat_ads`;

DROP TABLE IF EXISTS `publicis-demo-515613.bronze._stg_load_snapchat_ads`;
