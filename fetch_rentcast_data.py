import argparse
from pathlib import Path

from dotenv import load_dotenv

from src.real_estate_intelligence.ingest.rentcast_client import (
    RentCastMarket,
    fetch_and_save_rentcast_data,
)


BASE_DIR = Path(__file__).resolve().parent


def parse_market(value: str) -> RentCastMarket:
    try:
        city, state = value.rsplit(",", 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Markets must use the format City,ST") from exc
    return RentCastMarket(city=city.strip(), state=state.strip().upper())


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch and cache RentCast listing data.")
    parser.add_argument(
        "--market",
        action="append",
        type=parse_market,
        default=[],
        help="Market to fetch, formatted as City,ST. Can be provided multiple times.",
    )
    parser.add_argument("--limit", type=int, default=25, help="Listings to request per endpoint.")
    parser.add_argument(
        "--output",
        default=str(BASE_DIR / "data" / "raw" / "rentcast_listings.csv"),
        help="Normalized CSV output path.",
    )
    parser.add_argument(
        "--cache-dir",
        default=str(BASE_DIR / "data" / "raw" / "api_cache"),
        help="Directory for raw cached API responses.",
    )
    args = parser.parse_args()

    load_dotenv()
    markets = args.market or [
        RentCastMarket(city="Austin", state="TX"),
        RentCastMarket(city="Dallas", state="TX"),
        RentCastMarket(city="Denver", state="CO"),
    ]

    df = fetch_and_save_rentcast_data(
        markets=markets,
        output_path=args.output,
        cache_dir=args.cache_dir,
        limit=args.limit,
    )
    print(f"Fetched and normalized {len(df)} listings.")
    print(f"Wrote: {args.output}")
    print(f"Cached raw API responses in: {args.cache_dir}")


if __name__ == "__main__":
    main()
