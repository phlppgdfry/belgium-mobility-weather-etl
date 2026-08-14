import pytest

from mobility_etl.transform import transform_weather


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

