# Real Estate Market Intelligence

A Python market-intelligence dashboard that turns real-estate listing data into investor-focused metrics, market scorecards, optional Groq-powered generative AI recommendations, and an executive report.

The project demonstrates a complete real-estate analytics workflow using structured listing data, reproducible processing, and an interactive Streamlit dashboard.

## Live Dashboard

Open the deployed Streamlit dashboard here:

https://real-estate-market-intelligence-gyvpjmbbxqn498ru2kxgnn.streamlit.app/

The Docker and `127.0.0.1` links below are for running the project on your own computer. External viewers should use the deployed Streamlit link above.

## Project Overview

The project follows a simple analytics workflow:

```text
raw/API listing data
-> clean and enrich data
-> calculate market signals
-> score markets by persona
-> generate AI market brief
-> create executive report
-> show Streamlit dashboard
```

It answers questions such as:

- Which neighborhoods have the strongest rental yield?
- Which markets are moving fastest?
- Which areas have the highest price per square foot?
- Where might buyers have negotiation leverage?
- Which city is strongest for investors, buyers, sellers, or negotiation-focused buyers?
- How do markets compare across Texas, Colorado, Florida, and New Jersey?

## Features

- Cleans raw real-estate listing data with Pandas
- Calculates `price_per_sqft`, rental yield, and market-speed labels
- Scores markets for investment, affordability, market heat, and buyer leverage
- Generates transparent AI-style market recommendations from scored features
- Optionally calls Groq to generate a real LLM-written market brief from structured scores
- Writes an executive Markdown report
- Displays state/city filters, KPIs, charts, AI insights, scorecards, and data tables in Streamlit
- Includes Docker support for reproducible local runs

## Tech Stack

- Python
- Pandas
- Streamlit
- Plotly
- Groq API, optional
- Docker

## Repository Structure

```text
real_estate_market_intelligence/
  data/
    raw/listings.csv
    processed/
  src/
    real_estate_intelligence/
      ingest/data_cleaner.py
      engine/market_analyzer.py
      engine/scoring.py
      ai/groq_generator.py
      ai/insight_generator.py
      serve/report_generator.py
  app.py
  run.py
  requirements.txt
  Dockerfile
  docker-compose.yml
```

## Data

The repository includes a demo listing dataset:

```text
data/raw/listings.csv
```

Each row represents one listing with fields such as:

- city
- state
- neighborhood
- property type
- bedrooms and bathrooms
- square footage
- list price
- estimated monthly rent
- days on market
- year built
- listing status

The cleaning step enriches the dataset with:

- `price_per_sqft`
- `monthly_rent_yield`
- `annual_rent_yield_pct`
- `market_speed`

The scoring layer then creates:

- `investment_score`
- `affordability_score`
- `market_heat_score`
- `buyer_leverage_score`
- `overall_market_score`

## Local Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Run the pipeline:

```bash
.venv/bin/python run.py
```

To generate an additional real LLM-written brief with Groq:

```bash
.venv/bin/python run.py --use-groq
```

This requires `GROQ_API_KEY` in `.env`. The dashboard does not call Groq on every click; it reads the saved JSON output.

This creates:

```text
data/processed/clean_listings.csv
data/processed/market_scores.csv
market_insights.json
ai_market_brief.json
executive_report.md
```

Start the dashboard:

```bash
.venv/bin/streamlit run app.py
```

Open:

```text
http://127.0.0.1:8501
```

## Optional API Ingestion

The project can fetch real-estate listings from RentCast and cache the raw API response locally. API calls are made only when the fetch script is run manually; the dashboard reads processed local files.

Create a local `.env` file:

```bash
cp .env.example .env
```

Add your RentCast API key:

```env
RENTCAST_API_KEY=your_rentcast_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

Fetch one or more markets:

```bash
.venv/bin/python fetch_rentcast_data.py --market Austin,TX --limit 10
```

Run the pipeline from the fetched data:

```bash
.venv/bin/python run.py --raw-path data/raw/rentcast_listings.csv
```

API cache files and normalized API CSVs are intentionally ignored by Git:

```text
data/raw/api_cache/
data/raw/rentcast_listings.csv
```

## Streamlit Cloud Deployment

The app is deployment-safe because `app.py` can generate demo dashboard outputs from `data/raw/listings.csv` when processed files are missing.

Use these settings in Streamlit Community Cloud:

```text
Repository: Joe05-08/real-estate-market-intelligence
Branch: main
Main file path: app.py
```

The deployed app uses the committed demo dataset by default. Keep API keys out of GitHub; add secrets in Streamlit only if you later add a controlled API or LLM workflow.

## Docker

Build and run with Docker Compose:

```bash
docker compose up --build
```

The dashboard will be available at:

```text
http://127.0.0.1:8502
```

This Docker URL only works on the machine running Docker. For sharing the project with recruiters or external viewers, use the deployed Streamlit dashboard link at the top of this README.

## How The Pipeline Works

`run.py` is the project entry point. It calls three stages:

1. `data_cleaner.py`
   Loads the raw CSV, validates columns, converts numeric fields, calculates real-estate metrics, and writes the processed CSV.

2. `market_analyzer.py`
   Groups the cleaned listings by city and neighborhood, calculates market-level signals, and generates insight cards.

3. `scoring.py`
   Creates city-level and neighborhood-level scores for investment quality, affordability, market heat, and buyer leverage.

4. `insight_generator.py`
   Converts the scored market signals into transparent AI-style recommendations for investors, first-time buyers, sellers, and negotiation-focused buyers. When `--use-groq` is enabled, it also stores a Groq-generated natural-language brief.

5. `groq_generator.py`
   Sends structured market scores to Groq's OpenAI-compatible chat completions endpoint and returns a JSON market brief. This is optional and only runs when explicitly requested.

6. `report_generator.py`
   Converts the generated insights into a Markdown executive report.

The dashboard in `app.py` reads the processed CSV, market score CSV, insight JSON, and AI market brief JSON. It does not call external APIs on every click.

## Current Scope

- Uses a local demo dataset for reproducible analysis
- Includes demo markets across Texas, Colorado, Florida, and New Jersey
- Generates insights from transparent scoring and optional Groq LLM generation
- Runs locally with Python or Docker

## Future Enhancements

- Add Census or FRED data for neighborhood/economic context
- Add scheduled data refresh jobs for API-backed deployments
- Add tests for cleaning and insight generation
- Add richer historical trend analysis

## Portfolio Summary

This project demonstrates an end-to-end data product workflow:

```text
data ingestion -> cleaning -> feature engineering -> market scoring -> AI-style insight generation -> dashboard/reporting
```
