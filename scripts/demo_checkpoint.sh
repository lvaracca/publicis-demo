#!/usr/bin/env bash
# Utilitaire de gestion des checkpoints de la démo Publicis Media France
# Usage :
#   ./scripts/demo_checkpoint.sh status
#   ./scripts/demo_checkpoint.sh goto <step-0-baseline|step-1-snapchat-ingestion|step-2-schema-drift|step-3-silver-dbt-snapchat|step-4-dq-and-lineage|step-5-serving-complete>
#   ./scripts/demo_checkpoint.sh reset-to-t0   # Remet Git + BigQuery dans l'état T0 (Meta + TikTok uniquement, prêt pour live demo from scratch)

set -euo pipefail

PROJECT_ID="publicis-demo-515613"
REGION="europe-west1"
CMD="${1:-status}"

case "$CMD" in
  status)
    echo "=== Git Branch & Tags ==="
    git status -sb
    git tag -l 'step-*' -n1
    echo ""
    echo "=== BigQuery Tables (bronze / silver / gold) ==="
    for ds in bronze silver gold dq_monitoring; do
      echo "--- ${ds} ---"
      bq ls --project_id="$PROJECT_ID" "${PROJECT_ID}:${ds}"
    done
    ;;

  goto)
    TAG="${2:?Spécifiez un tag (ex: step-0-baseline, step-3-silver-dbt-snapchat, step-5-serving-complete)}"
    echo "Bascule sur le checkpoint Git : $TAG"
    git checkout -f "$TAG"
    ;;

  reset-to-t0)
    echo "=== Remise à zéro T0 (Meta + TikTok uniquement, avant onboarding Snapchat) ==="
    git checkout -f step-0-baseline
    bq rm -f -t "${PROJECT_ID}:bronze.brz_snapchat_ads" || true
    bq rm -f -t "${PROJECT_ID}:silver.stg_snapchat_ads" || true
    (cd dbt_social && ../.venv/bin/dbt build --profiles-dir . --full-refresh)
    echo "=== Projet prêt à T0 ! Pour revenir à l'état complet : git checkout main && ./scripts/demo_checkpoint.sh restore-full ==="
    ;;

  restore-full)
    echo "=== Restauration complète (Meta + TikTok + Snapchat + Conversational Analytics) ==="
    git checkout -f main
    bq query --project_id="$PROJECT_ID" --location="$REGION" --use_legacy_sql=false \
      --label datacloud:antigravity --label env:dev --label domain:social --label data_product:ingestion_snapchat_ads \
      < sql/ingestion/load_brz_snapchat_ads.sql
    bq query --project_id="$PROJECT_ID" --location="$REGION" --use_legacy_sql=false --label datacloud:antigravity \
      "ALTER TABLE \`${PROJECT_ID}.bronze.brz_snapchat_ads\` ADD COLUMN IF NOT EXISTS view_through_conversions INT64;"
    (cd dbt_social && ../.venv/bin/dbt build --profiles-dir . --full-refresh)
    .venv/bin/python conversational_analytics/setup_agent.py
    echo "=== Restauration complète terminée ! ==="
    ;;

  *)
    echo "Commande inconnue : $CMD"
    echo "Usage : $0 {status|goto <tag>|reset-to-t0|restore-full}"
    exit 1
    ;;
esac
