import json
import inspect
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.real_estate_intelligence.pipeline import run_pipeline


BASE_DIR = Path(__file__).resolve().parent
RAW_DEMO_PATH = BASE_DIR / "data" / "raw" / "listings.csv"
DATA_PATH = BASE_DIR / "data" / "processed" / "clean_listings.csv"
SCORES_PATH = BASE_DIR / "data" / "processed" / "market_scores.csv"
INSIGHTS_PATH = BASE_DIR / "market_insights.json"
AI_BRIEF_PATH = BASE_DIR / "ai_market_brief.json"


st.set_page_config(
    page_title="Real Estate Market Intelligence",
    page_icon="🏠",
    layout="wide",
)


def _file_mtime(path: Path) -> float:
    return path.stat().st_mtime if path.exists() else 0


def ensure_pipeline_outputs() -> None:
    """Create demo outputs on first app boot, including cloud deployments."""
    if DATA_PATH.exists() and SCORES_PATH.exists() and INSIGHTS_PATH.exists() and AI_BRIEF_PATH.exists():
        return
    if not RAW_DEMO_PATH.exists():
        return
    run_pipeline(raw_path=RAW_DEMO_PATH)


def _stretch_kwargs(streamlit_method) -> dict[str, str | bool]:
    version_parts = tuple(int(part) for part in st.__version__.split(".")[:2])
    if version_parts >= (1, 50) and "width" in inspect.signature(streamlit_method).parameters:
        return {"width": "stretch"}
    return {"use_container_width": True}


@st.cache_data
def load_data(
    data_mtime: float,
    scores_mtime: float,
    insights_mtime: float,
    ai_brief_mtime: float,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None, list[dict], dict]:
    listings = pd.read_csv(DATA_PATH) if DATA_PATH.exists() else None
    scores = pd.read_csv(SCORES_PATH) if SCORES_PATH.exists() else None
    insights = json.loads(INSIGHTS_PATH.read_text(encoding="utf-8")) if INSIGHTS_PATH.exists() else []
    ai_brief = json.loads(AI_BRIEF_PATH.read_text(encoding="utf-8")) if AI_BRIEF_PATH.exists() else {}
    return listings, scores, insights, ai_brief


def render_kpis(filtered: pd.DataFrame) -> None:
    metric_cols = st.columns(4)
    metric_cols[0].metric("Listings", f"{len(filtered):,}")
    metric_cols[1].metric("Median Price", f"${filtered['list_price'].median():,.0f}")
    metric_cols[2].metric("Median $/Sqft", f"${filtered['price_per_sqft'].median():,.0f}")
    metric_cols[3].metric("Avg Yield", f"{filtered['annual_rent_yield_pct'].mean():.1f}%")


def render_overview(filtered: pd.DataFrame, insights: list[dict]) -> None:
    render_kpis(filtered)
    st.divider()

    left, right = st.columns(2)
    with left:
        st.subheader("Price by Neighborhood")
        price_chart = px.bar(
            filtered.groupby(["city", "neighborhood"], as_index=False)["list_price"].median(),
            x="neighborhood",
            y="list_price",
            color="city",
            labels={"list_price": "Median Price", "neighborhood": "Neighborhood"},
        )
        st.plotly_chart(price_chart, **_stretch_kwargs(st.plotly_chart))

    with right:
        st.subheader("Yield vs Market Speed")
        scatter = px.scatter(
            filtered,
            x="days_on_market",
            y="annual_rent_yield_pct",
            size="list_price",
            color="city",
            hover_data=["neighborhood", "property_type", "bedrooms", "sqft"],
            labels={"days_on_market": "Days on Market", "annual_rent_yield_pct": "Annual Rent Yield %"},
        )
        st.plotly_chart(scatter, **_stretch_kwargs(st.plotly_chart))

    st.subheader("Strategic Insights")
    for insight in insights:
        with st.container(border=True):
            st.markdown(f"### {insight['title']}")
            st.write(f"**Type:** {insight['insight_type']}")
            st.info(insight["summary"])
            st.success(insight["recommendation"])
            st.progress(insight["confidence_score"], text=f"Confidence: {int(insight['confidence_score'] * 100)}%")


def render_ai_brief(ai_brief: dict) -> None:
    if not ai_brief:
        st.warning("AI market brief is not available. Run the pipeline to generate it.")
        return

    generation_method = ai_brief.get("generation_method", "scoring_rules")
    if generation_method == "scoring_rules_plus_groq_llm":
        st.caption("Generated with market scoring plus a Groq-hosted LLM.")
    else:
        st.caption("Generated with the free explainable scoring engine. Run the pipeline with --use-groq for a real LLM brief.")

    if "generative_ai_brief" in ai_brief:
        groq_brief = ai_brief["generative_ai_brief"]
        st.subheader("Generative AI Brief")
        st.info(groq_brief["executive_summary"])
        st.write(f"**Top opportunity:** {groq_brief['top_opportunity']}")
        st.write(f"**Risk watch:** {groq_brief['risk_watch']}")
        st.write(f"**Data caveat:** {groq_brief['data_caveat']}")
        for recommendation in groq_brief["persona_recommendations"]:
            with st.container(border=True):
                st.markdown(f"### {recommendation['persona']}")
                st.write(recommendation["recommendation"])
                st.caption(recommendation["reasoning"])
        metadata = groq_brief.get("llm_metadata", {})
        if metadata:
            st.caption(f"LLM provider: {metadata.get('provider')} | Model: {metadata.get('model')}")

    st.subheader("Executive AI Market Brief")
    st.info(ai_brief["executive_summary"])

    opportunity, leverage = st.columns(2)
    with opportunity:
        with st.container(border=True):
            item = ai_brief["top_neighborhood_opportunity"]
            st.markdown(f"### {item['headline']}")
            st.write(item["name"])
            st.success(item["reasoning"])
    with leverage:
        with st.container(border=True):
            item = ai_brief["top_negotiation_neighborhood"]
            st.markdown(f"### {item['headline']}")
            st.write(item["name"])
            st.warning(item["reasoning"])

    st.subheader("Persona Recommendations")
    columns = st.columns(2)
    for index, recommendation in enumerate(ai_brief["persona_recommendations"]):
        with columns[index % 2]:
            with st.container(border=True):
                st.markdown(f"### {recommendation['persona']}")
                st.write(f"**Best market:** {recommendation['best_market']}")
                st.info(recommendation["headline"])
                st.write(recommendation["reasoning"])
                st.success(recommendation["next_step"])


def render_market_scores(scores: pd.DataFrame | None, selected_states: list[str], selected_cities: list[str]) -> None:
    if scores is None:
        st.warning("Market scores are not available. Run the pipeline to generate them.")
        return

    filtered_scores = scores[
        scores["state"].isin(selected_states)
        & scores["city"].isin(selected_cities)
    ]
    score_columns = [
        "investment_score",
        "affordability_score",
        "market_heat_score",
        "buyer_leverage_score",
        "overall_market_score",
    ]

    st.subheader("City Scorecard")
    score_chart = px.bar(
        filtered_scores.melt(
            id_vars=["city"],
            value_vars=score_columns,
            var_name="score_type",
            value_name="score",
        ),
        x="city",
        y="score",
        color="score_type",
        barmode="group",
        labels={"score": "Score", "city": "City", "score_type": "Score Type"},
    )
    st.plotly_chart(score_chart, **_stretch_kwargs(st.plotly_chart))

    display_columns = [
        "state",
        "city",
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
    st.dataframe(filtered_scores[display_columns], **_stretch_kwargs(st.dataframe))


ensure_pipeline_outputs()
df, scores, insights, ai_brief = load_data(
    _file_mtime(DATA_PATH),
    _file_mtime(SCORES_PATH),
    _file_mtime(INSIGHTS_PATH),
    _file_mtime(AI_BRIEF_PATH),
)

st.title("Real Estate Market Intelligence")
st.caption("A market scoring and AI-style intelligence dashboard built from real-estate listing data.")

if df is None:
    st.error("Could not generate dashboard data from the demo dataset.")
    st.stop()

city_filter = st.sidebar.multiselect("City", sorted(df["city"].unique()), default=sorted(df["city"].unique()))
state_filter = st.sidebar.multiselect("State", sorted(df["state"].unique()), default=sorted(df["state"].unique()))
property_filter = st.sidebar.multiselect(
    "Property Type",
    sorted(df["property_type"].unique()),
    default=sorted(df["property_type"].unique()),
)

filtered = df[
    df["state"].isin(state_filter)
    & df["city"].isin(city_filter)
    & df["property_type"].isin(property_filter)
]

selected_cities = sorted(filtered["city"].unique())

if filtered.empty:
    st.warning("No listings match the selected filters. Choose at least one city and property type.")
    st.stop()

overview_tab, ai_tab, scores_tab, data_tab = st.tabs(
    ["Overview", "AI Market Insights", "Market Scores", "Data Explorer"]
)

with overview_tab:
    render_overview(filtered, insights)

with ai_tab:
    render_ai_brief(ai_brief)

with scores_tab:
    render_market_scores(scores, state_filter, selected_cities)

with data_tab:
    st.dataframe(filtered, **_stretch_kwargs(st.dataframe))
