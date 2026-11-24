#!/usr/bin/env python3
"""
Creates or updates the persistent Google Cloud Conversational Analytics Data Agent
(Gemini Data Analytics API) for Publicis Media France.

Key governance guarantees:
  - Single data source: `publicis-demo-515613.gold.dp_social_performance` (NEVER Bronze or Silver).
  - Canonical CTR definition embedded in glossary terms and golden queries:
      CTR = SAFE_DIVIDE(SUM(clicks), SUM(impressions))  -- NEVER AVG(ctr)
  - Accessible directly in BigQuery Studio -> Conversational Analytics AND via API/CLI.
"""

from __future__ import annotations

import os
from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import geminidataanalytics_v1beta as gda
from google.protobuf import field_mask_pb2

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "publicis-demo-515613")
LOCATION = "global"
AGENT_ID = "publicis-social-gold-agent"

SYSTEM_INSTRUCTION = """You are the certified Paid Social Analytics Assistant for Publicis Media France.
Respond in the same language as the user's question (English by default, or French if the user writes in French), in a clear, concise, and structured manner.

STRICT GOVERNANCE RULES:
1. You query EXCLUSIVELY the certified Gold Data Product `publicis-demo-515613.gold.dp_social_performance`.
   You NEVER have access to technical Bronze (`bronze.*`) or Silver (`silver.*`) tables. If a user asks to query Bronze or Silver, politely decline and explain that Publicis Media France governance prohibits Talk-to-Data agents from reading technical layers.
2. CANONICAL KPI FORMULAS (defined once, identical to Looker Studio):
   - CTR (Click-Through Rate): ALWAYS `SAFE_DIVIDE(SUM(clicks), SUM(impressions))` (formatted as percentage with 2 decimals, e.g., 2.05%). NEVER use AVG(ctr).
   - Media Spend: `SUM(spend_eur)` in Euros (EUR).
   - CPM EUR: `SAFE_DIVIDE(SUM(spend_eur), SUM(impressions)) * 1000`.
   - CPC EUR: `SAFE_DIVIDE(SUM(spend_eur), SUM(clicks))`.
   - Conversion Rate (CVR): `SAFE_DIVIDE(SUM(conversions), SUM(clicks))`.
3. Pilot Clients:
   - `maison_eclat` ("Maison Éclat")
   - `autonova_fr` ("AutoNova France")
4. Platforms: `meta` (Meta Ads), `tiktok` (TikTok Ads), `snapchat` (Snapchat Ads).
5. Latest date in the dataset: 2026-11-23. When a user asks for "the last 7 days" or "this week", anchor relative to `MAX(date_day)` in the table.
6. Always state the analyzed date range and the canonical CTR formula used to guarantee transparency with BI teams.
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
                display_name="CTR (Click-Through Rate)",
                description="Canonical weighted click-through rate: SAFE_DIVIDE(SUM(clicks), SUM(impressions)). Never average daily ratios.",
                labels=["kpi", "social", "certified"],
            ),
            gda.GlossaryTerm(
                display_name="Spend EUR",
                description="Normalized media spend in Euros: SUM(spend_eur).",
                labels=["kpi", "finops", "certified"],
            ),
            gda.GlossaryTerm(
                display_name="CPM EUR",
                description="Cost per mille impressions in Euros: SAFE_DIVIDE(SUM(spend_eur), SUM(impressions)) * 1000.",
                labels=["kpi", "social", "certified"],
            ),
            gda.GlossaryTerm(
                display_name="CPC EUR",
                description="Cost per click in Euros: SAFE_DIVIDE(SUM(spend_eur), SUM(clicks)).",
                labels=["kpi", "social", "certified"],
            ),
        ],
        example_queries=[
            gda.ExampleQuery(
                natural_language_question="What is Maison Éclat's CTR by platform over the last 30 days?",
                sql_query=f"""
SELECT
  platform,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  ROUND(SUM(spend_eur), 2) AS spend_eur,
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
                natural_language_question="What is Maison Éclat's daily Snapchat CTR over the last 7 days?",
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
        display_name="Publicis Social Gold Agent (Certified CTR)",
        description=(
            "Publicis Media France Conversational Analytics Agent. "
            "Restricted exclusively to certified Data Product gold.dp_social_performance "
            "with canonical KPI definitions shared with Looker Studio."
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

    update_mask = field_mask_pb2.FieldMask(
        paths=["display_name", "description", "labels", "data_analytics_agent"]
    )

    try:
        client.get_data_agent(name=agent_name)
        print(f"Updating existing Data Agent: {agent_name}")
        updated = client.update_data_agent_sync(
            request=gda.UpdateDataAgentRequest(data_agent=agent, update_mask=update_mask)
        )
        print(f"Data Agent updated: {updated.name}")
    except NotFound:
        print(f"Creating new Conversational Analytics Data Agent: {agent_name}")
        try:
            created = client.create_data_agent_sync(
                request=gda.CreateDataAgentRequest(
                    parent=parent,
                    data_agent_id=AGENT_ID,
                    data_agent=agent,
                )
            )
            print(f"Data Agent created successfully: {created.name}")
        except AlreadyExists:
            updated = client.update_data_agent_sync(
                request=gda.UpdateDataAgentRequest(data_agent=agent, update_mask=update_mask)
            )
            print(f"Data Agent updated: {updated.name}")

    print(
        f"\nBigQuery Studio URL (Conversational Analytics):\n"
        f"https://console.cloud.google.com/bigquery/conversational-analytics?project={PROJECT_ID}"
    )


if __name__ == "__main__":
    main()
