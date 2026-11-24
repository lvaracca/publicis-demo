#!/usr/bin/env python3
"""
Checks schema drift between an incoming CSV file in GCS and its ODCS v3 Data Contract
(contracts/<source>.contract.yaml).

Automatically classifies drift into:
  - NON_BREAKING_ADDITIVE (new nullable column added)
  - BREAKING (required column removed/renamed or primary key modified)
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

import yaml
from google.cloud import storage

PROJECT_ID = "publicis-demo-515613"


def read_gcs_csv_header(gcs_uri: str) -> list[str]:
    if not gcs_uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI: {gcs_uri}")
    bucket_name, blob_path = gcs_uri[5:].split("/", 1)
    client = storage.Client(project=PROJECT_ID)
    blob = client.bucket(bucket_name).blob(blob_path)
    first_chunk = blob.download_as_bytes(start=0, end=8192).decode("utf-8")
    first_line = first_chunk.splitlines()[0]
    return next(csv.reader(io.StringIO(first_line)))


def check_drift(contract_path: Path, gcs_uri: str) -> dict:
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    contract_cols = [
        c["name"]
        for c in contract["schema"]["columns"]
        if not c["name"].startswith("_")
    ]
    pk_cols = set(contract["schema"].get("primaryKey", []))
    csv_cols = read_gcs_csv_header(gcs_uri)

    added = [c for c in csv_cols if c not in contract_cols]
    removed = [c for c in contract_cols if c not in csv_cols]
    pk_impacted = [c for c in removed if c in pk_cols]

    if removed:
        severity = "BREAKING"
        action = "BLOCK_INGESTION_AND_ALERT_STEWARD"
    elif added:
        severity = "NON_BREAKING_ADDITIVE"
        action = "PROPOSE_PR_CONTRACT_V1_1_AND_TERRAFORM"
    else:
        severity = "COMPLIANT"
        action = "PROCEED_WITH_INGESTION"

    return {
        "contract": str(contract_path),
        "contract_version": contract.get("version"),
        "gcs_file": gcs_uri,
        "status": severity,
        "recommended_action": action,
        "added_columns": added,
        "missing_columns": removed,
        "primary_key_impacted": pk_impacted,
    }


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: check_schema_drift.py <contract_yaml> <gs://bucket/path.csv>")
        sys.exit(2)
    report = check_drift(Path(sys.argv[1]), sys.argv[2])
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["status"] == "BREAKING":
        sys.exit(1)


if __name__ == "__main__":
    main()
