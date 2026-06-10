# Real Estate Market Intelligence

This is a local learning project modeled after an AI market intelligence pipeline.
It turns real-estate listing data into market metrics, insight cards, an executive report, and a Streamlit dashboard.

## What You Are Building

```text
raw listings CSV
→ clean and enrich data
→ calculate market signals
→ generate insight cards
→ create executive report
→ show dashboard
```

## Step 1: Install Dependencies

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Step 2: Run The Pipeline

```bash
.venv/bin/python run.py
```

This creates:

- `data/processed/clean_listings.csv`
- `market_insights.json`
- `executive_report.md`

## Step 3: Start The Dashboard

```bash
.venv/bin/streamlit run app.py
```

Open:

```text
http://127.0.0.1:8501
```

## How It Works

- `data/raw/listings.csv`: sample real-estate listing data
- `src/real_estate_intelligence/ingest/data_cleaner.py`: validates and enriches listings
- `src/real_estate_intelligence/engine/market_analyzer.py`: finds investment, pricing, demand, and affordability signals
- `src/real_estate_intelligence/serve/report_generator.py`: writes a simple executive report
- `app.py`: Streamlit dashboard
- `run.py`: runs the full pipeline

## Next Improvements

- Add live Zillow/Realtor-style data from an API
- Add city and ZIP-code filters
- Add LLM-generated narrative insights
- Add rent estimate confidence scoring
- Push to GitHub and deploy the dashboard
