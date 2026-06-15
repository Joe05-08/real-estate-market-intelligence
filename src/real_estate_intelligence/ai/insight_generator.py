from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.real_estate_intelligence.ai.groq_generator import DEFAULT_GROQ_MODEL, generate_groq_brief


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _pct(value: float) -> str:
    return f"{value:.1f}%"


def _score(value: float) -> str:
    return f"{value:.0f}/100"


def _market(row: pd.Series) -> str:
    return str(getattr(row, "market", row.city))


def generate_ai_market_brief(
    city_scores: pd.DataFrame,
    neighborhood_scores: pd.DataFrame,
    output_path: str | Path,
    use_groq: bool = False,
    groq_model: str = DEFAULT_GROQ_MODEL,
) -> dict:
    """Generate transparent AI-style market narratives from scored metrics."""
    output_path = Path(output_path)

    top_investor_city = city_scores.sort_values("investment_score", ascending=False).iloc[0]
    top_affordable_city = city_scores.sort_values("affordability_score", ascending=False).iloc[0]
    hottest_city = city_scores.sort_values("market_heat_score", ascending=False).iloc[0]
    leverage_city = city_scores.sort_values("buyer_leverage_score", ascending=False).iloc[0]
    top_neighborhood = neighborhood_scores.sort_values("investment_score", ascending=False).iloc[0]
    leverage_neighborhood = neighborhood_scores.sort_values("buyer_leverage_score", ascending=False).iloc[0]

    top_investor_market = _market(top_investor_city)
    top_affordable_market = _market(top_affordable_city)
    hottest_market = _market(hottest_city)
    leverage_market = _market(leverage_city)

    if top_investor_market == top_affordable_market:
        executive_summary = (
            f"{top_investor_market} currently leads both investor screening and affordability in this "
            f"sample. {hottest_market} shows the strongest demand signal, and {leverage_market} "
            "offers the best buyer-leverage setup based on sampled listings."
        )
    else:
        executive_summary = (
            f"{top_investor_market} currently leads for investor screening, while "
            f"{top_affordable_market} is the strongest affordability candidate. "
            f"{hottest_market} shows the strongest demand signal, and {leverage_market} "
            "offers the best buyer-leverage setup based on sampled listings."
        )

    city_rankings = city_scores[
        [
            "city",
            "state",
            "market",
            "overall_market_score",
            "investment_score",
            "affordability_score",
            "market_heat_score",
            "buyer_leverage_score",
            "median_price",
            "avg_rent_yield",
            "median_days_on_market",
        ]
    ].to_dict(orient="records")

    recommendations = [
        {
            "persona": "Investor",
            "best_market": top_investor_market,
            "headline": f"{top_investor_market} ranks highest for investor screening",
            "reasoning": (
                f"It combines a {_pct(top_investor_city.avg_rent_yield)} average rent yield, "
                f"{_money(top_investor_city.median_price)} median entry price, and an investment "
                f"score of {_score(top_investor_city.investment_score)}."
            ),
            "next_step": (
                "Shortlist listings with above-market yield, then validate tax, insurance, HOA, vacancy, "
                "and repair assumptions before underwriting."
            ),
        },
        {
            "persona": "First-time Buyer",
            "best_market": top_affordable_market,
            "headline": f"{top_affordable_market} is the most affordable market in this sample",
            "reasoning": (
                f"It has an affordability score of {_score(top_affordable_city.affordability_score)} "
                f"with a median list price of {_money(top_affordable_city.median_price)}."
            ),
            "next_step": (
                "Use this market as the first comparison point, then filter by commute, school quality, "
                "monthly payment, and inspection risk."
            ),
        },
        {
            "persona": "Seller",
            "best_market": hottest_market,
            "headline": f"{hottest_market} has the strongest demand signal",
            "reasoning": (
                f"It has a market heat score of {_score(hottest_city.market_heat_score)} and a median "
                f"{hottest_city.median_days_on_market:.0f} days on market."
            ),
            "next_step": (
                "Use comparable sales to test pricing power, but monitor active inventory so the listing "
                "does not sit stale."
            ),
        },
        {
            "persona": "Negotiation-focused Buyer",
            "best_market": leverage_market,
            "headline": f"{leverage_market} may offer the best negotiation setup",
            "reasoning": (
                f"It has a buyer leverage score of {_score(leverage_city.buyer_leverage_score)} and "
                f"a median {leverage_city.median_days_on_market:.0f} days on market."
            ),
            "next_step": (
                "Look for older listings, price reductions, seller credits, and inspection leverage."
            ),
        },
    ]

    brief = {
        "executive_summary": executive_summary,
        "top_neighborhood_opportunity": {
            "name": f"{top_neighborhood.neighborhood}, {_market(top_neighborhood)}",
            "headline": f"{top_neighborhood.neighborhood} is the strongest neighborhood opportunity",
            "reasoning": (
                f"It has an investment score of {_score(top_neighborhood.investment_score)}, "
                f"{_pct(top_neighborhood.avg_rent_yield)} average yield, and a median price of "
                f"{_money(top_neighborhood.median_price)}."
            ),
        },
        "top_negotiation_neighborhood": {
            "name": f"{leverage_neighborhood.neighborhood}, {_market(leverage_neighborhood)}",
            "headline": f"{leverage_neighborhood.neighborhood} may offer buyer leverage",
            "reasoning": (
                f"It has a buyer leverage score of {_score(leverage_neighborhood.buyer_leverage_score)} "
                f"and a median {leverage_neighborhood.median_days_on_market:.0f} days on market."
            ),
        },
        "persona_recommendations": recommendations,
        "city_rankings": city_rankings,
        "generation_method": "scoring_rules",
    }

    if use_groq:
        brief["generative_ai_brief"] = generate_groq_brief(brief, model=groq_model)
        brief["generation_method"] = "scoring_rules_plus_groq_llm"

    output_path.write_text(json.dumps(brief, indent=2), encoding="utf-8")
    return brief
