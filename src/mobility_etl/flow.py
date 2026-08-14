from __future__ import annotations

from prefect import flow, get_run_logger, task

from .config import database_url
from .extract import extract_all_weather
from .load import get_engine, load_weather
from .transform import transform_weather


@task(retries=3, retry_delay_seconds=10)
def extract() -> list[dict]:
    return extract_all_weather()


@task
def transform(records: list[dict]):
    return transform_weather(records)


@task(retries=2)
def load(frame) -> int:
    return load_weather(frame, get_engine(database_url()))


@flow(name="belgium-mobility-weather-etl", log_prints=True)
def mobility_weather_etl() -> int:
    logger = get_run_logger()
    records = extract()
    frame = transform(records)
    loaded = load(frame)
    logger.info("Loaded %s rows across %s cities", loaded, frame["city"].nunique())
    return loaded


def main() -> None:
    mobility_weather_etl()


if __name__ == "__main__":
    main()

