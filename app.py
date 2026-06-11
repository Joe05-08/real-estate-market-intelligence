import json
import inspect
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from run import run_pipeline


BASE_DIR = Path(__file__).resolve().parent
RAW_DEMO_PATH = BASE_DIR / "data" / "raw" / "listings.csv"
DATA_PATH = BASE_DIR / "data" / "processed" / "clean_listings.csv"
INSIGHTS_PATH = BASE_DIR / "market_insights.json"


st.set_page_config(
    page_title="Real Estate Market Intelligence",
    page_icon="🏠",
    layout="wide",
)


def _file_mtime(path: Path) -> float:
    return path.stat().st_mtime if path.exists() else 0


def ensure_pipeline_outputs() -> None:
    """Create demo outputs on first app boot, including cloud deployments."""
    if DATA_PATH.exists() and INSIGHTS_PATH.exists():
        return
    if not RAW_DEMO_PATH.exists():
        return
    run_pipeline(raw_path=RAW_DEMO_PATH)


def _stretch_kwargs(streamlit_method) -> dict[str, str | bool]:
    if "width" in inspect.signature(streamlit_method).parameters:
        return {"width": "stretch"}
    return {"use_container_width": True}


@st.cache_data
def load_data(data_mtime: float, insights_mtime: float) -> tuple[pd.DataFrame | None, list[dict]]:
    listings = pd.read_csv(DATA_PATH) if DATA_PATH.exists() else None
    insights = json.loads(INSIGHTS_PATH.read_text(encoding="utf-8")) if INSIGHTS_PATH.exists() else []
    return listings, insights


ensure_pipeline_outputs()
df, insights = load_data(_file_mtime(DATA_PATH), _file_mtime(INSIGHTS_PATH))

st.title("Real Estate Market Intelligence")
st.caption("A local market analysis dashboard built from real-estate listing data.")

if df is None:
    st.error("Could not generate dashboard data from the demo dataset.")
    st.stop()

city_filter = st.sidebar.multiselect("City", sorted(df["city"].unique()), default=sorted(df["city"].unique()))
property_filter = st.sidebar.multiselect(
    "Property Type",
    sorted(df["property_type"].unique()),
    default=sorted(df["property_type"].unique()),
)

filtered = df[df["city"].isin(city_filter) & df["property_type"].isin(property_filter)]

if filtered.empty:
    st.warning("No listings match the selected filters. Choose at least one city and property type.")
    st.stop()

metric_cols = st.columns(4)
metric_cols[0].metric("Listings", f"{len(filtered):,}")
metric_cols[1].metric("Median Price", f"${filtered['list_price'].median():,.0f}")
metric_cols[2].metric("Median $/Sqft", f"${filtered['price_per_sqft'].median():,.0f}")
metric_cols[3].metric("Avg Yield", f"{filtered['annual_rent_yield_pct'].mean():.1f}%")

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

with st.expander("View Clean Listing Data"):
    st.dataframe(filtered, **_stretch_kwargs(st.dataframe))
