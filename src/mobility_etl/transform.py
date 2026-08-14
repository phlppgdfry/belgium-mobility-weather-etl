from __future__ import annotations

import pandas as pd


def transform_weather(records: list[dict]) -> pd.DataFrame:
    """Standardise source fields and derive analysis-ready mobility indicators."""
    frame = pd.DataFrame(records)
    if frame.empty:
        raise ValueError("No weather records were extracted.")
    frame["observed_at"] = pd.to_datetime(frame["observed_at"], format="%Y-%m-%dT%H:%M")
    frame["extracted_at"] = pd.to_datetime(frame["extracted_at"], utc=True)
    frame = frame.drop_duplicates(subset=["city", "observed_at"], keep="last")
    frame["is_rainy"] = frame["precipitation_mm"].gt(0).astype(bool)
    frame["day_of_week"] = frame["observed_at"].dt.day_name()
    frame["hour"] = frame["observed_at"].dt.hour
    commute_bonus = frame["hour"].isin([7, 8, 9, 16, 17, 18]).astype(int) * 20
    rain_penalty = (frame["precipitation_mm"] * 12).clip(upper=55)
    frame["estimated_mobility_demand"] = (100 + commute_bonus - rain_penalty).round().clip(lower=20)
    columns = ["city", "observed_at", "temperature_c", "precipitation_mm", "weather_code", "is_rainy", "day_of_week", "hour", "estimated_mobility_demand", "extracted_at"]
    return frame[columns].sort_values(["city", "observed_at"])

