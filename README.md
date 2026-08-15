# Belgium Bike Share Intelligence ETL

> A production-minded data product that combines Belgian weather forecasts with live Villo! bike-share availability, retains historical snapshots, validates data quality and exposes operational insights.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Prefect](https://img.shields.io/badge/Orchestration-Prefect-024DFD)
![CI](https://github.com/YOUR_GITHUB_USERNAME/belgium-mobility-weather-etl/actions/workflows/quality.yml/badge.svg)

## Why this project

This repository demonstrates the complete ETL lifecycle rather than a one-off notebook:

```text
Open-Meteo + CityBikes/Villo! → Extract (retries) → Validate + Transform → PostgreSQL → dbt marts + Streamlit
```

It is deliberately **idempotent** for weather and **append-only** for live bike-share snapshots. This creates a real historical time series. The weather demand score is an explainable contextual proxy—not claimed as observed bike-trip data:

`100 + 20 during commute hours − (12 × precipitation, capped at 55)`

## Stack

| Concern | Choice | What it demonstrates |
| --- | --- | --- |
| Sources | Open-Meteo + CityBikes/Villo! public APIs | multi-source extraction, timeouts, source normalization |
| Transformation | Pandas + quality gates | validation, de-duplication, derived features |
| Orchestration | Prefect | observable flow, task retries |
| Warehouse | PostgreSQL | schema design and conflict-safe upserts |
| Analytics | dbt + Streamlit | semantic SQL models and stakeholder-friendly output |
| Quality | pytest, Ruff, GitHub Actions | repeatable, automated checks |

## Run locally

Prerequisites: Python 3.11+ and Docker Desktop.

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/belgium-mobility-weather-etl.git
cd belgium-mobility-weather-etl
cp .env.example .env
make up
make install
make run
make dashboard
```

The dashboard opens at `http://localhost:8501`. PostgreSQL is exposed on port `5433`, avoiding conflicts with a database already running on your Mac. Run `make test` and `make lint` before committing. `docker compose up --build` starts PostgreSQL and the dashboard together.

## What the pipeline stores

| Layer | Table | Purpose |
| --- | --- | --- |
| Raw | `raw_ingestion_payload` | Immutable Villo!/CityBikes API payload for replayability |
| Dimension | `dim_bike_station` | Current station name, location and capacity |
| Fact | `fact_station_status` | Append-only availability snapshot per station and run |
| Fact | `fact_mobility_weather` | Forecast weather and contextual demand signal |
| Operations | `etl_run_audit` | Reserved audit table for run-level monitoring |

Before loading, the pipeline rejects a station feed with too few stations, negative values or duplicate snapshots. To make freshness a blocking production gate, set `MAX_SOURCE_STALENESS_MINUTES=180` (or your own threshold); it is disabled locally because public aggregators can publish delayed upstream timestamps.

## Run it automatically

`.github/workflows/scheduled-pipeline.yml` runs hourly and can also be triggered manually. To enable it, create a GitHub environment called `production` and add its `DATABASE_URL` secret, using a hosted PostgreSQL URL (for example Neon, Supabase or Railway). GitHub Actions must be enabled for the repository.

### dbt (optional analytics layer)

Install `dbt-postgres`, copy the example profile to your dbt profiles directory, then run:

```bash
dbt deps --project-dir dbt
dbt test --project-dir dbt
dbt run --project-dir dbt
```

## Data model

`fact_mobility_weather` has one unique row per `(city, observed_at)` and contains raw-enough weather metrics plus analysis-ready fields. `fact_station_status` stores every Villo! reading, allowing you to answer questions such as “which stations are repeatedly empty at 08:30?”

- `temperature_c`, `precipitation_mm`, `weather_code`
- `is_rainy`, `day_of_week`, `hour`
- `estimated_mobility_demand`
- `extracted_at` for lineage and freshness

The dbt mart aggregates those rows into a daily city-demand view.

## Reliability notes

- HTTP extraction has a 20-second timeout and Prefect retries failed requests three times.
- Station data is quality-gated for count, freshness, duplicate keys and impossible negative values.
- Weather loads use conflict-safe updates; Villo! snapshots preserve history.
- Raw source payloads are retained for replayability and debugging.
- Tests cover deduplication, business rules, station state derivation and failing quality gates.

## Next enhancements

- Add station-level anomaly alerts to Slack/Discord.
- Add a geospatial catchment model and weather-to-availability analysis.
- Deploy the dashboard to Streamlit Community Cloud or Render.
- Train a demand forecast once enough historical snapshots are collected.

## Data source

Weather forecast data comes from [Open-Meteo](https://open-meteo.com/). Live Villo! availability comes through the [CityBikes API](https://api.citybik.es/v2/networks/villo), following the [GBFS](https://gbfs.org/) ecosystem. Check each source’s attribution and usage terms before a production deployment.
