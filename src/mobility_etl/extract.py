from __future__ import annotations

from datetime import UTC, datetime

import requests

from .config import CITIES, CITYBIKES_VILLO_URL

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather(city_name: str, latitude: float, longitude: float) -> list[dict]:
    """Fetch the hourly forecast for one city and return source-tagged records."""
    response = requests.get(OPEN_METEO_URL, params={
        "latitude": latitude, "longitude": longitude,
        "hourly": "temperature_2m,precipitation,weather_code", "forecast_days": 3,
        "timezone": "Europe/Brussels",
    }, timeout=20)
    response.raise_for_status()
    hourly = response.json()["hourly"]
    extracted_at = datetime.now(UTC).isoformat()
    return [{"city": city_name, "observed_at": observed_at, "temperature_c": temperature,
             "precipitation_mm": precipitation, "weather_code": weather_code, "extracted_at": extracted_at}
            for observed_at, temperature, precipitation, weather_code in zip(
                hourly["time"], hourly["temperature_2m"], hourly["precipitation"], hourly["weather_code"], strict=True)]


def extract_all_weather() -> list[dict]:
    return [record for city in CITIES for record in fetch_weather(city.name, city.latitude, city.longitude)]


def fetch_villo_stations() -> tuple[list[dict], dict]:
    """Fetch real-time Villo! station availability through the public CityBikes API."""
    response = requests.get(CITYBIKES_VILLO_URL, timeout=20)
    response.raise_for_status()
    payload = response.json()
    extracted_at = datetime.now(UTC).isoformat()
    network = payload["network"]
    records = []
    for station in network["stations"]:
        extra = station.get("extra", {})
        records.append(
            {
                "network": "villo", "city": "Brussels", "station_id": station["id"],
                "station_name": station["name"], "latitude": station["latitude"],
                "longitude": station["longitude"], "capacity": extra.get("slots"),
                "available_bikes": station.get("free_bikes", 0),
                "available_ebikes": extra.get("ebikes", 0),
                "available_docks": station.get("empty_slots", 0),
                "is_renting": extra.get("renting", False), "is_returning": extra.get("returning", False),
                "source_updated_at": extra.get("last_updated") or station.get("timestamp"),
                "snapshot_at": extracted_at,
            }
        )
    metadata = {"network": network.get("name", "villo"), "station_count": len(records), "payload": payload}
    return records, metadata
