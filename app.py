import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "processed" / "clean_listings.csv"
INSIGHTS_PATH = BASE_DIR / "market_insights.json"


st.set_page_config(
    page_title="Real Estate Market Intelligence",
    page_icon="🏠",
    layout="wide",
)


@st.cache_data
def load_data() -> tuple[pd.DataFrame | None, list[dict]]:
    listings = pd.read_csv(DATA_PATH) if DATA_PATH.exists() else None
    insights = json.loads(INSIGHTS_PATH.read_text(encoding="utf-8")) if INSIGHTS_PATH.exists() else []
    return listings, insights


df, insights = load_data()

st.title("Real Estate Market Intelligence")
st.caption("A local AI-style market analysis dashboard built from listing data.")

if df is None:
    st.error("Run `python run.py` first to generate processed data and insights.")
    st.stop()

city_filter = st.sidebar.multiselect("City", sorted(df["city"].unique()), default=sorted(df["city"].unique()))
property_filter = st.sidebar.multiselect(
    "Property Type",
    sorted(df["property_type"].unique()),
    default=sorted(df["property_type"].unique()),
)

filtered = df[df["city"].isin(city_filter) & df["property_type"].isin(property_filter)]

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
    st.plotly_chart(price_chart, use_container_width=True)

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
    st.plotly_chart(scatter, use_container_width=True)

st.subheader("Strategic Insights")
for insight in insights:
    with st.container(border=True):
        st.markdown(f"### {insight['title']}")
        st.write(f"**Type:** {insight['insight_type']}")
        st.info(insight["summary"])
        st.success(insight["recommendation"])
        st.progress(insight["confidence_score"], text=f"Confidence: {int(insight['confidence_score'] * 100)}%")

with st.expander("View Clean Listing Data"):
    st.dataframe(filtered, use_container_width=True)
