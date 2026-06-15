from pathlib import Path

from dotenv import load_dotenv

from src.real_estate_intelligence.ai.groq_generator import DEFAULT_GROQ_MODEL
from src.real_estate_intelligence.ai.insight_generator import generate_ai_market_brief
from src.real_estate_intelligence.engine.market_analyzer import generate_market_insights
from src.real_estate_intelligence.engine.scoring import build_city_scores, build_neighborhood_scores
from src.real_estate_intelligence.ingest.data_cleaner import clean_listings
from src.real_estate_intelligence.serve.report_generator import generate_report


BASE_DIR = Path(__file__).resolve().parents[2]


def run_pipeline(
    raw_path: Path | None = None,
    use_groq: bool = False,
    groq_model: str = DEFAULT_GROQ_MODEL,
) -> None:
    load_dotenv()
    raw_path = raw_path or BASE_DIR / "data" / "raw" / "listings.csv"
    processed_path = BASE_DIR / "data" / "processed" / "clean_listings.csv"
    scores_path = BASE_DIR / "data" / "processed" / "market_scores.csv"
    insights_path = BASE_DIR / "market_insights.json"
    ai_brief_path = BASE_DIR / "ai_market_brief.json"
    report_path = BASE_DIR / "executive_report.md"

    listings = clean_listings(raw_path, processed_path)
    city_scores = build_city_scores(listings, scores_path)
    neighborhood_scores = build_neighborhood_scores(listings)
    insights = generate_market_insights(listings, insights_path)
    ai_brief = generate_ai_market_brief(
        city_scores,
        neighborhood_scores,
        ai_brief_path,
        use_groq=use_groq,
        groq_model=groq_model,
    )
    generate_report(insights, report_path, ai_brief=ai_brief)

    print(f"Processed listings: {len(listings)}")
    print(f"Wrote: {processed_path}")
    print(f"Wrote: {scores_path}")
    print(f"Wrote: {insights_path}")
    print(f"Wrote: {ai_brief_path}")
    print(f"Wrote: {report_path}")
