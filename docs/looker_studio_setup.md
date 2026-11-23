# Configuration Looker Studio (Acte 5 — Serving BI unifié sur la couche Gold)

> **Temps de mise en place : 2 minutes** (à faire une seule fois avant l'atelier de mercredi matin, puis sauvegarder le rapport Looker Studio en favori).

## 1. Connexion directe au Data Product certifié Gold (1 clic)

Ouvrir ce lien avec le compte `admin@lvaracca.altostrat.com` (ou créer une source BigQuery sur `publicis-demo-515613 → gold → dp_social_performance`) :

- **Lien direct Data Source Looker Studio** :
  `https://lookerstudio.google.com/datasources/create?connectorId=BIG_QUERY&projectId=publicis-demo-515613&datasetId=gold&tableId=dp_social_performance`

> **Note Sécurité / RLS** : dans les paramètres de la source de données Looker Studio, choisir **Identifiants du lecteur (Viewer's credentials)** afin que la **Row-Level Security BigQuery** (`rls_client_isolation`) s'applique automatiquement à chaque utilisateur métier/client !

## 2. Champs calculés canoniques (identiques à Conversational Analytics)

Ajouter ces 3 champs calculés dans la source de données Looker Studio (exactement les mêmes formules que dans `context_bundle/social_kpis.context.md` et dans l'agent Conversational Analytics) :

| Nom du champ | Formule Looker Studio | Type / Format |
| :--- | :--- | :--- |
| **`CTR`** | `SUM(clicks) / SUM(impressions)` | Pourcentage (`0,00 %`) |
| **`CPM EUR`** | `(SUM(spend_eur) / SUM(impressions)) * 1000` | Devise (`EUR`) |
| **`CPC EUR`** | `SUM(spend_eur) / SUM(clicks)` | Devise (`EUR`) |

> **Point pédagogique clé** : montrer que `CTR` est défini comme un **ratio agrégé** (`SUM(clicks) / SUM(impressions)`) et non une moyenne de pourcentages (`AVG`), garantissant **0 écart** entre Looker Studio et Conversational Analytics.

## 3. Mise en page recommandée (1 seule page épurée)

1. **Filtres en en-tête** :
   - Sélecteur de plage de dates : fixer par défaut du **`25 oct. 2026` au `23 nov. 2026`** (les 30 jours couverts par Snapchat).
   - Contrôle de filtre sur `client_name` (sélectionner **`Maison Éclat`** pendant l'Acte 5).
   - Contrôle de filtre sur `platform`.
2. **Bandeau KPI (Scorecards)** : `Spend EUR` (`SUM(spend_eur)`), `Impressions`, `Clicks`, **`CTR`**.
3. **Tableau de comparaison par Plateforme** (`platform` en dimension ; `Impressions`, `Clicks`, `Spend EUR`, **`CTR`** en métriques) :
   - Chiffres de contrôle attendus pour **Maison Éclat (25 oct. – 23 nov. 2026)** :
     - **`snapchat`** : **`2,05 %`** (`238 558` clics / `11 618 756` impressions, `97 185,08 €`)
     - **`meta`** : **`1,88 %`** (`355 215` clics / `18 926 462` impressions, `165 435,20 €`)
     - **`tiktok`** : **`1,72 %`** (`386 728` clics / `22 488 582` impressions, `172 823,27 €`)
4. **Courbe temporelle quotidienne du `CTR`** (`date_day` en axe X, `platform` en série, `CTR` en axe Y) :
   - Permet de visualiser instantanément la chute du CTR Snapchat de Maison Éclat le **23 nov. 2026** (`2,12 %` → **`1,47 %`**) investiguée à l'Acte 4 !
