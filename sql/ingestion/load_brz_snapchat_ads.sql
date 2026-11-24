-- Ingestion as Code — Snapchat Ads (Adverity GCS Landing -> BigQuery Bronze)
-- Generated from contracts/snapchat_ads.contract.yaml (v1.0.0)
-- Idempotent: creates partitioned/clustered table with FinOps labels and loads the sample file.

DECLARE min_dt DATE;
DECLARE max_dt DATE;

CREATE TABLE IF NOT EXISTS `publicis-demo-515613.bronze.brz_snapchat_ads` (
  report_date DATE NOT NULL OPTIONS(description="Daily delivery date"),
  client_id STRING NOT NULL OPTIONS(description="Publicis advertiser identifier"),
  account_id STRING NOT NULL OPTIONS(description="Snapchat ad account ID"),
  account_name STRING NOT NULL OPTIONS(description="Snapchat ad account name"),
  campaign_id STRING NOT NULL OPTIONS(description="Snapchat campaign ID"),
  campaign_name STRING NOT NULL OPTIONS(description="Campaign name (Publicis taxonomy)"),
  campaign_objective STRING NOT NULL OPTIONS(description="Campaign objective"),
  campaign_status STRING NOT NULL OPTIONS(description="Campaign status"),
  ad_squad_id STRING NOT NULL OPTIONS(description="Ad Squad ID"),
  ad_squad_name STRING NOT NULL OPTIONS(description="Ad Squad name"),
  currency STRING NOT NULL OPTIONS(description="Source currency (USD)"),
  spend_micro INT64 NOT NULL OPTIONS(description="Spend in micro-currency units (divide by 1e6)"),
  impressions INT64 NOT NULL OPTIONS(description="Number of impressions"),
  swipes INT64 NOT NULL OPTIONS(description="Number of swipes (clicks)"),
  video_views INT64 OPTIONS(description="Number of video views"),
  purchases INT64 OPTIONS(description="Number of purchases"),
  _ingested_at TIMESTAMP NOT NULL OPTIONS(description="Technical Bronze ingestion timestamp"),
  _source_file STRING NOT NULL OPTIONS(description="Source Adverity GCS file URI")
)
PARTITION BY report_date
CLUSTER BY client_id, campaign_id
OPTIONS(
  description="Snapchat Ads raw daily social performance ingested from Adverity GCS landing.",
  require_partition_filter=true,
  partition_expiration_days=730,
  labels=[("env", "dev"), ("domain", "social"), ("source", "snapchat_ads"), ("data_product", "ingestion_snapchat_ads"), ("managed_by", "terraform")]
);

-- Staging load from Adverity CSV file in GCS
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

-- Idempotent partition insert using script variables (complies with require_partition_filter = true / FinOps)
SET (min_dt, max_dt) = (
  SELECT AS STRUCT MIN(report_date), MAX(report_date)
  FROM `publicis-demo-515613.bronze._stg_load_snapchat_ads`
);

DELETE FROM `publicis-demo-515613.bronze.brz_snapchat_ads`
WHERE report_date BETWEEN min_dt AND max_dt;

INSERT INTO `publicis-demo-515613.bronze.brz_snapchat_ads` (
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
  _ingested_at,
  _source_file
)
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
