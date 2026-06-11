from pathlib import Path
import argparse

from src.real_estate_intelligence.engine.market_analyzer import generate_market_insights
from src.real_estate_intelligence.ingest.data_cleaner import clean_listings
from src.real_estate_intelligence.serve.report_generator import generate_report


BASE_DIR = Path(__file__).resolve().parent


def run_pipeline(raw_path: Path | None = None) -> None:
    raw_path = raw_path or BASE_DIR / "data" / "raw" / "listings.csv"
    processed_path = BASE_DIR / "data" / "processed" / "clean_listings.csv"
    insights_path = BASE_DIR / "market_insights.json"
    report_path = BASE_DIR / "executive_report.md"

    listings = clean_listings(raw_path, processed_path)
    insights = generate_market_insights(listings, insights_path)
    generate_report(insights, report_path)

    print(f"Processed listings: {len(listings)}")
    print(f"Wrote: {processed_path}")
    print(f"Wrote: {insights_path}")
    print(f"Wrote: {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the real-estate market intelligence pipeline.")
    parser.add_argument(
        "--raw-path",
        type=Path,
        default=None,
        help="Input listing CSV. Defaults to data/raw/listings.csv.",
    )
    args = parser.parse_args()
    run_pipeline(raw_path=args.raw_path)
