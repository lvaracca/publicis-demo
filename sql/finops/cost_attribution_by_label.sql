-- FinOps & BigQuery Cost Attribution by Client, Data Product, and Agent
-- Uses mandatory labels enforced in AGENTS.md (Terraform, dbt, Conversational Analytics)

SELECT
  DATE(creation_time) AS query_date,
  (SELECT value FROM UNNEST(labels) WHERE key = 'env') AS env,
  (SELECT value FROM UNNEST(labels) WHERE key = 'domain') AS domain,
  COALESCE((SELECT value FROM UNNEST(labels) WHERE key = 'data_product'), 'ad_hoc') AS data_product,
  COALESCE((SELECT value FROM UNNEST(labels) WHERE key = 'client'), 'multi_client') AS client,
  COALESCE((SELECT value FROM UNNEST(labels) WHERE key = 'agent'), 'pipeline_or_bi') AS agent,
  COUNT(*) AS total_jobs,
  ROUND(SUM(total_bytes_billed) / POW(1024, 3), 4) AS total_gb_billed,
  -- Estimated On-Demand cost (~$6.25 / TiB in europe-west1)
  ROUND((SUM(total_bytes_billed) / POW(1024, 4)) * 6.25, 6) AS estimated_cost_usd
FROM `publicis-demo-515613`.`region-europe-west1`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY total_gb_billed DESC, total_jobs DESC
LIMIT 30;
