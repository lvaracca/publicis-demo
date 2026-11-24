#!/usr/bin/env python3
"""
Deterministic synthetic data generator for the Publicis Media France demo.
GCP Project: publicis-demo-515613 (europe-west1)

Generates and loads into BigQuery / GCS:
  - ref.ref_fx_rates, ref.ref_media_taxonomy, ref.ref_clients_rls
  - bronze.brz_meta_ads, bronze.brz_tiktok_ads (T0: 90 days, 2 pilot clients)
  - GCS Adverity landing CSVs for Snapchat Ads:
      * 2026-11-23/snapchat_ads_2026_11_23_sample.csv (Day 0 + 4 realistic anomalies)
      * 2026-11-24/snapchat_ads_2026_11_24_v2_drift.csv (Day+1: additive column view_through_conversions)
      * 2026-11-24/snapchat_ads_2026_11_24_v2_breaking.csv (Day+1 breaking variant: swipes -> swipe_ups)
"""

from __future__ import annotations

import csv
import datetime as dt
import os
import random
from pathlib import Path
from typing import Any

from google.cloud import bigquery, storage

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "publicis-demo-515613")
REGION = os.environ.get("GCP_REGION", "europe-west1")
BUCKET_NAME = f"{PROJECT_ID}-landing"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

END_DATE = dt.date(2026, 11, 23)
START_DATE = END_DATE - dt.timedelta(days=89)  # 90 days
SNAP_START_DATE = END_DATE - dt.timedelta(days=29)  # 30 days
INGESTED_AT = "2026-11-23T06:30:00Z"

CLIENTS = {
    "maison_eclat": {
        "code": "ECLAT",
        "brands": ["SERUM", "PARFUM"],
        "meta_acc": ("act_meta_eclat_01", "Maison Eclat FR - Meta"),
        "tiktok_acc": ("act_tt_eclat_01", "Maison Eclat FR - TikTok"),
        "snap_acc": ("act_snap_eclat_01", "Maison Eclat FR - Snapchat"),
    },
    "autonova_fr": {
        "code": "AUTONOVA",
        "brands": ["HYBRID", "SUVEV"],
        "meta_acc": ("act_meta_auto_01", "AutoNova France - Meta"),
        "tiktok_acc": ("act_tt_auto_01", "AutoNova France - TikTok"),
        "snap_acc": ("act_snap_auto_01", "AutoNova France - Snapchat"),
    },
}


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_ref_tables(rng: random.Random) -> dict[str, tuple[list[str], list[dict[str, Any]]]]:
    fx_rows = []
    d = START_DATE - dt.timedelta(days=5)
    while d <= END_DATE + dt.timedelta(days=7):
        usd_rate = round(0.92 + rng.uniform(-0.008, 0.008), 4)
        gbp_rate = round(1.17 + rng.uniform(-0.01, 0.01), 4)
        fx_rows.extend([
            {"rate_date": d.isoformat(), "currency_code": "EUR", "rate_to_eur": 1.0},
            {"rate_date": d.isoformat(), "currency_code": "USD", "rate_to_eur": usd_rate},
            {"rate_date": d.isoformat(), "currency_code": "GBP", "rate_to_eur": gbp_rate},
        ])
        d += dt.timedelta(days=1)

    taxonomy_rows = [
        {"taxonomy_type": "BRAND", "code": "SERUM", "label": "Éclat Anti-Aging Serum", "client_id": "maison_eclat"},
        {"taxonomy_type": "BRAND", "code": "PARFUM", "label": "Éclat Eau de Parfum", "client_id": "maison_eclat"},
        {"taxonomy_type": "BRAND", "code": "HYBRID", "label": "AutoNova Urban Hybrid", "client_id": "autonova_fr"},
        {"taxonomy_type": "BRAND", "code": "SUVEV", "label": "AutoNova Full-Electric SUV", "client_id": "autonova_fr"},
        {"taxonomy_type": "OBJECTIVE", "code": "AWR", "label": "Awareness", "client_id": "ALL"},
        {"taxonomy_type": "OBJECTIVE", "code": "TRAF", "label": "Traffic", "client_id": "ALL"},
        {"taxonomy_type": "OBJECTIVE", "code": "CONV", "label": "Conversion", "client_id": "ALL"},
        {"taxonomy_type": "FUNNEL", "code": "UPPER", "label": "Upper Funnel", "client_id": "ALL"},
        {"taxonomy_type": "FUNNEL", "code": "MID", "label": "Mid Funnel", "client_id": "ALL"},
        {"taxonomy_type": "FUNNEL", "code": "LOWER", "label": "Lower Funnel", "client_id": "ALL"},
    ]

    rls_rows = [
        {
            "client_id": "maison_eclat",
            "user_principal": "admin@lvaracca.altostrat.com",
            "role_scope": "agency_admin",
            "is_active": True,
        },
        {
            "client_id": "autonova_fr",
            "user_principal": "admin@lvaracca.altostrat.com",
            "role_scope": "agency_admin",
            "is_active": True,
        },
        {
            "client_id": "maison_eclat",
            "user_principal": "lvaracca@gcp.altostrat.com",
            "role_scope": "agency_admin",
            "is_active": True,
        },
        {
            "client_id": "autonova_fr",
            "user_principal": "lvaracca@gcp.altostrat.com",
            "role_scope": "agency_admin",
            "is_active": True,
        },
        {
            "client_id": "maison_eclat",
            "user_principal": f"sa-talk-to-data-gold@{PROJECT_ID}.iam.gserviceaccount.com",
            "role_scope": "client_scoped_agent",
            "is_active": True,
        },
        {
            "client_id": "maison_eclat",
            "user_principal": "steward.eclat@publicismedia.fr",
            "role_scope": "client_steward",
            "is_active": True,
        },
        {
            "client_id": "autonova_fr",
            "user_principal": "steward.autonova@publicismedia.fr",
            "role_scope": "client_steward",
            "is_active": True,
        },
    ]

    return {
        "ref_fx_rates": (["rate_date", "currency_code", "rate_to_eur"], fx_rows),
        "ref_media_taxonomy": (["taxonomy_type", "code", "label", "client_id"], taxonomy_rows),
        "ref_clients_rls": (["client_id", "user_principal", "role_scope", "is_active"], rls_rows),
    }


def generate_meta_and_tiktok(rng: random.Random) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    meta_rows: list[dict[str, Any]] = []
    tiktok_rows: list[dict[str, Any]] = []

    objectives = [
        ("AWR", "UPPER", "AWARENESS", 0.011, 6.5),
        ("TRAF", "MID", "TRAFFIC", 0.019, 8.2),
        ("CONV", "LOWER", "CONVERSION", 0.026, 11.5),
    ]

    d = START_DATE
    while d <= END_DATE:
        date_str = d.isoformat()
        weekday_boost = 1.12 if d.weekday() < 5 else 0.92
        for client_id, cfg in CLIENTS.items():
            for b_idx, brand in enumerate(cfg["brands"], start=1):
                for o_idx, (obj_code, funnel, obj_full, base_ctr, base_cpm) in enumerate(objectives, start=1):
                    # --- META ADS ---
                    m_acc_id, m_acc_name = cfg["meta_acc"]
                    m_camp_id = f"camp_meta_{cfg['code'].lower()}_{b_idx}{o_idx}"
                    # Existing SCD2 history on Meta for maison_eclat camp 11 (switched on Nov 1)
                    if client_id == "maison_eclat" and b_idx == 1 and o_idx == 1 and d >= dt.date(2026, 11, 1):
                        m_camp_name = f"FR_{cfg['code']}_{brand}_TRAF_MID_2026"
                        m_obj = "TRAFFIC"
                    else:
                        m_camp_name = f"FR_{cfg['code']}_{brand}_{obj_code}_{funnel}_2026"
                        m_obj = obj_full

                    for a_idx in range(1, 4):
                        impr = int(rng.randint(18000, 48000) * weekday_boost)
                        ctr = max(0.004, base_ctr * rng.uniform(0.85, 1.15))
                        clicks = int(round(impr * ctr))
                        spend = round((impr / 1000.0) * base_cpm * rng.uniform(0.9, 1.1), 2)
                        vviews = int(impr * rng.uniform(0.22, 0.42))
                        convs = int(clicks * rng.uniform(0.03, 0.09)) if obj_code == "CONV" else int(clicks * rng.uniform(0.005, 0.02))
                        meta_rows.append({
                            "report_date": date_str,
                            "client_id": client_id,
                            "account_id": m_acc_id,
                            "account_name": m_acc_name,
                            "campaign_id": m_camp_id,
                            "campaign_name": m_camp_name,
                            "campaign_objective": m_obj,
                            "campaign_status": "ACTIVE",
                            "adset_id": f"adset_meta_{cfg['code'].lower()}_{b_idx}{o_idx}_{a_idx}",
                            "adset_name": f"{brand}_{obj_code}_AUDIENCE_{a_idx}",
                            "currency": "EUR",
                            "spend": spend,
                            "impressions": impr,
                            "link_clicks": clicks,
                            "video_views": vviews,
                            "conversions": convs,
                            "_ingested_at": INGESTED_AT,
                            "_source_file": f"gs://{BUCKET_NAME}/adverity/meta_ads/{date_str}/meta_ads.csv",
                        })

                    # --- TIKTOK ADS ---
                    t_acc_id, t_acc_name = cfg["tiktok_acc"]
                    t_camp_id = f"camp_tt_{cfg['code'].lower()}_{b_idx}{o_idx}"
                    t_camp_name = f"FR_{cfg['code']}_{brand}_{obj_code}_{funnel}_2026"
                    for a_idx in range(1, 4):
                        impr = int(rng.randint(22000, 56000) * weekday_boost)
                        ctr = max(0.005, (base_ctr * 0.92) * rng.uniform(0.85, 1.15))
                        clicks = int(round(impr * ctr))
                        spend_usd = round((impr / 1000.0) * (base_cpm * 0.95) * rng.uniform(0.9, 1.1), 2)
                        vviews = int(impr * rng.uniform(0.35, 0.60))
                        convs = int(clicks * rng.uniform(0.02, 0.07)) if obj_code == "CONV" else int(clicks * rng.uniform(0.004, 0.015))
                        tiktok_rows.append({
                            "report_date": date_str,
                            "client_id": client_id,
                            "account_id": t_acc_id,
                            "account_name": t_acc_name,
                            "campaign_id": t_camp_id,
                            "campaign_name": t_camp_name,
                            "objective_type": obj_full,
                            "campaign_status": "ACTIVE",
                            "adgroup_id": f"adgrp_tt_{cfg['code'].lower()}_{b_idx}{o_idx}_{a_idx}",
                            "adgroup_name": f"{brand}_{obj_code}_CREATIVE_{a_idx}",
                            "currency": "USD",
                            "spend": spend_usd,
                            "impressions": impr,
                            "clicks": clicks,
                            "video_play_actions": vviews,
                            "conversions": convs,
                            "_ingested_at": INGESTED_AT,
                            "_source_file": f"gs://{BUCKET_NAME}/adverity/tiktok_ads/{date_str}/tiktok_ads.csv",
                        })
        d += dt.timedelta(days=1)

    return meta_rows, tiktok_rows


def generate_snapchat_csvs(rng: random.Random) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Generates Adverity Snapchat Ads CSVs (Day 0 + Day+1 additive drift + Day+1 breaking drift).
    Includes the 4 intentional anomalies used across Acts 1-4.
    """
    j0_rows: list[dict[str, Any]] = []

    snap_specs = [
        ("maison_eclat", "camp_snap_eclat_01", "SERUM", "AWR", "UPPER", "AWARENESS", 0.024, 9.5),
        ("maison_eclat", "camp_snap_eclat_02", "PARFUM", "AWR", "UPPER", "AWARENESS", 0.014, 7.0),
        ("maison_eclat", "camp_snap_eclat_03", "SERUM", "CONV", "LOWER", "CONVERSION", 0.028, 12.0),
        ("maison_eclat", "camp_snap_eclat_04", "PARFUM", "TRAF", "MID", "TRAFFIC", 0.017, 8.0),
        ("autonova_fr", "camp_snap_auto_01", "HYBRID", "AWR", "UPPER", "AWARENESS", 0.015, 7.5),
        ("autonova_fr", "camp_snap_auto_02", "SUVEV", "CONV", "LOWER", "CONVERSION", 0.022, 10.8),
        ("autonova_fr", "camp_snap_auto_03", "HYBRID", "TRAF", "MID", "TRAFFIC", 0.018, 8.6),
    ]

    d = SNAP_START_DATE
    while d <= END_DATE:
        date_str = d.isoformat()
        for client_id, camp_id, brand, obj_code, funnel, obj_full, base_ctr, base_cpm in snap_specs:
            cfg = CLIENTS[client_id]
            acc_id, acc_name = cfg["snap_acc"]

            # ANOMALY 2 (SCD2): camp_snap_eclat_01 switches on Nov 18 from AWARENESS -> CONVERSION
            if camp_id == "camp_snap_eclat_01" and d >= dt.date(2026, 11, 18):
                camp_name = "FR_ECLAT_SERUM_CONV_LOWER_2026"
                camp_obj = "CONVERSION"
            # ANOMALY 3 (Malformed taxonomy): camp_snap_eclat_04 has 4 tokens instead of 6
            elif camp_id == "camp_snap_eclat_04":
                camp_name = "FR_ECLAT_TEST_NO_TAXO"
                camp_obj = obj_full
            else:
                camp_name = f"FR_{cfg['code']}_{brand}_{obj_code}_{funnel}_2026"
                camp_obj = obj_full

            for a_idx in range(1, 5):
                ad_squad_id = f"adsquad_{camp_id}_{a_idx:02d}"
                ad_squad_name = f"{brand}_SNAP_SQUAD_{a_idx:02d}"
                impr = rng.randint(14000, 34000)
                ctr = max(0.006, base_ctr * rng.uniform(0.92, 1.08))

                # ANOMALY 4b (Act 4 Story - CTR drop on 2026-11-23 for maison_eclat):
                # Broad upper-funnel impressions surge x2.6 on camp_snap_eclat_02 (0.85% CTR)
                # while lower-funnel retargeting volume drops on camp_snap_eclat_03
                if d == END_DATE and client_id == "maison_eclat":
                    if camp_id == "camp_snap_eclat_02":
                        impr = int(impr * 2.6)
                        ctr = 0.0085
                    elif camp_id == "camp_snap_eclat_03":
                        impr = int(impr * 0.45)

                swipes = int(round(impr * ctr))
                spend_usd = round((impr / 1000.0) * base_cpm * rng.uniform(0.92, 1.08), 2)
                spend_micro = int(round(spend_usd * 1_000_000))
                vviews = int(impr * rng.uniform(0.30, 0.55))
                purchases = int(swipes * rng.uniform(0.03, 0.08)) if camp_obj == "CONVERSION" else int(swipes * rng.uniform(0.005, 0.02))

                row = {
                    "report_date": date_str,
                    "client_id": client_id,
                    "account_id": acc_id,
                    "account_name": acc_name,
                    "campaign_id": camp_id,
                    "campaign_name": camp_name,
                    "campaign_objective": camp_obj,
                    "campaign_status": "ACTIVE",
                    "ad_squad_id": ad_squad_id,
                    "ad_squad_name": ad_squad_name,
                    "currency": "USD",
                    "spend_micro": spend_micro,
                    "impressions": impr,
                    "swipes": swipes,
                    "video_views": vviews,
                    "purchases": purchases,
                }
                j0_rows.append(row)
        d += dt.timedelta(days=1)

    # ANOMALY 1 (3 exact duplicates on 2026-11-22)
    dup_candidates = [r for r in j0_rows if r["report_date"] == "2026-11-22"][:3]
    for dup in dup_candidates:
        j0_rows.append(dict(dup))

    # ANOMALY 4a (2 impossible metric rows: impressions = 0 and swipes > 0 on 2026-11-21)
    j0_rows.append({
        "report_date": "2026-11-21",
        "client_id": "maison_eclat",
        "account_id": "act_snap_eclat_01",
        "account_name": "Maison Eclat FR - Snapchat",
        "campaign_id": "camp_snap_eclat_01",
        "campaign_name": "FR_ECLAT_SERUM_CONV_LOWER_2026",
        "campaign_objective": "CONVERSION",
        "campaign_status": "ACTIVE",
        "ad_squad_id": "adsquad_camp_snap_eclat_01_98",
        "ad_squad_name": "SERUM_SNAP_ANOMALY_98",
        "currency": "USD",
        "spend_micro": 0,
        "impressions": 0,
        "swipes": 14,
        "video_views": 0,
        "purchases": 0,
    })
    j0_rows.append({
        "report_date": "2026-11-21",
        "client_id": "autonova_fr",
        "account_id": "act_snap_auto_01",
        "account_name": "AutoNova France - Snapchat",
        "campaign_id": "camp_snap_auto_01",
        "campaign_name": "FR_AUTONOVA_HYBRID_AWR_UPPER_2026",
        "campaign_objective": "AWARENESS",
        "campaign_status": "ACTIVE",
        "ad_squad_id": "adsquad_camp_snap_auto_01_99",
        "ad_squad_name": "HYBRID_SNAP_ANOMALY_99",
        "currency": "USD",
        "spend_micro": 0,
        "impressions": 0,
        "swipes": 9,
        "video_views": 0,
        "purchases": 0,
    })

    # Day+1 (2026-11-24): Non-breaking additive schema drift (+ view_through_conversions)
    j1_date = (END_DATE + dt.timedelta(days=1)).isoformat()
    j1_drift_rows: list[dict[str, Any]] = []
    j1_breaking_rows: list[dict[str, Any]] = []

    for base_row in [r for r in j0_rows if r["report_date"] == END_DATE.isoformat()]:
        r_drift = dict(base_row)
        r_drift["report_date"] = j1_date
        r_drift["view_through_conversions"] = int(r_drift["purchases"] * rng.uniform(0.2, 0.5))
        j1_drift_rows.append(r_drift)

        r_break = dict(r_drift)
        r_break["swipe_ups"] = r_break.pop("swipes")
        j1_breaking_rows.append(r_break)

    return j0_rows, j1_drift_rows, j1_breaking_rows


def load_bq_table(
    bq: bigquery.Client,
    dataset: str,
    table: str,
    csv_path: Path,
    schema: list[bigquery.SchemaField],
    partition_field: str | None = None,
    clustering_fields: list[str] | None = None,
    require_partition_filter: bool = False,
    labels: dict[str, str] | None = None,
    description: str = "",
) -> int:
    table_id = f"{PROJECT_ID}.{dataset}.{table}"
    bq.delete_table(table_id, not_found_ok=True)

    tbl = bigquery.Table(table_id, schema=schema)
    tbl.description = description
    if partition_field:
        tbl.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field=partition_field,
        )
        tbl.require_partition_filter = require_partition_filter
    if clustering_fields:
        tbl.clustering_fields = clustering_fields
    if labels:
        tbl.labels = labels

    bq.create_table(tbl)

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        labels={"datacloud": "antigravity", "env": "dev", "domain": "social", "data_product": f"seed_{table}"},
    )
    with csv_path.open("rb") as f:
        job = bq.load_table_from_file(f, table_id, location=REGION, job_config=job_config)
    job.result()
    dest = bq.get_table(table_id)
    return dest.num_rows


def upload_to_gcs(gcs: storage.Client, local_path: Path, blob_name: str) -> str:
    bucket = gcs.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(str(local_path), content_type="text/csv")
    return f"gs://{BUCKET_NAME}/{blob_name}"


def main() -> None:
    rng = random.Random(42)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    bq = bigquery.Client(project=PROJECT_ID, location=REGION)
    gcs = storage.Client(project=PROJECT_ID)

    print(f"=== Generating Publicis Media France demo data ({PROJECT_ID} / {REGION}) ===")

    # 1. Reference tables
    refs = generate_ref_tables(rng)
    ref_schemas = {
        "ref_fx_rates": [
            bigquery.SchemaField("rate_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("currency_code", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("rate_to_eur", "FLOAT64", mode="REQUIRED"),
        ],
        "ref_media_taxonomy": [
            bigquery.SchemaField("taxonomy_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("code", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("label", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("client_id", "STRING", mode="REQUIRED"),
        ],
        "ref_clients_rls": [
            bigquery.SchemaField("client_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_principal", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("role_scope", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("is_active", "BOOL", mode="REQUIRED"),
        ],
    }
    for name, (fields, rows) in refs.items():
        p = DATA_DIR / f"{name}.csv"
        write_csv(p, fields, rows)
        n = load_bq_table(
            bq, "ref", name, p, ref_schemas[name],
            labels={"env": "dev", "domain": "social", "layer": "ref", "managed_by": "terraform"},
            description=f"Publicis Media France canonical reference table - {name}",
        )
        print(f"  [BQ] ref.{name}: {n} rows")

    # 2. Bronze T0: Meta Ads & TikTok Ads
    meta_rows, tiktok_rows = generate_meta_and_tiktok(rng)

    meta_fields = [
        "report_date", "client_id", "account_id", "account_name", "campaign_id",
        "campaign_name", "campaign_objective", "campaign_status", "adset_id", "adset_name",
        "currency", "spend", "impressions", "link_clicks", "video_views", "conversions",
        "_ingested_at", "_source_file",
    ]
    meta_csv = DATA_DIR / "brz_meta_ads.csv"
    write_csv(meta_csv, meta_fields, meta_rows)
    meta_schema = [
        bigquery.SchemaField("report_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("client_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("account_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("account_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("campaign_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("campaign_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("campaign_objective", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("campaign_status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("adset_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("adset_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("currency", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("spend", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("impressions", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("link_clicks", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("video_views", "INT64", mode="NULLABLE"),
        bigquery.SchemaField("conversions", "INT64", mode="NULLABLE"),
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_source_file", "STRING", mode="REQUIRED"),
    ]
    n_meta = load_bq_table(
        bq, "bronze", "brz_meta_ads", meta_csv, meta_schema,
        partition_field="report_date",
        clustering_fields=["client_id", "campaign_id"],
        require_partition_filter=True,
        labels={"env": "dev", "domain": "social", "source": "meta_ads", "data_product": "ingestion_meta_ads", "managed_by": "terraform"},
        description="Meta Ads raw daily social performance ingested from Adverity GCS landing.",
    )
    print(f"  [BQ] bronze.brz_meta_ads: {n_meta} rows (partitioned report_date, clustered client_id/campaign_id)")

    tiktok_fields = [
        "report_date", "client_id", "account_id", "account_name", "campaign_id",
        "campaign_name", "objective_type", "campaign_status", "adgroup_id", "adgroup_name",
        "currency", "spend", "impressions", "clicks", "video_play_actions", "conversions",
        "_ingested_at", "_source_file",
    ]
    tiktok_csv = DATA_DIR / "brz_tiktok_ads.csv"
    write_csv(tiktok_csv, tiktok_fields, tiktok_rows)
    tiktok_schema = [
        bigquery.SchemaField("report_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("client_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("account_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("account_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("campaign_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("campaign_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("objective_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("campaign_status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("adgroup_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("adgroup_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("currency", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("spend", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("impressions", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("clicks", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("video_play_actions", "INT64", mode="NULLABLE"),
        bigquery.SchemaField("conversions", "INT64", mode="NULLABLE"),
        bigquery.SchemaField("_ingested_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_source_file", "STRING", mode="REQUIRED"),
    ]
    n_tt = load_bq_table(
        bq, "bronze", "brz_tiktok_ads", tiktok_csv, tiktok_schema,
        partition_field="report_date",
        clustering_fields=["client_id", "campaign_id"],
        require_partition_filter=True,
        labels={"env": "dev", "domain": "social", "source": "tiktok_ads", "data_product": "ingestion_tiktok_ads", "managed_by": "terraform"},
        description="TikTok Ads raw daily social performance ingested from Adverity GCS landing.",
    )
    print(f"  [BQ] bronze.brz_tiktok_ads: {n_tt} rows (partitioned report_date, clustered client_id/campaign_id)")

    # 3. GCS Landing: Snapchat Ads Day 0 + Day+1 (Schema Drift)
    j0_rows, j1_drift_rows, j1_breaking_rows = generate_snapchat_csvs(rng)

    snap_j0_fields = [
        "report_date", "client_id", "account_id", "account_name", "campaign_id",
        "campaign_name", "campaign_objective", "campaign_status", "ad_squad_id", "ad_squad_name",
        "currency", "spend_micro", "impressions", "swipes", "video_views", "purchases",
    ]
    snap_j0_local = DATA_DIR / "snapchat_ads_2026_11_23_sample.csv"
    write_csv(snap_j0_local, snap_j0_fields, j0_rows)
    uri_j0 = upload_to_gcs(gcs, snap_j0_local, "adverity/snapchat_ads/2026-11-23/snapchat_ads_2026_11_23_sample.csv")
    print(f"  [GCS] {uri_j0} ({len(j0_rows)} rows)")

    snap_j1_drift_fields = snap_j0_fields + ["view_through_conversions"]
    snap_j1_drift_local = DATA_DIR / "snapchat_ads_2026_11_24_v2_drift.csv"
    write_csv(snap_j1_drift_local, snap_j1_drift_fields, j1_drift_rows)
    uri_j1_drift = upload_to_gcs(gcs, snap_j1_drift_local, "adverity/snapchat_ads/2026-11-24/snapchat_ads_2026_11_24_v2_drift.csv")
    print(f"  [GCS] {uri_j1_drift} ({len(j1_drift_rows)} rows — additive drift +view_through_conversions)")

    snap_j1_break_fields = [f if f != "swipes" else "swipe_ups" for f in snap_j1_drift_fields]
    snap_j1_break_local = DATA_DIR / "snapchat_ads_2026_11_24_v2_breaking.csv"
    write_csv(snap_j1_break_local, snap_j1_break_fields, j1_breaking_rows)
    uri_j1_break = upload_to_gcs(gcs, snap_j1_break_local, "adverity/snapchat_ads/2026-11-24/snapchat_ads_2026_11_24_v2_breaking.csv")
    print(f"  [GCS] {uri_j1_break} ({len(j1_breaking_rows)} rows — breaking drift swipes->swipe_ups)")

    print("=== Data generation completed successfully! ===")


if __name__ == "__main__":
    main()
