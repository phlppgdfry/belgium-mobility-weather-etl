from __future__ import annotations

from prefect import flow, get_run_logger, task

from .config import database_url
from .extract import extract_all_weather, fetch_villo_stations
from .load import get_engine, load_station_status, load_weather, record_raw_payload
from .quality import validate_station_snapshots
from .transform import transform_station_status, transform_weather


@task(retries=3, retry_delay_seconds=10)
def extract_weather() -> list[dict]:
    return extract_all_weather()


@task
def transform_weather_task(records: list[dict]):
    return transform_weather(records)


@task(retries=2)
def load_weather_task(frame) -> int:
    return load_weather(frame, get_engine(database_url()))


@flow(name="belgium-mobility-weather-etl", log_prints=True)
def mobility_weather_etl() -> int:
    logger = get_run_logger()
    weather_records = extract_weather()
    weather_frame = transform_weather_task(weather_records)
    weather_loaded = load_weather_task(weather_frame)
    station_records, metadata = fetch_villo_stations()
    dimensions, snapshots = transform_station_status(station_records)
    quality = validate_station_snapshots(snapshots)
    engine = get_engine(database_url())
    record_raw_payload("citybikes_villo", snapshots["snapshot_at"].iloc[0], metadata["payload"], engine)
    stations_loaded = load_station_status(dimensions, snapshots, engine)
    logger.info("Weather rows: %s; Villo! snapshots: %s; quality: %s", weather_loaded, stations_loaded, quality)
    return weather_loaded + stations_loaded


def main() -> None:
    mobility_weather_etl()


if __name__ == "__main__":
    main()
