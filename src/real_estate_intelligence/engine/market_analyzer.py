from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _pct(value: float) -> str:
    return f"{value:.1f}%"


def _market_time_signal(row: pd.Series) -> dict:
    if row.median_days <= 21:
        return {
            "title": f"{row.neighborhood} is moving fastest",
            "type": "Demand Signal",
            "summary": (
                f"{row.neighborhood}, {row.city} has a median of {row.median_days:.0f} days on market, "
                "suggesting stronger near-term buyer demand than slower neighborhoods."
            ),
            "recommendation": (
                "Buyers should prepare financing and offer terms before touring. Sellers in this area "
                "can test firmer pricing if comparable sales support it."
            ),
            "confidence": 0.84,
        }

    if row.median_days <= 60:
        return {
            "title": f"{row.neighborhood} has the shortest market time",
            "type": "Relative Demand Signal",
            "summary": (
                f"{row.neighborhood}, {row.city} has the shortest median market time in this dataset "
                f"at {row.median_days:.0f} days."
            ),
            "recommendation": (
                "Treat this as a relative demand signal, then compare against recent comps and local "
                "inventory before assuming strong pricing power."
            ),
            "confidence": 0.78,
        }

    return {
        "title": f"{row.neighborhood} is the least stale segment",
        "type": "Inventory Quality Signal",
        "summary": (
            f"{row.neighborhood}, {row.city} has the shortest median market time in this dataset, "
            f"but it is still {row.median_days:.0f} days. That suggests the fetched listings are stale "
            "or the sampled inventory is slow-moving."
        ),
        "recommendation": (
            "Use this result as a data-quality flag. Refresh the API cache, widen the market sample, "
            "or filter for more recent listings before making demand conclusions."
        ),
        "confidence": 0.62,
    }


def generate_market_insights(df: pd.DataFrame, output_path: str | Path) -> list[dict]:
    """Generate simple, explainable real-estate market insights."""
    output_path = Path(output_path)

    neighborhood = (
        df.groupby(["city", "neighborhood"])
        .agg(
            median_price=("list_price", "median"),
            median_ppsf=("price_per_sqft", "median"),
            median_days=("days_on_market", "median"),
            avg_yield=("annual_rent_yield_pct", "mean"),
            listing_count=("listing_id", "count"),
        )
        .reset_index()
    )

    city = (
        df.groupby("city")
        .agg(
            median_price=("list_price", "median"),
            median_ppsf=("price_per_sqft", "median"),
            avg_days=("days_on_market", "mean"),
            avg_yield=("annual_rent_yield_pct", "mean"),
            listing_count=("listing_id", "count"),
        )
        .reset_index()
    )

    best_yield = neighborhood.sort_values("avg_yield", ascending=False).iloc[0]
    fastest = neighborhood.sort_values("median_days", ascending=True).iloc[0]
    premium = neighborhood.sort_values("median_ppsf", ascending=False).iloc[0]
    value_city = city.sort_values(["median_price", "avg_yield"], ascending=[True, False]).iloc[0]
    slow = neighborhood.sort_values("median_days", ascending=False).iloc[0]
    market_time = _market_time_signal(fastest)
    has_single_city = len(city) == 1

    insights = [
        {
            "title": f"{best_yield.neighborhood} has the strongest rental yield",
            "insight_type": "Investor Opportunity",
            "summary": (
                f"{best_yield.neighborhood}, {best_yield.city} shows an average annual rent "
                f"yield of {_pct(best_yield.avg_yield)}, the highest in the current dataset."
            ),
            "recommendation": (
                "Prioritize this area for rental-property screening, then validate taxes, HOA fees, "
                "vacancy assumptions, and repair costs before making an offer."
            ),
            "confidence_score": 0.88,
            "supporting_data": best_yield.to_dict(),
        },
        {
            "title": market_time["title"],
            "insight_type": market_time["type"],
            "summary": market_time["summary"],
            "recommendation": market_time["recommendation"],
            "confidence_score": market_time["confidence"],
            "supporting_data": fastest.to_dict(),
        },
        {
            "title": f"{premium.neighborhood} is the price-per-square-foot premium market",
            "insight_type": "Pricing Power",
            "summary": (
                f"{premium.neighborhood}, {premium.city} has the highest median price per square foot "
                f"at {_money(premium.median_ppsf)}."
            ),
            "recommendation": (
                "Use this area as a premium benchmark. Investors should be cautious unless rents, "
                "appreciation, or redevelopment upside justify the entry price."
            ),
            "confidence_score": 0.82,
            "supporting_data": premium.to_dict(),
        },
        {
            "title": (
                f"{value_city.city} market snapshot"
                if has_single_city
                else f"{value_city.city} offers the lowest median entry price"
            ),
            "insight_type": "Affordability Signal",
            "summary": (
                f"{value_city.city} has a median listing price of {_money(value_city.median_price)} "
                f"and averages {_pct(value_city.avg_yield)} yield."
                if has_single_city
                else (
                    f"{value_city.city} has the lowest city-level median listing price at "
                    f"{_money(value_city.median_price)} while averaging {_pct(value_city.avg_yield)} yield."
                )
            ),
            "recommendation": (
                "Use this city-level snapshot as a baseline, then add more markets for stronger "
                "cross-market comparison."
                if has_single_city
                else (
                    "Position this city as the first screen for budget-sensitive buyers or early-stage "
                    "investors comparing multiple markets."
                )
            ),
            "confidence_score": 0.8,
            "supporting_data": value_city.to_dict(),
        },
        {
            "title": f"{slow.neighborhood} may have negotiation room",
            "insight_type": "Buyer Leverage",
            "summary": (
                f"{slow.neighborhood}, {slow.city} has the slowest median market time at "
                f"{slow.median_days:.0f} days."
            ),
            "recommendation": (
                "Look for stale listings, price reductions, and seller concessions. Slow market time "
                "can create room for inspection credits or lower offers."
            ),
            "confidence_score": 0.78,
            "supporting_data": slow.to_dict(),
        },
    ]

    output_path.write_text(json.dumps(insights, indent=2), encoding="utf-8")
    return insights
