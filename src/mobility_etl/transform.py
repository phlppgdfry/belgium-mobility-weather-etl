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


def transform_station_status(records: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create slowly-changing station attributes and append-only availability snapshots."""
    frame = pd.DataFrame(records)
    if frame.empty:
        raise ValueError("No bike-share station records were extracted.")
    frame["snapshot_at"] = pd.to_datetime(frame["snapshot_at"], utc=True)
    frame["source_updated_at"] = pd.to_datetime(frame["source_updated_at"], utc=True, errors="coerce")
    frame["capacity"] = pd.to_numeric(frame["capacity"], errors="coerce").fillna(0).astype(int)
    for column in ["available_bikes", "available_ebikes", "available_docks"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0).astype(int)
    frame["occupancy_pct"] = (frame["available_bikes"] / frame["capacity"].replace(0, pd.NA) * 100).fillna(0).round(1)
    frame["availability_state"] = "healthy"
    frame.loc[frame["available_bikes"].eq(0), "availability_state"] = "empty"
    frame.loc[frame["available_docks"].eq(0), "availability_state"] = "full"
    frame.loc[~(frame["is_renting"] & frame["is_returning"]), "availability_state"] = "unavailable"
    dimensions = frame[["network", "city", "station_id", "station_name", "latitude", "longitude", "capacity"]].drop_duplicates("station_id")
    snapshots = frame[["network", "station_id", "snapshot_at", "source_updated_at", "available_bikes", "available_ebikes", "available_docks", "is_renting", "is_returning", "occupancy_pct", "availability_state"]]
    return dimensions, snapshots
