from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from .config import MAX_SOURCE_STALENESS_MINUTES, MIN_EXPECTED_STATIONS


def validate_station_snapshots(snapshots: pd.DataFrame) -> dict[str, int | float]:
    """Fail fast on broken or stale source data before it reaches the warehouse."""
    if len(snapshots) < MIN_EXPECTED_STATIONS:
        raise ValueError(f"Expected at least {MIN_EXPECTED_STATIONS} stations; received {len(snapshots)}.")
    numeric = ["available_bikes", "available_ebikes", "available_docks", "occupancy_pct"]
    if (snapshots[numeric] < 0).any().any():
        raise ValueError("Station availability cannot be negative.")
    if snapshots.duplicated(["station_id", "snapshot_at"]).any():
        raise ValueError("Duplicate station snapshots detected.")
    latest_source = snapshots["source_updated_at"].dropna().max()
    if pd.notna(latest_source):
        age = (datetime.now(UTC) - latest_source.to_pydatetime()).total_seconds() / 60
        if age > MAX_SOURCE_STALENESS_MINUTES:
            raise ValueError(f"Bike-share source is stale ({age:.0f} minutes old).")
    return {
        "stations": len(snapshots), "empty_stations": int(snapshots.available_bikes.eq(0).sum()),
        "full_stations": int(snapshots.available_docks.eq(0).sum()),
        "avg_occupancy_pct": float(snapshots.occupancy_pct.mean().round(1)),
    }
