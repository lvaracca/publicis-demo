# Looker Studio Setup Guide (Act 5 — Unified BI Serving on the Gold Layer)

> **Setup time: 2 minutes** (create once before the workshop and bookmark the Looker Studio report).

## 1. Direct Connection to the Certified Gold Data Product (1-Click)

Open this link while signed in as `admin@lvaracca.altostrat.com` (or create a BigQuery data source pointing to `publicis-demo-515613 → gold → dp_social_performance`):

- **Direct Looker Studio Data Source URL**:
  `https://lookerstudio.google.com/datasources/create?connectorId=BIG_QUERY&projectId=publicis-demo-515613&datasetId=gold&tableId=dp_social_performance`

> **Security / RLS Note**: in the Looker Studio data source settings, select **Viewer's credentials** so BigQuery **Row-Level Security** (`rls_client_isolation`) automatically applies to each business user or client!

## 2. Canonical Calculated Fields (Identical to Conversational Analytics)

Add these 3 calculated fields in the Looker Studio data source (matching `context_bundle/social_kpis.context.md` and the Conversational Analytics agent word-for-word):

| Field Name | Looker Studio Formula | Type / Format |
| :--- | :--- | :--- |
| **`CTR`** | `SUM(clicks) / SUM(impressions)` | Percent (`0.00%`) |
| **`CPM EUR`** | `(SUM(spend_eur) / SUM(impressions)) * 1000` | Currency (`EUR`) |
| **`CPC EUR`** | `SUM(spend_eur) / SUM(clicks)` | Currency (`EUR`) |

> **Key Teaching Point**: `CTR` is defined as an **aggregated ratio** (`SUM(clicks) / SUM(impressions)`), never an average of daily ratios (`AVG`), guaranteeing **zero discrepancy** between Looker Studio and Conversational Analytics.

## 3. Recommended Report Layout (Clean Single Page)

1. **Header Filter Controls**:
   - Date range control: default to **`Oct 25, 2026` – `Nov 23, 2026`** (the 30-day Snapchat window).
   - Filter control on `client_name` (select **`Maison Éclat`** during Act 5).
   - Filter control on `platform`.
2. **KPI Scorecards**: `Spend EUR` (`SUM(spend_eur)`), `Impressions`, `Clicks`, **`CTR`**.
3. **Platform Comparison Table** (`platform` dimension; `Impressions`, `Clicks`, `Spend EUR`, **`CTR`** metrics):
   - Expected reference numbers for **Maison Éclat (Oct 25 – Nov 23, 2026)**:
     - **`snapchat`**: **`2.05%`** (`238,558` clicks / `11,618,756` impressions, `€97,185.08`)
     - **`meta`**: **`1.88%`** (`355,215` clicks / `18,926,462` impressions, `€165,435.20`)
     - **`tiktok`**: **`1.72%`** (`386,728` clicks / `22,488,582` impressions, `€172,823.27`)
4. **Daily CTR Time-Series Chart** (`date_day` X-axis, `platform` breakdown dimension, `CTR` metric):
   - Clearly highlights Maison Éclat's Snapchat CTR drop on **Nov 23, 2026** (`2.12%` → **`1.47%`**) investigated in Act 4!
