from pathlib import Path
import argparse

from src.real_estate_intelligence.ai.groq_generator import DEFAULT_GROQ_MODEL
from src.real_estate_intelligence.pipeline import run_pipeline


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the real-estate market intelligence pipeline.")
    parser.add_argument(
        "--raw-path",
        type=Path,
        default=None,
        help="Input listing CSV. Defaults to data/raw/listings.csv.",
    )
    parser.add_argument(
        "--use-groq",
        action="store_true",
        help="Use Groq to generate an additional real LLM market brief. Requires GROQ_API_KEY.",
    )
    parser.add_argument(
        "--groq-model",
        default=DEFAULT_GROQ_MODEL,
        help="Groq model to use when --use-groq is enabled.",
    )
    args = parser.parse_args()
    try:
        run_pipeline(raw_path=args.raw_path, use_groq=args.use_groq, groq_model=args.groq_model)
    except RuntimeError as error:
        raise SystemExit(str(error)) from error
