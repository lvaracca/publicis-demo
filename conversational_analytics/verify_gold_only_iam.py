#!/usr/bin/env python3
"""
Live proof (Act 5) of Publicis Media France security & governance controls:
KEYLESS impersonation (zero JSON keys) of Service Account `sa-talk-to-data-gold`:

  1. Read `gold.dp_social_performance`          -> ALLOWED + RLS enforced (sees `maison_eclat` ONLY, 0 `autonova_fr` rows)
  2. Read `silver.fct_social_performance_daily` -> BLOCKED (403 Access Denied)
  3. Read `bronze.brz_meta_ads`                 -> BLOCKED (403 Access Denied)
"""

from __future__ import annotations

import os
import google.auth
from google.auth import impersonated_credentials
from google.api_core.exceptions import Forbidden
from google.cloud import bigquery

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "publicis-demo-515613")
REGION = "europe-west1"
SA_EMAIL = f"sa-talk-to-data-gold@{PROJECT_ID}.iam.gserviceaccount.com"


def main() -> None:
    source_creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    target_creds = impersonated_credentials.Credentials(
        source_credentials=source_creds,
        target_principal=SA_EMAIL,
        target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
        lifetime=300,
    )
    bq = bigquery.Client(project=PROJECT_ID, location=REGION, credentials=target_creds)

    print(f"=== Keyless IAM + RLS Verification as {SA_EMAIL} ===\n")

    # Test 1: Gold + RLS
    print("1) Querying GOLD (`gold.dp_social_performance`):")
    q_gold = f"""
      SELECT
        client_id,
        platform,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        ROUND(SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100, 2) AS ctr_pct
      FROM `{PROJECT_ID}.gold.dp_social_performance`
      WHERE date_day BETWEEN DATE('2026-10-25') AND DATE('2026-11-23')
      GROUP BY client_id, platform
      ORDER BY client_id, platform
    """
    job_cfg = bigquery.QueryJobConfig(
        labels={
            "datacloud": "antigravity",
            "env": "dev",
            "client": "maison_eclat",
            "data_product": "dp_social_performance",
            "agent": "talk_to_data_gold",
        }
    )
    rows = list(bq.query(q_gold, job_config=job_cfg).result())
    clients_seen = sorted({r.client_id for r in rows})
    print(f"   [OK] Access allowed. Clients visible via RLS: {clients_seen}")
    for r in rows:
        print(f"        - {r.client_id:14s} | {r.platform:8s} | impr={r.impressions:9d} | clicks={r.clicks:7d} | CTR={r.ctr_pct:.2f}%")
    assert clients_seen == ["maison_eclat"], f"Expected RLS to expose maison_eclat only, got: {clients_seen}"
    print("   [OK] Client isolation verified: 0 rows of autonova_fr visible!\n")

    # Test 2: Silver (must be denied)
    print("2) Attempting read on SILVER (`silver.fct_social_performance_daily`):")
    try:
        list(bq.query(f"SELECT COUNT(*) FROM `{PROJECT_ID}.silver.fct_social_performance_daily`").result())
        raise RuntimeError("ERROR: agent must NOT be able to read Silver!")
    except Forbidden as exc:
        print(f"   [BLOCKED - EXPECTED 403] {str(exc).splitlines()[0]}\n")

    # Test 3: Bronze (must be denied)
    print("3) Attempting read on BRONZE (`bronze.brz_meta_ads`):")
    try:
        list(bq.query(f"SELECT COUNT(*) FROM `{PROJECT_ID}.bronze.brz_meta_ads` WHERE report_date = DATE('2026-11-23')").result())
        raise RuntimeError("ERROR: agent must NOT be able to read Bronze!")
    except Forbidden as exc:
        print(f"   [BLOCKED - EXPECTED 403] {str(exc).splitlines()[0]}\n")

    print("=== ALL GOVERNANCE & SECURITY CONTROLS VERIFIED ===")


if __name__ == "__main__":
    main()
