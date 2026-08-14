# Belgium Mobility Weather ETL

> A production-minded data-engineering portfolio project: collect public weather forecasts for Belgian cities, transform them into transparent mobility-demand signals, and load them into PostgreSQL for analysis.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Prefect](https://img.shields.io/badge/Orchestration-Prefect-024DFD)
![CI](https://github.com/YOUR_GITHUB_USERNAME/belgium-mobility-weather-etl/actions/workflows/quality.yml/badge.svg)

## Why this project

This repository demonstrates the complete ETL lifecycle rather than a one-off notebook:

```text
Open-Meteo API → Extract (retries) → Transform (Pandas) → Load (PostgreSQL upsert) → Dashboard / dbt marts
```

It is deliberately **idempotent**: a second run updates the same city/timestamp records rather than duplicating them. The demand score is an explainable demo proxy—not claimed as observed bike-trip data:

`100 + 20 during commute hours − (12 × precipitation, capped at 55)`

## Stack

| Concern | Choice | What it demonstrates |
| --- | --- | --- |
| Source | Open-Meteo public API | API extraction, timeouts, source normalization |
| Transformation | Pandas | validation, de-duplication, derived features |
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

The dashboard opens at `http://localhost:8501`. Run `make test` and `make lint` before committing.

### dbt (optional analytics layer)

Install `dbt-postgres`, copy the example profile to your dbt profiles directory, then run:

```bash
dbt deps --project-dir dbt
dbt test --project-dir dbt
dbt run --project-dir dbt
```

## Data model

`fact_mobility_weather` has one unique row per `(city, observed_at)` and contains raw-enough weather metrics plus analysis-ready fields:

- `temperature_c`, `precipitation_mm`, `weather_code`
- `is_rainy`, `day_of_week`, `hour`
- `estimated_mobility_demand`
- `extracted_at` for lineage and freshness

The dbt mart aggregates those rows into a daily city-demand view.

## Reliability notes

- HTTP extraction has a 20-second timeout and Prefect retries failed requests three times.
- Empty data fails fast instead of silently loading no records.
- The load uses a temporary staging table and PostgreSQL `ON CONFLICT` upsert.
- Tests cover duplicate handling, business-rule derivation, and empty-input validation.

## Next enhancements

- Add real GBFS bike-share station feeds as a second source.
- Persist raw JSON payloads in object storage for replayability.
- Add Great Expectations/Soda checks and Slack alerts.
- Deploy scheduled Prefect runs and the dashboard to cloud infrastructure.

## Data source

Weather forecast data comes from [Open-Meteo](https://open-meteo.com/). Check its attribution and usage terms before a production deployment.

