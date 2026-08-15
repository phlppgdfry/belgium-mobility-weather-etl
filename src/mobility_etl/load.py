from __future__ import annotations

import json

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DDL = """
CREATE TABLE IF NOT EXISTS fact_mobility_weather (
  city TEXT NOT NULL, observed_at TIMESTAMP NOT NULL,
  temperature_c DOUBLE PRECISION NOT NULL, precipitation_mm DOUBLE PRECISION NOT NULL,
  weather_code INTEGER NOT NULL, is_rainy BOOLEAN NOT NULL, day_of_week TEXT NOT NULL,
  hour INTEGER NOT NULL, estimated_mobility_demand DOUBLE PRECISION NOT NULL,
  extracted_at TIMESTAMPTZ NOT NULL, PRIMARY KEY (city, observed_at)
);
CREATE TABLE IF NOT EXISTS dim_bike_station (
  station_id TEXT PRIMARY KEY, network TEXT NOT NULL, city TEXT NOT NULL, station_name TEXT NOT NULL,
  latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL, capacity INTEGER NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS fact_station_status (
  station_id TEXT NOT NULL REFERENCES dim_bike_station(station_id), network TEXT NOT NULL,
  snapshot_at TIMESTAMPTZ NOT NULL, source_updated_at TIMESTAMPTZ,
  available_bikes INTEGER NOT NULL, available_ebikes INTEGER NOT NULL, available_docks INTEGER NOT NULL,
  is_renting BOOLEAN NOT NULL, is_returning BOOLEAN NOT NULL, occupancy_pct DOUBLE PRECISION NOT NULL,
  availability_state TEXT NOT NULL, PRIMARY KEY (station_id, snapshot_at)
);
CREATE TABLE IF NOT EXISTS etl_run_audit (
  run_id UUID PRIMARY KEY, pipeline_name TEXT NOT NULL, started_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ, status TEXT NOT NULL, rows_loaded INTEGER NOT NULL DEFAULT 0,
  source_station_count INTEGER, details JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS raw_ingestion_payload (
  source TEXT NOT NULL, extracted_at TIMESTAMPTZ NOT NULL, payload JSONB NOT NULL,
  PRIMARY KEY (source, extracted_at)
);
"""


def get_engine(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True)


def load_weather(frame: pd.DataFrame, engine: Engine) -> int:
    """Idempotently upsert transformed records into the analytics fact table."""
    initialize_schema(engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE TEMP TABLE staging_weather (LIKE fact_mobility_weather) ON COMMIT DROP"))
        frame.to_sql("staging_weather", connection, if_exists="append", index=False)
        connection.execute(text("""INSERT INTO fact_mobility_weather SELECT * FROM staging_weather
            ON CONFLICT (city, observed_at) DO UPDATE SET
            temperature_c = EXCLUDED.temperature_c, precipitation_mm = EXCLUDED.precipitation_mm,
            weather_code = EXCLUDED.weather_code, is_rainy = EXCLUDED.is_rainy,
            day_of_week = EXCLUDED.day_of_week, hour = EXCLUDED.hour,
            estimated_mobility_demand = EXCLUDED.estimated_mobility_demand,
            extracted_at = EXCLUDED.extracted_at"""))
    return len(frame)


def initialize_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        for statement in DDL.split(";"):
            if statement.strip():
                connection.execute(text(statement))


def load_station_status(dimensions: pd.DataFrame, snapshots: pd.DataFrame, engine: Engine) -> int:
    """Upsert station attributes and retain every real-time availability snapshot."""
    initialize_schema(engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE TEMP TABLE staging_stations (LIKE dim_bike_station) ON COMMIT DROP"))
        dimensions.to_sql("staging_stations", connection, if_exists="append", index=False)
        connection.execute(text("""INSERT INTO dim_bike_station (network, city, station_id, station_name, latitude, longitude, capacity)
            SELECT network, city, station_id, station_name, latitude, longitude, capacity FROM staging_stations
            ON CONFLICT (station_id) DO UPDATE SET network = EXCLUDED.network, city = EXCLUDED.city,
              station_name = EXCLUDED.station_name, latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude,
              capacity = EXCLUDED.capacity, updated_at = NOW()"""))
        connection.execute(text("CREATE TEMP TABLE staging_status (LIKE fact_station_status) ON COMMIT DROP"))
        snapshots.to_sql("staging_status", connection, if_exists="append", index=False)
        connection.execute(text("""INSERT INTO fact_station_status
            SELECT * FROM staging_status ON CONFLICT (station_id, snapshot_at) DO NOTHING"""))
    return len(snapshots)


def record_raw_payload(source: str, extracted_at: pd.Timestamp, payload: dict, engine: Engine) -> None:
    initialize_schema(engine)
    with engine.begin() as connection:
        connection.execute(text("""INSERT INTO raw_ingestion_payload (source, extracted_at, payload)
            VALUES (:source, :extracted_at, CAST(:payload AS jsonb)) ON CONFLICT DO NOTHING"""),
            {"source": source, "extracted_at": extracted_at.to_pydatetime(), "payload": json.dumps(payload)})
