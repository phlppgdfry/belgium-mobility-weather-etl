from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    name: str
    latitude: float
    longitude: float


CITIES = (
    City("Antwerp", 51.2194, 4.4025), City("Brussels", 50.8503, 4.3517),
    City("Ghent", 51.0543, 3.7174), City("Leuven", 50.8798, 4.7005),
    City("Liège", 50.6326, 5.5797),
)

CITYBIKES_VILLO_URL = "https://api.citybik.es/v2/networks/villo"
MIN_EXPECTED_STATIONS = 100
MAX_SOURCE_STALENESS_MINUTES = int(os.getenv("MAX_SOURCE_STALENESS_MINUTES", "0"))


def database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql+psycopg://mobility:mobility@localhost:5433/mobility")
