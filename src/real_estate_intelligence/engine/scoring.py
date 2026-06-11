from __future__ import annotations

from pathlib import Path

import pandas as pd


def _score(series: pd.Series, *, higher_is_better: bool = True) -> pd.Series:
    low = series.min()
    high = series.max()
    if pd.isna(low) or pd.isna(high) or high == low:
        return pd.Series(50.0, index=series.index)

    normalized = (series - low) / (high - low)
    if not higher_is_better:
        normalized = 1 - normalized
    return (normalized * 100).round(1)


def _weighted_score(parts: dict[str, tuple[pd.Series, float]]) -> pd.Series:
    total_weight = sum(weight for _, weight in parts.values())
    weighted = sum(series * weight for series, weight in parts.values()) / total_weight
    return weighted.round(1)


def build_city_scores(df: pd.DataFrame, output_path: str | Path | None = None) -> pd.DataFrame:
    """Create explainable city-level scores for investment, affordability, demand, and leverage."""
    scores = (
        df.groupby("city")
        .agg(
            listing_count=("listing_id", "count"),
            median_price=("list_price", "median"),
            median_ppsf=("price_per_sqft", "median"),
            median_days_on_market=("days_on_market", "median"),
            avg_rent_yield=("annual_rent_yield_pct", "mean"),
            avg_estimated_rent=("estimated_rent", "mean"),
        )
        .reset_index()
    )

    yield_score = _score(scores["avg_rent_yield"], higher_is_better=True)
    price_score = _score(scores["median_price"], higher_is_better=False)
    ppsf_score = _score(scores["median_ppsf"], higher_is_better=False)
    speed_score = _score(scores["median_days_on_market"], higher_is_better=False)
    leverage_days_score = _score(scores["median_days_on_market"], higher_is_better=True)

    scores["investment_score"] = _weighted_score(
        {
            "yield": (yield_score, 0.5),
            "entry_price": (price_score, 0.25),
            "market_speed": (speed_score, 0.25),
        }
    )
    scores["affordability_score"] = _weighted_score(
        {
            "entry_price": (price_score, 0.65),
            "price_per_sqft": (ppsf_score, 0.35),
        }
    )
    scores["market_heat_score"] = _weighted_score(
        {
            "market_speed": (speed_score, 0.7),
            "yield": (yield_score, 0.3),
        }
    )
    scores["buyer_leverage_score"] = _weighted_score(
        {
            "stale_inventory": (leverage_days_score, 0.7),
            "entry_price": (price_score, 0.3),
        }
    )
    scores["overall_market_score"] = _weighted_score(
        {
            "investment": (scores["investment_score"], 0.35),
            "affordability": (scores["affordability_score"], 0.2),
            "heat": (scores["market_heat_score"], 0.25),
            "leverage": (scores["buyer_leverage_score"], 0.2),
        }
    )

    score_columns = [
        "investment_score",
        "affordability_score",
        "market_heat_score",
        "buyer_leverage_score",
        "overall_market_score",
    ]
    scores[score_columns] = scores[score_columns].clip(lower=0, upper=100)
    scores = scores.sort_values("overall_market_score", ascending=False).reset_index(drop=True)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        scores.to_csv(output_path, index=False)

    return scores


def build_neighborhood_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Score neighborhoods so the AI brief can explain local opportunities."""
    neighborhoods = (
        df.groupby(["city", "neighborhood"])
        .agg(
            listing_count=("listing_id", "count"),
            median_price=("list_price", "median"),
            median_ppsf=("price_per_sqft", "median"),
            median_days_on_market=("days_on_market", "median"),
            avg_rent_yield=("annual_rent_yield_pct", "mean"),
        )
        .reset_index()
    )

    neighborhoods["investment_score"] = _weighted_score(
        {
            "yield": (_score(neighborhoods["avg_rent_yield"], higher_is_better=True), 0.55),
            "entry_price": (_score(neighborhoods["median_price"], higher_is_better=False), 0.25),
            "speed": (_score(neighborhoods["median_days_on_market"], higher_is_better=False), 0.2),
        }
    )
    neighborhoods["buyer_leverage_score"] = _weighted_score(
        {
            "stale_inventory": (_score(neighborhoods["median_days_on_market"], higher_is_better=True), 0.7),
            "entry_price": (_score(neighborhoods["median_price"], higher_is_better=False), 0.3),
        }
    )

    return neighborhoods.sort_values("investment_score", ascending=False).reset_index(drop=True)
