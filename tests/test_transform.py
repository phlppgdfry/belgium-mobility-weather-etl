from datetime import UTC, datetime

import pytest

from mobility_etl.quality import validate_station_snapshots
from mobility_etl.transform import transform_station_status, transform_weather


def test_transform_deduplicates_and_derives_demand():
    records = [
        {"city": "Ghent", "observed_at": "2026-08-14T08:00", "temperature_c": 18.0, "precipitation_mm": 0.0, "weather_code": 1, "extracted_at": "2026-08-14T06:00:00+00:00"},
        {"city": "Ghent", "observed_at": "2026-08-14T08:00", "temperature_c": 19.0, "precipitation_mm": 1.0, "weather_code": 61, "extracted_at": "2026-08-14T06:05:00+00:00"},
    ]
    result = transform_weather(records)
    assert len(result) == 1
    assert result.iloc[0].is_rainy
    assert result.iloc[0].estimated_mobility_demand == 108


def test_transform_rejects_empty_input():
    with pytest.raises(ValueError, match="No weather"):
        transform_weather([])


def test_station_transform_derives_availability_state():
    dimensions, snapshots = transform_station_status([{
        "network": "villo", "city": "Brussels", "station_id": "a1", "station_name": "Central",
        "latitude": 50.8, "longitude": 4.3, "capacity": 10, "available_bikes": 0,
        "available_ebikes": 0, "available_docks": 10, "is_renting": True, "is_returning": True,
        "source_updated_at": "2026-08-15T10:00:00+00:00", "snapshot_at": "2026-08-15T10:01:00+00:00",
    }])
    assert len(dimensions) == 1
    assert snapshots.iloc[0].availability_state == "empty"


def test_quality_rejects_too_few_stations():
    _, snapshots = transform_station_status([{
        "network": "villo", "city": "Brussels", "station_id": "a1", "station_name": "Central",
        "latitude": 50.8, "longitude": 4.3, "capacity": 10, "available_bikes": 2,
        "available_ebikes": 0, "available_docks": 8, "is_renting": True, "is_returning": True,
        "source_updated_at": datetime.now(UTC).isoformat(), "snapshot_at": datetime.now(UTC).isoformat(),
    }])
    with pytest.raises(ValueError, match="Expected at least"):
        validate_station_snapshots(snapshots)
