#!/usr/bin/env python3
"""
Client CLI pour interroger l'agent Google Cloud Conversational Analytics
(`publicis-social-gold-agent`) en live pendant la démo Acte 5.

Affiche :
  1. Le SQL exact généré par Conversational Analytics sur `gold.dp_social_performance`
  2. La réponse finale en français (CTR identique à Looker Studio)

Usage :
  .venv/bin/python conversational_analytics/ask_agent.py "Quel est le CTR de Maison Éclat sur Snapchat vs Meta sur les 30 derniers jours ?"
"""

from __future__ import annotations

import os
import sys
from google.cloud import geminidataanalytics_v1beta as gda

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "publicis-demo-515613")
LOCATION = "global"
AGENT_ID = "publicis-social-gold-agent"


def ask(question: str) -> None:
    client = gda.DataChatServiceClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"
    agent_name = f"{parent}/dataAgents/{AGENT_ID}"

    request = gda.ChatRequest(
        parent=parent,
        messages=[
            gda.Message(user_message=gda.UserMessage(text=question))
        ],
        data_agent_context=gda.DataAgentContext(
            data_agent=agent_name,
        ),
    )

    print(f"\n[Question] {question}")
    print(f"[Agent]    {agent_name}")
    print("-" * 72)

    generated_sqls: list[str] = []
    final_parts: list[str] = []
    suggestions: list[str] = []

    for chunk in client.chat(request=request):
        sys_msg = chunk.system_message
        if not sys_msg:
            continue

        # Capture le SQL généré par Conversational Analytics
        data_msg = getattr(sys_msg, "data", None)
        if data_msg:
            sql_candidate = getattr(data_msg, "generated_sql", None)
            if sql_candidate and sql_candidate.strip():
                generated_sqls.append(sql_candidate.strip())

        # Capture les blocs texte (en séparant les pensées, suggestions et réponse finale)
        text_msg = getattr(sys_msg, "text", None)
        if text_msg and text_msg.parts:
            raw_type = getattr(text_msg, "text_type", None)
            type_name = getattr(raw_type, "name", str(raw_type))
            if "THOUGHT" in type_name or "PROGRESS" in type_name:
                continue
            elif "UNSPECIFIED" in type_name or raw_type == 0:
                for part in text_msg.parts:
                    if part and part.strip():
                        suggestions.append(part.strip())
            else:
                text = "\n\n".join(p.strip() for p in text_msg.parts if p and p.strip())
                if text:
                    final_parts.append(text)

    if generated_sqls:
        print("\n[SQL généré par Conversational Analytics (Couche Gold uniquement)]")
        for sql in generated_sqls:
            print(sql)
            print()

    print("[Réponse Conversational Analytics]")
    print("\n\n".join(final_parts).strip())
    if suggestions:
        print("\n[Questions de suivi suggérées]")
        for s in suggestions:
            print(f"  • {s}")
    print("-" * 72)


def main() -> None:
    if len(sys.argv) < 2:
        question = (
            "Quel est le CTR de Maison Éclat sur Snapchat, Meta et TikTok "
            "entre le 25 octobre 2026 et le 23 novembre 2026 ?"
        )
    else:
        question = " ".join(sys.argv[1:])
    ask(question)


if __name__ == "__main__":
    main()
