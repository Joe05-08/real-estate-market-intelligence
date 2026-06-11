from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd
import requests


BASE_URL = "https://api.rentcast.io/v1"


@dataclass(frozen=True)
class RentCastMarket:
    city: str
    state: str

    @property
    def slug(self) -> str:
        return f"{self.city.lower().replace(' ', '-')}-{self.state.lower()}"


def _headers(api_key: str) -> dict[str, str]:
    return {"X-Api-Key": api_key, "Accept": "application/json"}


def _get_json(endpoint: str, params: dict[str, Any], api_key: str) -> list[dict[str, Any]]:
    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        headers=_headers(api_key),
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError(f"Expected list response from {endpoint}, got {type(payload).__name__}")
    return payload


def fetch_market_listings(
    market: RentCastMarket,
    api_key: str,
    cache_dir: str | Path,
    limit: int = 25,
) -> dict[str, list[dict[str, Any]]]:
    """Fetch sale and rental listings for a market and cache the raw responses."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    base_params = {
        "city": market.city,
        "state": market.state,
        "limit": limit,
    }
    sale_listings = _get_json("listings/sale", base_params, api_key)
    rental_listings = _get_json("listings/rental/long-term", base_params, api_key)

    payload = {
        "sale_listings": sale_listings,
        "rental_listings": rental_listings,
    }
    cache_path = cache_dir / f"rentcast_{market.slug}.json"
    cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _rent_key(listing: dict[str, Any]) -> tuple[str, int | None, str]:
    bedrooms = _number(listing.get("bedrooms"))
    return (
        str(listing.get("zipCode") or ""),
        int(bedrooms) if bedrooms is not None else None,
        str(listing.get("propertyType") or "Unknown"),
    )


def _build_rent_lookup(rental_listings: list[dict[str, Any]]) -> dict[tuple[str, int | None, str], float]:
    grouped: dict[tuple[str, int | None, str], list[float]] = {}
    for listing in rental_listings:
        rent = _number(listing.get("price"))
        if rent is None:
            continue
        grouped.setdefault(_rent_key(listing), []).append(rent)
    return {key: median(values) for key, values in grouped.items() if values}


def _estimated_rent(
    listing: dict[str, Any],
    rent_lookup: dict[tuple[str, int | None, str], float],
    fallback_rent: float | None,
) -> tuple[float | None, str]:
    exact_key = _rent_key(listing)
    if exact_key in rent_lookup:
        return rent_lookup[exact_key], "zip_bedrooms_property_type"

    zip_code, bedrooms, _ = exact_key
    zip_bedroom_values = [
        rent for (rent_zip, rent_bedrooms, _), rent in rent_lookup.items()
        if rent_zip == zip_code and rent_bedrooms == bedrooms
    ]
    if zip_bedroom_values:
        return median(zip_bedroom_values), "zip_bedrooms"

    return fallback_rent, "market_median"


def _fallback_rent_from_price(sale_listing: dict[str, Any], rental_listings: list[dict[str, Any]]) -> float | None:
    sqft = _number(sale_listing.get("squareFootage"))
    if not sqft:
        return None

    rent_per_sqft = []
    for rental in rental_listings:
        rent = _number(rental.get("price"))
        rental_sqft = _number(rental.get("squareFootage"))
        if rent is not None and rental_sqft:
            rent_per_sqft.append(rent / rental_sqft)

    if not rent_per_sqft:
        return None
    return round(median(rent_per_sqft) * sqft, 2)


def normalize_rentcast_payload(payloads: list[dict[str, list[dict[str, Any]]]]) -> pd.DataFrame:
    """Convert cached RentCast responses to this project's listing CSV schema."""
    rows: list[dict[str, Any]] = []

    for payload in payloads:
        rental_listings = payload.get("rental_listings", [])
        sale_listings = payload.get("sale_listings", [])
        rental_prices = [
            rent for rent in (_number(listing.get("price")) for listing in rental_listings)
            if rent is not None
        ]
        fallback_rent = median(rental_prices) if rental_prices else None
        rent_lookup = _build_rent_lookup(rental_listings)

        for listing in sale_listings:
            sqft = _number(listing.get("squareFootage"))
            list_price = _number(listing.get("price"))
            bedrooms = _number(listing.get("bedrooms"))
            bathrooms = _number(listing.get("bathrooms"))
            days_on_market = _number(listing.get("daysOnMarket"))

            if None in (sqft, list_price, bedrooms, bathrooms, days_on_market):
                continue

            estimated_rent, rent_source = _estimated_rent(listing, rent_lookup, fallback_rent)
            if rent_source == "market_median":
                sqft_based_rent = _fallback_rent_from_price(listing, rental_listings)
                if sqft_based_rent is not None:
                    estimated_rent = sqft_based_rent
                    rent_source = "market_rent_per_sqft"
            if estimated_rent is None:
                continue

            zip_code = str(listing.get("zipCode") or "Unknown")
            rows.append(
                {
                    "listing_id": listing.get("id"),
                    "city": listing.get("city"),
                    "neighborhood": f"ZIP {zip_code}",
                    "property_type": listing.get("propertyType") or "Unknown",
                    "bedrooms": int(bedrooms),
                    "bathrooms": bathrooms,
                    "sqft": int(sqft),
                    "list_price": list_price,
                    "estimated_rent": estimated_rent,
                    "days_on_market": int(days_on_market),
                    "year_built": int(_number(listing.get("yearBuilt")) or 0),
                    "status": str(listing.get("status") or "Unknown").lower(),
                    "rent_estimate_source": rent_source,
                }
            )

    return pd.DataFrame(rows)


def fetch_and_save_rentcast_data(
    markets: list[RentCastMarket],
    output_path: str | Path,
    cache_dir: str | Path,
    limit: int = 25,
) -> pd.DataFrame:
    """Fetch RentCast data, cache raw responses, and write a normalized listing CSV."""
    api_key = os.getenv("RENTCAST_API_KEY")
    if not api_key:
        raise RuntimeError("RENTCAST_API_KEY is missing. Add it to a local .env file.")

    payloads = [
        fetch_market_listings(market=market, api_key=api_key, cache_dir=cache_dir, limit=limit)
        for market in markets
    ]
    df = normalize_rentcast_payload(payloads)
    if df.empty:
        raise RuntimeError("RentCast returned no usable sale listings after normalization.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df
