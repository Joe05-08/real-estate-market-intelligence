from __future__ import annotations

import json
import os
from typing import Any

import requests


GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


def _compact_scores(city_rankings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
        "market",
        "city",
        "state",
        "overall_market_score",
        "investment_score",
        "affordability_score",
        "market_heat_score",
        "buyer_leverage_score",
        "median_price",
        "avg_rent_yield",
        "median_days_on_market",
    ]
    return [{field: row.get(field) for field in fields if field in row} for row in city_rankings]


def build_groq_prompt(base_brief: dict[str, Any]) -> str:
    compact_input = {
        "executive_summary": base_brief["executive_summary"],
        "top_neighborhood_opportunity": base_brief["top_neighborhood_opportunity"],
        "top_negotiation_neighborhood": base_brief["top_negotiation_neighborhood"],
        "persona_recommendations": base_brief["persona_recommendations"],
        "city_rankings": _compact_scores(base_brief["city_rankings"]),
    }

    return f"""
You are a real-estate market intelligence analyst.

Use the structured market scores below to write a concise executive market brief.
Do not invent data. Only use numbers and markets from the input.

Return only valid JSON with this schema:
{{
  "executive_summary": "string",
  "top_opportunity": "string",
  "risk_watch": "string",
  "persona_recommendations": [
    {{
      "persona": "string",
      "recommendation": "string",
      "reasoning": "string"
    }}
  ],
  "data_caveat": "string"
}}

STRUCTURED_INPUT:
{json.dumps(compact_input, indent=2)}
""".strip()


def generate_groq_brief(
    base_brief: dict[str, Any],
    model: str = DEFAULT_GROQ_MODEL,
) -> dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to .env or your environment.")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You generate concise real-estate market intelligence in valid JSON.",
            },
            {"role": "user", "content": build_groq_prompt(base_brief)},
        ],
        "temperature": 0.2,
        "max_tokens": 900,
        "response_format": {"type": "json_object"},
    }

    response = requests.post(
        GROQ_CHAT_COMPLETIONS_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=45,
    )
    response.raise_for_status()
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    generated = json.loads(content)
    generated["llm_metadata"] = {
        "provider": "Groq",
        "model": model,
        "usage": result.get("usage", {}),
    }
    return generated
