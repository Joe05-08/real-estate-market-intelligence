from pathlib import Path
import argparse

from src.real_estate_intelligence.pipeline import run_pipeline


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
