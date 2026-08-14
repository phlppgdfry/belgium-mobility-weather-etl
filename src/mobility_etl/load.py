from __future__ import annotations

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
"""


def get_engine(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True)


def load_weather(frame: pd.DataFrame, engine: Engine) -> int:
    """Idempotently upsert transformed records into the analytics fact table."""
    with engine.begin() as connection:
        connection.execute(text(DDL))
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

