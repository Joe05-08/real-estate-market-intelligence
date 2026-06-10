from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "listing_id",
    "city",
    "neighborhood",
    "property_type",
    "bedrooms",
    "bathrooms",
    "sqft",
    "list_price",
    "estimated_rent",
    "days_on_market",
    "year_built",
    "status",
}


def clean_listings(raw_path: str | Path, processed_path: str | Path) -> pd.DataFrame:
    """Load raw listing data, validate it, add market metrics, and save it."""
    raw_path = Path(raw_path)
    processed_path = Path(processed_path)

    df = pd.read_csv(raw_path)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    numeric_columns = [
        "bedrooms",
        "bathrooms",
        "sqft",
        "list_price",
        "estimated_rent",
        "days_on_market",
        "year_built",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=numeric_columns)
    df = df[df["sqft"] > 0].copy()
    df["price_per_sqft"] = (df["list_price"] / df["sqft"]).round(2)
    df["monthly_rent_yield"] = (df["estimated_rent"] / df["list_price"]).round(4)
    df["annual_rent_yield_pct"] = (df["monthly_rent_yield"] * 12 * 100).round(2)
    df["market_speed"] = pd.cut(
        df["days_on_market"],
        bins=[-1, 21, 45, 10_000],
        labels=["fast", "normal", "slow"],
    )

    processed_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(processed_path, index=False)
    return df
