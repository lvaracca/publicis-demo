#!/usr/bin/env python3
"""
Crée ou met à jour l'agent persistant Google Cloud Conversational Analytics
(Gemini Data Analytics API) pour Publicis Media France.

Points clés gouvernance :
  - Source unique : `publicis-demo-515613.gold.dp_social_performance` (JAMAIS Bronze ni Silver).
  - Définition canonique du CTR embarquée dans le glossaire et les golden queries :
      CTR = SAFE_DIVIDE(SUM(clicks), SUM(impressions))  -- JAMAIS AVG(ctr)
  - Visible directement dans BigQuery Studio -> Conversational Analytics ET interrogeable via API/CLI.
"""

from __future__ import annotations

import os
from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import geminidataanalytics_v1beta as gda

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "publicis-demo-515613")
LOCATION = "global"
AGENT_ID = "publicis-social-gold-agent"

SYSTEM_INSTRUCTION = """Tu es l'assistant analytique certifié Paid Social de Publicis Media France.
Réponds toujours en français, de manière claire, précise et structurée.

RÈGLES DE GOUVERNANCE STRICTES :
1. Tu interroges EXCLUSIVEMENT le Data Product certifié Gold `publicis-demo-515613.gold.dp_social_performance`.
   Tu n'as jamais accès aux tables techniques Bronze (`bronze.*`) ni Silver (`silver.*`). Si un utilisateur te demande d'interroger Bronze ou Silver, explique poliment que la politique de gouvernance Publicis interdit aux agents Talk-to-Data de lire les couches techniques.
2. FORMULES KPI CANONIQUES (définies une seule fois, identiques à Looker Studio) :
   - CTR (Taux de clic) : TOUJOURS `SAFE_DIVIDE(SUM(clicks), SUM(impressions))` (exprimé en pourcentage avec 2 décimales, ex. 1,84 %). NE JAMAIS utiliser AVG(ctr).
   - Investissement / Spend : `SUM(spend_eur)` en Euros (€).
   - CPM EUR : `SAFE_DIVIDE(SUM(spend_eur), SUM(impressions)) * 1000`.
   - CPC EUR : `SAFE_DIVIDE(SUM(spend_eur), SUM(clicks))`.
   - Taux de conversion (CVR) : `SAFE_DIVIDE(SUM(conversions), SUM(clicks))`.
3. Clients pilotes :
   - `maison_eclat` (Maison Éclat)
   - `autonova_fr` (AutoNova France)
4. Plateformes : `meta` (Meta Ads), `tiktok` (TikTok Ads), `snapchat` (Snapchat Ads).
5. Date de référence la plus récente dans le jeu de données : 2026-11-23. Si l'utilisateur demande « les 7 derniers jours » ou « cette semaine », base-toi sur la date maximale disponible dans la table (`MAX(date_day)`), par exemple `date_day BETWEEN DATE_SUB((SELECT MAX(date_day) FROM ...), INTERVAL 6 DAY) AND (SELECT MAX(date_day) FROM ...)`.
6. Indique toujours brièvement la période analysée et la formule utilisée pour le CTR afin de garantir la transparence avec les équipes BI.
"""


def build_context() -> gda.Context:
    return gda.Context(
        system_instruction=SYSTEM_INSTRUCTION,
        datasource_references=gda.DatasourceReferences(
            bq=gda.BigQueryTableReferences(
                table_references=[
                    gda.BigQueryTableReference(
                        project_id=PROJECT_ID,
                        dataset_id="gold",
                        table_id="dp_social_performance",
                    )
                ]
            )
        ),
        glossary_terms=[
            gda.GlossaryTerm(
                display_name="CTR (Taux de clic)",
                description="Taux de clic pondéré canonique : SAFE_DIVIDE(SUM(clicks), SUM(impressions)). Ne jamais moyenner des ratios journaliers.",
                labels=["kpi", "social", "certified"],
            ),
            gda.GlossaryTerm(
                display_name="Spend EUR",
                description="Investissement média normalisé en Euros : SUM(spend_eur).",
                labels=["kpi", "finops", "certified"],
            ),
            gda.GlossaryTerm(
                display_name="CPM EUR",
                description="Coût pour mille impressions en Euros : SAFE_DIVIDE(SUM(spend_eur), SUM(impressions)) * 1000.",
                labels=["kpi", "social", "certified"],
            ),
            gda.GlossaryTerm(
                display_name="CPC EUR",
                description="Coût par clic en Euros : SAFE_DIVIDE(SUM(spend_eur), SUM(clicks)).",
                labels=["kpi", "social", "certified"],
            ),
        ],
        example_queries=[
            gda.ExampleQuery(
                natural_language_question="Quel est le CTR de Maison Éclat par plateforme sur les 30 derniers jours ?",
                sql_query=f"""
SELECT
  platform,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  ROUND(SAFE_DIVIDE(SUM(spend_eur), 1), 2) AS spend_eur,
  ROUND(SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100, 2) AS ctr_pct
FROM `{PROJECT_ID}.gold.dp_social_performance`
WHERE client_id = 'maison_eclat'
  AND date_day >= DATE('2026-10-25')
  AND date_day <= DATE('2026-11-23')
GROUP BY platform
ORDER BY ctr_pct DESC
""".strip(),
            ),
            gda.ExampleQuery(
                natural_language_question="Quel est le CTR quotidien de Maison Éclat sur Snapchat sur les 7 derniers jours ?",
                sql_query=f"""
SELECT
  date_day,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  ROUND(SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100, 2) AS ctr_pct
FROM `{PROJECT_ID}.gold.dp_social_performance`
WHERE client_id = 'maison_eclat'
  AND platform = 'snapchat'
  AND date_day BETWEEN DATE('2026-11-17') AND DATE('2026-11-23')
GROUP BY date_day
ORDER BY date_day
""".strip(),
            ),
        ],
        options=gda.ConversationOptions(
            chart=gda.ChartOptions(image=gda.ChartOptions.ImageOptions(no_image={})),
        ),
    )


def main() -> None:
    client = gda.DataAgentServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"
    agent_name = f"{parent}/dataAgents/{AGENT_ID}"
    ctx = build_context()

    agent = gda.DataAgent(
        name=agent_name,
        display_name="Publicis Social Gold Agent (CTR Certifié)",
        description=(
            "Agent Conversational Analytics Publicis Media France. "
            "Accès restreint au Data Product certifié gold.dp_social_performance "
            "avec définitions KPI canoniques partagées avec Looker Studio."
        ),
        labels={
            "env": "dev",
            "domain": "social",
            "data_product": "dp_social_performance",
            "datacloud": "antigravity",
        },
        data_analytics_agent=gda.DataAnalyticsAgent(
            published_context=ctx,
        ),
    )

    try:
        client.get_data_agent(name=agent_name)
        print(f"Mise à jour de l'agent existant : {agent_name}")
        updated = client.update_data_agent_sync(
            request=gda.UpdateDataAgentRequest(data_agent=agent)
        )
        print(f"Agent mis à jour : {updated.name}")
    except NotFound:
        print(f"Création du nouvel agent Conversational Analytics : {agent_name}")
        try:
            created = client.create_data_agent_sync(
                request=gda.CreateDataAgentRequest(
                    parent=parent,
                    data_agent_id=AGENT_ID,
                    data_agent=agent,
                )
            )
            print(f"Agent créé avec succès : {created.name}")
        except AlreadyExists:
            updated = client.update_data_agent_sync(
                request=gda.UpdateDataAgentRequest(data_agent=agent)
            )
            print(f"Agent mis à jour : {updated.name}")

    print(
        f"\nURL Console BigQuery Studio (Conversational Analytics) :\n"
        f"https://console.cloud.google.com/bigquery/conversational-analytics?project={PROJECT_ID}"
    )


if __name__ == "__main__":
    main()
